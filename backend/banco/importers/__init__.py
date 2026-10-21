from __future__ import annotations

import hashlib
from pathlib import Path

from ..models import Account, Transaction


def make_hash(account_id: int, *parts: object) -> str:
    """Build a stable per-account dedup hash. Used as `import_hash` on Transaction."""
    key = "|".join([str(account_id), *(str(p) for p in parts)])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def import_file(path: str | Path, account: Account, **kwargs) -> list[Transaction]:
    """Dispatcher: pick a parser based on file extension. Returns parsed (un-persisted) transactions."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".ofx":
        from . import ofx
        return ofx.parse(path, account)
    if ext == ".csv":
        from . import csv_generic
        mapping = kwargs.get("mapping")
        if mapping is None:
            raise ValueError("CSV import requires a `mapping=CsvMapping(...)` argument")
        return csv_generic.parse(path, account, mapping)
    raise ValueError(f"Unsupported file format: {ext}")
