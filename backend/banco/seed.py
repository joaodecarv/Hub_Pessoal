"""First-run seed data so a brand-new banco.db is immediately usable. Idempotent: runs only when the DB has no accounts and no categories."""
from __future__ import annotations

import sqlite3

from .models import Account, AccountKind, Category, TransactionKind
from .repositories import AccountRepository, CategoryRepository


def seed_if_empty(conn: sqlite3.Connection) -> None:
    accounts = AccountRepository(conn)
    cats = CategoryRepository(conn)
    if accounts.list() or cats.list():
        return

    accounts.add(Account(name="Carteira", kind=AccountKind.CASH))

    cats.add(Category(name="Salário",  kind=TransactionKind.INCOME,  color="#2F9E44"))
    cats.add(Category(name="Aluguel",  kind=TransactionKind.EXPENSE, color="#E03131", is_fixed=True))
    cats.add(Category(name="Internet", kind=TransactionKind.EXPENSE, color="#6D5AED", is_fixed=True))
    cats.add(Category(name="Mercado",  kind=TransactionKind.EXPENSE, color="#F08C00"))
    cats.add(Category(name="Lazer",    kind=TransactionKind.EXPENSE, color="#0E9BB8"))
    cats.add(Category(name="Reserva",  kind=TransactionKind.SAVINGS, color="#2563EB"))

    conn.commit()
