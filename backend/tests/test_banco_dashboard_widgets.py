"""Behavior of the dashboard widget endpoints: account balances, goals, top expenses."""


def test_balances_sum_all_transactions_per_account(client):
    """Balance = income + savings − expenses over every transaction ever (Banco's
    sign rule). Seed: +100000 +15000 −(3000+7000+10000+20000+5000) = 70000."""
    resp = client.get("/api/banco/balances")
    assert resp.status_code == 200

    assert resp.json() == [
        {"id": 1, "name": "Checking", "kind": "checking", "balance_cents": 70000},
    ]


def test_goals_report_saved_vs_target(client):
    """The 'Reserva' goal is funded by the Feb savings transaction (15000 of 60000)."""
    resp = client.get("/api/banco/goals")
    assert resp.status_code == 200

    [goal] = resp.json()
    assert goal["name"] == "Reserva"
    assert goal["target_cents"] == 60000
    assert goal["saved_cents"] == 15000
    assert goal["achieved"] is False
    assert goal["deadline"] is None
    assert goal["on_track"] is None  # no deadline -> no pace to judge


def test_top_expenses_are_the_months_largest_first(client):
    """Feb 2026 has two expenses; they come back largest first, income/savings excluded."""
    resp = client.get("/api/banco/top-expenses?year=2026&month=2&limit=5")
    assert resp.status_code == 200

    body = resp.json()
    assert [t["description"] for t in body] == ["Aluguel fev", "Mercado fev"]
    assert [t["amount_cents"] for t in body] == [20000, 5000]
    assert body[0]["date"] == "2026-02-10"


def test_top_expenses_respects_limit(client):
    resp = client.get("/api/banco/top-expenses?year=2026&month=2&limit=1")
    assert [t["description"] for t in resp.json()] == ["Aluguel fev"]
