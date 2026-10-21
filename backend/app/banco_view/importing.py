"""Statement import under /api/banco/import: a stateless preview, then a commit.

Preview parses the uploaded file and writes nothing. Commit receives the rows the
user kept (categories possibly edited) and writes them in one SQLite transaction.
Like transactions.py, errors are a single readable Portuguese sentence in `detail`.
"""
import csv
import dataclasses
import io
import json
import re
import tempfile
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile

from banco import db, repositories
from banco.importers import import_file
from banco.importers.csv_generic import CsvMapping
from banco.models import Transaction, TransactionKind
from banco.services import RuleService

from app.banco_view.common import (
    connection, is_positive_int, raise_422,
)

router = APIRouter(prefix="/import")

_SAMPLE_ROWS = 3


def _decode(content: bytes) -> tuple[str, str]:
    """(text, encoding). utf-8-sig swallows a BOM; latin-1 never fails, which suits
    the older Brazilian bank exports."""
    try:
        return content.decode("utf-8-sig"), "utf-8-sig"
    except UnicodeDecodeError:
        return content.decode("latin-1"), "latin-1"


def _describe_csv(content: bytes) -> dict:
    """What the mapping step needs: header, a few sample rows and a guessed
    encoding/delimiter."""
    text, encoding = _decode(content)
    try:
        delimiter = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|").delimiter
    except csv.Error:
        delimiter = ","
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=delimiter) if r]
    if not rows:
        raise HTTPException(422, "O arquivo CSV está vazio")
    return {
        "columns": rows[0],
        "sample": rows[1:1 + _SAMPLE_ROWS],
        "suggested": {"encoding": encoding, "delimiter": delimiter},
    }


_MAPPING_STRINGS = ("date_format", "decimal_separator", "thousands_separator", "encoding", "delimiter")
_MAPPING_BOOLS = ("has_header", "invert_sign")
_MAPPING_COLUMNS = ("date_col", "description_col", "amount_col", "debit_col", "credit_col")


def _build_mapping(raw) -> CsvMapping:
    """Check a mapping coming from the client and turn it into a CsvMapping."""
    if not isinstance(raw, dict):
        raise HTTPException(422, "Mapeamento inválido")
    fields = {f.name for f in dataclasses.fields(CsvMapping)}
    values = {k: v for k, v in raw.items() if k in fields}

    for name in _MAPPING_COLUMNS:
        v = values.get(name)
        if v is not None and (isinstance(v, bool) or not isinstance(v, (str, int)) or v == ""):
            raise HTTPException(422, f"Mapeamento inválido: coluna '{name}' incorreta")
    for name in _MAPPING_STRINGS:
        if name in values and (not isinstance(values[name], str) or values[name] == ""):
            raise HTTPException(422, f"Mapeamento inválido: '{name}' incorreto")
    for name in _MAPPING_BOOLS:
        if name in values and not isinstance(values[name], bool):
            raise HTTPException(422, f"Mapeamento inválido: '{name}' incorreto")
    if values.get("date_col") is None:
        raise HTTPException(422, "Mapeamento inválido: informe a coluna da data")
    if values.get("description_col") is None:
        raise HTTPException(422, "Mapeamento inválido: informe a coluna da descrição")
    if values.get("amount_col") is None and values.get("debit_col") is None and values.get("credit_col") is None:
        raise HTTPException(422, "Mapeamento inválido: informe a coluna do valor")
    return CsvMapping(**values)


def _csv_error(exc: Exception) -> str:
    """Translate the importer's failures into something readable."""
    if isinstance(exc, KeyError):
        return f"Coluna {exc} não encontrada no arquivo. Confira o mapeamento"
    if isinstance(exc, IndexError):
        return "Há linhas com menos colunas do que o mapeamento espera. Confira o mapeamento"
    if isinstance(exc, UnicodeDecodeError):
        return "A codificação do arquivo não bate com o mapeamento"
    message = str(exc)
    if m := re.match(r"time data '(.*)' does not match format '(.*)'", message):
        return f"Data '{m[1]}' não bate com o formato {m[2]}. Confira o mapeamento"
    if m := re.match(r"Could not parse amount '(.*)'", message):
        return f"Valor '{m[1]}' inválido. Confira o mapeamento"
    return "Não foi possível ler o CSV com este mapeamento"


def _parse_file(account, filename: str, content: bytes, mapping: CsvMapping | None) -> list[Transaction]:
    suffix = Path(filename).suffix.lower()
    if suffix not in (".ofx", ".csv"):
        raise HTTPException(422, "Formato não suportado. Envie um arquivo .ofx ou .csv")
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(content)
        tmp.flush()
        try:
            parsed = import_file(tmp.name, account, mapping=mapping)
        except Exception as exc:
            if suffix == ".csv":
                raise HTTPException(422, _csv_error(exc))
            raise HTTPException(422, "Não foi possível ler o arquivo OFX. Confira se é um extrato válido")
    if not parsed:
        raise HTTPException(422, "Nenhuma transação encontrada no arquivo")
    return parsed


def _already_imported(conn, import_hash: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM transactions WHERE import_hash = ?", (import_hash,)
    ).fetchone() is not None


@router.post("/preview")
async def preview(
    account_id: int = Form(...),
    file: UploadFile = File(...),
    mapping: str | None = Form(None),   # JSON CsvMapping; wins over the one saved for the account
    remap: bool = Form(False),          # CSV: ask for the columns even if a mapping is saved
):
    content = await file.read()
    filename = file.filename or ""
    with connection() as conn:
        account = repositories.AccountRepository(conn).get(account_id)
        if account is None:
            raise HTTPException(422, "Conta não encontrada")

        csv_mapping = None
        saved = repositories.CsvMappingRepository(conn).get(account_id)
        if Path(filename).suffix.lower() == ".csv":
            if mapping:
                try:
                    csv_mapping = _build_mapping(json.loads(mapping))
                except json.JSONDecodeError:
                    raise HTTPException(422, "Mapeamento inválido")
            elif not remap:
                csv_mapping = saved
            if csv_mapping is None:
                return {
                    "needs_mapping": True,
                    "mapping": dataclasses.asdict(saved) if saved else None,
                    **_describe_csv(content),
                }

        parsed = _parse_file(account, filename, content, csv_mapping)
        categories = {c.id: c for c in repositories.CategoryRepository(conn).list()}
        rules = RuleService(conn)
        seen: set[str] = set()
        rows = []
        for t in parsed:
            suggested = rules.apply(t.description)
            if suggested is not None and categories[suggested].kind != t.kind:
                suggested = None  # a rule must not file an expense under an income category
            rows.append({
                "date": t.date.isoformat(),
                "amount_cents": t.amount_cents,
                "kind": t.kind.value,
                "description": t.description,
                "import_hash": t.import_hash,
                "category_id": suggested,
                # Already in the database, or a repeat of an earlier row in this file.
                "duplicate": t.import_hash in seen or _already_imported(conn, t.import_hash),
            })
            seen.add(t.import_hash)
        return {
            "needs_mapping": False,
            "mapping": dataclasses.asdict(csv_mapping) if csv_mapping else None,
            "rows": rows,
        }


def _parse_rows(conn, account_id: int, raw_rows) -> list[Transaction]:
    """Validate the committed rows; raise one 422 listing every problem found."""
    errors: list[str] = []
    categories = {c.id: c for c in repositories.CategoryRepository(conn).list()}
    transactions: list[Transaction] = []

    for n, row in enumerate(raw_rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"Linha {n}: formato inválido")
            continue
        problems: list[str] = []

        amount = row.get("amount_cents")
        if not is_positive_int(amount):
            problems.append("valor deve ser maior que zero")
        try:
            parsed_date = date.fromisoformat(row.get("date"))
        except (TypeError, ValueError):
            problems.append("data inválida")
        try:
            kind = TransactionKind(row.get("kind"))
        except ValueError:
            kind = None
            problems.append("tipo inválido")
        description = row.get("description")
        if not isinstance(description, str) or not description.strip():
            problems.append("descrição é obrigatória")
        import_hash = row.get("import_hash")
        if not isinstance(import_hash, str) or not import_hash:
            problems.append("identificador de importação ausente")
        category_id = row.get("category_id")
        if category_id is not None:
            category = categories.get(category_id)
            if category is None:
                problems.append("categoria não encontrada")
            elif kind is not None and category.kind != kind:
                problems.append("categoria não corresponde ao tipo")

        if problems:
            errors.append(f"Linha {n}: " + ", ".join(problems))
            continue
        transactions.append(Transaction(
            date=parsed_date, amount_cents=amount, kind=kind, description=description.strip(),
            account_id=account_id, category_id=category_id, import_hash=import_hash,
        ))

    raise_422(errors)
    return transactions


@router.post("/commit")
def commit(body: dict = Body(...)):
    with connection() as conn:
        account_id = body.get("account_id")
        if repositories.AccountRepository(conn).get(account_id) is None:
            raise HTTPException(422, "Conta não encontrada")
        raw_rows = body.get("rows")
        if not isinstance(raw_rows, list) or not raw_rows:
            raise HTTPException(422, "Nenhuma linha selecionada para importar")
        transactions = _parse_rows(conn, account_id, raw_rows)
        mapping = body.get("mapping")
        csv_mapping = _build_mapping(mapping) if mapping is not None else None

        imported = skipped = 0
        seen: set[str] = set()
        with db.transaction(conn):
            if csv_mapping is not None:
                repositories.CsvMappingRepository(conn).save(account_id, csv_mapping)
            tx_repo = repositories.TransactionRepository(conn)
            for tx in transactions:
                if tx.import_hash in seen or _already_imported(conn, tx.import_hash):
                    skipped += 1
                    continue
                seen.add(tx.import_hash)
                tx_repo.add(tx)
                imported += 1
        return {"imported": imported, "skipped": skipped}
