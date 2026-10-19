from datetime import date
from fastapi import APIRouter
from app.banco_view import adapter

router = APIRouter(prefix="/api/banco", tags=["banco"])

@router.get("/accounts")
def get_accounts():
    return adapter.list_accounts()

@router.get("/summary")
def get_summary(year: int | None=None, month: int | None=None):
    today = date.today()
    return adapter.month_summary(year or today.year, month or today.month)

@router.get("/trends")
def get_trends(year: int | None=None, month: int | None=None, months: int = 6):
    today = date.today()
    return adapter.monthly_trends(year or today.year, month or today.month, months)

@router.get("/fixed-variable")
def get_fixed_variable(year: int | None=None, month: int | None=None):
    today = date.today()
    return adapter.fixed_vs_variable(year or today.year, month or today.month)

@router.get("/transactions")
def get_transactions(limit: int = 50, offset: int = 0):
    return adapter.recent_transactions(limit=limit, offset=offset)

@router.get("/categories")
def get_categories(year: int | None=None, month: int | None=None):
    today = date.today()
    return adapter.categories_with_totals(year or today.year, month or today.month)

@router.get("/balances")
def get_balances():
    return adapter.account_balances()

@router.get("/goals")
def get_goals():
    return adapter.goals_progress()

@router.get("/top-expenses")
def get_top_expenses(year: int | None=None, month: int | None=None, limit: int = 5):
    today = date.today()
    return adapter.top_expenses(year or today.year, month or today.month, limit)
