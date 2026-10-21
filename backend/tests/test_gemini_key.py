"""Gemini key: status/save API and call-time use by the digest.

The Gemini SDK and the RSS fetch are the external boundaries, so they are
replaced; everything else is the real app driven through HTTP.
"""
import stat

import pytest
from fastapi.testclient import TestClient

from app import config
from app.feeds import digest


@pytest.fixture(autouse=True)
def no_ambient_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


@pytest.fixture
def api():
    from app.main import app
    with TestClient(app) as client:  # runs the lifespan (bootstrap creates the data dirs)
        yield client


@pytest.fixture
def fake_gemini(monkeypatch):
    """Records the api_key each Gemini client is built with."""
    used = []

    class FakeClient:
        def __init__(self, api_key):
            used.append(api_key)
            self.models = self

        def generate_content(self, model, contents):
            class Resp:
                text = "# resumo"
            return Resp()

    monkeypatch.setattr(digest.genai, "Client", FakeClient)
    monkeypatch.setattr(digest, "fetch_topic", lambda topic: [])
    return used


def test_status_is_false_without_key(api):
    assert api.get("/api/config/gemini").json() == {"configured": False}


def test_saving_key_writes_env_with_mode_600_and_never_echoes_it(api):
    r = api.put("/api/config/gemini", json={"api_key": "  SECRET-123  "})
    assert r.status_code == 200
    assert r.json() == {"configured": True}
    assert "SECRET-123" not in r.text
    assert "SECRET-123" not in api.get("/api/config/gemini").text

    env = config.CONFIG_DIR / ".env"
    assert "SECRET-123" in env.read_text()
    assert stat.S_IMODE(env.stat().st_mode) == 0o600


def test_blank_key_is_rejected_in_portuguese(api):
    r = api.put("/api/config/gemini", json={"api_key": "   "})
    assert r.status_code == 422
    assert "chave" in r.json()["detail"].lower()
    assert api.get("/api/config/gemini").json() == {"configured": False}


def test_refresh_without_key_returns_readable_error_pointing_to_settings(api, fake_gemini):
    r = api.post("/api/digest/refresh?topic=ai")
    assert r.status_code == 409
    assert "Configurações" in r.json()["detail"]
    assert fake_gemini == []


def test_digest_uses_key_saved_after_startup_without_restart(api, fake_gemini):
    api.put("/api/config/gemini", json={"api_key": "first"})
    assert api.post("/api/digest/refresh?topic=ai").status_code == 200
    api.put("/api/config/gemini", json={"api_key": "second"})
    assert api.post("/api/digest/refresh?topic=ai").status_code == 200
    assert fake_gemini == ["first", "second"]


def test_environment_key_is_a_fallback_and_saved_key_wins(api, fake_gemini, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "from-dev-env")
    assert api.get("/api/config/gemini").json() == {"configured": True}
    api.post("/api/digest/refresh?topic=ai")
    api.put("/api/config/gemini", json={"api_key": "saved"})
    api.post("/api/digest/refresh?topic=ai")
    assert fake_gemini == ["from-dev-env", "saved"]


def test_saving_key_preserves_other_env_lines(api):
    config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (config.CONFIG_DIR / ".env").write_text("OTHER=1\nGEMINI_API_KEY=old\n")
    api.put("/api/config/gemini", json={"api_key": "new"})
    text = (config.CONFIG_DIR / ".env").read_text()
    assert "OTHER=1" in text and "new" in text and "old" not in text


def test_app_imports_without_any_key():
    import importlib, sys
    sys.modules.pop("app.feeds.digest", None)
    importlib.import_module("app.feeds.digest")
