"""Monthly budgets under /api/banco/budgets.

A budget is versioned by the month it starts in: the limit in effect for month M is
the most recent one whose start is on or before M. Setting or removing a limit in a
month therefore changes that month and every later one, never the earlier ones.
"""
from fastapi import APIRouter, Body, HTTPException, Response

from banco import db, repositories, services
from banco.models import TransactionKind

from app.banco_view.adapter import _connect

router = APIRouter(prefix="/budgets")


def _check_month(year: int, month: int) -> None:
    if not 1 <= month <= 12 or not 1900 <= year <= 9999:
        raise HTTPException(422, "Mês inválido")


def _expense_category_or_error(conn, category_id: int):
    category = repositories.CategoryRepository(conn).get(category_id)
    if category is None:
        raise HTTPException(404, "Categoria não encontrada")
    if category.kind != TransactionKind.EXPENSE:
        raise HTTPException(422, "Só categorias de despesa têm orçamento")
    return category


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


@router.put("/{category_id}")
def set_budget(category_id: int, body: dict = Body(...)):
    """Set the category's monthly limit from `year`/`month` onward."""
    conn = _connect()
    try:
        _expense_category_or_error(conn, category_id)
        year, month, limit = body.get("year"), body.get("month"), body.get("limit_cents")
        if not (_is_int(year) and _is_int(month)):
            raise HTTPException(422, "Mês inválido")
        _check_month(year, month)
        if not _is_int(limit) or limit <= 0:
            raise HTTPException(422, "Limite deve ser maior que zero")
        with db.transaction(conn):
            repositories.BudgetRepository(conn).set_for_month(category_id, year, month, limit)
        return {"category_id": category_id, "year": year, "month": month, "limit_cents": limit}
    finally:
        conn.close()


@router.delete("/{category_id}", status_code=204)
def remove_budget(category_id: int, year: int | None = None, month: int | None = None):
    """Stop budgeting the category from `year`/`month` onward."""
    conn = _connect()
    try:
        _expense_category_or_error(conn, category_id)
        if year is None or month is None:
            raise HTTPException(422, "Mês inválido")
        _check_month(year, month)
        with db.transaction(conn):
            repositories.BudgetRepository(conn).end_from_month(category_id, year, month)
        return Response(status_code=204)
    finally:
        conn.close()


@router.get("")
def list_budgets(year: int, month: int):
    """Every expense category for the month: its effective limit (null if none), the
    month it starts in, and what was spent. Budgeted categories come first."""
    _check_month(year, month)
    conn = _connect()
    try:
        effective = {b.category_id: b for b in repositories.BudgetRepository(conn).list_effective(year, month)}
        spent = {
            s.category_id: s.total_cents
            for s in services.ReportService(conn).category_breakdown(year, month, TransactionKind.EXPENSE)
        }
        rows = []
        for c in repositories.CategoryRepository(conn).list(TransactionKind.EXPENSE):
            budget = effective.get(c.id)
            rows.append({
                "category_id": c.id,
                "category_name": c.name,
                "color": c.color,
                "budget_cents": budget.month_cents if budget else None,
                "starts_on": budget.starts_on.isoformat() if budget else None,
                "spent_cents": spent.get(c.id, 0),
            })
        rows.sort(key=lambda r: (r["budget_cents"] is None, r["category_name"].lower()))
        return rows
    finally:
        conn.close()
