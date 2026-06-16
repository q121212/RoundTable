"""Project records, membership, and project settings.

Imports downward only (validation, policies, action_log, notification_outbox);
never the sprint/ticket/board layers.
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from ..config import settings
from ..db import (
    TICKET_STATUSES,
    TICKET_TYPES,
    get_conn,
    json_dumps,
    row_to_dict,
    rows_to_dicts,
    utcnow,
)
from ._action_log import log_action
from ._notification_outbox import ensure_notification_preferences
from ._policies import require_project_admin
from ._validation import (
    normalize_github_repo,
    normalize_project_statuses,
    normalize_project_ticket_types,
    normalize_stats_visibility,
    normalize_ticket_delete_policy,
    project_statuses,
    project_stats_visibility,
    project_ticket_delete_own_only,
    project_ticket_delete_policy,
    project_ticket_types,
    validate_project_key,
)


def get_project_by_key(project_key: str) -> Dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM projects WHERE key = ?", (project_key.upper(),)).fetchone()
        project = row_to_dict(row)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project


def get_project_for_ticket_key(ticket_key: str) -> Dict[str, Any]:
    project_key = ticket_key.split("-", 1)[0].upper()
    return get_project_by_key(project_key)


def delete_project(user: Dict[str, Any], project_key: str, confirmation: str = "") -> None:
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    expected = "%s/%s" % (project["key"], project["name"])
    if confirmation.strip() not in {project["key"], expected}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type the project key to confirm deletion.",
        )
    with get_conn() as conn:
        # foreign_keys=ON cascades tickets, members, comments, action_log, links.
        conn.execute("DELETE FROM projects WHERE id = ?", (project["id"],))


def update_project_settings(
    user: Dict[str, Any],
    project_key: str,
    name: str,
    description: str = "",
    repo: str = "",
    statuses: Optional[List[str]] = None,
    ticket_types: Optional[List[str]] = None,
    stats_visibility: Optional[str] = None,
    ticket_delete_policy: Optional[str] = None,
    ticket_delete_own_only: Optional[bool] = None,
) -> Dict[str, Any]:
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    name = name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project name is required")
    enabled_statuses = project_statuses(project) if statuses is None else normalize_project_statuses(statuses)
    enabled_ticket_types = (
        project_ticket_types(project) if ticket_types is None else normalize_project_ticket_types(ticket_types)
    )
    enabled_stats_visibility = (
        project_stats_visibility(project) if stats_visibility is None else normalize_stats_visibility(stats_visibility)
    )
    enabled_ticket_delete_policy = (
        project_ticket_delete_policy(project)
        if ticket_delete_policy is None
        else normalize_ticket_delete_policy(ticket_delete_policy)
    )
    enabled_ticket_delete_own_only = (
        project_ticket_delete_own_only(project)
        if ticket_delete_own_only is None
        else bool(ticket_delete_own_only)
    )
    with get_conn() as conn:
        used_statuses = {
            row["status"]
            for row in conn.execute(
                "SELECT DISTINCT status FROM tickets WHERE project_id = ?",
                (project["id"],),
            ).fetchall()
        }
        disabled_used = sorted(used_statuses.difference(enabled_statuses), key=TICKET_STATUSES.index)
        if disabled_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot disable statuses that still contain tickets: %s" % ", ".join(disabled_used),
            )
        used_ticket_types = {
            row["ticket_type"]
            for row in conn.execute(
                "SELECT DISTINCT ticket_type FROM tickets WHERE project_id = ?",
                (project["id"],),
            ).fetchall()
        }
        disabled_used_types = sorted(used_ticket_types.difference(enabled_ticket_types), key=TICKET_TYPES.index)
        if disabled_used_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot disable ticket types that are still used: %s" % ", ".join(disabled_used_types),
            )
        next_values = {
            "name": name,
            "description": description.strip(),
            "github_repo_full_name": normalize_github_repo(repo) or None,
            "statuses_json": json_dumps(enabled_statuses),
            "ticket_types_json": json_dumps(enabled_ticket_types),
            "stats_visibility": enabled_stats_visibility,
            "ticket_delete_policy": enabled_ticket_delete_policy,
            "ticket_delete_own_only": 1 if enabled_ticket_delete_own_only else 0,
        }
        changes = {
            key: [project.get(key), value]
            for key, value in next_values.items()
            if (project.get(key) or "") != (value or "")
        }
        if changes:
            conn.execute(
                """
                UPDATE projects
                SET name = ?,
                    description = ?,
                    github_repo_full_name = ?,
                    statuses_json = ?,
                    ticket_types_json = ?,
                    stats_visibility = ?,
                    ticket_delete_policy = ?,
                    ticket_delete_own_only = ?
                WHERE id = ?
                """,
                (
                    next_values["name"],
                    next_values["description"],
                    next_values["github_repo_full_name"],
                    next_values["statuses_json"],
                    next_values["ticket_types_json"],
                    next_values["stats_visibility"],
                    next_values["ticket_delete_policy"],
                    next_values["ticket_delete_own_only"],
                    project["id"],
                ),
            )
            log_action(conn, int(project["id"]), None, user["id"], "project_updated", metadata={"changes": changes})
        return row_to_dict(conn.execute("SELECT * FROM projects WHERE id = ?", (project["id"],)).fetchone()) or {}


def list_projects(user: Dict[str, Any]) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        if user.get("role") == "admin":
            rows = conn.execute(
                """
                SELECT projects.*,
                       COUNT(tickets.id) AS ticket_count
                FROM projects
                LEFT JOIN tickets ON tickets.project_id = projects.id
                GROUP BY projects.id
                ORDER BY projects.created_at DESC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT projects.*,
                       COUNT(tickets.id) AS ticket_count
                FROM projects
                JOIN project_members ON project_members.project_id = projects.id
                LEFT JOIN tickets ON tickets.project_id = projects.id
                WHERE project_members.user_id = ?
                GROUP BY projects.id
                ORDER BY projects.created_at DESC
                """,
                (user["id"],),
            ).fetchall()
        return rows_to_dicts(rows)


def create_project(
    user: Dict[str, Any], key: str, name: str, description: str = "", repo: str = ""
) -> Dict[str, Any]:
    key = validate_project_key(key)
    name = name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project name is required")
    now = utcnow()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO projects
                (key, name, description, created_by, github_repo_full_name, statuses_json, ticket_types_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                key,
                name,
                description.strip(),
                user["id"],
                normalize_github_repo(repo) or None,
                json_dumps(TICKET_STATUSES),
                json_dumps(TICKET_TYPES),
                now,
            ),
        )
        project_id = int(cur.lastrowid)
        conn.execute(
            """
            INSERT INTO project_members (project_id, user_id, role, created_at)
            VALUES (?, ?, 'admin', ?)
            """,
            (project_id, user["id"], now),
        )
        log_action(conn, project_id, None, user["id"], "project_created", metadata={"key": key})
        return row_to_dict(conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()) or {}


def project_members(project_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        return rows_to_dicts(
            conn.execute(
                """
                SELECT users.id,
                       users.login,
                       users.name,
                       users.avatar_url,
                       project_members.role AS project_role
                FROM project_members
                JOIN users ON users.id = project_members.user_id
                WHERE project_members.project_id = ?
                ORDER BY users.login
                """,
                (project_id,),
            ).fetchall()
        )


def search_project_users(project_id: int, query: str, limit: int = 8, small_project_limit: int = 12) -> List[Dict[str, Any]]:
    clean = query.strip().lstrip("@")
    with get_conn() as conn:
        if not clean:
            count = int(
                conn.execute(
                    "SELECT COUNT(*) AS c FROM project_members WHERE project_id = ?",
                    (project_id,),
                ).fetchone()["c"]
            )
            if count > small_project_limit:
                return []
            return rows_to_dicts(
                conn.execute(
                    """
                    SELECT users.id,
                           users.login,
                           users.name,
                           users.avatar_url,
                           project_members.role AS project_role
                    FROM project_members
                    JOIN users ON users.id = project_members.user_id
                    WHERE project_members.project_id = ?
                    ORDER BY users.login
                    LIMIT ?
                    """,
                    (project_id, small_project_limit),
                ).fetchall()
            )
        like = clean.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return rows_to_dicts(
            conn.execute(
                """
                SELECT users.id,
                       users.login,
                       users.name,
                       users.avatar_url,
                       project_members.role AS project_role
                FROM project_members
                JOIN users ON users.id = project_members.user_id
                WHERE project_members.project_id = ?
                  AND (
                    users.login LIKE ? ESCAPE '\\'
                    OR COALESCE(users.name, '') LIKE ? ESCAPE '\\'
                  )
                ORDER BY
                  CASE WHEN users.login LIKE ? ESCAPE '\\' THEN 0 ELSE 1 END,
                  users.login
                LIMIT ?
                """,
                (project_id, f"%{like}%", f"%{like}%", f"{like}%", limit),
            ).fetchall()
        )


def require_project_member_conn(conn: Any, project_id: int, user_id: int) -> None:
    row = conn.execute(
        """
        SELECT users.id
        FROM users
        JOIN project_members ON project_members.user_id = users.id
        WHERE users.id = ? AND project_members.project_id = ?
        """,
        (user_id, project_id),
    ).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee must be a project member.",
        )


def add_project_member(project_id: int, login: str, role: str = "member") -> None:
    if role not in {"admin", "member", "viewer"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid member role")
    login = login.strip()
    if not login:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Login is required")
    with get_conn() as conn:
        user = conn.execute("SELECT id FROM users WHERE login = ?", (login,)).fetchone()
        if not user:
            user = conn.execute(
                """
                INSERT INTO users (login, name, role, created_at)
                VALUES (?, ?, ?, ?)
                RETURNING id
                """,
                (
                    login,
                    login,
                    "admin" if login in settings.admin_github_logins else "member",
                    utcnow(),
                ),
            ).fetchone()
            ensure_notification_preferences(conn, int(user["id"]))
        conn.execute(
            """
            INSERT INTO project_members (project_id, user_id, role, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(project_id, user_id) DO UPDATE SET role = excluded.role
            """,
            (project_id, user["id"], role, utcnow()),
        )


def update_project_member(project_id: int, member_user_id: int, role: str) -> None:
    if role not in {"admin", "member", "viewer"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid member role")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT role FROM project_members WHERE project_id = ? AND user_id = ?",
            (project_id, member_user_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found")
        if row["role"] == "admin" and role != "admin":
            admin_count = conn.execute(
                "SELECT COUNT(*) AS c FROM project_members WHERE project_id = ? AND role = 'admin'",
                (project_id,),
            ).fetchone()["c"]
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Project must keep at least one admin.",
                )
        conn.execute(
            "UPDATE project_members SET role = ? WHERE project_id = ? AND user_id = ?",
            (role, project_id, member_user_id),
        )


def remove_project_member(project_id: int, member_user_id: int) -> None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT role FROM project_members WHERE project_id = ? AND user_id = ?",
            (project_id, member_user_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found")
        if row["role"] == "admin":
            admin_count = conn.execute(
                "SELECT COUNT(*) AS c FROM project_members WHERE project_id = ? AND role = 'admin'",
                (project_id,),
            ).fetchone()["c"]
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Project must keep at least one admin.",
                )
        conn.execute("DELETE FROM project_members WHERE project_id = ? AND user_id = ?", (project_id, member_user_id))
