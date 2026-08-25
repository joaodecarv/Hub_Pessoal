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

@router.get("/transactions")
def get_transactions(limit: int = 50, offset: int = 0):
    return adapter.recent_transactions(limit=limit, offset=offset)

@router.get("/categories")
def get_categories(year: int | None=None, month: int | None=None):
    today = date.today()
    return adapter.categories_with_totals(year or today.year, month or today.month)