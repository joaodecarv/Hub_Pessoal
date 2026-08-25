import sqlite3
import sys
from app import config

if str(config.BANCO_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(config.BANCO_SRC_PATH))
    
from banco import repositories, services
from banco.models import TransactionKind
from banco.repositories import SortBy

def _connect() -> sqlite3.Connection:
    """Open the SAME SQLite file Banco uses, but READ-ONLY.
  
      `file:...?mode=ro` + uri=True asks SQLite for a read-only handle, so a bug
      in our code can never write to your real finances. We still set
      row_factory = sqlite3.Row because Banco's row-mappers read columns by name
      (r["id"], r["name"], ...)."""
    uri=f"file:{config.BANCO_DB_PATH}?mode=ro"
    conn=sqlite3.connect(uri, uri=True)
    conn.row_factory=sqlite3.Row
    return conn

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