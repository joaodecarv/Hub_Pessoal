"""Transaction CRUD under /api/banco/transactions.

The write endpoints take a plain dict body and validate it by hand so every 422
carries one readable Portuguese sentence in `detail` (pydantic's default is a list
of English error objects, which the side panel cannot show as-is).
"""
import calendar
from datetime import date

from fastapi import APIRouter, Body, HTTPException, Query, Response

from banco import db, repositories
from banco.models import Transaction, TransactionKind

from app.banco_view.adapter import _connect

router = APIRouter(prefix="/transactions")


def _to_dict(t: Transaction, goal_id: int | None) -> dict:
    return {
        "id": t.id,
        "date": t.date.isoformat(),
        "amount_cents": t.amount_cents,
        "kind": t.kind.value,
        "description": t.description,
        "account_id": t.account_id,
        "category_id": t.category_id,
        "notes": t.notes,
        "is_fixed_override": t.is_fixed_override,
        "goal_id": goal_id,
    }


def _parse(conn, body: dict) -> tuple[Transaction, int | None]:
    """Validate the request body against the database; return the Transaction and
    its goal_id, or raise a 422 listing every problem found."""
    errors: list[str] = []

    amount = body.get("amount_cents")
    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        errors.append("Valor deve ser maior que zero")

    try:
        parsed_date = date.fromisoformat(body.get("date"))
    except (TypeError, ValueError):
        parsed_date = None
        errors.append("Data inválida")

    try:
        kind = TransactionKind(body.get("kind"))
    except ValueError:
        kind = None
        errors.append("Tipo deve ser receita, despesa ou poupança")

    description = body.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("Descrição é obrigatória")

    account_id = body.get("account_id")
    if account_id is None:
        errors.append("Conta é obrigatória")
    elif repositories.AccountRepository(conn).get(account_id) is None:
        errors.append("Conta não encontrada")

    category_id = body.get("category_id")
    if category_id is not None:
        category = repositories.CategoryRepository(conn).get(category_id)
        if category is None:
            errors.append("Categoria não encontrada")
        elif kind is not None and category.kind != kind:
            errors.append("Categoria não corresponde ao tipo da transação")

    is_fixed_override = body.get("is_fixed_override")
    if is_fixed_override is not None and not isinstance(is_fixed_override, bool):
        errors.append("Fixa/variável deve ser verdadeiro, falso ou vazio")

    goal_id = body.get("goal_id")
    if goal_id is not None:
        if repositories.GoalRepository(conn).get(goal_id) is None:
            errors.append("Meta não encontrada")
        elif kind != TransactionKind.SAVINGS:
            errors.append("Meta só pode ser usada em transações de poupança")

    if errors:
        raise HTTPException(422, "; ".join(errors))

    return Transaction(
        date=parsed_date,
        amount_cents=amount,
        kind=kind,
        description=description.strip(),
        account_id=account_id,
        category_id=category_id,
        is_fixed_override=is_fixed_override,
        notes=body.get("notes") or "",
    ), goal_id


def _sync_goal(conn, tx_id: int, goal_id: int | None) -> None:
    goals = repositories.GoalRepository(conn)
    if goal_id is None:
        goals.remove_contribution(tx_id)
    else:
        goals.add_contribution(goal_id, tx_id)


def _get_or_404(conn, tx_id: int) -> Transaction:
    tx = repositories.TransactionRepository(conn).get(tx_id)
    if tx is None:
        raise HTTPException(404, "Transação não encontrada")
    return tx


@router.get("/options")
def get_options():
    """Everything the transaction form and filter bar choose from, in one call.
    Declared before "/{tx_id}" so "options" is not parsed as an id."""
    conn = _connect()
    try:
        return {
            "accounts": [
                {"id": a.id, "name": a.name, "kind": a.kind.value}
                for a in repositories.AccountRepository(conn).list()
            ],
            "categories": [
                {"id": c.id, "name": c.name, "kind": c.kind.value,
                 "color": c.color, "is_fixed": c.is_fixed}
                for c in repositories.CategoryRepository(conn).list()
            ],
            "goals": [
                {"id": g.id, "name": g.name, "archived": g.archived}
                for g in repositories.GoalRepository(conn).list(include_archived=True)
            ],
        }
    finally:
        conn.close()


@router.get("")
def list_transactions(
    response: Response,
    year: int | None = None,
    month: int | None = Query(None, ge=1, le=12),
    account_id: int | None = None,
    category_id: int | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Newest first. The body is the page; the total number of rows matching the
    filters is in the X-Total-Count header so the body stays a plain array."""
    date_from = date_to = None
    if month is not None and year is None:
        raise HTTPException(422, "Informe o ano junto com o mês")
    if year is not None:
        first_month, last_month = (month, month) if month else (1, 12)
        date_from = date(year, first_month, 1)
        date_to = date(year, last_month, calendar.monthrange(year, last_month)[1])

    conn = _connect()
    try:
        matching = repositories.TransactionRepository(conn).list(
            date_from=date_from, date_to=date_to,
            account_id=account_id, category_id=category_id,
            search=q or None,
        )
        goal_of = dict(conn.execute("SELECT transaction_id, goal_id FROM goal_contributions").fetchall())
        response.headers["X-Total-Count"] = str(len(matching))
        return [_to_dict(t, goal_of.get(t.id)) for t in matching[offset:offset + limit]]
    finally:
        conn.close()


@router.post("", status_code=201)
def create_transaction(body: dict = Body(...)):
    conn = _connect()
    try:
        tx, goal_id = _parse(conn, body)
        with db.transaction(conn):
            repositories.TransactionRepository(conn).add(tx)
            _sync_goal(conn, tx.id, goal_id)
        return _to_dict(tx, goal_id)
    finally:
        conn.close()


@router.get("/{tx_id}")
def get_transaction(tx_id: int):
    conn = _connect()
    try:
        tx = _get_or_404(conn, tx_id)
        return _to_dict(tx, repositories.GoalRepository(conn).contribution_for(tx_id))
    finally:
        conn.close()


@router.put("/{tx_id}")
def update_transaction(tx_id: int, body: dict = Body(...)):
    conn = _connect()
    try:
        _get_or_404(conn, tx_id)
        tx, goal_id = _parse(conn, body)
        tx.id = tx_id
        with db.transaction(conn):
            repositories.TransactionRepository(conn).update(tx)
            _sync_goal(conn, tx_id, goal_id)
        return _to_dict(tx, goal_id)
    finally:
        conn.close()


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: int):
    conn = _connect()
    try:
        _get_or_404(conn, tx_id)
        with db.transaction(conn):
            repositories.TransactionRepository(conn).delete(tx_id)
        return Response(status_code=204)
    finally:
        conn.close()
