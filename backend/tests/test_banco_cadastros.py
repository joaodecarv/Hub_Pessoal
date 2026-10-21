"""Accounts, categories and rules (Configurações) through the HTTP API."""
BASE = "/api/banco/cadastros"


def test_list_accounts_includes_transaction_count(client):
    resp = client.get(f"{BASE}/accounts")

    assert resp.status_code == 200
    assert resp.json() == [
        {"id": 1, "name": "Checking", "kind": "checking", "transaction_count": 7},
    ]


def test_create_account(client):
    resp = client.post(f"{BASE}/accounts", json={"name": "Nubank", "kind": "credit_card"})

    assert resp.status_code == 201
    created = resp.json()
    assert created == {"id": created["id"], "name": "Nubank", "kind": "credit_card",
                       "transaction_count": 0}
    assert created in client.get(f"{BASE}/accounts").json()


def test_update_account_renames_and_changes_kind(client):
    resp = client.put(f"{BASE}/accounts/1", json={"name": "Itaú", "kind": "savings"})

    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "name": "Itaú", "kind": "savings", "transaction_count": 7}
    assert client.get(f"{BASE}/accounts").json() == [resp.json()]


def test_invalid_account_is_rejected_with_a_readable_422(client):
    for bad, mentions in [
        ({"name": "  ", "kind": "cash"}, "Nome"),
        ({"name": "X", "kind": "bitcoin"}, "Tipo"),
        ({"kind": "cash"}, "Nome"),
    ]:
        resp = client.post(f"{BASE}/accounts", json=bad)
        assert resp.status_code == 422
        assert mentions in resp.json()["detail"]
    assert client.put(f"{BASE}/accounts/1", json={"name": "", "kind": "cash"}).status_code == 422
    assert len(client.get(f"{BASE}/accounts").json()) == 1


def test_duplicate_account_name_is_409(client):
    resp = client.post(f"{BASE}/accounts", json={"name": "Checking", "kind": "cash"})
    assert resp.status_code == 409
    assert "Checking" in resp.json()["detail"]

    other = client.post(f"{BASE}/accounts", json={"name": "Outra", "kind": "cash"}).json()
    assert client.put(f"{BASE}/accounts/{other['id']}",
                      json={"name": "Checking", "kind": "cash"}).status_code == 409


def test_unknown_account_is_404(client):
    assert client.put(f"{BASE}/accounts/99", json={"name": "X", "kind": "cash"}).status_code == 404
    assert client.delete(f"{BASE}/accounts/99").status_code == 404


def test_account_with_transactions_cannot_be_deleted(client):
    resp = client.delete(f"{BASE}/accounts/1")

    assert resp.status_code == 409
    assert "7 transações" in resp.json()["detail"]
    assert len(client.get(f"{BASE}/accounts").json()) == 1
    assert len(client.get("/api/banco/transactions").json()) == 7


def test_empty_account_can_be_deleted(client):
    new_id = client.post(f"{BASE}/accounts", json={"name": "Vazia", "kind": "cash"}).json()["id"]

    assert client.delete(f"{BASE}/accounts/{new_id}").status_code == 204
    assert [a["id"] for a in client.get(f"{BASE}/accounts").json()] == [1]


# ---------- categories ----------
# Seed: 1 Aluguel (expense, fixed, 2 txs), 2 Mercado (expense, 3 txs, 2 budgets),
# 3 Salário (income, 1 tx), 4 Viagem (expense, 1 budget, no txs).

def _category(**overrides):
    body = {"name": "Lazer", "kind": "expense", "color": "#112233", "is_fixed": False}
    body.update(overrides)
    return body


def _add_rules(*rows):
    """(pattern, category_id) rows inserted straight into the test database."""
    import sqlite3
    from app import config
    conn = sqlite3.connect(config.BANCO_DB_PATH)
    conn.executemany(
        "INSERT INTO category_rules (pattern, match_type, category_id) VALUES (?, 'contains', ?)", rows)
    conn.commit()
    conn.close()


def test_list_categories(client):
    resp = client.get(f"{BASE}/categories")

    assert resp.status_code == 200
    assert {c["name"]: (c["id"], c["kind"], c["color"], c["is_fixed"]) for c in resp.json()} == {
        "Aluguel": (1, "expense", "#8a6d3b", True),
        "Mercado": (2, "expense", "#5b7a8a", False),
        "Salário": (3, "income", "#3a7a4a", False),
        "Viagem": (4, "expense", "#6a5a8a", False),
    }


def test_create_then_update_category(client):
    created = client.post(f"{BASE}/categories", json=_category())
    assert created.status_code == 201
    new_id = created.json()["id"]
    assert created.json() == {"id": new_id, **_category()}

    changed = _category(name="Diversão", kind="expense", color="#AABBCC", is_fixed=True)
    resp = client.put(f"{BASE}/categories/{new_id}", json=changed)
    assert resp.status_code == 200
    assert resp.json() == {"id": new_id, **changed}
    assert {"id": new_id, **changed} in client.get(f"{BASE}/categories").json()


def test_invalid_category_is_rejected_with_a_readable_422(client):
    for overrides, mentions in [
        (dict(name=" "), "Nome"),
        (dict(kind="transfer"), "Tipo"),
        (dict(color="azul"), "Cor"),
        (dict(color="#12345"), "Cor"),
        (dict(is_fixed="sim"), "Fixa"),
    ]:
        resp = client.post(f"{BASE}/categories", json=_category(**overrides))
        assert resp.status_code == 422
        assert mentions in resp.json()["detail"]
    assert len(client.get(f"{BASE}/categories").json()) == 4


def test_duplicate_category_name_is_409_and_unknown_is_404(client):
    assert client.post(f"{BASE}/categories", json=_category(name="Mercado")).status_code == 409
    assert client.put(f"{BASE}/categories/4", json=_category(name="Mercado")).status_code == 409
    assert client.put(f"{BASE}/categories/99", json=_category()).status_code == 404
    assert client.delete(f"{BASE}/categories/99").status_code == 404
    assert client.get(f"{BASE}/categories/99/impact").status_code == 404


def test_delete_impact_counts_transactions_rules_and_budgets(client):
    _add_rules(("padaria", 2), ("super", 2), ("uber", 4))

    assert client.get(f"{BASE}/categories/2/impact").json() == {
        "transactions": 3, "rules": 2, "budgets": 2}
    assert client.get(f"{BASE}/categories/4/impact").json() == {
        "transactions": 0, "rules": 1, "budgets": 1}
    assert client.get(f"{BASE}/categories/3/impact").json() == {
        "transactions": 1, "rules": 0, "budgets": 0}


def test_deleting_a_category_nulls_transactions_and_cascades_rules_and_budgets(client):
    _add_rules(("padaria", 2), ("uber", 4))

    assert client.delete(f"{BASE}/categories/2").status_code == 204

    # SET NULL: the three Mercado transactions survive, uncategorized.
    mercado = [t for t in client.get("/api/banco/transactions").json()
               if t["description"].startswith("Mercado")]
    assert len(mercado) == 3 and all(t["category_id"] is None for t in mercado)
    # CASCADE: Mercado's rule and both budgets are gone; other categories' stay.
    import sqlite3
    from app import config
    conn = sqlite3.connect(config.BANCO_DB_PATH)
    assert conn.execute("SELECT category_id FROM category_rules").fetchall() == [(4,)]
    assert conn.execute("SELECT category_id FROM budgets").fetchall() == [(4,)]
    conn.close()
    assert 2 not in [c["id"] for c in client.get(f"{BASE}/categories").json()]


# ---------- rules ----------

def _rule(**overrides):
    body = {"pattern": "padaria", "match_type": "contains", "category_id": 2, "priority": 100}
    body.update(overrides)
    return body


def test_create_and_fetch_rules_ordered_by_priority(client):
    late = client.post(f"{BASE}/rules", json=_rule(pattern="super", priority=200))
    assert late.status_code == 201
    assert late.json() == {"id": late.json()["id"], **_rule(pattern="super", priority=200)}
    early = client.post(f"{BASE}/rules", json=_rule(pattern=r"^PIX .*aluguel", match_type="regex",
                                                    category_id=1, priority=10)).json()
    default = client.post(f"{BASE}/rules", json={"pattern": "uber", "match_type": "contains",
                                                 "category_id": 4}).json()

    listed = client.get(f"{BASE}/rules").json()
    assert [r["id"] for r in listed] == [early["id"], default["id"], late.json()["id"]]
    assert default["priority"] == 100
    assert early["match_type"] == "regex"


def test_update_rule(client):
    rule_id = client.post(f"{BASE}/rules", json=_rule()).json()["id"]

    changed = _rule(pattern="mercado livre", category_id=4, priority=5)
    resp = client.put(f"{BASE}/rules/{rule_id}", json=changed)

    assert resp.status_code == 200
    assert resp.json() == {"id": rule_id, **changed}
    assert client.get(f"{BASE}/rules").json() == [{"id": rule_id, **changed}]


def test_invalid_rule_is_rejected_with_a_readable_422(client):
    for overrides, mentions in [
        (dict(pattern="  "), "Padrão"),
        (dict(match_type="starts"), "Tipo de regra"),
        (dict(match_type="regex", pattern="(abc"), "Expressão regular"),
        (dict(category_id=99), "Categoria"),
        (dict(category_id=None), "Categoria"),
        (dict(priority="alta"), "Prioridade"),
        (dict(priority=True), "Prioridade"),
    ]:
        resp = client.post(f"{BASE}/rules", json=_rule(**overrides))
        assert resp.status_code == 422, overrides
        assert mentions in resp.json()["detail"]
    assert client.get(f"{BASE}/rules").json() == []


def test_delete_rule_and_unknown_rule_is_404(client):
    rule_id = client.post(f"{BASE}/rules", json=_rule()).json()["id"]

    assert client.delete(f"{BASE}/rules/{rule_id}").status_code == 204
    assert client.get(f"{BASE}/rules").json() == []
    assert client.delete(f"{BASE}/rules/{rule_id}").status_code == 404
    assert client.put(f"{BASE}/rules/{rule_id}", json=_rule()).status_code == 404
