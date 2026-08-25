"""Behavior of GET /api/banco/trends — the multi-month expense trend."""
from datetime import date


def test_trends_returns_requested_months_oldest_first(client):
    """A 3-month window ending at Feb 2026 yields Dec, Jan, Feb in chronological order."""
    resp = client.get("/api/banco/trends?year=2026&month=2&months=3")
    assert resp.status_code == 200

    body = resp.json()
    assert [(e["year"], e["month"]) for e in body] == [(2025, 12), (2026, 1), (2026, 2)]


def test_trends_uses_real_totals_and_zero_fills_empty_months(client):
    """Feb 2026 sums its seeded rows; March 2026 (no transactions) is zeros, not skipped."""
    resp = client.get("/api/banco/trends?year=2026&month=3&months=2")
    feb, mar = resp.json()

    assert (feb["year"], feb["month"]) == (2026, 2)
    assert feb["expense_cents"] == 25000   # 20000 Aluguel + 5000 Mercado
    assert feb["income_cents"] == 100000
    assert feb["savings_cents"] == 15000

    assert (mar["year"], mar["month"]) == (2026, 3)
    assert mar["expense_cents"] == 0
    assert mar["income_cents"] == 0


def test_trends_walks_across_a_year_boundary(client):
    """A window ending Feb 2026 reaches back into 2025 correctly."""
    resp = client.get("/api/banco/trends?year=2026&month=2&months=4")
    body = resp.json()

    assert [(e["year"], e["month"]) for e in body] == [
        (2025, 11), (2025, 12), (2026, 1), (2026, 2),
    ]
    assert [e["expense_cents"] for e in body] == [3000, 7000, 10000, 25000]


def test_trends_defaults_to_six_months_ending_this_month(client):
    """No params -> 6 entries, ending at the current month."""
    resp = client.get("/api/banco/trends")
    body = resp.json()
    today = date.today()

    assert len(body) == 6
    assert (body[-1]["year"], body[-1]["month"]) == (today.year, today.month)
