"""Generic CSV importer with a per-account column mapping.

Each bank ships a different CSV layout, so we don't hardcode any of them.
Instead, the user (or UI) builds a `CsvMapping` once per account; the app stores it
and reuses it on every subsequent import.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Union

from ..models import Account, Transaction, TransactionKind, to_cents
from . import make_hash

ColumnRef = Union[str, int]  # column name (header) or 0-based index


@dataclass
class CsvMapping:
    date_col: ColumnRef
    description_col: ColumnRef
    # Either a single signed amount column, OR separate debit/credit columns.
    amount_col: Optional[ColumnRef] = None
    debit_col: Optional[ColumnRef] = None      # money going out (positive value in source)
    credit_col: Optional[ColumnRef] = None     # money coming in (positive value in source)
    date_format: str = "%d/%m/%Y"
    decimal_separator: str = ","               # "," for pt-BR, "." for en-US
    thousands_separator: str = "."             # "." for pt-BR, "," for en-US
    has_header: bool = True
    encoding: str = "utf-8"
    delimiter: str = ","
    invert_sign: bool = False                  # flip if a bank reports expenses as positive


def _pick(row: list[str] | dict[str, str], col: ColumnRef) -> str:
    if isinstance(col, int):
        return row[col] if isinstance(row, list) else list(row.values())[col]
    return row[col] if isinstance(row, dict) else row[int(col)]


def _parse_amount(raw: str, mapping: CsvMapping) -> Decimal:
    s = raw.strip().replace(mapping.thousands_separator, "")
    if mapping.decimal_separator != ".":
        s = s.replace(mapping.decimal_separator, ".")
    s = s.replace(" ", "")
    if not s:
        return Decimal("0")
    try:
        return Decimal(s)
    except InvalidOperation as e:
        raise ValueError(f"Could not parse amount {raw!r}") from e


def parse(path: Path, account: Account, mapping: CsvMapping) -> list[Transaction]:
    if account.id is None:
        raise ValueError("Account must be persisted (have an id) before importing")
    if mapping.amount_col is None and not (mapping.debit_col or mapping.credit_col):
        raise ValueError("Mapping must define either amount_col or debit/credit columns")

    transactions: list[Transaction] = []
    occurrences: dict[tuple, int] = {}
    with open(path, newline="", encoding=mapping.encoding) as f:
        if mapping.has_header:
            reader = csv.DictReader(f, delimiter=mapping.delimiter)
            rows = list(reader)
        else:
            reader = csv.reader(f, delimiter=mapping.delimiter)
            rows = list(reader)

        for row in rows:
            date_raw = _pick(row, mapping.date_col).strip()
            description = _pick(row, mapping.description_col).strip() or "(sem descrição)"

            if mapping.amount_col is not None:
                amount = _parse_amount(_pick(row, mapping.amount_col), mapping)
            else:
                debit = _parse_amount(_pick(row, mapping.debit_col), mapping) if mapping.debit_col else Decimal("0")
                credit = _parse_amount(_pick(row, mapping.credit_col), mapping) if mapping.credit_col else Decimal("0")
                amount = credit - debit

            if mapping.invert_sign:
                amount = -amount

            if amount == 0:
                continue

            tx_date = datetime.strptime(date_raw, mapping.date_format).date()
            kind = TransactionKind.EXPENSE if amount < 0 else TransactionKind.INCOME
            amount_cents = to_cents(abs(amount))
            key = (tx_date.isoformat(), amount_cents, kind.value, description)
            # Identical rows in one file are distinct transactions: the Nth repeat gets its
            # index in the hash. The first keeps the plain hash, so earlier imports still dedupe.
            n = occurrences[key] = occurrences.get(key, -1) + 1
            import_hash = make_hash(account.id, "csv", *key, *([n] if n else []))

            transactions.append(Transaction(
                date=tx_date,
                amount_cents=amount_cents,
                kind=kind,
                description=description,
                account_id=account.id,
                import_hash=import_hash,
            ))
    return transactions
