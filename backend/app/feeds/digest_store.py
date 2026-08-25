import sqlite3
from datetime import datetime
from app import config

def _connect():
      """Open the hub's own writable SQLite database."""
      conn = sqlite3.connect(config.HUB_DB_PATH)
      conn.row_factory = sqlite3.Row
      return conn
  
  
def init_db():
    """Create the digests table if it doesn't exist yet (safe to call repeatedly)."""
    with _connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS digests ("
            "  topic TEXT PRIMARY KEY,"
            "  markdown TEXT NOT NULL,"
            "  updated_at TEXT NOT NULL"
            ")"
        )


def save_digest(topic, markdown):
    """Insert (or overwrite) the cached digest for a topic. Returns the timestamp."""
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO digests (topic, markdown, updated_at) VALUES (?, ?, ?)",
            (topic, markdown, now),
        )
    return now


def load_digest(topic):
    """Return the cached digest as a dict, or None if nothing cached yet."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT topic, markdown, updated_at FROM digests WHERE topic = ?",
            (topic,),
        ).fetchone()
    if row is None:
        return None
    return {"topic": row["topic"], "markdown": row["markdown"], "updated_at": row["updated_at"]}
