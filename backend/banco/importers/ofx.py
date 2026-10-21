"""OFX importer — works for most Brazilian banks (Itaú, Inter, Bradesco, etc.) that export .ofx statements.

Requires `ofxparse` (in requirements.txt). Install inside a venv:
    python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from ..models import Account, Transaction, TransactionKind, to_cents
from . import make_hash


def parse(path: Path, account: Account) -> list[Transaction]:
    from ofxparse import OfxParser  # imported lazily so the rest of the app runs without it

    if account.id is None:
        raise ValueError("Account must be persisted (have an id) before importing")

    with open(path, "rb") as f:
        ofx = OfxParser.parse(f)

    transactions: list[Transaction] = []
    for ofx_account in ofx.accounts:
        for t in ofx_account.statement.transactions:
            amount: Decimal = t.amount
            kind = TransactionKind.EXPENSE if amount < 0 else TransactionKind.INCOME
            description = (t.payee or t.memo or "").strip() or "(sem descrição)"
            # FITID is the bank's stable per-transaction id — perfect for dedup
            fitid = getattr(t, "id", None) or getattr(t, "fitid", None)
            import_hash = make_hash(account.id, "ofx", fitid or f"{t.date.isoformat()}|{amount}|{description}")

            transactions.append(Transaction(
                date=t.date.date() if hasattr(t.date, "date") else t.date,
                amount_cents=to_cents(abs(amount)),
                kind=kind,
                description=description,
                account_id=account.id,
                import_hash=import_hash,
            ))
    return transactions
