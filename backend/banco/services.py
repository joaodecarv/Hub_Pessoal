"""Reporting / business-logic layer. Reads from SQLite, returns plain dataclasses
ready to be bound to UI widgets (donut chart, summary cards, etc.).

No Qt imports here. No SQL outside this file's helpers.
"""
from __future__ import annotations

import calendar
import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

import re

from .models import MatchType, Transaction, TransactionKind, from_cents
from .repositories import (
    CategoryRuleRepository,
    RecurringTemplateRepository,
    TransactionRepository,
)
from .importers import make_hash

UNCATEGORIZED_COLOR = "#565f89"
UNCATEGORIZED_LABEL = "Sem categoria"


# ---------- result types ----------

@dataclass
class MonthlyTotals:
    year: int
    month: int
    income_cents: int
    expense_cents: int
    savings_cents: int

    @property
    def income(self) -> Decimal: return from_cents(self.income_cents)
    @property
    def expense(self) -> Decimal: return from_cents(self.expense_cents)
    @property
    def savings(self) -> Decimal: return from_cents(self.savings_cents)

    @property
    def net_cents(self) -> int:
        """What's left over after expenses and savings transfers."""
        return self.income_cents - self.expense_cents - self.savings_cents

    @property
    def net(self) -> Decimal: return from_cents(self.net_cents)

    @property
    def savings_rate(self) -> Decimal:
        """Savings as a fraction of income (0..1). 0 if no income."""
        if self.income_cents == 0:
            return Decimal("0")
        return (Decimal(self.savings_cents) / Decimal(self.income_cents)).quantize(Decimal("0.0001"))


@dataclass
class MonthlySummary:
    current: MonthlyTotals
    previous: MonthlyTotals

    @property
    def income_delta_cents(self) -> int: return self.current.income_cents - self.previous.income_cents
    @property
    def expense_delta_cents(self) -> int: return self.current.expense_cents - self.previous.expense_cents
    @property
    def savings_delta_cents(self) -> int: return self.current.savings_cents - self.previous.savings_cents


@dataclass
class CategorySlice:
    """One slice of the donut chart."""
    category_id: Optional[int]      # None = uncategorized bucket
    category_name: str
    color: str
    kind: TransactionKind
    is_fixed: bool
    total_cents: int

    @property
    def total(self) -> Decimal: return from_cents(self.total_cents)


@dataclass
class FixedVsVariable:
    fixed_cents: int
    variable_cents: int

    @property
    def fixed(self) -> Decimal: return from_cents(self.fixed_cents)
    @property
    def variable(self) -> Decimal: return from_cents(self.variable_cents)
    @property
    def total_cents(self) -> int: return self.fixed_cents + self.variable_cents


@dataclass
class GoalProgress:
    goal_id: int
    name: str
    target_cents: int
    saved_cents: int
    deadline: Optional[date]
    created_on: date

    @property
    def target(self) -> Decimal: return from_cents(self.target_cents)
    @property
    def saved(self) -> Decimal: return from_cents(self.saved_cents)

    @property
    def remaining_cents(self) -> int:
        return max(0, self.target_cents - self.saved_cents)

    @property
    def remaining(self) -> Decimal:
        return from_cents(self.remaining_cents)

    @property
    def ratio(self) -> float:
        """Saved / target. May exceed 1.0 if the user over-shoots."""
        return self.saved_cents / self.target_cents if self.target_cents else 0.0

    @property
    def achieved(self) -> bool:
        return self.saved_cents >= self.target_cents

    @property
    def days_remaining(self) -> Optional[int]:
        if self.deadline is None:
            return None
        return (self.deadline - date.today()).days

    @property
    def on_track(self) -> Optional[bool]:
        """True if pace matches what we'd expect at this point in the timeline.
        None when there's no deadline or the goal is already achieved.
        False when overdue or behind the linear pace."""
        if self.deadline is None or self.achieved:
            return None
        today = date.today()
        if today >= self.deadline:
            return False
        total_days = (self.deadline - self.created_on).days
        if total_days <= 0:
            return self.achieved
        elapsed = (today - self.created_on).days
        expected_ratio = max(0.0, min(1.0, elapsed / total_days))
        return self.ratio >= expected_ratio


@dataclass
class BudgetProgress:
    category_id: int
    category_name: str
    category_color: str
    budget_cents: int
    spent_cents: int

    @property
    def budget(self) -> Decimal: return from_cents(self.budget_cents)
    @property
    def spent(self) -> Decimal: return from_cents(self.spent_cents)
    @property
    def remaining_cents(self) -> int: return self.budget_cents - self.spent_cents
    @property
    def remaining(self) -> Decimal: return from_cents(self.remaining_cents)

    @property
    def ratio(self) -> float:
        """Spent / budget. > 1.0 means over budget. 0.0 if budget is 0."""
        return self.spent_cents / self.budget_cents if self.budget_cents else 0.0

    @property
    def over_budget(self) -> bool:
        return self.spent_cents > self.budget_cents


# ---------- service ----------

def _month_bounds(year: int, month: int) -> tuple[str, str]:
    last = calendar.monthrange(year, month)[1]
    return date(year, month, 1).isoformat(), date(year, month, last).isoformat()


def _prev_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


class ReportService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def monthly_totals(self, year: int, month: int) -> MonthlyTotals:
        start, end = _month_bounds(year, month)
        rows = self.conn.execute(
            """SELECT kind, COALESCE(SUM(amount_cents), 0) AS total
                 FROM transactions
                WHERE date BETWEEN ? AND ?
                GROUP BY kind""",
            (start, end),
        ).fetchall()
        by_kind = {r["kind"]: r["total"] for r in rows}
        return MonthlyTotals(
            year=year, month=month,
            income_cents=by_kind.get("income", 0),
            expense_cents=by_kind.get("expense", 0),
            savings_cents=by_kind.get("savings", 0),
        )

    def monthly_summary(self, year: int, month: int) -> MonthlySummary:
        py, pm = _prev_month(year, month)
        return MonthlySummary(
            current=self.monthly_totals(year, month),
            previous=self.monthly_totals(py, pm),
        )

    def category_breakdown(
        self, year: int, month: int, kind: TransactionKind = TransactionKind.EXPENSE
    ) -> list[CategorySlice]:
        """Per-category totals for the donut chart, sorted largest-first.
        Uncategorized transactions are bucketed into a single 'Sem categoria' slice."""
        start, end = _month_bounds(year, month)
        rows = self.conn.execute(
            """SELECT c.id          AS category_id,
                      c.name        AS category_name,
                      c.color       AS color,
                      c.is_fixed    AS is_fixed,
                      SUM(t.amount_cents) AS total
                 FROM transactions t
                 LEFT JOIN categories c ON c.id = t.category_id
                WHERE t.date BETWEEN ? AND ?
                  AND t.kind = ?
                GROUP BY c.id
                ORDER BY total DESC""",
            (start, end, kind.value),
        ).fetchall()

        slices: list[CategorySlice] = []
        for r in rows:
            if r["category_id"] is None:
                slices.append(CategorySlice(
                    category_id=None,
                    category_name=UNCATEGORIZED_LABEL,
                    color=UNCATEGORIZED_COLOR,
                    kind=kind,
                    is_fixed=False,
                    total_cents=r["total"],
                ))
            else:
                slices.append(CategorySlice(
                    category_id=r["category_id"],
                    category_name=r["category_name"],
                    color=r["color"],
                    kind=TransactionKind(kind.value),  # categories share the kind we filtered by
                    is_fixed=bool(r["is_fixed"]),
                    total_cents=r["total"],
                ))
        return slices

    def fixed_vs_variable(self, year: int, month: int) -> FixedVsVariable:
        """Split monthly expenses into fixed vs variable, respecting per-transaction overrides."""
        start, end = _month_bounds(year, month)
        rows = self.conn.execute(
            """SELECT COALESCE(t.is_fixed_override, c.is_fixed, 0) AS resolved_fixed,
                      SUM(t.amount_cents)                          AS total
                 FROM transactions t
                 LEFT JOIN categories c ON c.id = t.category_id
                WHERE t.date BETWEEN ? AND ?
                  AND t.kind = 'expense'
                GROUP BY resolved_fixed""",
            (start, end),
        ).fetchall()
        by_fixed = {r["resolved_fixed"]: r["total"] for r in rows}
        return FixedVsVariable(
            fixed_cents=by_fixed.get(1, 0),
            variable_cents=by_fixed.get(0, 0),
        )

    def budget_progress(self, year: int, month: int) -> list[BudgetProgress]:
        """For every category with an effective budget this month, return budget vs spent.
        Categories without a budget are omitted. Sorted by ratio descending (over-budget first)."""
        start, end = _month_bounds(year, month)
        first_of_month = f"{year:04d}-{month:02d}-01"
        rows = self.conn.execute(
            """WITH effective AS (
                   SELECT b.category_id, b.month_cents
                     FROM budgets b
                     JOIN (
                         SELECT category_id, MAX(starts_on) AS latest
                           FROM budgets
                          WHERE starts_on <= ?
                          GROUP BY category_id
                     ) latest_b
                       ON b.category_id = latest_b.category_id
                      AND b.starts_on   = latest_b.latest
               )
               SELECT c.id           AS category_id,
                      c.name         AS category_name,
                      c.color        AS category_color,
                      e.month_cents  AS budget_cents,
                      COALESCE((
                          SELECT SUM(t.amount_cents)
                            FROM transactions t
                           WHERE t.category_id = c.id
                             AND t.kind = 'expense'
                             AND t.date BETWEEN ? AND ?
                      ), 0)          AS spent_cents
                 FROM effective e
                 JOIN categories c ON c.id = e.category_id
                WHERE e.month_cents > 0""",
            (first_of_month, start, end),
        ).fetchall()
        progress = [
            BudgetProgress(
                category_id=r["category_id"],
                category_name=r["category_name"],
                category_color=r["category_color"],
                budget_cents=r["budget_cents"],
                spent_cents=r["spent_cents"],
            )
            for r in rows
        ]
        progress.sort(key=lambda p: p.ratio, reverse=True)
        return progress


# ---------- auto-categorization rules ----------

class RuleService:
    """Match a transaction description against user-defined rules and return the
    first matching category_id (by ascending priority). Returns None if nothing matches."""

    def __init__(self, conn: sqlite3.Connection):
        self.rules_repo = CategoryRuleRepository(conn)

    def apply(self, description: str) -> Optional[int]:
        if not description:
            return None
        haystack_lower = description.lower()
        for rule in self.rules_repo.list():
            if rule.match_type == MatchType.CONTAINS:
                if rule.pattern.lower() in haystack_lower:
                    return rule.category_id
            elif rule.match_type == MatchType.REGEX:
                try:
                    if re.search(rule.pattern, description, flags=re.IGNORECASE):
                        return rule.category_id
                except re.error:
                    # invalid pattern — skip this rule rather than crash the import
                    continue
        return None


# ---------- recurring transactions ----------

class RecurringService:
    """Materializes recurring templates into real transactions, once per month.
    Idempotent via two layers: `last_run_on` filters out templates already processed
    this month, and `import_hash` UNIQUE on the transaction is the safety net."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.templates = RecurringTemplateRepository(conn)
        self.tx_repo = TransactionRepository(conn)

    def run_due(self, today: date) -> int:
        """Create one transaction per due template. Returns how many were created."""
        created = 0
        last_day = calendar.monthrange(today.year, today.month)[1]
        for t in self.templates.list_due(today):
            effective_day = min(t.day_of_month, last_day)
            if effective_day > today.day:
                continue
            tx_date = date(today.year, today.month, effective_day)
            tx = Transaction(
                date=tx_date,
                amount_cents=t.amount_cents,
                kind=t.kind,
                description=t.description,
                account_id=t.account_id,
                category_id=t.category_id,
                is_fixed_override=t.is_fixed_override,
                import_hash=make_hash(
                    t.account_id, "recurring", tx_date.isoformat(),
                    t.amount_cents, t.kind.value, t.id,
                ),
                notes=t.notes,
            )
            before_id = tx.id
            self.tx_repo.add(tx)
            # tx.id stays None on dedup collision (existing row returned, not the one we passed)
            self.templates.mark_run(t.id, today)
            if tx.id is not None and tx.id != before_id:
                created += 1
        return created


# ---------- goals ----------

class GoalService:
    """Computes saved-vs-target progress for each goal in a single query.
    Knows nothing about UI — returns plain GoalProgress dataclasses."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_progress(self, *, include_archived: bool = False) -> list[GoalProgress]:
        sql = """SELECT g.id           AS goal_id,
                        g.name         AS name,
                        g.target_cents AS target_cents,
                        g.deadline     AS deadline,
                        g.created_at   AS created_at,
                        COALESCE(SUM(t.amount_cents), 0) AS saved_cents
                   FROM goals g
                   LEFT JOIN goal_contributions gc ON gc.goal_id = g.id
                   LEFT JOIN transactions t       ON t.id = gc.transaction_id"""
        if not include_archived:
            sql += " WHERE g.archived = 0"
        sql += " GROUP BY g.id ORDER BY g.deadline IS NULL, g.deadline, g.name COLLATE NOCASE"
        rows = self.conn.execute(sql).fetchall()
        out: list[GoalProgress] = []
        for r in rows:
            created_raw = r["created_at"]
            # created_at is a sqlite "YYYY-MM-DD HH:MM:SS" string from datetime('now')
            created_on = date.fromisoformat(created_raw.split(" ", 1)[0])
            out.append(GoalProgress(
                goal_id=r["goal_id"],
                name=r["name"],
                target_cents=r["target_cents"],
                saved_cents=r["saved_cents"],
                deadline=date.fromisoformat(r["deadline"]) if r["deadline"] else None,
                created_on=created_on,
            ))
        return out
