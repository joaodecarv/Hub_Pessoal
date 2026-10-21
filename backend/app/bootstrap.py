"""Startup data bootstrap: make sure everything the app reads and writes exists.

Runs once per app start (dev server and, later, the packaged executable). Idempotent.
"""
import shutil
import sqlite3
from datetime import date

from app import config
from app.feeds import digest_store
from banco import db
from banco.seed import seed_if_empty

BACKUPS_TO_KEEP = 14


def run(today: date | None = None) -> None:
    """`today` is injectable so tests don't depend on the clock."""
    today = today or date.today()

    config.BANCO_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.HUB_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

    _prepare_banco()
    _migrate_legacy_hub_db()
    digest_store.init_db()
    _backup_banco(today)


def _prepare_banco() -> None:
    db.init_db(config.BANCO_DB_PATH)
    conn = db.connect(config.BANCO_DB_PATH)
    try:
        seed_if_empty(conn)
    finally:
        conn.close()


def _migrate_legacy_hub_db() -> None:
    if not config.HUB_DB_PATH.exists() and config.LEGACY_HUB_DB_PATH.exists():
        shutil.copy2(config.LEGACY_HUB_DB_PATH, config.HUB_DB_PATH)


def _backup_banco(today: date) -> None:
    backup_dir = config.BANCO_DB_PATH.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    target = backup_dir / f"banco-{today:%Y-%m-%d}.db"
    if not target.exists():
        # sqlite's backup API gives a consistent copy even if the file is open elsewhere.
        src = sqlite3.connect(config.BANCO_DB_PATH)
        dst = sqlite3.connect(target)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()

    # ISO dates sort chronologically, so name order is age order.
    for old in sorted(backup_dir.glob("banco-????-??-??.db"))[:-BACKUPS_TO_KEEP]:
        old.unlink()
