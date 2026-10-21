"""The hub:// bridge, driven through its public entry point `Bridge.handle`.

Synthetic requests go in, (status, headers, body) comes out, exactly as the Qt
scheme handler will see them. No Qt, no socket: the real FastAPI app runs in
memory against the temp banco.db that conftest seeds.
"""
import json
from pathlib import Path

import pytest

from app import config
from app.desktop.bridge import Bridge
from conftest import _seed


@pytest.fixture
def static_dir(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>Hub</title>")
    (dist / "assets" / "app.js").write_text("console.log('hub')")
    return dist


@pytest.fixture
def bridge(tmp_path, static_dir, monkeypatch):
    db_path = Path(tmp_path / "banco_test.db")
    _seed(db_path)
    monkeypatch.setattr(config, "BANCO_DB_PATH", db_path)

    from app.main import app
    b = Bridge(app, static_dir)
    b.start()
    yield b
    b.stop()


def _json(response):
    return json.loads(response.body)


def test_get_with_query_reaches_the_api(bridge):
    r = bridge.handle("GET", "/api/banco/transactions?year=2026&month=2", {}, b"")

    assert r.status == 200
    assert r.header("x-total-count") == "4"
    assert r.header("content-type") == "application/json"
    assert {t["description"] for t in _json(r)} == {
        "Salario fev", "Poupanca fev", "Aluguel fev", "Mercado fev",
    }


def test_post_json_creates_and_returns_status(bridge):
    body = json.dumps({
        "date": "2026-03-10", "amount_cents": 4200, "kind": "expense",
        "description": "Padaria", "account_id": 1, "category_id": 2,
    }).encode()

    r = bridge.handle("POST", "/api/banco/transactions",
                      {"Content-Type": "application/json", "Content-Length": str(len(body))}, body)

    assert r.status == 201
    created = _json(r)
    assert created["description"] == "Padaria"
    again = bridge.handle("GET", f"/api/banco/transactions/{created['id']}", {}, b"")
    assert _json(again)["amount_cents"] == 4200


def test_unknown_api_route_is_404_not_the_spa(bridge):
    r = bridge.handle("GET", "/api/nao-existe", {}, b"")

    assert r.status == 404
    assert r.header("content-type") == "application/json"


def test_multipart_upload_reaches_the_app_byte_for_byte(static_dir):
    # No import route exists yet, so a stand-in endpoint reports what it received.
    from fastapi import FastAPI, Request
    echo = FastAPI()

    @echo.post("/api/upload")
    async def upload(request: Request):
        raw = await request.body()
        return {"content_type": request.headers["content-type"], "size": len(raw),
                "has_file": b"\x00\xffOFXDATA" in raw}

    boundary = "hubboundary123"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="extrato.ofx"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + b"\x00\xffOFXDATA" + f"\r\n--{boundary}--\r\n".encode()

    b = Bridge(echo, static_dir)
    b.start()
    try:
        r = b.handle("POST", "/api/upload",
                     {"Content-Type": f"multipart/form-data; boundary={boundary}"}, body)
    finally:
        b.stop()

    assert r.status == 200
    assert _json(r) == {"content_type": f"multipart/form-data; boundary={boundary}",
                        "size": len(body), "has_file": True}


def test_static_file_is_served_with_its_type(bridge):
    r = bridge.handle("GET", "/assets/app.js", {}, b"")

    assert r.status == 200
    assert r.body == b"console.log('hub')"
    assert r.header("content-type").startswith("text/javascript")


def test_unknown_page_path_falls_back_to_index_html(bridge):
    r = bridge.handle("GET", "/transacoes?mes=3", {}, b"")

    assert r.status == 200
    assert r.header("content-type").startswith("text/html")
    assert b"<title>Hub</title>" in r.body


def test_path_outside_the_build_is_not_served(bridge, tmp_path):
    (tmp_path / "secret.txt").write_text("nope")

    r = bridge.handle("GET", "/../secret.txt", {}, b"")

    assert b"nope" not in r.body


def test_start_runs_the_data_bootstrap(static_dir):
    from app.main import app
    b = Bridge(app, static_dir)
    b.start()
    try:
        r = b.handle("GET", "/api/banco/accounts", {}, b"")
    finally:
        b.stop()

    assert r.status == 200
    assert _json(r) != []  # default data seeded into a banco.db that did not exist
