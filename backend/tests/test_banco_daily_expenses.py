"""Behavior of GET /api/banco/daily-expenses — per-day spending for the month curve."""


def test_daily_expenses_has_one_entry_per_day_with_only_expenses_summed(client):
    """Feb 2026 has 28 days; only day 10 (Aluguel) and day 20 (Mercado) have expenses.
    The Feb 1 income and Feb 3 savings must not count."""
    resp = client.get("/api/banco/daily-expenses?year=2026&month=2")
    assert resp.status_code == 200

    body = resp.json()
    assert [d["day"] for d in body] == list(range(1, 29))
    spent = {d["day"]: d["expense_cents"] for d in body if d["expense_cents"]}
    assert spent == {10: 20000, 20: 5000}
