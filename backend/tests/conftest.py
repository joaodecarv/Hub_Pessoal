"""Test harness for the Banco read-only API.

We never touch João's real banco.db. Instead each test run gets a throwaway
SQLite file built from Banco's own SCHEMA and seeded with a small, known set of
transactions across several months. We point `config.BANCO_DB_PATH` at that file
(the adapter reads it read-only at call time) and drive the real FastAPI app
through a TestClient — so the tests exercise the whole stack the way a browser
would, without caring about internal function wiring.
"""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import config
# Importing the adapter puts Banco's source on sys.path, so `banco.db` is importable.
from app.banco_view import adapter  # noqa: F401
from banco.db import SCHEMA


# (date, amount_cents, kind, description, category_id) for one checking account.
# Categories: 1 = Aluguel (fixed expense), 2 = Mercado (variable expense).
SEED_TRANSACTIONS = [
    ("2025-11-25",  3000, "expense", "Mercado nov",   2),  # Nov 2025 expense = 3000
    ("2025-12-05",  7000, "expense", "Aluguel dez",   1),  # Dec 2025 expense = 7000
    ("2026-01-15", 10000, "expense", "Mercado jan",   2),  # Jan 2026 expense = 10000
    ("2026-02-01", 100000, "income", "Salario fev",   None),
    ("2026-02-03", 15000, "savings", "Poupanca fev",  None),
    ("2026-02-10", 20000, "expense", "Aluguel fev",   1),  # Feb fixed expense
    ("2026-02-20",  5000, "expense", "Mercado fev",   2),  # Feb variable expense
    # March 2026 intentionally left empty -> must report zeros, not a gap.
]


def _seed(db_path):
    """Create the temp DB with Banco's schema and our known rows (writable here;
    the app will only ever read it)."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT INTO accounts (id, name, kind) VALUES (1, 'Checking', 'checking')"
        )
        conn.executemany(
            "INSERT INTO categories (id, name, kind, color, is_fixed) VALUES (?,?,?,?,?)",
            [
                (1, "Aluguel", "expense", "#8a6d3b", 1),
                (2, "Mercado", "expense", "#5b7a8a", 0),
            ],
        )
        conn.executemany(
            "INSERT INTO transactions (date, amount_cents, kind, description, account_id, category_id) "
            "VALUES (?,?,?,?,1,?)",
            SEED_TRANSACTIONS,
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "banco_test.db"
    _seed(db_path)
    monkeypatch.setattr(config, "BANCO_DB_PATH", str(db_path))

    # Import the app only after the DB path is patched.
    from app.main import app
    return TestClient(app)
