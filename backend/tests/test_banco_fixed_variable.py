"""Behavior of GET /api/banco/fixed-variable — the fixed vs variable expense split."""


def test_fixed_variable_splits_month_expenses(client):
    """Feb 2026: Aluguel (fixed category) is fixed, Mercado (variable) is variable,
    and the two halves sum to the month's total expense."""
    resp = client.get("/api/banco/fixed-variable?year=2026&month=2")
    assert resp.status_code == 200

    body = resp.json()
    assert body["fixed_cents"] == 20000     # Aluguel
    assert body["variable_cents"] == 5000   # Mercado
    assert body["fixed_cents"] + body["variable_cents"] == 25000  # = Feb expense total


def test_fixed_variable_defaults_to_current_month(client):
    """No params -> the current month, returning the two integer cent fields."""
    resp = client.get("/api/banco/fixed-variable")
    assert resp.status_code == 200

    body = resp.json()
    assert isinstance(body["fixed_cents"], int)
    assert isinstance(body["variable_cents"], int)
