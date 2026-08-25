"""Characterization tests guarding the existing endpoints the new dashboard relies on.

These lock the JSON contracts for /summary and /categories so the UI work (and
future refactors) can't silently change their shape.
"""


def test_summary_returns_current_and_previous_totals(client):
    resp = client.get("/api/banco/summary?year=2026&month=2")
    assert resp.status_code == 200

    body = resp.json()
    assert body["year"] == 2026 and body["month"] == 2
    for block in ("current", "previous"):
        assert set(body[block]) >= {
            "income_cents", "expense_cents", "savings_cents", "net_cents",
        }
    # Feb has expenses; Jan (previous) also has one seeded expense.
    assert body["current"]["expense_cents"] == 25000
    assert body["previous"]["expense_cents"] == 10000


def test_categories_breakdown_largest_first(client):
    resp = client.get("/api/banco/categories?year=2026&month=2")
    assert resp.status_code == 200

    body = resp.json()
    # Feb expenses: Aluguel 20000 (largest), then Mercado 5000.
    assert [c["category_name"] for c in body] == ["Aluguel", "Mercado"]
    assert [c["total_cents"] for c in body] == [20000, 5000]
    assert set(body[0]) >= {
        "category_id", "category_name", "color", "is_fixed", "total_cents",
    }
