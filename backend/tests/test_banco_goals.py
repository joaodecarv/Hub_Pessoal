"""Goals CRUD, archiving and progress through the HTTP API."""
BASE = "/api/banco/goals"
TX = "/api/banco/transactions"


def _goal(**overrides):
    body = {"name": "Viagem", "target_cents": 500000, "deadline": "2027-06-30", "notes": "Japão"}
    body.update(overrides)
    return body


def _by_name(client):
    return {g["name"]: g for g in client.get(f"{BASE}/overview").json()}


def test_overview_lists_goals_with_progress_and_notes(client):
    goals = client.get(f"{BASE}/overview").json()

    assert len(goals) == 1
    reserva = goals[0]
    assert reserva["id"] == 1
    assert reserva["name"] == "Reserva"
    assert reserva["target_cents"] == 60000
    assert reserva["saved_cents"] == 15000       # the seeded Feb savings transaction
    assert reserva["deadline"] is None
    assert reserva["notes"] == ""
    assert reserva["archived"] is False
    assert reserva["achieved"] is False


def test_create_returns_the_goal_with_zero_progress_and_it_shows_in_the_overview(client):
    created = client.post(BASE, json=_goal())

    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Viagem"
    assert body["target_cents"] == 500000
    assert body["deadline"] == "2027-06-30"
    assert body["notes"] == "Japão"
    assert body["archived"] is False
    assert body["saved_cents"] == 0
    assert _by_name(client)["Viagem"]["id"] == body["id"]


def test_create_without_deadline_or_notes(client):
    body = client.post(BASE, json={"name": "Notebook", "target_cents": 700000}).json()

    assert body["deadline"] is None
    assert body["notes"] == ""


def test_update_replaces_fields_but_keeps_progress(client):
    changed = _goal(name="Reserva grande", target_cents=90000, deadline=None, notes="12 meses")

    resp = client.put(f"{BASE}/1", json=changed)

    assert resp.status_code == 200
    body = resp.json()
    assert (body["name"], body["target_cents"], body["deadline"], body["notes"]) == (
        "Reserva grande", 90000, None, "12 meses")
    assert body["saved_cents"] == 15000
    assert _by_name(client)["Reserva grande"]["target_cents"] == 90000


def test_invalid_bodies_get_one_readable_message_and_nothing_is_saved(client):
    for overrides, message in [
        ({"name": "  "}, "Nome é obrigatório"),
        ({"target_cents": 0}, "Valor alvo deve ser maior que zero"),
        ({"target_cents": "100"}, "Valor alvo deve ser maior que zero"),
        ({"deadline": "30/06/2027"}, "Prazo inválido"),
    ]:
        for resp in (client.post(BASE, json=_goal(**overrides)),
                     client.put(f"{BASE}/1", json=_goal(**overrides))):
            assert resp.status_code == 422
            assert resp.json()["detail"] == message

    assert client.post(BASE, json={}).json()["detail"] == (
        "Nome é obrigatório; Valor alvo deve ser maior que zero")
    assert list(_by_name(client)) == ["Reserva"]


def test_archive_moves_the_goal_out_of_the_dashboard_list_and_unarchive_brings_it_back(client):
    archived = client.put(f"{BASE}/1/archive", json={"archived": True})

    assert archived.status_code == 200
    assert archived.json()["archived"] is True
    assert archived.json()["saved_cents"] == 15000          # progress is kept
    assert _by_name(client)["Reserva"]["archived"] is True  # still in the management list
    assert client.get(BASE).json() == []                     # but not on the dashboard

    restored = client.put(f"{BASE}/1/archive", json={"archived": False})

    assert restored.json()["archived"] is False
    assert [g["name"] for g in client.get(BASE).json()] == ["Reserva"]


def test_archived_goals_are_listed_after_the_active_ones(client):
    client.put(f"{BASE}/1/archive", json={"archived": True})
    client.post(BASE, json=_goal(name="Zebra"))

    assert [g["name"] for g in client.get(f"{BASE}/overview").json()] == ["Zebra", "Reserva"]


def test_archive_requires_a_boolean(client):
    resp = client.put(f"{BASE}/1/archive", json={"archived": "sim"})

    assert resp.status_code == 422
    assert resp.json()["detail"] == "Informe se a meta está arquivada (verdadeiro ou falso)"


def test_delete_removes_the_goal_and_its_links_but_keeps_the_transactions(client):
    resp = client.delete(f"{BASE}/1")

    assert resp.status_code == 204
    assert client.get(f"{BASE}/overview").json() == []
    kept = client.get(f"{TX}/5").json()                      # the Feb savings transaction
    assert kept["amount_cents"] == 15000
    assert kept["goal_id"] is None


def test_linking_a_savings_transaction_updates_progress_and_deleting_it_removes_the_deposit(client):
    deposit = {"date": "2026-03-05", "amount_cents": 20000, "kind": "savings",
               "description": "Aporte", "account_id": 1, "goal_id": 1}

    tx_id = client.post(TX, json=deposit).json()["id"]
    assert _by_name(client)["Reserva"]["saved_cents"] == 35000

    client.put(f"{TX}/{tx_id}", json={**deposit, "goal_id": None})
    assert _by_name(client)["Reserva"]["saved_cents"] == 15000

    client.put(f"{TX}/{tx_id}", json=deposit)
    client.delete(f"{TX}/{tx_id}")
    assert _by_name(client)["Reserva"]["saved_cents"] == 15000


def test_update_archive_or_delete_unknown_goal_is_404(client):
    assert client.put(f"{BASE}/999", json=_goal()).status_code == 404
    assert client.put(f"{BASE}/999/archive", json={"archived": True}).status_code == 404
    assert client.delete(f"{BASE}/999").status_code == 404
