"""Monthly budgets through the HTTP API: the effective list for a month, and the
"from this month on" semantics of setting and removing a limit.

Seed: Mercado R$ 80 from Jan 2026 and R$ 60 from Mar 2026; Viagem R$ 300 from Jan 2026
(no spending); Aluguel has no budget. Feb 2026 spending: Aluguel 200, Mercado 50.
"""
BASE = "/api/banco/budgets"
HISTORY = "/api/banco/category-history"


def _month(client, year, month):
    resp = client.get(BASE, params={"year": year, "month": month})
    assert resp.status_code == 200
    return {row["category_name"]: row for row in resp.json()}


def _limits(client, year, month):
    return {name: row["budget_cents"] for name, row in _month(client, year, month).items()}


def test_lists_every_expense_category_with_its_effective_limit_and_spending(client):
    rows = _month(client, 2026, 2)

    assert set(rows) == {"Aluguel", "Mercado", "Viagem"}   # no income category
    assert rows["Mercado"] == {
        "category_id": 2, "category_name": "Mercado", "color": "#5b7a8a",
        "budget_cents": 8000, "starts_on": "2026-01-01", "spent_cents": 5000,
    }
    assert rows["Aluguel"]["budget_cents"] is None
    assert rows["Aluguel"]["starts_on"] is None
    assert rows["Aluguel"]["spent_cents"] == 20000
    assert rows["Viagem"]["spent_cents"] == 0


def test_budgeted_categories_come_first(client):
    rows = client.get(BASE, params={"year": 2026, "month": 2}).json()

    assert [r["category_name"] for r in rows] == ["Mercado", "Viagem", "Aluguel"]


def test_limit_changes_with_the_month(client):
    assert _limits(client, 2025, 12)["Mercado"] is None    # before any budget
    assert _limits(client, 2026, 2)["Mercado"] == 8000
    assert _limits(client, 2026, 3)["Mercado"] == 6000
    assert _limits(client, 2026, 9)["Mercado"] == 6000     # carries forward


def test_setting_a_limit_applies_from_that_month_onward_not_before(client):
    resp = client.put(f"{BASE}/1", json={"year": 2026, "month": 2, "limit_cents": 25000})

    assert resp.status_code == 200
    assert resp.json() == {"category_id": 1, "year": 2026, "month": 2, "limit_cents": 25000}
    assert _limits(client, 2026, 1)["Aluguel"] is None
    assert _limits(client, 2026, 2)["Aluguel"] == 25000
    assert _limits(client, 2027, 6)["Aluguel"] == 25000


def test_setting_a_limit_stops_at_the_next_change_already_on_record(client):
    client.put(f"{BASE}/2", json={"year": 2026, "month": 2, "limit_cents": 7000})

    assert _limits(client, 2026, 1)["Mercado"] == 8000
    assert _limits(client, 2026, 2)["Mercado"] == 7000
    assert _limits(client, 2026, 3)["Mercado"] == 6000     # the March change still stands


def test_setting_a_limit_in_a_month_that_already_has_one_replaces_it(client):
    client.put(f"{BASE}/2", json={"year": 2026, "month": 3, "limit_cents": 9000})
    client.put(f"{BASE}/2", json={"year": 2026, "month": 3, "limit_cents": 9500})

    assert _limits(client, 2026, 3)["Mercado"] == 9500
    assert _limits(client, 2026, 2)["Mercado"] == 8000


def _remove(client, category_id, year, month):
    return client.delete(f"{BASE}/{category_id}", params={"year": year, "month": month})


def test_removing_a_budget_applies_from_that_month_onward_not_before(client):
    resp = _remove(client, 2, 2026, 2)

    assert resp.status_code == 204
    assert _limits(client, 2026, 1)["Mercado"] == 8000     # earlier months keep it
    assert _limits(client, 2026, 2)["Mercado"] is None
    assert _limits(client, 2026, 3)["Mercado"] is None     # the later R$ 60 change goes too
    assert _limits(client, 2027, 1)["Mercado"] is None


def test_removing_in_a_month_with_its_own_change_does_not_fall_back_to_the_previous_limit(client):
    _remove(client, 2, 2026, 3)

    assert _limits(client, 2026, 2)["Mercado"] == 8000
    assert _limits(client, 2026, 3)["Mercado"] is None
    assert _limits(client, 2026, 8)["Mercado"] is None


def test_removing_the_first_budget_leaves_no_trace_before_or_after(client):
    _remove(client, 4, 2026, 1)

    assert _limits(client, 2025, 12)["Viagem"] is None
    assert _limits(client, 2026, 1)["Viagem"] is None
    assert _limits(client, 2026, 6)["Viagem"] is None


def test_a_limit_can_be_set_again_after_removal(client):
    _remove(client, 2, 2026, 2)
    client.put(f"{BASE}/2", json={"year": 2026, "month": 6, "limit_cents": 5000})

    assert _limits(client, 2026, 1)["Mercado"] == 8000
    assert _limits(client, 2026, 5)["Mercado"] is None
    assert _limits(client, 2026, 6)["Mercado"] == 5000
    assert _limits(client, 2026, 7)["Mercado"] == 5000

    client.put(f"{BASE}/2", json={"year": 2026, "month": 2, "limit_cents": 4000})
    assert _limits(client, 2026, 2)["Mercado"] == 4000


def test_a_removed_budget_is_gone_from_the_dashboard_history_too(client):
    _remove(client, 2, 2026, 3)

    rows = client.get(HISTORY, params={"year": 2026, "month": 3}).json()
    assert {r["category_name"]: r["budget_cents"] for r in rows}["Mercado"] is None


def test_removing_a_budget_that_does_not_exist_is_a_no_op(client):
    assert _remove(client, 1, 2026, 2).status_code == 204  # Aluguel never had one
    assert _limits(client, 2026, 2)["Aluguel"] is None


def test_invalid_removal_requests(client):
    assert _remove(client, 999, 2026, 2).status_code == 404
    assert _remove(client, 3, 2026, 2).json()["detail"] == "Só categorias de despesa têm orçamento"
    assert _remove(client, 2, 2026, 13).json()["detail"] == "Mês inválido"
    assert client.delete(f"{BASE}/2").json()["detail"] == "Mês inválido"
    assert _limits(client, 2026, 2)["Mercado"] == 8000


def test_invalid_limit_requests_get_one_readable_message(client):
    def put(category_id, **body):
        return client.put(f"{BASE}/{category_id}", json={"year": 2026, "month": 2, "limit_cents": 1000, **body})

    for body, message in [
        ({"limit_cents": 0}, "Limite deve ser maior que zero"),
        ({"limit_cents": "10"}, "Limite deve ser maior que zero"),
        ({"month": 13}, "Mês inválido"),
        ({"year": None}, "Mês inválido"),
    ]:
        resp = put(1, **body)
        assert resp.status_code == 422
        assert resp.json()["detail"] == message

    assert put(3).status_code == 422                       # Salário is income
    assert put(3).json()["detail"] == "Só categorias de despesa têm orçamento"
    assert put(999).status_code == 404
    assert _limits(client, 2026, 2)["Aluguel"] is None
