"""Goal management under /api/banco/goals.

GET /api/banco/goals (the dashboard card) lives in router.py and only lists active
goals; this module adds the management side: the full list with archived goals, and
create / edit / archive / delete. Write bodies are validated by hand so every 422
carries one readable Portuguese sentence in `detail`, like the transactions API.
"""
from datetime import date

from fastapi import APIRouter, Body, HTTPException, Response

from banco import db, repositories, services
from banco.models import Goal

from app.banco_view.adapter import _connect

router = APIRouter(prefix="/goals")


def _to_dict(goal, progress) -> dict:
    return {
        "id": goal.id,
        "name": goal.name,
        "target_cents": goal.target_cents,
        "deadline": goal.deadline.isoformat() if goal.deadline else None,
        "notes": goal.notes,
        "archived": goal.archived,
        "saved_cents": progress.saved_cents,
        "achieved": progress.achieved,
        "on_track": progress.on_track,
        "days_remaining": progress.days_remaining,
    }


def _all_goals(conn) -> list[dict]:
    progress = {p.goal_id: p for p in services.GoalService(conn).list_progress(include_archived=True)}
    return [
        _to_dict(g, progress[g.id])
        for g in repositories.GoalRepository(conn).list(include_archived=True)
    ]


@router.get("/overview")
def goals_overview():
    """Every goal, archived ones included, with progress. Archived goals come last."""
    conn = _connect()
    try:
        return _all_goals(conn)
    finally:
        conn.close()


def _parse(body: dict) -> Goal:
    """Validate the request body; raise one 422 listing every problem found."""
    errors: list[str] = []

    name = body.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("Nome é obrigatório")

    target = body.get("target_cents")
    if not isinstance(target, int) or isinstance(target, bool) or target <= 0:
        errors.append("Valor alvo deve ser maior que zero")

    deadline = None
    if body.get("deadline"):
        try:
            deadline = date.fromisoformat(body["deadline"])
        except (TypeError, ValueError):
            errors.append("Prazo inválido")

    if errors:
        raise HTTPException(422, "; ".join(errors))

    return Goal(name=name.strip(), target_cents=target, deadline=deadline, notes=body.get("notes") or "")


def _one(conn, goal_id: int) -> dict:
    return next(g for g in _all_goals(conn) if g["id"] == goal_id)


def _get_or_404(conn, goal_id: int) -> Goal:
    goal = repositories.GoalRepository(conn).get(goal_id)
    if goal is None:
        raise HTTPException(404, "Meta não encontrada")
    return goal


@router.post("", status_code=201)
def create_goal(body: dict = Body(...)):
    conn = _connect()
    try:
        goal = _parse(body)
        with db.transaction(conn):
            repositories.GoalRepository(conn).add(goal)
        return _one(conn, goal.id)
    finally:
        conn.close()


@router.put("/{goal_id}")
def update_goal(goal_id: int, body: dict = Body(...)):
    conn = _connect()
    try:
        current = _get_or_404(conn, goal_id)
        goal = _parse(body)
        goal.id = goal_id
        goal.archived = current.archived
        with db.transaction(conn):
            repositories.GoalRepository(conn).update(goal)
        return _one(conn, goal_id)
    finally:
        conn.close()


@router.put("/{goal_id}/archive")
def archive_goal(goal_id: int, body: dict = Body(...)):
    conn = _connect()
    try:
        goal = _get_or_404(conn, goal_id)
        archived = body.get("archived")
        if not isinstance(archived, bool):
            raise HTTPException(422, "Informe se a meta está arquivada (verdadeiro ou falso)")
        goal.archived = archived
        with db.transaction(conn):
            repositories.GoalRepository(conn).update(goal)
        return _one(conn, goal_id)
    finally:
        conn.close()


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: int):
    """Removes the goal and (by cascade) its deposit links; the transactions stay."""
    conn = _connect()
    try:
        _get_or_404(conn, goal_id)
        with db.transaction(conn):
            repositories.GoalRepository(conn).delete(goal_id)
        return Response(status_code=204)
    finally:
        conn.close()
