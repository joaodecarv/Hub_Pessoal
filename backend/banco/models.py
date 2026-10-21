from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional


class TransactionKind(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    SAVINGS = "savings"


class AccountKind(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    CASH = "cash"


class MatchType(str, Enum):
    CONTAINS = "contains"
    REGEX = "regex"


def to_cents(value: Decimal | str | int) -> int:
    """R$ 12,34 (any form) -> 1234 cents. Always round to 2 decimals."""
    d = Decimal(str(value)) if not isinstance(value, Decimal) else value
    return int((d * 100).quantize(Decimal("1")))


def from_cents(cents: int) -> Decimal:
    """1234 -> Decimal('12.34')."""
    return (Decimal(cents) / 100).quantize(Decimal("0.01"))


@dataclass
class Account:
    name: str
    kind: AccountKind
    id: Optional[int] = None


@dataclass
class Category:
    name: str
    kind: TransactionKind          # income / expense / savings
    color: str                     # hex like "#7AA2F7"
    is_fixed: bool = False         # only meaningful for expenses
    id: Optional[int] = None


@dataclass
class Transaction:
    date: date
    amount_cents: int              # always positive; sign comes from `kind`
    kind: TransactionKind
    description: str
    account_id: int
    category_id: Optional[int] = None
    is_fixed_override: Optional[bool] = None  # None = inherit from category
    import_hash: Optional[str] = None
    notes: str = ""
    id: Optional[int] = None

    @property
    def amount(self) -> Decimal:
        return from_cents(self.amount_cents)

    @property
    def signed_amount(self) -> Decimal:
        sign = -1 if self.kind == TransactionKind.EXPENSE else 1
        return self.amount * sign


@dataclass
class CategoryRule:
    pattern: str
    match_type: MatchType
    category_id: int
    priority: int = 100
    id: Optional[int] = None


@dataclass
class Budget:
    category_id: int
    month_cents: int          # always >= 0
    starts_on: date           # first day of the month the budget takes effect
    id: Optional[int] = None

    @property
    def month_amount(self) -> Decimal:
        return from_cents(self.month_cents)


@dataclass
class RecurringTemplate:
    description: str
    day_of_month: int              # 1..31; clamped to month-end when month is shorter
    kind: TransactionKind
    amount_cents: int              # always positive; sign comes from `kind`
    account_id: int
    category_id: Optional[int] = None
    is_fixed_override: Optional[bool] = None
    notes: str = ""
    active: bool = True
    last_run_on: Optional[date] = None     # NULL = never run yet
    id: Optional[int] = None

    @property
    def amount(self) -> Decimal:
        return from_cents(self.amount_cents)


@dataclass
class Goal:
    name: str
    target_cents: int                       # always > 0
    deadline: Optional[date] = None         # None = sem prazo
    notes: str = ""
    archived: bool = False
    id: Optional[int] = None

    @property
    def target(self) -> Decimal:
        return from_cents(self.target_cents)
