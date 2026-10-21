"""OFX/CSV import (preview + commit) through the HTTP API."""
import json
import sqlite3
from pathlib import Path

from app import config

FIXTURES = Path(__file__).parent / "fixtures"
PREVIEW = "/api/banco/import/preview"
COMMIT = "/api/banco/import/commit"
TRANSACTIONS = "/api/banco/transactions"
SEED_COUNT = 7

CSV_MAPPING = {
    "date_col": "Data", "description_col": "Histórico", "amount_col": "Valor",
    "date_format": "%d/%m/%Y", "decimal_separator": ",", "thousands_separator": ".",
    "has_header": True, "encoding": "utf-8-sig", "delimiter": ";", "invert_sign": False,
}


def _add_rule(pattern, category_id, match_type="contains", priority=100):
    conn = sqlite3.connect(config.BANCO_DB_PATH)
    try:
        conn.execute(
            "INSERT INTO category_rules (pattern, match_type, category_id, priority) VALUES (?,?,?,?)",
            (pattern, match_type, category_id, priority),
        )
        conn.commit()
    finally:
        conn.close()


def _preview(client, filename, account_id=1, mapping=None, **extra):
    data = {"account_id": str(account_id), **extra}
    if mapping is not None:
        data["mapping"] = json.dumps(mapping)
    content = (FIXTURES / filename).read_bytes()
    return client.post(PREVIEW, data=data, files={"file": (filename, content)})


def _count(client):
    return int(client.get(TRANSACTIONS).headers["X-Total-Count"])


def test_ofx_preview_infers_kind_and_suggests_category_from_rules(client):
    _add_rule("zaffari", 2)       # Mercado (expense)
    _add_rule("salario", 3)       # Salário (income)

    resp = _preview(client, "extrato.ofx")

    assert resp.status_code == 200
    body = resp.json()
    assert body["needs_mapping"] is False
    rows = {r["description"]: r for r in body["rows"]}
    assert len(rows) == 3
    assert rows["SUPERMERCADO ZAFFARI"]["date"] == "2026-03-05"
    assert rows["SUPERMERCADO ZAFFARI"]["amount_cents"] == 4590
    assert rows["SUPERMERCADO ZAFFARI"]["kind"] == "expense"
    assert rows["SUPERMERCADO ZAFFARI"]["category_id"] == 2
    assert rows["SALARIO EMPRESA XYZ"]["kind"] == "income"
    assert rows["SALARIO EMPRESA XYZ"]["category_id"] == 3
    assert rows["PIX FULANO"]["category_id"] is None
    assert all(r["duplicate"] is False and r["import_hash"] for r in rows.values())
    assert _count(client) == SEED_COUNT  # preview writes nothing


def _commit(client, rows, account_id=1, **extra):
    return client.post(COMMIT, json={"account_id": account_id, "rows": rows, **extra})


def _chosen(preview_body):
    """What the UI sends back: the preview rows minus its display-only flags."""
    return [{k: v for k, v in r.items() if k != "duplicate"} for r in preview_body["rows"]]


def test_commit_writes_rows_and_reimporting_the_same_file_is_idempotent(client):
    _add_rule("zaffari", 2)
    first = _preview(client, "extrato.ofx").json()

    committed = _commit(client, _chosen(first))

    assert committed.status_code == 200
    assert committed.json() == {"imported": 3, "skipped": 0}
    assert _count(client) == SEED_COUNT + 3
    imported = client.get(TRANSACTIONS, params={"year": 2026, "month": 3}).json()
    zaffari = next(t for t in imported if t["description"] == "SUPERMERCADO ZAFFARI")
    assert (zaffari["amount_cents"], zaffari["kind"], zaffari["account_id"], zaffari["category_id"]) == (4590, "expense", 1, 2)

    again = _preview(client, "extrato.ofx").json()
    assert [r["duplicate"] for r in again["rows"]] == [True, True, True]

    recommitted = _commit(client, _chosen(again))  # even if the client sends them anyway
    assert recommitted.json() == {"imported": 0, "skipped": 3}
    assert _count(client) == SEED_COUNT + 3


def test_csv_without_a_mapping_asks_for_one_and_describes_the_columns(client):
    resp = _preview(client, "extrato.csv")

    assert resp.status_code == 200
    body = resp.json()
    assert body["needs_mapping"] is True
    assert body["columns"] == ["Data", "Histórico", "Valor"]
    assert body["sample"][0] == ["05/03/2026", "SUPERMERCADO ZAFFARI", "-45,90"]
    assert body["suggested"] == {"encoding": "utf-8-sig", "delimiter": ";"}
    assert body["mapping"] is None
    assert _count(client) == SEED_COUNT


def test_csv_preview_with_a_mapping_parses_signs_and_brazilian_numbers(client):
    resp = _preview(client, "extrato.csv", mapping=CSV_MAPPING)

    assert resp.status_code == 200
    rows = {r["description"]: r for r in resp.json()["rows"]}
    assert (rows["SUPERMERCADO ZAFFARI"]["kind"], rows["SUPERMERCADO ZAFFARI"]["amount_cents"]) == ("expense", 4590)
    assert (rows["SALARIO EMPRESA XYZ"]["kind"], rows["SALARIO EMPRESA XYZ"]["amount_cents"]) == ("income", 350000)
    assert rows["PIX FULANO"]["date"] == "2026-03-18"


def test_invert_sign_flips_expenses_and_income(client):
    resp = _preview(client, "extrato.csv", mapping={**CSV_MAPPING, "invert_sign": True})

    kinds = {r["description"]: r["kind"] for r in resp.json()["rows"]}
    assert kinds["SUPERMERCADO ZAFFARI"] == "income"
    assert kinds["SALARIO EMPRESA XYZ"] == "expense"


def test_mapping_used_in_a_commit_is_saved_and_reused_for_that_account(client):
    first = _preview(client, "extrato.csv", mapping=CSV_MAPPING).json()
    _commit(client, _chosen(first), mapping=CSV_MAPPING)

    resp = _preview(client, "extrato.csv")  # no mapping sent this time

    body = resp.json()
    assert body["needs_mapping"] is False
    assert body["mapping"]["date_col"] == "Data"
    assert len(body["rows"]) == 3


def test_a_preview_alone_does_not_save_the_mapping(client):
    _preview(client, "extrato.csv", mapping=CSV_MAPPING)

    assert _preview(client, "extrato.csv").json()["needs_mapping"] is True


def test_remap_asks_for_columns_again_and_returns_the_saved_mapping(client):
    first = _preview(client, "extrato.csv", mapping=CSV_MAPPING).json()
    _commit(client, _chosen(first), mapping=CSV_MAPPING)

    body = _preview(client, "extrato.csv", remap="true").json()

    assert body["needs_mapping"] is True
    assert body["columns"] == ["Data", "Histórico", "Valor"]
    assert body["mapping"]["amount_col"] == "Valor"


def test_a_mapping_that_does_not_fit_the_file_is_a_readable_422_and_is_not_saved(client):
    wrong = {**CSV_MAPPING, "amount_col": "Montante"}

    resp = _preview(client, "extrato.csv", mapping=wrong)
    assert resp.status_code == 422
    assert "Montante" in resp.json()["detail"]

    assert _preview(client, "extrato.csv").json()["needs_mapping"] is True


def test_commit_with_a_malformed_mapping_is_422_and_writes_nothing(client):
    rows = _chosen(_preview(client, "extrato.csv", mapping=CSV_MAPPING).json())
    broken = {k: v for k, v in CSV_MAPPING.items() if k != "date_col"}

    resp = _commit(client, rows, mapping=broken)

    assert resp.status_code == 422
    assert _count(client) == SEED_COUNT


def test_a_csv_with_an_unparseable_date_is_a_readable_422(client):
    resp = _preview(client, "extrato_data_ruim.csv", mapping=CSV_MAPPING)

    assert resp.status_code == 422
    assert "ontem" in resp.json()["detail"]


def test_an_invalid_ofx_is_a_readable_422_and_writes_nothing(client):
    resp = _preview(client, "lixo.ofx")

    assert resp.status_code == 422
    assert "OFX" in resp.json()["detail"]
    assert _count(client) == SEED_COUNT


def test_unsupported_extension_and_unknown_account_are_422(client):
    txt = client.post(PREVIEW, data={"account_id": "1"}, files={"file": ("extrato.pdf", b"x")})
    assert txt.status_code == 422
    assert ".ofx" in txt.json()["detail"]

    no_account = _preview(client, "extrato.ofx", account_id=99)
    assert no_account.status_code == 422
    assert no_account.json()["detail"] == "Conta não encontrada"


def test_a_rule_pointing_at_a_category_of_another_kind_is_not_suggested(client):
    _add_rule("zaffari", 3)  # Salário is an income category; Zaffari is an expense

    rows = _preview(client, "extrato.ofx").json()["rows"]

    zaffari = next(r for r in rows if r["description"] == "SUPERMERCADO ZAFFARI")
    assert zaffari["category_id"] is None


def test_commit_with_one_bad_row_writes_nothing(client):
    rows = _chosen(_preview(client, "extrato.ofx").json())
    rows[2]["category_id"] = 3  # income category on an expense row

    resp = _commit(client, rows)

    assert resp.status_code == 422
    assert "Linha 3" in resp.json()["detail"]
    assert _count(client) == SEED_COUNT


def test_commit_with_no_rows_or_unknown_account_is_422(client):
    assert _commit(client, []).status_code == 422
    assert _commit(client, [{}], account_id=99).status_code == 422


def test_a_repeated_row_inside_one_file_is_flagged_and_imported_once(client):
    content = (FIXTURES / "extrato.csv").read_bytes()
    doubled = content + content.split(b"\n", 1)[1]  # same three lines twice

    body = client.post(PREVIEW, data={"account_id": "1", "mapping": json.dumps(CSV_MAPPING)},
                       files={"file": ("extrato.csv", doubled)}).json()
    assert [r["duplicate"] for r in body["rows"]] == [False] * 3 + [True] * 3

    result = _commit(client, _chosen(body), mapping=CSV_MAPPING).json()
    assert result == {"imported": 3, "skipped": 3}


def test_commit_uses_the_category_edited_in_the_preview(client):
    rows = _chosen(_preview(client, "extrato.ofx").json())
    pix = next(r for r in rows if r["description"] == "PIX FULANO")
    pix["category_id"] = 2

    _commit(client, [pix])

    saved = client.get(TRANSACTIONS, params={"q": "PIX FULANO"}).json()
    assert saved[0]["category_id"] == 2
