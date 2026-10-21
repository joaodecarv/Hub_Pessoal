"""The adapter's connection is the one handle every write endpoint will use.
It must be writable and must enforce the schema's delete semantics."""
import sqlite3

import pytest

from app.banco_view import adapter


def test_connection_can_write(client):
    conn = adapter.connect()
    try:
        conn.execute("INSERT INTO accounts (name, kind) VALUES ('Cartão', 'credit_card')")
        conn.commit()
    finally:
        conn.close()

    assert "Cartão" in [a["name"] for a in adapter.list_accounts()]


def test_connection_enforces_foreign_keys(client):
    conn = adapter.connect()
    try:
        # Account 1 has transactions, so deleting it must be refused (ON DELETE RESTRICT).
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM accounts WHERE id = 1")
    finally:
        conn.close()
