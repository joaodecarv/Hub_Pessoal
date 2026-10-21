from pathlib import Path

from fastapi.testclient import TestClient


def test_version_route_returns_contents_of_version_file():
    from app.main import app
    expected = (Path(__file__).resolve().parents[2] / "VERSION").read_text().strip()
    assert TestClient(app).get("/api/config/version").json() == {"version": expected}
