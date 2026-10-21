from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    kind        TEXT    NOT NULL CHECK (kind IN ('checking','savings','credit_card','cash'))
);

CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    kind        TEXT    NOT NULL CHECK (kind IN ('income','expense','savings')),
    color       TEXT    NOT NULL,
    is_fixed    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transactions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    date                TEXT    NOT NULL,                       -- ISO YYYY-MM-DD
    amount_cents        INTEGER NOT NULL CHECK (amount_cents >= 0),
    kind                TEXT    NOT NULL CHECK (kind IN ('income','expense','savings')),
    description         TEXT    NOT NULL,
    account_id          INTEGER NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    category_id         INTEGER          REFERENCES categories(id) ON DELETE SET NULL,
    is_fixed_override   INTEGER,                                -- NULL = inherit from category
    import_hash         TEXT    UNIQUE,
    notes               TEXT    NOT NULL DEFAULT '',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tx_date     ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_tx_kind     ON transactions(kind);
CREATE INDEX IF NOT EXISTS idx_tx_category ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_tx_account  ON transactions(account_id);

CREATE TABLE IF NOT EXISTS csv_mappings (
    account_id INTEGER PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
    json       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS category_rules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern     TEXT    NOT NULL,
    match_type  TEXT    NOT NULL CHECK (match_type IN ('contains','regex')),
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    priority    INTEGER NOT NULL DEFAULT 100,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_rules_priority ON category_rules(priority, id);

CREATE TABLE IF NOT EXISTS budgets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    month_cents INTEGER NOT NULL CHECK (month_cents >= 0),
    starts_on   TEXT    NOT NULL,  -- ISO YYYY-MM-01
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_budgets_lookup ON budgets(category_id, starts_on DESC);

CREATE TABLE IF NOT EXISTS recurring_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    description         TEXT    NOT NULL,
    day_of_month        INTEGER NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
    kind                TEXT    NOT NULL CHECK (kind IN ('income','expense','savings')),
    amount_cents        INTEGER NOT NULL CHECK (amount_cents >= 0),
    account_id          INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    category_id         INTEGER          REFERENCES categories(id) ON DELETE SET NULL,
    is_fixed_override   INTEGER,
    notes               TEXT    NOT NULL DEFAULT '',
    active              INTEGER NOT NULL DEFAULT 1,
    last_run_on         TEXT,                              -- ISO YYYY-MM-DD, NULL = nunca rodou
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_recurring_active ON recurring_templates(active, day_of_month);

CREATE TABLE IF NOT EXISTS goals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    target_cents INTEGER NOT NULL CHECK (target_cents > 0),
    deadline     TEXT,                                     -- ISO YYYY-MM-DD, NULL = sem prazo
    notes        TEXT    NOT NULL DEFAULT '',
    archived     INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS goal_contributions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id        INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    transaction_id INTEGER NOT NULL UNIQUE REFERENCES transactions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_goal_contrib_goal ON goal_contributions(goal_id);
"""


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Use as: `with transaction(conn): conn.execute(...)`. Commits on success, rolls back on error."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
