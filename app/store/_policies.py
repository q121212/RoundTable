"""Project authorization policies.

Depends only on db access and the pure validation helpers, so it can be
imported by the CRUD modules without a cycle. It must not import the rest of
app.store.
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from ..db import get_conn
from ._validation import (
    project_stats_visibility,
    project_ticket_delete_own_only,
    project_ticket_delete_policy,
)


def require_project_access(user: Dict[str, Any], project_id: int, write: bool = False) -> None:
    if user.get("role") == "admin":
        return
    with get_conn() as conn:
        row = conn.execute(
            "SELECT role FROM project_members WHERE project_id = ? AND user_id = ?",
            (project_id, user["id"]),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project access denied")
    if write and row["role"] == "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Write access denied")


def project_role_for_user(user: Dict[str, Any], project_id: int) -> str:
    if user.get("role") == "admin":
        return "admin"
    with get_conn() as conn:
        row = conn.execute(
            "SELECT role FROM project_members WHERE project_id = ? AND user_id = ?",
            (project_id, user["id"]),
        ).fetchone()
    return str(row["role"]) if row else ""


def require_project_admin(user: Dict[str, Any], project_id: int) -> None:
    if user.get("role") == "admin":
        return
    with get_conn() as conn:
        row = conn.execute(
            "SELECT role FROM project_members WHERE project_id = ? AND user_id = ?",
            (project_id, user["id"]),
        ).fetchone()
    if not row or row["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project admin required")


def require_project_stats_access(user: Dict[str, Any], project: Dict[str, Any]) -> None:
    require_project_access(user, int(project["id"]))
    role = project_role_for_user(user, int(project["id"]))
    visibility = project_stats_visibility(project)
    if visibility == "admin":
        require_project_admin(user, int(project["id"]))
    if visibility == "member" and role == "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project member required")


def can_view_project_stats(user: Dict[str, Any], project: Dict[str, Any]) -> bool:
    role = project_role_for_user(user, int(project["id"]))
    visibility = project_stats_visibility(project)
    if role == "admin":
        return True
    if visibility == "viewer":
        return role in {"member", "viewer"}
    if visibility == "member":
        return role == "member"
    return False


def can_delete_ticket(user: Dict[str, Any], project: Dict[str, Any], ticket: Optional[Dict[str, Any]] = None) -> bool:
    role = project_role_for_user(user, int(project["id"]))
    policy = project_ticket_delete_policy(project)
    if role == "admin":
        return True
    if project_ticket_delete_own_only(project):
        if not ticket or int(ticket.get("reporter_id") or 0) != int(user["id"]):
            return False
    if policy == "member" and role == "member":
        return True
    if policy == "viewer" and role in {"member", "viewer"}:
        return True
    return False


def require_ticket_delete_access(user: Dict[str, Any], project: Dict[str, Any], ticket: Dict[str, Any]) -> None:
    require_project_access(user, int(project["id"]))
    if not can_delete_ticket(user, project, ticket):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ticket delete access denied")
