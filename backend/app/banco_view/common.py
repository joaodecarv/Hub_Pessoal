"""Helpers shared by the Banco write endpoints."""
from contextlib import contextmanager

from fastapi import HTTPException

from app.banco_view import adapter


@contextmanager
def connection():
    """Open the Banco database for one request and close it afterwards. Used as
    `with connection() as conn:` inside the handler, so the connection stays in the
    handler's own thread (sqlite3 connections cannot cross threads)."""
    conn = adapter.connect()
    try:
        yield conn
    finally:
        conn.close()


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_positive_int(value) -> bool:
    return is_int(value) and value > 0


def raise_422(errors: list[str]) -> None:
    """One 422 whose `detail` is a readable sentence listing every problem found."""
    if errors:
        raise HTTPException(422, "; ".join(errors))


def get_or_404(item, message: str):
    if item is None:
        raise HTTPException(404, message)
    return item
