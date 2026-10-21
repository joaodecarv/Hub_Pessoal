"""Test harness for the Banco API.

We never touch João's real banco.db, hub.db or config dir. An autouse fixture
points every path in `config` at a pytest tmp dir for every test; the `client`
fixture then builds a throwaway SQLite file from Banco's own SCHEMA, seeded with
a small, known set of transactions across several months, and points
`config.BANCO_DB_PATH` at it (the adapter reads it at call time). We drive the
real FastAPI app through a TestClient — so the tests exercise the whole stack the
way a browser would, without caring about internal function wiring.
"""
import os
import sqlite3

# app.feeds.digest builds a Gemini client at import time, which requires a key.
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import pytest
from fastapi.testclient import TestClient

from app import config
from banco.db import SCHEMA


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    """Redirect every on-disk location the app uses into tmp_path."""
    monkeypatch.setattr(config, "BANCO_DB_PATH", tmp_path / "data" / "banco" / "banco.db")
    monkeypatch.setattr(config, "HUB_DB_PATH", tmp_path / "data" / "hubpessoal" / "hub.db")
    monkeypatch.setattr(config, "LEGACY_HUB_DB_PATH", tmp_path / "legacy" / "hub.db")
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path / "config" / "hubpessoal")


# (date, amount_cents, kind, description, category_id) for one checking account.
# Categories: 1 = Aluguel (fixed expense), 2 = Mercado (variable expense), 3 = Salário (income).
SEED_TRANSACTIONS = [
    ("2025-11-25",  3000, "expense", "Mercado nov",   2),  # Nov 2025 expense = 3000
    ("2025-12-05",  7000, "expense", "Aluguel dez",   1),  # Dec 2025 expense = 7000
    ("2026-01-15", 10000, "expense", "Mercado jan",   2),  # Jan 2026 expense = 10000
    ("2026-02-01", 100000, "income", "Salario fev",   3),
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
                (3, "Salário", "income", "#3a7a4a", 0),
                (4, "Viagem", "expense", "#6a5a8a", 0),
            ],
        )
        # Mercado budget: R$ 80 from Jan 2026, lowered to R$ 60 from Mar 2026. Aluguel has none.
        # Viagem has a R$ 300 budget but no transactions at all.
        conn.executemany(
            "INSERT INTO budgets (category_id, month_cents, starts_on) VALUES (?,?,?)",
            [(2, 8000, "2026-01-01"), (2, 6000, "2026-03-01"), (4, 30000, "2026-01-01")],
        )
        conn.executemany(
            "INSERT INTO transactions (date, amount_cents, kind, description, account_id, category_id) "
            "VALUES (?,?,?,?,1,?)",
            SEED_TRANSACTIONS,
        )
        # A goal funded by the Feb savings transaction (id 5), with no deadline.
        conn.execute(
            "INSERT INTO goals (id, name, target_cents, created_at) "
            "VALUES (1, 'Reserva', 60000, '2026-01-01 00:00:00')"
        )
        conn.execute("INSERT INTO goal_contributions (goal_id, transaction_id) VALUES (1, 5)")
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
