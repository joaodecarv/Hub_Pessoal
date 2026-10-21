"""Startup data bootstrap, driven through its public entry point `bootstrap.run`.

`conftest.isolated_paths` points every path at a tmp dir (nothing exists yet) and
the date is injected, so no test touches real data or depends on the clock.
"""
import sqlite3
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app import bootstrap, config


def _api():
    from app.main import app
    return TestClient(app)


def _write_hub_db(path, markdown):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE digests (topic TEXT PRIMARY KEY, markdown TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        conn.execute("INSERT INTO digests VALUES ('ai', ?, '2026-01-01T00:00:00')", (markdown,))
        conn.commit()
    finally:
        conn.close()


def _count(table, path=None):
    conn = sqlite3.connect(path or config.BANCO_DB_PATH)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def _backups():
    return sorted(p.name for p in (config.BANCO_DB_PATH.parent / "backups").glob("banco-*.db"))


def test_missing_banco_gets_schema_and_default_data():
    bootstrap.run(today=date(2026, 3, 1))

    api = _api()
    assert api.get("/api/banco/accounts").json() != []
    assert api.get("/api/banco/transactions").json() == []
    assert _count("categories") > 0


def test_existing_banco_is_left_untouched():
    bootstrap.run(today=date(2026, 3, 1))
    conn = sqlite3.connect(config.BANCO_DB_PATH)
    conn.execute("DELETE FROM categories")
    conn.execute("INSERT INTO accounts (name, kind) VALUES ('Minha conta', 'checking')")
    conn.commit()
    conn.close()

    bootstrap.run(today=date(2026, 3, 2))

    names = [a["name"] for a in _api().get("/api/banco/accounts").json()]
    assert "Minha conta" in names
    assert _count("categories") == 0


def test_creates_the_config_dir():
    bootstrap.run(today=date(2026, 3, 1))

    assert config.CONFIG_DIR.is_dir()


def test_legacy_hub_db_is_copied_when_none_exists_yet():
    _write_hub_db(config.LEGACY_HUB_DB_PATH, "legado")

    bootstrap.run(today=date(2026, 3, 1))

    assert _api().get("/api/digest", params={"topic": "ai"}).json()["markdown"] == "legado"
    assert config.LEGACY_HUB_DB_PATH.exists()  # copied, not moved


def test_legacy_hub_db_never_overwrites_an_existing_one():
    _write_hub_db(config.LEGACY_HUB_DB_PATH, "legado")
    _write_hub_db(config.HUB_DB_PATH, "atual")

    bootstrap.run(today=date(2026, 3, 1))

    assert _api().get("/api/digest", params={"topic": "ai"}).json()["markdown"] == "atual"


def test_fresh_install_without_legacy_hub_db_still_serves_digests():
    bootstrap.run(today=date(2026, 3, 1))

    assert _api().get("/api/digest", params={"topic": "ai"}).json() is None


def test_backup_is_a_dated_copy_of_the_banco():
    bootstrap.run(today=date(2026, 3, 1))

    assert _backups() == ["banco-2026-03-01.db"]
    assert _count("categories", config.BANCO_DB_PATH.parent / "backups" / "banco-2026-03-01.db") > 0


def test_at_most_one_backup_per_day():
    bootstrap.run(today=date(2026, 3, 1))
    conn = sqlite3.connect(config.BANCO_DB_PATH)
    conn.execute("INSERT INTO accounts (name, kind) VALUES ('Depois do backup', 'checking')")
    conn.commit()
    conn.close()

    bootstrap.run(today=date(2026, 3, 1))

    assert _backups() == ["banco-2026-03-01.db"]
    copy = sqlite3.connect(config.BANCO_DB_PATH.parent / "backups" / "banco-2026-03-01.db")
    try:
        names = [r[0] for r in copy.execute("SELECT name FROM accounts")]
    finally:
        copy.close()
    assert "Depois do backup" not in names


def test_starting_the_app_runs_the_bootstrap():
    from app.main import app

    with TestClient(app) as api:
        assert api.get("/api/banco/accounts").json() != []
    assert config.HUB_DB_PATH.exists()


def test_only_the_14_most_recent_backups_are_kept():
    start = date(2026, 3, 1)
    for i in range(16):
        bootstrap.run(today=start + timedelta(days=i))

    expected = [f"banco-{start + timedelta(days=i):%Y-%m-%d}.db" for i in range(2, 16)]
    assert _backups() == expected
