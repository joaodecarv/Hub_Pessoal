"""Accounts, categories and categorization rules under /api/banco/cadastros.

Same convention as transactions.py: write bodies are plain dicts validated by hand
so every 422 carries one readable Portuguese sentence in `detail`.
"""
import re
import sqlite3

from fastapi import APIRouter, Body, HTTPException, Response

from banco import db, repositories
from banco.models import (
    Account, AccountKind, Category, CategoryRule, MatchType, TransactionKind,
)

from app.banco_view.adapter import _connect

router = APIRouter(prefix="/api/banco/cadastros", tags=["cadastros"])

HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")
DEFAULT_PRIORITY = 100  # same default as the category_rules table


def _name(body: dict, errors: list[str]) -> str:
    name = body.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("Nome é obrigatório")
        return ""
    return name.strip()


def _enum(enum_cls, value, message: str, errors: list[str]):
    try:
        return enum_cls(value)
    except ValueError:
        errors.append(message)
        return None


def _save(conn, write, duplicate_message: str):
    """Run `write` in a transaction; a UNIQUE violation on the name becomes a 409."""
    try:
        with db.transaction(conn):
            write()
    except sqlite3.IntegrityError as e:
        if "UNIQUE" in str(e):
            raise HTTPException(409, duplicate_message)
        raise


# ---------- accounts ----------

def _account_to_dict(conn, a: Account) -> dict:
    count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE account_id = ?", (a.id,)
    ).fetchone()[0]
    return {"id": a.id, "name": a.name, "kind": a.kind.value, "transaction_count": count}


def _parse_account(body: dict) -> Account:
    errors: list[str] = []
    name = _name(body, errors)
    kind = _enum(AccountKind, body.get("kind"),
                 "Tipo deve ser corrente, poupança, cartão ou dinheiro", errors)
    if errors:
        raise HTTPException(422, "; ".join(errors))
    return Account(name=name, kind=kind)


def _account_or_404(conn, account_id: int) -> Account:
    account = repositories.AccountRepository(conn).get(account_id)
    if account is None:
        raise HTTPException(404, "Conta não encontrada")
    return account


@router.get("/accounts")
def list_accounts():
    conn = _connect()
    try:
        return [_account_to_dict(conn, a) for a in repositories.AccountRepository(conn).list()]
    finally:
        conn.close()


@router.post("/accounts", status_code=201)
def create_account(body: dict = Body(...)):
    account = _parse_account(body)
    conn = _connect()
    try:
        _save(conn, lambda: repositories.AccountRepository(conn).add(account),
              f"Já existe uma conta chamada {account.name}")
        return _account_to_dict(conn, account)
    finally:
        conn.close()


@router.put("/accounts/{account_id}")
def update_account(account_id: int, body: dict = Body(...)):
    conn = _connect()
    try:
        _account_or_404(conn, account_id)
        account = _parse_account(body)
        account.id = account_id
        _save(conn, lambda: repositories.AccountRepository(conn).update(account),
              f"Já existe uma conta chamada {account.name}")
        return _account_to_dict(conn, account)
    finally:
        conn.close()


@router.delete("/accounts/{account_id}", status_code=204)
def delete_account(account_id: int):
    conn = _connect()
    try:
        account = _account_or_404(conn, account_id)
        count = _account_to_dict(conn, account)["transaction_count"]
        if count:
            raise HTTPException(
                409,
                f"A conta {account.name} tem {count} {'transação' if count == 1 else 'transações'} "
                "e não pode ser excluída. "
                "Exclua ou mova as transações antes.",
            )
        with db.transaction(conn):
            repositories.AccountRepository(conn).delete(account_id)
        return Response(status_code=204)
    finally:
        conn.close()


# ---------- categories ----------

def _category_to_dict(c: Category) -> dict:
    return {"id": c.id, "name": c.name, "kind": c.kind.value, "color": c.color,
            "is_fixed": c.is_fixed}


def _parse_category(body: dict) -> Category:
    errors: list[str] = []
    name = _name(body, errors)
    kind = _enum(TransactionKind, body.get("kind"),
                 "Tipo deve ser receita, despesa ou poupança", errors)
    color = body.get("color")
    if not isinstance(color, str) or not HEX_COLOR.fullmatch(color):
        errors.append("Cor deve estar no formato #RRGGBB")
    is_fixed = body.get("is_fixed", False)
    if not isinstance(is_fixed, bool):
        errors.append("Fixa/variável deve ser verdadeiro ou falso")
    if errors:
        raise HTTPException(422, "; ".join(errors))
    return Category(name=name, kind=kind, color=color, is_fixed=is_fixed)


def _category_or_404(conn, category_id: int) -> Category:
    category = repositories.CategoryRepository(conn).get(category_id)
    if category is None:
        raise HTTPException(404, "Categoria não encontrada")
    return category


def _count_for_category(conn, table: str, category_id: int) -> int:
    return conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE category_id = ?", (category_id,)
    ).fetchone()[0]


@router.get("/categories")
def list_categories():
    conn = _connect()
    try:
        return [_category_to_dict(c) for c in repositories.CategoryRepository(conn).list()]
    finally:
        conn.close()


@router.post("/categories", status_code=201)
def create_category(body: dict = Body(...)):
    category = _parse_category(body)
    conn = _connect()
    try:
        _save(conn, lambda: repositories.CategoryRepository(conn).add(category),
              f"Já existe uma categoria chamada {category.name}")
        return _category_to_dict(category)
    finally:
        conn.close()


@router.put("/categories/{category_id}")
def update_category(category_id: int, body: dict = Body(...)):
    conn = _connect()
    try:
        _category_or_404(conn, category_id)
        category = _parse_category(body)
        category.id = category_id
        _save(conn, lambda: repositories.CategoryRepository(conn).update(category),
              f"Já existe uma categoria chamada {category.name}")
        return _category_to_dict(category)
    finally:
        conn.close()


@router.get("/categories/{category_id}/impact")
def category_delete_impact(category_id: int):
    """What deleting the category would do: transactions lose their category
    (SET NULL), its rules and budgets are deleted (CASCADE)."""
    conn = _connect()
    try:
        _category_or_404(conn, category_id)
        return {
            "transactions": _count_for_category(conn, "transactions", category_id),
            "rules": _count_for_category(conn, "category_rules", category_id),
            "budgets": _count_for_category(conn, "budgets", category_id),
        }
    finally:
        conn.close()


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int):
    conn = _connect()
    try:
        _category_or_404(conn, category_id)
        with db.transaction(conn):
            repositories.CategoryRepository(conn).delete(category_id)
        return Response(status_code=204)
    finally:
        conn.close()


# ---------- rules ----------

def _rule_to_dict(r: CategoryRule) -> dict:
    return {"id": r.id, "pattern": r.pattern, "match_type": r.match_type.value,
            "category_id": r.category_id, "priority": r.priority}


def _parse_rule(conn, body: dict) -> CategoryRule:
    errors: list[str] = []
    pattern = body.get("pattern")
    if not isinstance(pattern, str) or not pattern.strip():
        errors.append("Padrão é obrigatório")
        pattern = ""
    match_type = _enum(MatchType, body.get("match_type"),
                       'Tipo de regra deve ser "contém" ou "regex"', errors)
    if match_type == MatchType.REGEX and pattern:
        try:
            re.compile(pattern)
        except re.error as e:
            errors.append(f"Expressão regular inválida: {e}")

    category_id = body.get("category_id")
    if category_id is None or repositories.CategoryRepository(conn).get(category_id) is None:
        errors.append("Categoria não encontrada")

    priority = body.get("priority", DEFAULT_PRIORITY)
    if not isinstance(priority, int) or isinstance(priority, bool):
        errors.append("Prioridade deve ser um número inteiro")

    if errors:
        raise HTTPException(422, "; ".join(errors))
    return CategoryRule(pattern=pattern.strip(), match_type=match_type,
                        category_id=category_id, priority=priority)


def _rule_or_404(conn, rule_id: int) -> CategoryRule:
    rule = repositories.CategoryRuleRepository(conn).get(rule_id)
    if rule is None:
        raise HTTPException(404, "Regra não encontrada")
    return rule


@router.get("/rules")
def list_rules():
    """Ascending priority (the order they are applied), ties by id."""
    conn = _connect()
    try:
        return [_rule_to_dict(r) for r in repositories.CategoryRuleRepository(conn).list()]
    finally:
        conn.close()


@router.post("/rules", status_code=201)
def create_rule(body: dict = Body(...)):
    conn = _connect()
    try:
        rule = _parse_rule(conn, body)
        with db.transaction(conn):
            repositories.CategoryRuleRepository(conn).add(rule)
        return _rule_to_dict(rule)
    finally:
        conn.close()


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, body: dict = Body(...)):
    conn = _connect()
    try:
        _rule_or_404(conn, rule_id)
        rule = _parse_rule(conn, body)
        rule.id = rule_id
        with db.transaction(conn):
            repositories.CategoryRuleRepository(conn).update(rule)
        return _rule_to_dict(rule)
    finally:
        conn.close()


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int):
    conn = _connect()
    try:
        _rule_or_404(conn, rule_id)
        with db.transaction(conn):
            repositories.CategoryRuleRepository(conn).delete(rule_id)
        return Response(status_code=204)
    finally:
        conn.close()
