from __future__ import annotations

import sqlite3
from datetime import date
from enum import Enum
from typing import Optional

import dataclasses
import json

from .importers.csv_generic import CsvMapping
from .models import (
    Account,
    AccountKind,
    Budget,
    Category,
    CategoryRule,
    Goal,
    MatchType,
    RecurringTemplate,
    Transaction,
    TransactionKind,
)


def _first_of_month(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}-01"


class SortBy(str, Enum):
    DATE_DESC = "date_desc"        # most recent first
    DATE_ASC = "date_asc"
    AMOUNT_DESC = "amount_desc"    # most expensive first
    AMOUNT_ASC = "amount_asc"
    DESCRIPTION = "description"


_SORT_SQL = {
    SortBy.DATE_DESC:    "date DESC, id DESC",
    SortBy.DATE_ASC:     "date ASC,  id ASC",
    SortBy.AMOUNT_DESC:  "amount_cents DESC, date DESC",
    SortBy.AMOUNT_ASC:   "amount_cents ASC,  date DESC",
    SortBy.DESCRIPTION:  "description COLLATE NOCASE ASC",
}


# ---------- mappers ----------

def _row_to_account(r: sqlite3.Row) -> Account:
    return Account(id=r["id"], name=r["name"], kind=AccountKind(r["kind"]))


def _row_to_category(r: sqlite3.Row) -> Category:
    return Category(
        id=r["id"],
        name=r["name"],
        kind=TransactionKind(r["kind"]),
        color=r["color"],
        is_fixed=bool(r["is_fixed"]),
    )


def _row_to_budget(r: sqlite3.Row) -> Budget:
    return Budget(
        id=r["id"],
        category_id=r["category_id"],
        month_cents=r["month_cents"],
        starts_on=date.fromisoformat(r["starts_on"]),
    )


def _row_to_rule(r: sqlite3.Row) -> CategoryRule:
    return CategoryRule(
        id=r["id"],
        pattern=r["pattern"],
        match_type=MatchType(r["match_type"]),
        category_id=r["category_id"],
        priority=r["priority"],
    )


def _row_to_goal(r: sqlite3.Row) -> Goal:
    return Goal(
        id=r["id"],
        name=r["name"],
        target_cents=r["target_cents"],
        deadline=date.fromisoformat(r["deadline"]) if r["deadline"] else None,
        notes=r["notes"],
        archived=bool(r["archived"]),
    )


def _row_to_recurring(r: sqlite3.Row) -> RecurringTemplate:
    return RecurringTemplate(
        id=r["id"],
        description=r["description"],
        day_of_month=r["day_of_month"],
        kind=TransactionKind(r["kind"]),
        amount_cents=r["amount_cents"],
        account_id=r["account_id"],
        category_id=r["category_id"],
        is_fixed_override=None if r["is_fixed_override"] is None else bool(r["is_fixed_override"]),
        notes=r["notes"],
        active=bool(r["active"]),
        last_run_on=date.fromisoformat(r["last_run_on"]) if r["last_run_on"] else None,
    )


def _row_to_transaction(r: sqlite3.Row) -> Transaction:
    return Transaction(
        id=r["id"],
        date=date.fromisoformat(r["date"]),
        amount_cents=r["amount_cents"],
        kind=TransactionKind(r["kind"]),
        description=r["description"],
        account_id=r["account_id"],
        category_id=r["category_id"],
        is_fixed_override=None if r["is_fixed_override"] is None else bool(r["is_fixed_override"]),
        import_hash=r["import_hash"],
        notes=r["notes"],
    )


# ---------- accounts ----------

class AccountRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, account: Account) -> Account:
        cur = self.conn.execute(
            "INSERT INTO accounts (name, kind) VALUES (?, ?)",
            (account.name, account.kind.value),
        )
        account.id = cur.lastrowid
        return account

    def get(self, account_id: int) -> Optional[Account]:
        r = self.conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        return _row_to_account(r) if r else None

    def get_by_name(self, name: str) -> Optional[Account]:
        r = self.conn.execute("SELECT * FROM accounts WHERE name = ?", (name,)).fetchone()
        return _row_to_account(r) if r else None

    def list(self) -> list[Account]:
        rows = self.conn.execute("SELECT * FROM accounts ORDER BY name COLLATE NOCASE").fetchall()
        return [_row_to_account(r) for r in rows]

    def update(self, account: Account) -> None:
        if account.id is None:
            raise ValueError("Cannot update account without id")
        self.conn.execute(
            "UPDATE accounts SET name = ?, kind = ? WHERE id = ?",
            (account.name, account.kind.value, account.id),
        )

    def delete(self, account_id: int) -> None:
        self.conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))


# ---------- categories ----------

class CategoryRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, category: Category) -> Category:
        cur = self.conn.execute(
            "INSERT INTO categories (name, kind, color, is_fixed) VALUES (?, ?, ?, ?)",
            (category.name, category.kind.value, category.color, int(category.is_fixed)),
        )
        category.id = cur.lastrowid
        return category

    def get(self, category_id: int) -> Optional[Category]:
        r = self.conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
        return _row_to_category(r) if r else None

    def get_by_name(self, name: str) -> Optional[Category]:
        r = self.conn.execute("SELECT * FROM categories WHERE name = ?", (name,)).fetchone()
        return _row_to_category(r) if r else None

    def list(self, kind: Optional[TransactionKind] = None) -> list[Category]:
        if kind is None:
            rows = self.conn.execute(
                "SELECT * FROM categories ORDER BY kind, is_fixed DESC, name COLLATE NOCASE"
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM categories WHERE kind = ? ORDER BY is_fixed DESC, name COLLATE NOCASE",
                (kind.value,),
            ).fetchall()
        return [_row_to_category(r) for r in rows]

    def update(self, category: Category) -> None:
        if category.id is None:
            raise ValueError("Cannot update category without id")
        self.conn.execute(
            "UPDATE categories SET name = ?, kind = ?, color = ?, is_fixed = ? WHERE id = ?",
            (category.name, category.kind.value, category.color, int(category.is_fixed), category.id),
        )

    def delete(self, category_id: int) -> None:
        self.conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))


# ---------- transactions ----------

class TransactionRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, tx: Transaction) -> Transaction:
        """Insert a transaction. If import_hash collides with an existing row, returns the existing one (dedup)."""
        try:
            cur = self.conn.execute(
                """INSERT INTO transactions
                   (date, amount_cents, kind, description, account_id, category_id,
                    is_fixed_override, import_hash, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tx.date.isoformat(),
                    tx.amount_cents,
                    tx.kind.value,
                    tx.description,
                    tx.account_id,
                    tx.category_id,
                    None if tx.is_fixed_override is None else int(tx.is_fixed_override),
                    tx.import_hash,
                    tx.notes,
                ),
            )
            tx.id = cur.lastrowid
            return tx
        except sqlite3.IntegrityError:
            if tx.import_hash:
                existing = self.conn.execute(
                    "SELECT * FROM transactions WHERE import_hash = ?", (tx.import_hash,)
                ).fetchone()
                if existing:
                    return _row_to_transaction(existing)
            raise

    def get(self, tx_id: int) -> Optional[Transaction]:
        r = self.conn.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,)).fetchone()
        return _row_to_transaction(r) if r else None

    def list(
        self,
        *,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        kind: Optional[TransactionKind] = None,
        account_id: Optional[int] = None,
        category_id: Optional[int] = None,
        is_fixed: Optional[bool] = None,
        search: Optional[str] = None,
        sort: SortBy = SortBy.DATE_DESC,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[Transaction]:
        where: list[str] = []
        params: list = []

        if date_from is not None:
            where.append("t.date >= ?")
            params.append(date_from.isoformat())
        if date_to is not None:
            where.append("t.date <= ?")
            params.append(date_to.isoformat())
        if kind is not None:
            where.append("t.kind = ?")
            params.append(kind.value)
        if account_id is not None:
            where.append("t.account_id = ?")
            params.append(account_id)
        if category_id is not None:
            where.append("t.category_id = ?")
            params.append(category_id)
        if is_fixed is not None:
            # resolved: override wins, otherwise category's is_fixed, otherwise 0
            where.append("COALESCE(t.is_fixed_override, c.is_fixed, 0) = ?")
            params.append(int(is_fixed))
        if search:
            where.append("(t.description LIKE ? OR t.notes LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like])

        sql = """SELECT t.* FROM transactions t
                 LEFT JOIN categories c ON c.id = t.category_id"""
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += f" ORDER BY {_SORT_SQL[sort]}"
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        rows = self.conn.execute(sql, params).fetchall()
        return [_row_to_transaction(r) for r in rows]

    def update(self, tx: Transaction) -> None:
        if tx.id is None:
            raise ValueError("Cannot update transaction without id")
        self.conn.execute(
            """UPDATE transactions
               SET date = ?, amount_cents = ?, kind = ?, description = ?,
                   account_id = ?, category_id = ?, is_fixed_override = ?, notes = ?
               WHERE id = ?""",
            (
                tx.date.isoformat(),
                tx.amount_cents,
                tx.kind.value,
                tx.description,
                tx.account_id,
                tx.category_id,
                None if tx.is_fixed_override is None else int(tx.is_fixed_override),
                tx.notes,
                tx.id,
            ),
        )

    def delete(self, tx_id: int) -> None:
        self.conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]


# ---------- category rules ----------

class CategoryRuleRepository:
    """Rules that auto-assign a category to a transaction whose description matches a pattern.
    Rules are evaluated in ascending priority order; first match wins."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, rule: CategoryRule) -> CategoryRule:
        cur = self.conn.execute(
            """INSERT INTO category_rules (pattern, match_type, category_id, priority)
               VALUES (?, ?, ?, ?)""",
            (rule.pattern, rule.match_type.value, rule.category_id, rule.priority),
        )
        rule.id = cur.lastrowid
        return rule

    def get(self, rule_id: int) -> Optional[CategoryRule]:
        r = self.conn.execute(
            "SELECT * FROM category_rules WHERE id = ?", (rule_id,)
        ).fetchone()
        return _row_to_rule(r) if r else None

    def list(self) -> list[CategoryRule]:
        rows = self.conn.execute(
            "SELECT * FROM category_rules ORDER BY priority, id"
        ).fetchall()
        return [_row_to_rule(r) for r in rows]

    def update(self, rule: CategoryRule) -> None:
        if rule.id is None:
            raise ValueError("Cannot update rule without id")
        self.conn.execute(
            """UPDATE category_rules
               SET pattern = ?, match_type = ?, category_id = ?, priority = ?
               WHERE id = ?""",
            (rule.pattern, rule.match_type.value, rule.category_id, rule.priority, rule.id),
        )

    def delete(self, rule_id: int) -> None:
        self.conn.execute("DELETE FROM category_rules WHERE id = ?", (rule_id,))


# ---------- budgets ----------

class BudgetRepository:
    """Per-category monthly budgets with time-versioned values. The budget effective
    in month M is the most-recent row with starts_on <= first-of-M."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def set_for_month(
        self, category_id: int, year: int, month: int, month_cents: int
    ) -> Budget:
        """Insert or replace the budget whose starts_on is exactly this month.
        Use this from the UI for inline editing — it never creates duplicate rows
        for the same (category, month)."""
        starts_on = _first_of_month(year, month)
        existing = self.conn.execute(
            "SELECT id FROM budgets WHERE category_id = ? AND starts_on = ?",
            (category_id, starts_on),
        ).fetchone()
        if existing:
            self.conn.execute(
                "UPDATE budgets SET month_cents = ? WHERE id = ?",
                (month_cents, existing["id"]),
            )
            return Budget(
                id=existing["id"],
                category_id=category_id,
                month_cents=month_cents,
                starts_on=date.fromisoformat(starts_on),
            )
        cur = self.conn.execute(
            "INSERT INTO budgets (category_id, month_cents, starts_on) VALUES (?, ?, ?)",
            (category_id, month_cents, starts_on),
        )
        return Budget(
            id=cur.lastrowid,
            category_id=category_id,
            month_cents=month_cents,
            starts_on=date.fromisoformat(starts_on),
        )

    def get_effective(self, category_id: int, year: int, month: int) -> Optional[Budget]:
        starts_on = _first_of_month(year, month)
        r = self.conn.execute(
            """SELECT * FROM budgets
               WHERE category_id = ? AND starts_on <= ?
               ORDER BY starts_on DESC LIMIT 1""",
            (category_id, starts_on),
        ).fetchone()
        return _row_to_budget(r) if r else None

    def list_effective(self, year: int, month: int) -> list[Budget]:
        """All budgets effective in (year, month), one per category."""
        starts_on = _first_of_month(year, month)
        rows = self.conn.execute(
            """SELECT b.*
                 FROM budgets b
                 JOIN (
                     SELECT category_id, MAX(starts_on) AS latest
                       FROM budgets
                      WHERE starts_on <= ?
                      GROUP BY category_id
                 ) latest_b
                   ON b.category_id = latest_b.category_id
                  AND b.starts_on   = latest_b.latest""",
            (starts_on,),
        ).fetchall()
        return [_row_to_budget(r) for r in rows]

    def delete(self, budget_id: int) -> None:
        self.conn.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))

    def delete_for_month(self, category_id: int, year: int, month: int) -> None:
        self.conn.execute(
            "DELETE FROM budgets WHERE category_id = ? AND starts_on = ?",
            (category_id, _first_of_month(year, month)),
        )


# ---------- recurring templates ----------

class RecurringTemplateRepository:
    """Recurring transaction templates. The service layer turns each due template
    into a real Transaction once per month (see RecurringService.run_due)."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, t: RecurringTemplate) -> RecurringTemplate:
        cur = self.conn.execute(
            """INSERT INTO recurring_templates
               (description, day_of_month, kind, amount_cents, account_id, category_id,
                is_fixed_override, notes, active, last_run_on)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                t.description,
                t.day_of_month,
                t.kind.value,
                t.amount_cents,
                t.account_id,
                t.category_id,
                None if t.is_fixed_override is None else int(t.is_fixed_override),
                t.notes,
                int(t.active),
                t.last_run_on.isoformat() if t.last_run_on else None,
            ),
        )
        t.id = cur.lastrowid
        return t

    def get(self, template_id: int) -> Optional[RecurringTemplate]:
        r = self.conn.execute(
            "SELECT * FROM recurring_templates WHERE id = ?", (template_id,)
        ).fetchone()
        return _row_to_recurring(r) if r else None

    def list(self, *, active_only: bool = False) -> list[RecurringTemplate]:
        sql = "SELECT * FROM recurring_templates"
        if active_only:
            sql += " WHERE active = 1"
        sql += " ORDER BY day_of_month, description COLLATE NOCASE"
        rows = self.conn.execute(sql).fetchall()
        return [_row_to_recurring(r) for r in rows]

    def list_due(self, today: date) -> list[RecurringTemplate]:
        """Active templates whose last_run_on is before this month's first day.
        The 'day_of_month already passed' check is left to the service so the
        month-end clamp lives in one place (Python, not SQL)."""
        first_of_month = _first_of_month(today.year, today.month)
        rows = self.conn.execute(
            """SELECT * FROM recurring_templates
               WHERE active = 1
                 AND (last_run_on IS NULL OR last_run_on < ?)
               ORDER BY day_of_month, id""",
            (first_of_month,),
        ).fetchall()
        return [_row_to_recurring(r) for r in rows]

    def update(self, t: RecurringTemplate) -> None:
        if t.id is None:
            raise ValueError("Cannot update template without id")
        self.conn.execute(
            """UPDATE recurring_templates
               SET description = ?, day_of_month = ?, kind = ?, amount_cents = ?,
                   account_id = ?, category_id = ?, is_fixed_override = ?, notes = ?,
                   active = ?
               WHERE id = ?""",
            (
                t.description,
                t.day_of_month,
                t.kind.value,
                t.amount_cents,
                t.account_id,
                t.category_id,
                None if t.is_fixed_override is None else int(t.is_fixed_override),
                t.notes,
                int(t.active),
                t.id,
            ),
        )

    def mark_run(self, template_id: int, when: date) -> None:
        self.conn.execute(
            "UPDATE recurring_templates SET last_run_on = ? WHERE id = ?",
            (when.isoformat(), template_id),
        )

    def delete(self, template_id: int) -> None:
        self.conn.execute("DELETE FROM recurring_templates WHERE id = ?", (template_id,))


# ---------- goals + contributions ----------

class GoalRepository:
    """Savings goals plus the many-to-one junction that ties transactions to goals.
    A transaction can contribute to at most one goal (UNIQUE on transaction_id);
    re-assigning is silent UPSERT."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, g: Goal) -> Goal:
        cur = self.conn.execute(
            """INSERT INTO goals (name, target_cents, deadline, notes, archived)
               VALUES (?, ?, ?, ?, ?)""",
            (
                g.name,
                g.target_cents,
                g.deadline.isoformat() if g.deadline else None,
                g.notes,
                int(g.archived),
            ),
        )
        g.id = cur.lastrowid
        return g

    def get(self, goal_id: int) -> Optional[Goal]:
        r = self.conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
        return _row_to_goal(r) if r else None

    def list(self, *, include_archived: bool = False) -> list[Goal]:
        sql = "SELECT * FROM goals"
        if not include_archived:
            sql += " WHERE archived = 0"
        sql += " ORDER BY archived, deadline IS NULL, deadline, name COLLATE NOCASE"
        rows = self.conn.execute(sql).fetchall()
        return [_row_to_goal(r) for r in rows]

    def update(self, g: Goal) -> None:
        if g.id is None:
            raise ValueError("Cannot update goal without id")
        self.conn.execute(
            """UPDATE goals
               SET name = ?, target_cents = ?, deadline = ?, notes = ?, archived = ?
               WHERE id = ?""",
            (
                g.name,
                g.target_cents,
                g.deadline.isoformat() if g.deadline else None,
                g.notes,
                int(g.archived),
                g.id,
            ),
        )

    def delete(self, goal_id: int) -> None:
        self.conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))

    # ---- contributions ----

    def add_contribution(self, goal_id: int, transaction_id: int) -> None:
        """Bind a transaction to a goal. If it was already bound to another goal,
        moves it (UPSERT on transaction_id)."""
        self.conn.execute(
            """INSERT INTO goal_contributions (goal_id, transaction_id) VALUES (?, ?)
               ON CONFLICT(transaction_id) DO UPDATE SET goal_id = excluded.goal_id""",
            (goal_id, transaction_id),
        )

    def remove_contribution(self, transaction_id: int) -> None:
        self.conn.execute(
            "DELETE FROM goal_contributions WHERE transaction_id = ?",
            (transaction_id,),
        )

    def contribution_for(self, transaction_id: int) -> Optional[int]:
        """Return the goal_id this transaction contributes to, or None."""
        r = self.conn.execute(
            "SELECT goal_id FROM goal_contributions WHERE transaction_id = ?",
            (transaction_id,),
        ).fetchone()
        return r["goal_id"] if r else None

    def list_contributions(self, goal_id: int) -> list[int]:
        rows = self.conn.execute(
            "SELECT transaction_id FROM goal_contributions WHERE goal_id = ?",
            (goal_id,),
        ).fetchall()
        return [r["transaction_id"] for r in rows]


# ---------- csv mappings (per-account) ----------

class CsvMappingRepository:
    """One CsvMapping per account, stored as JSON. Saves the user from re-entering
    column choices every time they import a statement from the same bank."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get(self, account_id: int) -> Optional[CsvMapping]:
        r = self.conn.execute(
            "SELECT json FROM csv_mappings WHERE account_id = ?", (account_id,)
        ).fetchone()
        if r is None:
            return None
        return CsvMapping(**json.loads(r["json"]))

    def save(self, account_id: int, mapping: CsvMapping) -> None:
        payload = json.dumps(dataclasses.asdict(mapping))
        self.conn.execute(
            """INSERT INTO csv_mappings (account_id, json) VALUES (?, ?)
               ON CONFLICT(account_id) DO UPDATE SET json = excluded.json""",
            (account_id, payload),
        )

    def delete(self, account_id: int) -> None:
        self.conn.execute("DELETE FROM csv_mappings WHERE account_id = ?", (account_id,))
