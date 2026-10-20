"""Behavior of GET /api/banco/category-history — per-category totals over a window of months
(the planilha rows, their 6-month minis and the month-over-month share of income)."""


def test_expense_history_per_category_oldest_first_largest_current_first(client):
    """Window Dec 2025..Feb 2026: each category gets one total per month (zeros where it had
    nothing), and categories are ordered by the last month's total, largest first."""
    resp = client.get("/api/banco/category-history?year=2026&month=2&months=3")
    assert resp.status_code == 200

    body = resp.json()
    assert [c["category_name"] for c in body] == ["Aluguel", "Mercado", "Viagem"]
    aluguel, mercado, _ = body
    assert aluguel["history_cents"] == [7000, 0, 20000]
    assert mercado["history_cents"] == [0, 10000, 5000]
    assert aluguel["is_fixed"] is True and mercado["is_fixed"] is False


def test_budget_is_the_one_in_effect_for_the_last_month_or_null(client):
    """Mercado's budget is R$ 80 from Jan and R$ 60 from Mar; Aluguel has none."""
    feb = {c["category_name"]: c for c in client.get("/api/banco/category-history?year=2026&month=2&months=2").json()}
    mar = {c["category_name"]: c for c in client.get("/api/banco/category-history?year=2026&month=3&months=2").json()}

    assert feb["Mercado"]["budget_cents"] == 8000
    assert feb["Aluguel"]["budget_cents"] is None
    assert mar["Mercado"]["budget_cents"] == 6000


def test_budgeted_category_without_spending_still_appears_with_zeros(client):
    """Viagem has a budget but was never used: it is listed so its whole budget shows as available."""
    body = {c["category_name"]: c for c in client.get("/api/banco/category-history?year=2026&month=2&months=2").json()}

    assert body["Viagem"]["history_cents"] == [0, 0]
    assert body["Viagem"]["budget_cents"] == 30000
    assert body["Viagem"]["is_fixed"] is False


def test_income_kind_lists_income_categories_only(client):
    """kind=income returns the income sources (Salário), not expense categories or budgets."""
    body = client.get("/api/banco/category-history?year=2026&month=2&months=2&kind=income").json()

    assert [(c["category_name"], c["history_cents"], c["budget_cents"]) for c in body] == [
        ("Salário", [0, 100000], None),
    ]
