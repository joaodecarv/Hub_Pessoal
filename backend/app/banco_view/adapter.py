import calendar
import sqlite3
from datetime import date
from app import config

from banco import db, repositories, services
from banco.models import TransactionKind
from banco.repositories import SortBy

def _connect() -> sqlite3.Connection:
    """Open the SAME SQLite file Banco uses, writable, with foreign keys ON.

    Callers that write wrap the work in `banco.db.transaction(conn)` so a failed
    request rolls back. Rows come back as sqlite3.Row because Banco's row-mappers
    read columns by name (r["id"], r["name"], ...)."""
    return db.connect(config.BANCO_DB_PATH)

def list_accounts() -> list[dict]:
    """Every accounts as plain dicts: id, name, kind.
    
    We open a connection, hand it to Banco's own AccountRepository, and let
    Banco do the SQL. We only translate its Account objects into dicts, because
    the next layer (the API) sends dicts out as JSON.
    """
    conn=_connect()
    try:
        accounts=repositories.AccountRepository(conn).list()
        return [
            {"id": a.id, "name": a.name, "kind": a.kind.value}
            for a in accounts
        ]
    finally:
        conn.close()
        
        
def _totals_to_dict(t)->dict:
    """One MonthlyTotals -> plain dict. net_cents is a @property on the
      dataclass (income - expense - savings); we read it like a field."""
    return {
        "income_cents": t.income_cents,
        "expense_cents": t.expense_cents,
        "savings_cents": t.savings_cents,
        "net_cents": t.net_cents,
    }
    
def _prev_year_month(year: int, month: int) -> tuple[int, int]:
    """The (year, month) immediately before the given one (handles January)."""
    return (year - 1, 12) if month == 1 else (year, month - 1)


def monthly_trends(year: int, month: int, months: int = 6) -> list[dict]:
    """Income/expense/savings/net for the last `months` months, ending at the
    given month, oldest-first. Months with no transactions report zeros (not
    gaps), because we ask Banco for every month in the window."""
    walk = []
    y, m = year, month
    for _ in range(months):
        walk.append((y, m))
        y, m = _prev_year_month(y, m)
    walk.reverse()  # oldest first

    conn = _connect()
    try:
        report = services.ReportService(conn)
        out = []
        for yy, mm in walk:
            t = report.monthly_totals(yy, mm)
            out.append({"year": yy, "month": mm, **_totals_to_dict(t)})
        return out
    finally:
        conn.close()


def fixed_vs_variable(year: int, month: int) -> dict:
    """Split the month's expenses into fixed vs variable (in cents). Banco resolves
    each transaction's fixedness from its per-transaction override or its category."""
    conn = _connect()
    try:
        fv = services.ReportService(conn).fixed_vs_variable(year, month)
        return {"fixed_cents": fv.fixed_cents, "variable_cents": fv.variable_cents}
    finally:
        conn.close()


def month_summary(year:int, month:int) -> dict:
    """Income/expense/savings/net for the given month AND the month before it.
    Returns cents (integers). Formatting to 'R$ 5.200,00' is the frontend's job."""
    conn=_connect()
    try:
        summary = services.ReportService(conn).monthly_summary(year, month)
        return {
            "year": year,
            "month": month,
            "current": _totals_to_dict(summary.current),
            "previous": _totals_to_dict(summary.previous),
        }
    finally:
        conn.close()
        
def recent_transactions(limit: int=50,offset: int=0)->list[dict]:
    """Most-recent-first transactions, paged with limit/offset.

      Banco's TransactionRepository.list() does the SQL and sorting; we translate
      each Transaction into a JSON-ready dict. Two conversions matter:
        - date  -> ISO string ("2026-05-12"), because JSON has no date type
        - kind  -> its .value string ("expense"), not the enum object"""
    conn = _connect()
    try:
        txs = repositories.TransactionRepository(conn).list(
            sort=SortBy.DATE_DESC,
            limit=limit,
            offset=offset,
        )
        return [
            {
                "id": t.id,
                "date": t.date.isoformat(),
                "amount_cents": t.amount_cents,
                "kind": t.kind.value,
                "description": t.description,
                "account_id": t.account_id,
                "category_id": t.category_id,
                "notes": t.notes,
            }
            for t in txs
        ]
    finally:
        conn.close()
        
        
def categories_with_totals(year:int, month:int)->list[dict]:
    """Per-category spend for the month (the donut chart), largest first.

      Banco's category_breakdown defaults to EXPENSE and folds uncategorized
      transactions into one slice (category_id=None, name 'Sem categoria').
      We pass that through; the frontend can color the slices using `color`."""
    conn=_connect()
    try:
        slices = services.ReportService(conn).category_breakdown(
            year,
            month,
            kind=TransactionKind.EXPENSE,
        )
        return [
            {
                "category_id": s.category_id,
                "category_name": s.category_name,
                "color": s.color,
                "is_fixed": s.is_fixed,
                "total_cents": s.total_cents,
            }
            for s in slices
        ]
    finally:
        conn.close()


def account_balances() -> list[dict]:
    """Each account with its balance = sum of all its transactions, signed the way
    Banco signs them (expense negative; income and savings positive).

    Banco stores no opening balance, so this only matches the real bank if the
    opening balance was entered as a transaction (see PLAN.md, "Future: desktop app")."""
    conn = _connect()
    try:
        tx_repo = repositories.TransactionRepository(conn)
        out = []
        for a in repositories.AccountRepository(conn).list():
            balance = sum(
                -t.amount_cents if t.kind == TransactionKind.EXPENSE else t.amount_cents
                for t in tx_repo.list(account_id=a.id)
            )
            out.append({"id": a.id, "name": a.name, "kind": a.kind.value, "balance_cents": balance})
        return out
    finally:
        conn.close()


def goals_progress(year: int, month: int) -> list[dict]:
    """Active goals with saved-vs-target progress. Banco's GoalProgress computes the
    pace (on_track); we only flatten it, with the deadline as an ISO string or None.
    month_contribution_cents is what the goal's linked transactions added in year/month
    (Banco has no service for this, so we sum goal_contributions ourselves)."""
    last_day = calendar.monthrange(year, month)[1]
    conn = _connect()
    try:
        contributed = dict(conn.execute(
            """SELECT gc.goal_id, SUM(t.amount_cents)
                 FROM goal_contributions gc
                 JOIN transactions t ON t.id = gc.transaction_id
                WHERE t.date BETWEEN ? AND ?
                GROUP BY gc.goal_id""",
            (date(year, month, 1).isoformat(), date(year, month, last_day).isoformat()),
        ).fetchall())
        return [
            {
                "id": g.goal_id,
                "name": g.name,
                "target_cents": g.target_cents,
                "saved_cents": g.saved_cents,
                "deadline": g.deadline.isoformat() if g.deadline else None,
                "days_remaining": g.days_remaining,
                "achieved": g.achieved,
                "on_track": g.on_track,
                "month_contribution_cents": contributed.get(g.goal_id, 0),
            }
            for g in services.GoalService(conn).list_progress()
        ]
    finally:
        conn.close()


def top_expenses(year: int, month: int, limit: int = 5) -> list[dict]:
    """The month's largest expense transactions, largest first."""
    last_day = calendar.monthrange(year, month)[1]
    conn = _connect()
    try:
        txs = repositories.TransactionRepository(conn).list(
            date_from=date(year, month, 1),
            date_to=date(year, month, last_day),
            kind=TransactionKind.EXPENSE,
            sort=SortBy.AMOUNT_DESC,
            limit=limit,
        )
        return [
            {"id": t.id, "date": t.date.isoformat(), "description": t.description,
             "amount_cents": t.amount_cents}
            for t in txs
        ]
    finally:
        conn.close()


def daily_expenses(year: int, month: int) -> list[dict]:
    """Expense total for every day of the month (zero-filled), for the month-to-date curve."""
    last_day = calendar.monthrange(year, month)[1]
    conn = _connect()
    try:
        txs = repositories.TransactionRepository(conn).list(
            date_from=date(year, month, 1),
            date_to=date(year, month, last_day),
            kind=TransactionKind.EXPENSE,
        )
        by_day = [0] * last_day
        for t in txs:
            by_day[t.date.day - 1] += t.amount_cents
        return [{"day": d + 1, "expense_cents": c} for d, c in enumerate(by_day)]
    finally:
        conn.close()


def _month_window(year: int, month: int, months: int) -> list[tuple[int, int]]:
    """(year, month) pairs for `months` months ending at the given one, oldest first."""
    walk = [(year, month)]
    for _ in range(months - 1):
        walk.append(_prev_year_month(*walk[-1]))
    return walk[::-1]


def category_history(year: int, month: int, months: int = 6, kind: str = "expense") -> list[dict]:
    """Per-category totals for each month of the window (oldest first, zero where a category
    had nothing), ordered by the last month's total, largest first. Uncategorized rows share
    one 'Sem categoria' entry, as in Banco's category_breakdown."""
    window = _month_window(year, month, months)
    conn = _connect()
    try:
        report = services.ReportService(conn)
        rows: dict = {}
        for i, (yy, mm) in enumerate(window):
            for s in report.category_breakdown(yy, mm, kind=TransactionKind(kind)):
                row = rows.setdefault(s.category_id, {
                    "category_id": s.category_id,
                    "category_name": s.category_name,
                    "is_fixed": s.is_fixed,
                    "history_cents": [0] * len(window),
                })
                row["history_cents"][i] = s.total_cents
        budgets = {b.category_id: b.budget_cents for b in report.budget_progress(year, month)}
        categories = repositories.CategoryRepository(conn)
        for cid in budgets.keys() - rows.keys():
            c = categories.get(cid)
            if c.kind.value == kind:
                rows[cid] = {"category_id": cid, "category_name": c.name, "is_fixed": c.is_fixed,
                             "history_cents": [0] * len(window)}
        for row in rows.values():
            row["budget_cents"] = budgets.get(row["category_id"])
        return sorted(rows.values(), key=lambda r: r["history_cents"][-1], reverse=True)
    finally:
        conn.close()
