"""Transaction CRUD, filters and validation through the HTTP API."""
import pytest

BASE = "/api/banco/transactions"


def _payload(**overrides):
    body = {
        "date": "2026-03-10",
        "amount_cents": 4590,
        "kind": "expense",
        "description": "Padaria",
        "account_id": 1,
        "category_id": 2,
        "notes": "pão e leite",
        "is_fixed_override": None,
        "goal_id": None,
    }
    body.update(overrides)
    return body


def test_create_then_fetch_by_id(client):
    created = client.post(BASE, json=_payload())
    assert created.status_code == 201
    new_id = created.json()["id"]

    fetched = client.get(f"{BASE}/{new_id}")
    assert fetched.status_code == 200
    assert fetched.json() == {"id": new_id, **_payload()}


def test_update_replaces_every_field(client):
    new_id = client.post(BASE, json=_payload()).json()["id"]

    changed = _payload(
        date="2026-03-12", amount_cents=9900, description="Aluguel março",
        category_id=1, notes="", is_fixed_override=False,
    )
    resp = client.put(f"{BASE}/{new_id}", json=changed)

    assert resp.status_code == 200
    assert resp.json() == {"id": new_id, **changed}
    assert client.get(f"{BASE}/{new_id}").json() == {"id": new_id, **changed}


def test_get_update_or_delete_unknown_id_is_404(client):
    assert client.get(f"{BASE}/9999").status_code == 404
    assert client.put(f"{BASE}/9999", json=_payload()).status_code == 404
    assert client.delete(f"{BASE}/9999").status_code == 404


def test_delete_removes_the_transaction(client):
    new_id = client.post(BASE, json=_payload()).json()["id"]

    resp = client.delete(f"{BASE}/{new_id}")

    assert resp.status_code == 204
    assert client.get(f"{BASE}/{new_id}").status_code == 404


def _saved_in_reserva(client):
    goals = client.get("/api/banco/goals?year=2026&month=3").json()
    return next(g for g in goals if g["id"] == 1)["saved_cents"]


def test_goal_link_is_stored_changed_and_removed_with_the_transaction(client):
    # Seed: goal 1 already holds the 15000 Feb savings transaction.
    assert _saved_in_reserva(client) == 15000

    saving = _payload(kind="savings", category_id=None, amount_cents=2000, goal_id=1)
    new_id = client.post(BASE, json=saving).json()["id"]
    assert client.get(f"{BASE}/{new_id}").json()["goal_id"] == 1
    assert _saved_in_reserva(client) == 17000

    client.put(f"{BASE}/{new_id}", json={**saving, "amount_cents": 3000})
    assert _saved_in_reserva(client) == 18000

    client.put(f"{BASE}/{new_id}", json={**saving, "goal_id": None})
    assert client.get(f"{BASE}/{new_id}").json()["goal_id"] is None
    assert _saved_in_reserva(client) == 15000

    client.put(f"{BASE}/{new_id}", json=saving)
    client.delete(f"{BASE}/{new_id}")
    assert _saved_in_reserva(client) == 15000


INVALID = [
    (dict(amount_cents=0), "Valor"),
    (dict(amount_cents=-500), "Valor"),
    (dict(amount_cents="12,50"), "Valor"),
    (dict(date="2026-02-30"), "Data"),
    (dict(date="10/03/2026"), "Data"),
    (dict(date=None), "Data"),
    (dict(account_id=None), "Conta"),
    (dict(account_id=999), "Conta"),
    (dict(category_id=3), "Categoria"),   # Salário is an income category, tx is an expense
    (dict(category_id=999), "Categoria"),
    (dict(goal_id=999), "Meta"),
    (dict(description="   "), "Descrição"),
    (dict(kind="transfer"), "Tipo"),
    (dict(is_fixed_override="sim"), "Fixa"),
]


@pytest.mark.parametrize("overrides, mentions", INVALID)
def test_invalid_payload_is_rejected_with_a_readable_422(client, overrides, mentions):
    bad = _payload(**overrides)

    created = client.post(BASE, json=bad)
    assert created.status_code == 422
    assert isinstance(created.json()["detail"], str)
    assert mentions in created.json()["detail"]
    assert client.get(f"{BASE}/8").status_code == 404  # nothing was written

    existing = client.post(BASE, json=_payload()).json()["id"]
    updated = client.put(f"{BASE}/{existing}", json=bad)
    assert updated.status_code == 422
    assert client.get(f"{BASE}/{existing}").json()["description"] == "Padaria"


def test_missing_optional_fields_default_to_empty(client):
    minimal = {"date": "2026-03-10", "amount_cents": 100, "kind": "expense",
               "description": "Bala", "account_id": 1}
    new_id = client.post(BASE, json=minimal).json()["id"]

    body = client.get(f"{BASE}/{new_id}").json()
    assert body["category_id"] is None and body["notes"] == ""
    assert body["is_fixed_override"] is None and body["goal_id"] is None


def _descriptions(resp):
    assert resp.status_code == 200
    return [t["description"] for t in resp.json()]


def test_list_is_newest_first_and_carries_goal_link(client):
    resp = client.get(BASE)

    assert _descriptions(resp) == [
        "Mercado fev", "Aluguel fev", "Poupanca fev", "Salario fev",
        "Mercado jan", "Aluguel dez", "Mercado nov",
    ]
    savings = next(t for t in resp.json() if t["description"] == "Poupanca fev")
    assert savings["goal_id"] == 1
    assert savings["is_fixed_override"] is None


def test_list_filters_by_year_and_month(client):
    assert sorted(_descriptions(client.get(f"{BASE}?year=2026&month=2"))) == [
        "Aluguel fev", "Mercado fev", "Poupanca fev", "Salario fev"]
    assert len(client.get(f"{BASE}?year=2026").json()) == 5
    assert client.get(f"{BASE}?year=2026&month=3").json() == []


def test_list_month_without_year_is_422(client):
    resp = client.get(f"{BASE}?month=2")
    assert resp.status_code == 422
    assert "ano" in resp.json()["detail"]


def test_list_filters_by_category_and_search_text(client):
    assert sorted(_descriptions(client.get(f"{BASE}?category_id=2"))) == [
        "Mercado fev", "Mercado jan", "Mercado nov"]
    assert sorted(_descriptions(client.get(f"{BASE}?q=mercado"))) == [
        "Mercado fev", "Mercado jan", "Mercado nov"]
    assert _descriptions(client.get(f"{BASE}?q=mercado&year=2026&month=1")) == ["Mercado jan"]


def test_list_filters_by_account(client, tmp_path):
    import sqlite3
    from app import config
    conn = sqlite3.connect(config.BANCO_DB_PATH)
    conn.execute("INSERT INTO accounts (id, name, kind) VALUES (2, 'Cartão', 'credit_card')")
    conn.commit()
    conn.close()
    client.post(BASE, json=_payload(account_id=2, description="No cartão"))

    assert _descriptions(client.get(f"{BASE}?account_id=2")) == ["No cartão"]
    assert len(client.get(f"{BASE}?account_id=1").json()) == 7


def test_list_paginates_and_reports_the_total(client):
    first = client.get(f"{BASE}?limit=3&offset=0")
    second = client.get(f"{BASE}?limit=3&offset=3")
    everything = client.get(BASE).json()

    assert first.headers["X-Total-Count"] == "7"
    assert first.json() + second.json() == everything[:6]
    assert client.get(f"{BASE}?limit=3&offset=6").json() == everything[6:]

    filtered = client.get(f"{BASE}?q=mercado&limit=1")
    assert len(filtered.json()) == 1
    assert filtered.headers["X-Total-Count"] == "3"


def test_options_lists_what_the_form_and_filters_choose_from(client):
    resp = client.get(f"{BASE}/options")

    assert resp.status_code == 200
    body = resp.json()
    assert body["accounts"] == [{"id": 1, "name": "Checking", "kind": "checking"}]
    assert {c["name"]: (c["kind"], c["is_fixed"]) for c in body["categories"]} == {
        "Aluguel": ("expense", True), "Mercado": ("expense", False),
        "Salário": ("income", False), "Viagem": ("expense", False),
    }
    assert body["goals"] == [{"id": 1, "name": "Reserva", "archived": False}]


def test_writes_show_up_in_the_month_summary(client):
    def feb_expense():
        return client.get("/api/banco/summary?year=2026&month=2").json()["current"]["expense_cents"]

    assert feb_expense() == 25000
    new_id = client.post(BASE, json=_payload(date="2026-02-15", amount_cents=1000)).json()["id"]
    assert feb_expense() == 26000
    client.put(f"{BASE}/{new_id}", json=_payload(date="2026-02-15", amount_cents=400))
    assert feb_expense() == 25400
    client.delete(f"{BASE}/{new_id}")
    assert feb_expense() == 25000
