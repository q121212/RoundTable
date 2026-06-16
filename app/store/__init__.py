import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from ..config import settings
from ..db import (
    PRIORITIES,
    TICKET_STATUSES,
    TICKET_TYPES,
    get_conn,
    json_dumps,
    row_to_dict,
    rows_to_dicts,
    utcnow,
)
from ..security import hash_token, new_token


TICKET_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d+)\b")
MENTION_RE = re.compile(r"(?<![\w.-])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?)")
NOTIFY_ACTIONS = {"assigned", "status_changed", "commented", "closed", "reopened"}
GITHUB_REF_TYPES = {"branch", "commit", "pull_request", "tag"}
SPRINT_STATUSES = {"planned", "active", "closed"}

# Validators, normalizers, and per-project config helpers now live in
# _validation.py. Re-exported here so app.store stays the single public facade
# (the `as` aliases mark them as intentional re-exports for linters).
from ._validation import (  # noqa: E402
    STATS_VISIBILITIES as STATS_VISIBILITIES,
    TICKET_DELETE_POLICIES as TICKET_DELETE_POLICIES,
    normalize_github_installation_id as normalize_github_installation_id,
    normalize_github_link_url as normalize_github_link_url,
    normalize_github_repo as normalize_github_repo,
    normalize_project_statuses as normalize_project_statuses,
    normalize_project_ticket_types as normalize_project_ticket_types,
    normalize_stats_visibility as normalize_stats_visibility,
    normalize_ticket_delete_policy as normalize_ticket_delete_policy,
    project_stats_visibility as project_stats_visibility,
    project_statuses as project_statuses,
    project_ticket_delete_own_only as project_ticket_delete_own_only,
    project_ticket_delete_policy as project_ticket_delete_policy,
    project_ticket_types as project_ticket_types,
    validate_date_string as validate_date_string,
    validate_priority as validate_priority,
    validate_project_key as validate_project_key,
    validate_project_ticket_status as validate_project_ticket_status,
    validate_project_ticket_type as validate_project_ticket_type,
    validate_status as validate_status,
    validate_story_points as validate_story_points,
    validate_ticket_link_type as validate_ticket_link_type,
    validate_ticket_type as validate_ticket_type,
)


def upsert_user(
    login: str,
    github_id: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> Dict[str, Any]:
    login = login.strip()
    if not login:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Login is required")
    role = "admin" if login in settings.admin_github_logins else "member"
    if settings.allow_dev_login and not settings.admin_github_logins:
        role = "admin"
    now = utcnow()
    with get_conn() as conn:
        existing = conn.execute("SELECT * FROM users WHERE login = ?", (login,)).fetchone()
        if existing:
            user = row_to_dict(existing) or {}
            if user["role"] == "admin" and not settings.admin_github_logins:
                role = "admin"
            conn.execute(
                """
                UPDATE users
                SET github_id = COALESCE(?, github_id),
                    name = COALESCE(?, name),
                    email = COALESCE(?, email),
                    avatar_url = COALESCE(?, avatar_url),
                    role = ?
                WHERE id = ?
                """,
                (github_id, name, email, avatar_url, role, user["id"]),
            )
            user_id = user["id"]
        else:
            cur = conn.execute(
                """
                INSERT INTO users (github_id, login, name, email, avatar_url, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (github_id, login, name, email, avatar_url, role, now),
            )
            user_id = int(cur.lastrowid)
        ensure_notification_preferences(conn, user_id)
        return row_to_dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()) or {}


def sync_configured_admin_roles() -> None:
    """Keep global admins aligned with ADMIN_GITHUB_LOGINS when it is configured."""
    if not settings.admin_github_logins:
        return
    placeholders = ",".join("?" for _ in settings.admin_github_logins)
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE users
            SET role = CASE
                WHEN login IN (%s) THEN 'admin'
                ELSE 'member'
            END
            WHERE role = 'admin' OR login IN (%s)
            """
            % (placeholders, placeholders),
            tuple(settings.admin_github_logins) * 2,
        )


# Notification fan-out and preference storage live in _notification_outbox.py
# (imports _read_models, never _tickets/_action_log). Re-exported from facade.
from ._notification_outbox import (  # noqa: E402
    describe_action as describe_action,
    enqueue_notifications as enqueue_notifications,
    ensure_notification_preferences as ensure_notification_preferences,
    notification_preferences as notification_preferences,
    notification_preferences_conn as notification_preferences_conn,
    notification_recipients as notification_recipients,
    update_notification_preferences as update_notification_preferences,
)


def list_users() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM users ORDER BY login").fetchall())


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


# Project authorization policies live in _policies.py (cycle-free: db + the
# validation helpers only). Re-exported so app.store stays the public facade.
from ._policies import (  # noqa: E402
    can_delete_ticket as can_delete_ticket,
    can_view_project_stats as can_view_project_stats,
    project_role_for_user as project_role_for_user,
    require_project_access as require_project_access,
    require_project_admin as require_project_admin,
    require_project_stats_access as require_project_stats_access,
    require_ticket_delete_access as require_ticket_delete_access,
)


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


def list_project_sprints(project_id: int, include_closed: bool = True) -> List[Dict[str, Any]]:
    where = "sprints.project_id = ?"
    params: List[Any] = [project_id]
    if not include_closed:
        where += " AND sprints.status != 'closed'"
    with get_conn() as conn:
        sprints = rows_to_dicts(
            conn.execute(
                """
                SELECT sprints.*,
                       COUNT(tickets.id) AS ticket_count
                FROM sprints
                LEFT JOIN tickets ON tickets.sprint_id = sprints.id
                WHERE %s
                GROUP BY sprints.id
                ORDER BY
                  CASE sprints.status
                    WHEN 'active' THEN 1
                    WHEN 'planned' THEN 2
                    ELSE 3
                  END,
                  sprints.starts_on IS NULL,
                  sprints.starts_on DESC,
                  sprints.created_at DESC
                """
                % where,
                tuple(params),
            ).fetchall()
        )
        if not sprints:
            return sprints
        sprint_ids = [int(sprint["id"]) for sprint in sprints]
        placeholders = ",".join("?" for _ in sprint_ids)
        ticket_rows = rows_to_dicts(
            conn.execute(
                """
                SELECT sprint_id, key, title
                FROM (
                    SELECT sprint_id,
                           key,
                           title,
                           ROW_NUMBER() OVER (
                               PARTITION BY sprint_id
                               ORDER BY sort_order ASC, updated_at DESC, number DESC
                           ) AS row_number
                    FROM tickets
                    WHERE project_id = ?
                      AND sprint_id IN (%s)
                )
                WHERE row_number <= 8
                ORDER BY sprint_id, row_number
                """
                % placeholders,
                (project_id, *sprint_ids),
            ).fetchall()
        )
        tickets_by_sprint: Dict[int, List[Dict[str, Any]]] = {sprint_id: [] for sprint_id in sprint_ids}
        for ticket in ticket_rows:
            tickets_by_sprint.setdefault(int(ticket["sprint_id"]), []).append(ticket)
        for sprint in sprints:
            preview = tickets_by_sprint.get(int(sprint["id"]), [])[:8]
            sprint["ticket_preview"] = preview
            remaining = max(0, int(sprint.get("ticket_count") or 0) - len(preview))
            sprint["ticket_preview_more"] = remaining
        return sprints


def validate_project_sprint_conn(conn: Any, project_id: int, sprint_id: Optional[int]) -> Optional[int]:
    if not sprint_id:
        return None
    sprint = row_to_dict(
        conn.execute("SELECT * FROM sprints WHERE id = ? AND project_id = ?", (sprint_id, project_id)).fetchone()
    )
    if not sprint:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint does not belong to this project")
    return int(sprint_id)


def create_sprint(
    user: Dict[str, Any],
    project_key: str,
    name: str,
    goal: str = "",
    starts_on: str = "",
    ends_on: str = "",
    status_value: str = "planned",
) -> Dict[str, Any]:
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    name = name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint name is required")
    status_value = status_value if status_value in SPRINT_STATUSES else "planned"
    starts_on = validate_date_string(starts_on, "Sprint start date")
    ends_on = validate_date_string(ends_on, "Sprint end date")
    if starts_on and ends_on and ends_on < starts_on:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint end date cannot be before start date")
    now = utcnow()
    with get_conn() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO sprints
                    (project_id, name, goal, status, starts_on, ends_on, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project["id"],
                    name,
                    goal.strip(),
                    status_value,
                    starts_on or None,
                    ends_on or None,
                    user["id"],
                    now,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint name already exists") from exc
        log_action(conn, int(project["id"]), None, user["id"], "sprint_created", metadata={"name": name})
        return row_to_dict(conn.execute("SELECT * FROM sprints WHERE id = ?", (cur.lastrowid,)).fetchone()) or {}


def update_sprint(
    user: Dict[str, Any],
    project_key: str,
    sprint_id: int,
    name: str,
    goal: str = "",
    starts_on: str = "",
    ends_on: str = "",
) -> Dict[str, Any]:
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    name = name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint name is required")
    starts_on = validate_date_string(starts_on, "Sprint start date")
    ends_on = validate_date_string(ends_on, "Sprint end date")
    if starts_on and ends_on and ends_on < starts_on:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint end date cannot be before start date")
    with get_conn() as conn:
        sprint = row_to_dict(
            conn.execute("SELECT * FROM sprints WHERE id = ? AND project_id = ?", (sprint_id, project["id"])).fetchone()
        )
        if not sprint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
        try:
            conn.execute(
                """
                UPDATE sprints
                SET name = ?, goal = ?, starts_on = ?, ends_on = ?
                WHERE id = ?
                """,
                (name, goal.strip(), starts_on or None, ends_on or None, sprint_id),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint name already exists") from exc
        changes = {
            "name": [sprint["name"], name],
            "goal": [sprint["goal"] or "", goal.strip()],
            "starts_on": [sprint["starts_on"] or "", starts_on or ""],
            "ends_on": [sprint["ends_on"] or "", ends_on or ""],
        }
        log_action(
            conn,
            int(project["id"]),
            None,
            user["id"],
            "sprint_updated",
            field="sprint_details",
            old_value=sprint["name"],
            new_value=name,
            metadata={"changes": changes},
        )
        return row_to_dict(conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()) or {}


def update_sprint_status(user: Dict[str, Any], project_key: str, sprint_id: int, status_value: str) -> Dict[str, Any]:
    if status_value not in SPRINT_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sprint status")
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    now = utcnow()
    with get_conn() as conn:
        sprint = row_to_dict(
            conn.execute("SELECT * FROM sprints WHERE id = ? AND project_id = ?", (sprint_id, project["id"])).fetchone()
        )
        if not sprint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
        conn.execute(
            "UPDATE sprints SET status = ?, closed_at = ? WHERE id = ?",
            (status_value, now if status_value == "closed" else None, sprint_id),
        )
        log_action(
            conn,
            int(project["id"]),
            None,
            user["id"],
            "sprint_updated",
            field="sprint_status",
            old_value=sprint["status"],
            new_value=status_value,
        )
        return row_to_dict(conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()) or {}


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


def mentioned_user_ids_conn(conn: Any, project_id: int, text: str) -> List[int]:
    logins = {match.group(1).lower() for match in MENTION_RE.finditer(text or "")}
    if not logins:
        return []
    placeholders = ",".join("?" for _ in logins)
    rows = conn.execute(
        f"""
        SELECT users.id
        FROM users
        JOIN project_members ON project_members.user_id = users.id
        WHERE project_members.project_id = ?
          AND lower(users.login) IN ({placeholders})
        """,
        (project_id, *sorted(logins)),
    ).fetchall()
    return [int(row["id"]) for row in rows]


def refresh_ticket_mentions_conn(
    conn: Any,
    ticket_id: int,
    project_id: int,
    text: str,
    source_type: str,
    comment_id: Optional[int] = None,
) -> List[int]:
    if source_type not in {"description", "comment"}:
        raise ValueError("Unsupported mention source type")
    mentioned_ids = mentioned_user_ids_conn(conn, project_id, text)
    now = utcnow()
    if source_type == "description":
        conn.execute(
            "DELETE FROM ticket_mentions WHERE ticket_id = ? AND source_type = 'description'",
            (ticket_id,),
        )
    else:
        conn.execute(
            "DELETE FROM ticket_mentions WHERE ticket_id = ? AND comment_id = ? AND source_type = 'comment'",
            (ticket_id, comment_id),
        )
    for user_id in mentioned_ids:
        conn.execute(
            """
            INSERT OR IGNORE INTO ticket_mentions
                (ticket_id, comment_id, mentioned_user_id, source_type, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticket_id, comment_id, user_id, source_type, now),
        )
        conn.execute(
            "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
            (ticket_id, user_id, now),
        )
    return mentioned_ids


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


def create_ticket(
    user: Dict[str, Any],
    project_key: str,
    title: str,
    description: str = "",
    priority: str = "Medium",
    ticket_type: str = "Task",
    assignee_id: Optional[int] = None,
    sprint_id: Optional[int] = None,
    story_points: int = 0,
) -> Dict[str, Any]:
    title = title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket title is required")
    priority = validate_priority(priority)
    story_points = validate_story_points(story_points)
    project_key = validate_project_key(project_key)
    now = utcnow()
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        project = row_to_dict(conn.execute("SELECT * FROM projects WHERE key = ?", (project_key,)).fetchone())
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        require_project_access(user, int(project["id"]), write=True)
        if assignee_id:
            require_project_member_conn(conn, int(project["id"]), assignee_id)
        sprint_id = validate_project_sprint_conn(conn, int(project["id"]), sprint_id)
        ticket_type = validate_project_ticket_type(project, ticket_type)
        initial_status = project_statuses(project)[0]
        sort_order = first_ticket_sort_order_conn(conn, int(project["id"]), initial_status)
        number = int(project["next_ticket_number"])
        ticket_key = "%s-%s" % (project["key"], number)
        conn.execute(
            "UPDATE projects SET next_ticket_number = next_ticket_number + 1 WHERE id = ?",
            (project["id"],),
        )
        cur = conn.execute(
            """
            INSERT INTO tickets
                (project_id, number, key, title, description, ticket_type, status, priority,
                 sprint_id, story_points, sort_order, assignee_id, reporter_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project["id"],
                number,
                ticket_key,
                title,
                description.strip(),
                ticket_type,
                initial_status,
                priority,
                sprint_id,
                story_points,
                sort_order,
                assignee_id,
                user["id"],
                now,
                now,
            ),
        )
        ticket_id = int(cur.lastrowid)
        conn.execute(
            "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
            (ticket_id, user["id"], now),
        )
        if assignee_id:
            conn.execute(
                "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
                (ticket_id, assignee_id, now),
            )
        refresh_ticket_mentions_conn(conn, ticket_id, int(project["id"]), description, "description")
        log_action(
            conn,
            project["id"],
            ticket_id,
            user["id"],
            "ticket_created",
            metadata={
                "key": ticket_key,
                "title": title,
                "ticket_type": ticket_type,
                "sprint_id": sprint_id,
                "story_points": story_points,
            },
        )
        if assignee_id:
            log_action(
                conn,
                project["id"],
                ticket_id,
                user["id"],
                "assigned",
                field="assignee",
                old_value="",
                new_value=str(assignee_id),
            )
        return get_ticket_by_id_conn(conn, ticket_id)


# Read-only ticket helpers and row mappers live in _read_models.py — the seam
# that breaks the notifications<->tickets cycle (reads import nothing from
# tickets/action_log/notifications). Re-exported from the facade.
from ._read_models import (  # noqa: E402
    attach_ticket_link_summaries_conn as attach_ticket_link_summaries_conn,
    get_ticket as get_ticket,
    get_ticket_by_id_conn as get_ticket_by_id_conn,
    get_ticket_by_key_conn as get_ticket_by_key_conn,
    get_ticket_bundle as get_ticket_bundle,
    list_linkable_tickets_conn as list_linkable_tickets_conn,
    list_ticket_links_conn as list_ticket_links_conn,
)


def search_linkable_tickets(project_id: int, current_ticket_key: str, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    normalized_query = query.strip()
    if not normalized_query:
        return []
    like_query = normalized_query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    with get_conn() as conn:
        current = get_ticket_by_key_conn(conn, current_ticket_key)
        if int(current["project_id"]) != int(project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        return rows_to_dicts(
            conn.execute(
                """
                SELECT id, key, title, ticket_type, status
                FROM tickets
                WHERE project_id = ?
                  AND id != ?
                  AND (
                    key LIKE ? ESCAPE '\\'
                    OR title LIKE ? ESCAPE '\\'
                  )
                ORDER BY
                  CASE
                    WHEN key = ? THEN 0
                    WHEN key LIKE ? ESCAPE '\\' THEN 1
                    ELSE 2
                  END,
                  number DESC
                LIMIT ?
                """,
                (
                    project_id,
                    current["id"],
                    f"{like_query}%",
                    f"%{like_query}%",
                    normalized_query.upper(),
                    f"{like_query}%",
                    limit,
                ),
            ).fetchall()
        )


def link_ticket(
    user: Dict[str, Any],
    source_key: str,
    target_key: str,
    link_type: str = "relates",
) -> Dict[str, Any]:
    link_type = validate_ticket_link_type(link_type)
    target_key = target_key.strip().upper()
    if not target_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target ticket is required")
    now = utcnow()
    with get_conn() as conn:
        source = get_ticket_by_key_conn(conn, source_key)
        target = get_ticket_by_key_conn(conn, target_key)
        require_project_access(user, int(source["project_id"]), write=True)
        require_project_access(user, int(target["project_id"]), write=False)
        if int(source["id"]) == int(target["id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A ticket cannot link to itself")
        if int(source["project_id"]) != int(target["project_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket links are project-scoped")
        existing = row_to_dict(
            conn.execute(
                """
                SELECT *
                FROM ticket_links
                WHERE
                    (source_ticket_id = ? AND target_ticket_id = ?)
                    OR (source_ticket_id = ? AND target_ticket_id = ?)
                """,
                (source["id"], target["id"], target["id"], source["id"]),
            ).fetchone()
        )
        if existing:
            conn.execute(
                """
                UPDATE ticket_links
                SET source_ticket_id = ?, target_ticket_id = ?, link_type = ?, created_by = ?, created_at = ?
                WHERE id = ?
                """,
                (source["id"], target["id"], link_type, user["id"], now, existing["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO ticket_links
                    (project_id, source_ticket_id, target_ticket_id, link_type, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source["project_id"], source["id"], target["id"], link_type, user["id"], now),
            )
        conn.execute("UPDATE tickets SET updated_at = ? WHERE id IN (?, ?)", (now, source["id"], target["id"]))
        log_action(
            conn,
            source["project_id"],
            source["id"],
            user["id"],
            "linked",
            field="ticket_link",
            old_value="",
            new_value=target["key"],
            metadata={"link_type": link_type, "updated_existing": bool(existing)},
        )
        return {
            "source_key": source["key"],
            "target_key": target["key"],
            "link_type": link_type,
        }


def update_ticket_link(
    user: Dict[str, Any],
    ticket_key: str,
    link_id: int,
    target_key: str,
    link_type: str,
) -> Dict[str, Any]:
    link_type = validate_ticket_link_type(link_type)
    target_key = target_key.strip().upper()
    if not target_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target ticket is required")
    now = utcnow()
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        target = get_ticket_by_key_conn(conn, target_key)
        require_project_access(user, int(ticket["project_id"]), write=True)
        require_project_access(user, int(target["project_id"]), write=False)
        if int(ticket["id"]) == int(target["id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A ticket cannot link to itself")
        if int(ticket["project_id"]) != int(target["project_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket links are project-scoped")
        link = row_to_dict(
            conn.execute(
                """
                SELECT ticket_links.*, target.key AS target_key, source.key AS source_key
                FROM ticket_links
                JOIN tickets target ON target.id = ticket_links.target_ticket_id
                JOIN tickets source ON source.id = ticket_links.source_ticket_id
                WHERE ticket_links.id = ?
                """,
                (link_id,),
            ).fetchone()
        )
        if not link or int(link["project_id"]) != int(ticket["project_id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket link not found")
        if int(ticket["id"]) not in {int(link["source_ticket_id"]), int(link["target_ticket_id"])}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket link not found")
        duplicate = row_to_dict(
            conn.execute(
                """
                SELECT id
                FROM ticket_links
                WHERE id != ?
                  AND (
                    (source_ticket_id = ? AND target_ticket_id = ?)
                    OR (source_ticket_id = ? AND target_ticket_id = ?)
                  )
                """,
                (link_id, ticket["id"], target["id"], target["id"], ticket["id"]),
            ).fetchone()
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="These tickets are already linked")
        old_other_key = link["target_key"] if int(link["source_ticket_id"]) == int(ticket["id"]) else link["source_key"]
        conn.execute(
            """
            UPDATE ticket_links
            SET source_ticket_id = ?, target_ticket_id = ?, link_type = ?, created_by = ?, created_at = ?
            WHERE id = ?
            """,
            (ticket["id"], target["id"], link_type, user["id"], now, link_id),
        )
        conn.execute(
            "UPDATE tickets SET updated_at = ? WHERE id IN (?, ?, ?)",
            (now, ticket["id"], target["id"], link["source_ticket_id"] if int(link["source_ticket_id"]) != int(ticket["id"]) else link["target_ticket_id"]),
        )
        log_action(
            conn,
            ticket["project_id"],
            ticket["id"],
            user["id"],
            "linked",
            field="ticket_link",
            old_value=old_other_key,
            new_value=target["key"],
            metadata={"link_type": link_type, "updated_existing": True, "link_id": link_id},
        )
        return {
            "source_key": ticket["key"],
            "target_key": target["key"],
            "link_type": link_type,
        }


def unlink_ticket(user: Dict[str, Any], ticket_key: str, link_id: int) -> None:
    now = utcnow()
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        require_project_access(user, int(ticket["project_id"]), write=True)
        link = row_to_dict(
            conn.execute(
                """
                SELECT ticket_links.*, target.key AS target_key, source.key AS source_key
                FROM ticket_links
                JOIN tickets target ON target.id = ticket_links.target_ticket_id
                JOIN tickets source ON source.id = ticket_links.source_ticket_id
                WHERE ticket_links.id = ?
                """,
                (link_id,),
            ).fetchone()
        )
        if not link or int(link["project_id"]) != int(ticket["project_id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket link not found")
        if int(ticket["id"]) not in {int(link["source_ticket_id"]), int(link["target_ticket_id"])}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket link not found")
        other_key = link["target_key"] if int(link["source_ticket_id"]) == int(ticket["id"]) else link["source_key"]
        conn.execute("DELETE FROM ticket_links WHERE id = ?", (link_id,))
        conn.execute("UPDATE tickets SET updated_at = ? WHERE id IN (?, ?)", (now, link["source_ticket_id"], link["target_ticket_id"]))
        log_action(
            conn,
            ticket["project_id"],
            ticket["id"],
            user["id"],
            "unlinked",
            field="ticket_link",
            old_value=other_key,
            new_value="",
            metadata={"link_type": link["link_type"]},
        )


def board_for_project(project_key: str, user: Dict[str, Any], sprint_filter: str = "") -> Dict[str, Any]:
    project = get_project_by_key(project_key)
    require_project_access(user, int(project["id"]))
    statuses = project_statuses(project)
    with get_conn() as conn:
        where = ["tickets.project_id = ?"]
        params: List[Any] = [project["id"]]
        current_sprint = None
        if sprint_filter == "none":
            where.append("tickets.sprint_id IS NULL")
        elif sprint_filter == "active":
            active_sprints = rows_to_dicts(
                conn.execute(
                    "SELECT * FROM sprints WHERE project_id = ? AND status = 'active' ORDER BY starts_on DESC, created_at DESC",
                    (project["id"],),
                ).fetchall()
            )
            if active_sprints:
                placeholders = ",".join("?" for _ in active_sprints)
                where.append("tickets.sprint_id IN (%s)" % placeholders)
                params.extend([sprint["id"] for sprint in active_sprints])
            else:
                where.append("1 = 0")
        elif sprint_filter:
            current_sprint = row_to_dict(
                conn.execute(
                    "SELECT * FROM sprints WHERE project_id = ? AND id = ?",
                    (project["id"], sprint_filter),
                ).fetchone()
            )
            if current_sprint:
                where.append("tickets.sprint_id = ?")
                params.append(current_sprint["id"])
        rows = rows_to_dicts(
            conn.execute(
                """
                SELECT tickets.*,
                       sprints.name AS sprint_name,
                       sprints.status AS sprint_status,
                       sprints.starts_on AS sprint_starts_on,
                       sprints.ends_on AS sprint_ends_on,
                       assignee.login AS assignee_login,
                       assignee.name AS assignee_name,
                       assignee.avatar_url AS assignee_avatar_url,
                       reporter.login AS reporter_login,
                       reporter.name AS reporter_name,
                       reporter.avatar_url AS reporter_avatar_url
                FROM tickets
                LEFT JOIN sprints ON sprints.id = tickets.sprint_id
                LEFT JOIN users assignee ON assignee.id = tickets.assignee_id
                LEFT JOIN users reporter ON reporter.id = tickets.reporter_id
                WHERE %s
                ORDER BY
                    CASE tickets.status
                        WHEN 'Backlog' THEN 1
                        WHEN 'Todo' THEN 2
                        WHEN 'In Progress' THEN 3
                        WHEN 'Review' THEN 4
                        WHEN 'Done' THEN 5
                        ELSE 6
                    END,
                    tickets.sort_order ASC,
                    tickets.updated_at DESC,
                    tickets.number DESC
                """
                % " AND ".join(where),
                tuple(params),
            ).fetchall()
        )
        attach_ticket_link_summaries_conn(conn, rows)
    columns = {status_name: [] for status_name in statuses}
    for ticket in rows:
        columns.setdefault(ticket["status"], []).append(ticket)
    return {
        "project": project,
        "project_role": project_role_for_user(user, int(project["id"])),
        "statuses": statuses,
        "columns": columns,
        "sprints": list_project_sprints(int(project["id"])),
        "sprint_filter": sprint_filter,
        "current_sprint": current_sprint,
    }


def _stats_assignee_key(row: Dict[str, Any]) -> str:
    return str(row["assignee_id"]) if row["assignee_id"] is not None else "unassigned"


def _stats_sprint_key(row: Dict[str, Any]) -> str:
    return str(row["sprint_id"]) if row["sprint_id"] is not None else "none"


def _stats_aggregate(rows: List[Dict[str, Any]], key_fn) -> Dict[str, Dict[str, Any]]:
    """Count and sum story points per group value, in one pass over rows.
    Replaces a per-dimension SQL GROUP BY scan."""
    aggregates: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        value = key_fn(row)
        slot = aggregates.setdefault(value, {"group_value": value, "count": 0, "story_points": 0})
        slot["count"] += 1
        slot["story_points"] += int(row["story_points"] or 0)
    return aggregates


def _stats_previews(sorted_rows: List[Dict[str, Any]], key_fn, limit: int = 8) -> Dict[str, List[Dict[str, Any]]]:
    """Top-`limit` preview tickets per group value. `sorted_rows` must already be
    ordered (updated_at DESC, number DESC); taking the first `limit` per group in
    that order reproduces the per-partition ROW_NUMBER window."""
    previews: Dict[str, List[Dict[str, Any]]] = {}
    for row in sorted_rows:
        value = key_fn(row)
        bucket = previews.setdefault(value, [])
        if len(bucket) < limit:
            bucket.append(
                {
                    "group_value": value,
                    "key": row["key"],
                    "title": row["title"],
                    "story_points": row["story_points"],
                }
            )
    return previews


def _stats_group_from_maps(
    value: str,
    label: str,
    aggregates: Dict[str, Dict[str, Any]],
    previews: Dict[str, List[Dict[str, Any]]],
    href: str = "",
) -> Dict[str, Any]:
    aggregate = aggregates.get(value, {})
    count = int(aggregate.get("count") or 0)
    tickets = previews.get(value, [])
    return {
        "value": value,
        "label": label,
        "count": count,
        "story_points": int(aggregate.get("story_points") or 0),
        "tickets": tickets,
        "ticket_more": max(0, count - len(tickets)),
        "href": href,
    }


def project_statistics(project_key: str, user: Dict[str, Any]) -> Dict[str, Any]:
    project = get_project_by_key(project_key)
    require_project_stats_access(user, project)
    statuses = project_statuses(project)
    ticket_types = project_ticket_types(project)
    sprints = list_project_sprints(int(project["id"]))
    # Single scan over the project's tickets; all summaries, per-dimension
    # aggregates, and previews are then computed in Python. This replaces the
    # previous 12 separate SQL scans (1 summary + 5 group-bys + 5 windowed
    # previews + 1 assignee-label query) with one query.
    with get_conn() as conn:
        rows = rows_to_dicts(
            conn.execute(
                """
                SELECT tickets.status,
                       tickets.priority,
                       tickets.ticket_type,
                       tickets.assignee_id,
                       tickets.sprint_id,
                       tickets.story_points,
                       tickets.key,
                       tickets.title,
                       tickets.updated_at,
                       tickets.number,
                       users.name AS assignee_name,
                       users.login AS assignee_login,
                       users.avatar_url AS assignee_avatar_url
                FROM tickets
                LEFT JOIN users ON users.id = tickets.assignee_id
                WHERE tickets.project_id = ?
                """,
                (project["id"],),
            ).fetchall()
        )

    sorted_rows = sorted(rows, key=lambda row: (row["updated_at"], row["number"]), reverse=True)

    status_aggregates = _stats_aggregate(rows, lambda row: row["status"])
    priority_aggregates = _stats_aggregate(rows, lambda row: row["priority"])
    type_aggregates = _stats_aggregate(rows, lambda row: row["ticket_type"])
    assignee_aggregates = _stats_aggregate(rows, _stats_assignee_key)
    sprint_aggregates = _stats_aggregate(rows, _stats_sprint_key)
    status_previews = _stats_previews(sorted_rows, lambda row: row["status"])
    priority_previews = _stats_previews(sorted_rows, lambda row: row["priority"])
    type_previews = _stats_previews(sorted_rows, lambda row: row["ticket_type"])
    assignee_previews = _stats_previews(sorted_rows, _stats_assignee_key)
    sprint_previews = _stats_previews(sorted_rows, _stats_sprint_key)

    # Distinct assignees that have tickets (matches GROUP BY tickets.assignee_id).
    assignee_rows = []
    seen_assignees = set()
    for row in rows:
        value = _stats_assignee_key(row)
        if value in seen_assignees:
            continue
        seen_assignees.add(value)
        assignee_rows.append(
            {
                "value": value,
                "label": row["assignee_name"] or row["assignee_login"] or "Unassigned",
                "login": row["assignee_login"] or "",
                "avatar_url": row["assignee_avatar_url"] or "",
            }
        )

    open_statuses = ("Done", "Closed")
    summary_row = {
        "total_tickets": len(rows),
        "story_points": sum(int(row["story_points"] or 0) for row in rows),
        "open_tickets": sum(1 for row in rows if row["status"] not in open_statuses),
        "open_story_points": sum(
            int(row["story_points"] or 0) for row in rows if row["status"] not in open_statuses
        ),
        "done_tickets": sum(1 for row in rows if row["status"] == "Done"),
        "closed_tickets": sum(1 for row in rows if row["status"] == "Closed"),
    }

    total_points = int(summary_row.get("story_points") or 0)
    status_groups = [
        _stats_group_from_maps(
            status_name,
            status_name,
            status_aggregates,
            status_previews,
            "#status-%s" % status_name.lower().replace(" ", "-"),
        )
        for status_name in statuses
    ]
    max_count = max([1, *[int(group["count"]) for group in status_groups]])
    max_points = max(1, total_points)
    for group in status_groups:
        group["count_percent"] = int(round((group["count"] / max_count) * 100)) if max_count else 0
        group["points_percent"] = int(round((group["story_points"] / max_points) * 100)) if max_points else 0

    priority_groups = [
        _stats_group_from_maps(priority, priority, priority_aggregates, priority_previews)
        for priority in PRIORITIES
    ]
    type_groups = [
        _stats_group_from_maps(ticket_type, ticket_type, type_aggregates, type_previews)
        for ticket_type in ticket_types
    ]

    assignee_groups = sorted(
        [
            {
                **_stats_group_from_maps(str(group["value"]), str(group["label"]), assignee_aggregates, assignee_previews),
                "login": group["login"],
                "avatar_url": group["avatar_url"],
            }
            for group in assignee_rows
        ],
        key=lambda item: (-int(item["story_points"]), -int(item["count"]), item["label"].lower()),
    )

    sprint_groups = [
        {
            **_stats_group_from_maps(
                "none",
                "No sprint",
                sprint_aggregates,
                sprint_previews,
                "/p/%s/board?sprint=none" % project["key"],
            ),
            "status": "",
            "starts_on": "",
            "ends_on": "",
        }
    ]
    for sprint_item in sprints:
        sprint_key = str(sprint_item["id"])
        sprint_groups.append(
            {
                **_stats_group_from_maps(
                    sprint_key,
                    sprint_item["name"],
                    sprint_aggregates,
                    sprint_previews,
                    "/p/%s/board?sprint=%s" % (project["key"], sprint_item["id"]),
                ),
                "status": sprint_item.get("status") or "",
                "starts_on": sprint_item.get("starts_on") or "",
                "ends_on": sprint_item.get("ends_on") or "",
            }
        )

    return {
        "project": project,
        "project_role": project_role_for_user(user, int(project["id"])),
        "statuses": statuses,
        "ticket_types": ticket_types,
        "summary": {
            "total_tickets": int(summary_row.get("total_tickets") or 0),
            "open_tickets": int(summary_row.get("open_tickets") or 0),
            "done_tickets": int(summary_row.get("done_tickets") or 0),
            "closed_tickets": int(summary_row.get("closed_tickets") or 0),
            "story_points": total_points,
            "open_story_points": int(summary_row.get("open_story_points") or 0),
        },
        "status_groups": status_groups,
        "priority_groups": priority_groups,
        "type_groups": type_groups,
        "assignee_groups": assignee_groups,
        "sprint_groups": sprint_groups,
        "active_sprints": [sprint for sprint in sprints if sprint.get("status") == "active"],
    }


def next_ticket_sort_order_conn(conn: Any, project_id: int, status_value: str) -> float:
    value = conn.execute(
        "SELECT COALESCE(MAX(sort_order), 0) + 1000 FROM tickets WHERE project_id = ? AND status = ?",
        (project_id, status_value),
    ).fetchone()[0]
    return float(value)


def first_ticket_sort_order_conn(conn: Any, project_id: int, status_value: str) -> float:
    value = conn.execute(
        "SELECT COALESCE(MIN(sort_order), 1000) - 1000 FROM tickets WHERE project_id = ? AND status = ?",
        (project_id, status_value),
    ).fetchone()[0]
    return float(value)


def ticket_sort_order_after_conn(
    conn: Any,
    project_id: int,
    status_value: str,
    ticket_id: int,
    after_ticket_key: Optional[str],
) -> float:
    if not after_ticket_key:
        return first_ticket_sort_order_conn(conn, project_id, status_value)
    previous = row_to_dict(
        conn.execute(
            """
            SELECT id, sort_order
            FROM tickets
            WHERE project_id = ? AND status = ? AND key = ? AND id != ?
            """,
            (project_id, status_value, after_ticket_key, ticket_id),
        ).fetchone()
    )
    if not previous:
        return next_ticket_sort_order_conn(conn, project_id, status_value)
    next_row = conn.execute(
        """
        SELECT sort_order
        FROM tickets
        WHERE project_id = ?
          AND status = ?
          AND id != ?
          AND sort_order > ?
        ORDER BY sort_order ASC, updated_at DESC, number DESC
        LIMIT 1
        """,
        (project_id, status_value, ticket_id, previous["sort_order"]),
    ).fetchone()
    previous_order = float(previous["sort_order"] or 0)
    if not next_row:
        return previous_order + 1000
    next_order = float(next_row["sort_order"] or previous_order + 1000)
    if next_order <= previous_order:
        return previous_order + 1000
    return previous_order + ((next_order - previous_order) / 2)


def search_tickets(user: Dict[str, Any], query: str = "", project_key: str = "") -> List[Dict[str, Any]]:
    clean_query = query.strip()
    # Escape LIKE metacharacters so a user typing % or _ matches them literally
    # instead of turning the search into a wildcard over their whole scope.
    escaped = clean_query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    query_like = "%" + escaped + "%"
    params: List[Any] = []
    where = []
    if clean_query:
        where.append(
            "(tickets.key LIKE ? ESCAPE '\\' OR tickets.title LIKE ? ESCAPE '\\' "
            "OR tickets.description LIKE ? ESCAPE '\\')"
        )
        params.extend([query_like, query_like, query_like])
    if project_key.strip():
        where.append("projects.key = ?")
        params.append(project_key.strip().upper())
    if user.get("role") != "admin":
        where.append("project_members.user_id = ?")
        params.append(user["id"])
    sql = """
        SELECT tickets.*,
               projects.key AS project_key,
               projects.name AS project_name,
               assignee.login AS assignee_login,
               assignee.name AS assignee_name,
               assignee.avatar_url AS assignee_avatar_url
        FROM tickets
        JOIN projects ON projects.id = tickets.project_id
        LEFT JOIN users assignee ON assignee.id = tickets.assignee_id
    """
    if user.get("role") != "admin":
        sql += " JOIN project_members ON project_members.project_id = projects.id"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY tickets.updated_at DESC LIMIT 50"
    with get_conn() as conn:
        return rows_to_dicts(conn.execute(sql, tuple(params)).fetchall())


def update_ticket(
    user: Dict[str, Any],
    ticket_key: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    ticket_type: Optional[str] = None,
    status_value: Optional[str] = None,
    priority: Optional[str] = None,
    story_points: Optional[int] = None,
    story_points_touched: bool = False,
    assignee_id: Optional[int] = None,
    assignee_touched: bool = False,
    sprint_id: Optional[int] = None,
    sprint_touched: bool = False,
    position_after_key: Optional[str] = None,
    position_touched: bool = False,
) -> Dict[str, Any]:
    now = utcnow()
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        require_project_access(user, int(ticket["project_id"]), write=True)
        changes: List[Tuple[str, Any, Any]] = []
        if title is not None and title.strip() and title.strip() != ticket["title"]:
            changes.append(("title", ticket["title"], title.strip()))
        if description is not None and description.strip() != ticket["description"]:
            changes.append(("description", ticket["description"], description.strip()))
        if ticket_type is not None:
            project = row_to_dict(
                conn.execute("SELECT * FROM projects WHERE id = ?", (ticket["project_id"],)).fetchone()
            ) or {}
            ticket_type = validate_project_ticket_type(project, ticket_type)
            if ticket_type != ticket["ticket_type"]:
                changes.append(("ticket_type", ticket["ticket_type"], ticket_type))
        if status_value is not None:
            project = row_to_dict(
                conn.execute("SELECT * FROM projects WHERE id = ?", (ticket["project_id"],)).fetchone()
            ) or {}
            status_value = validate_project_ticket_status(project, status_value)
            if status_value != ticket["status"]:
                changes.append(("status", ticket["status"], status_value))
        if priority is not None:
            priority = validate_priority(priority)
            if priority != ticket["priority"]:
                changes.append(("priority", ticket["priority"], priority))
        if story_points_touched:
            story_points = validate_story_points(story_points)
            if story_points != int(ticket["story_points"] or 0):
                changes.append(("story_points", ticket["story_points"], story_points))
        if assignee_touched and assignee_id != ticket["assignee_id"]:
            if assignee_id:
                require_project_member_conn(conn, int(ticket["project_id"]), assignee_id)
            changes.append(("assignee_id", ticket["assignee_id"], assignee_id))
        if sprint_touched:
            sprint_id = validate_project_sprint_conn(conn, int(ticket["project_id"]), sprint_id)
            if sprint_id != ticket["sprint_id"]:
                changes.append(("sprint_id", ticket["sprint_id"], sprint_id))

        target_status = status_value if status_value is not None else ticket["status"]
        target_sort_order = ticket["sort_order"]
        if position_touched:
            target_sort_order = ticket_sort_order_after_conn(
                conn,
                int(ticket["project_id"]),
                str(target_status),
                int(ticket["id"]),
                position_after_key,
            )
        elif status_value is not None and status_value != ticket["status"]:
            target_sort_order = next_ticket_sort_order_conn(conn, int(ticket["project_id"]), str(target_status))
        sort_changed = target_sort_order != ticket["sort_order"]

        if not changes and not sort_changed:
            return get_ticket_by_id_conn(conn, ticket["id"])

        values = {
            "title": ticket["title"],
            "description": ticket["description"],
            "ticket_type": ticket["ticket_type"],
            "status": ticket["status"],
            "priority": ticket["priority"],
            "story_points": int(ticket["story_points"] or 0),
            "assignee_id": ticket["assignee_id"],
            "sprint_id": ticket["sprint_id"],
            "closed_at": ticket["closed_at"],
            "sort_order": ticket["sort_order"],
        }
        for field, _old, new in changes:
            if field == "status":
                values["status"] = new
                values["closed_at"] = now if new == "Closed" else None
            elif field == "assignee_id":
                values["assignee_id"] = new
            elif field == "sprint_id":
                values["sprint_id"] = new
            else:
                values[field] = new

        conn.execute(
            """
            UPDATE tickets
            SET title = ?, description = ?, ticket_type = ?, status = ?, priority = ?, story_points = ?,
                sprint_id = ?, sort_order = ?, assignee_id = ?, closed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                values["title"],
                values["description"],
                values["ticket_type"],
                values["status"],
                values["priority"],
                values["story_points"],
                values["sprint_id"],
                target_sort_order,
                values["assignee_id"],
                values["closed_at"],
                now,
                ticket["id"],
            ),
        )
        if values["assignee_id"]:
            conn.execute(
                "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
                (ticket["id"], values["assignee_id"], now),
            )
        if any(field == "description" for field, _old, _new in changes):
            refresh_ticket_mentions_conn(
                conn,
                int(ticket["id"]),
                int(ticket["project_id"]),
                str(values["description"] or ""),
                "description",
            )
        for field, old, new in changes:
            action = "ticket_updated"
            if field == "status":
                action = "closed" if new == "Closed" else "status_changed"
            if field == "ticket_type":
                action = "type_changed"
            if field == "assignee_id":
                action = "assigned"
            if field == "sprint_id":
                action = "sprint_changed"
            log_action(
                conn,
                ticket["project_id"],
                ticket["id"],
                user["id"],
                action,
                field=field,
                old_value="" if old is None else str(old),
                new_value="" if new is None else str(new),
            )
        status_changed = any(field == "status" for field, _old, _new in changes)
        if sort_changed and not status_changed:
            log_action(
                conn,
                ticket["project_id"],
                ticket["id"],
                user["id"],
                "reordered",
                field="sort_order",
                old_value="" if ticket["sort_order"] is None else str(ticket["sort_order"]),
                new_value=str(target_sort_order),
            )
        return get_ticket_by_id_conn(conn, ticket["id"])


def close_ticket(user: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
    return update_ticket(user, ticket_key, status_value="Closed")


def reopen_ticket(user: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
    project = get_project_for_ticket_key(ticket_key)
    statuses = project_statuses(project)
    target = "Todo" if "Todo" in statuses else statuses[0]
    return update_ticket(user, ticket_key, status_value=target)


def delete_ticket(user: Dict[str, Any], ticket_key: str, confirmation: str = "") -> Dict[str, Any]:
    ticket_key = ticket_key.upper()
    if confirmation.strip().upper() != ticket_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type the ticket key to confirm deletion.")
    project = get_project_for_ticket_key(ticket_key)
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        if int(ticket["project_id"]) != int(project["id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        require_ticket_delete_access(user, project, ticket)
        deleted = dict(ticket)
        deleted["project_key"] = project["key"]
        log_action(
            conn,
            int(project["id"]),
            None,
            user["id"],
            "ticket_deleted",
            metadata={"key": ticket["key"], "title": ticket["title"], "status": ticket["status"]},
        )
        conn.execute("DELETE FROM tickets WHERE id = ?", (ticket["id"],))
        return deleted


def add_comment(user: Dict[str, Any], ticket_key: str, body: str) -> Dict[str, Any]:
    body = body.strip()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment body is required")
    now = utcnow()
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        require_project_access(user, int(ticket["project_id"]), write=True)
        cur = conn.execute(
            "INSERT INTO comments (ticket_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
            (ticket["id"], user["id"], body, now),
        )
        conn.execute("UPDATE tickets SET updated_at = ? WHERE id = ?", (now, ticket["id"]))
        conn.execute(
            "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
            (ticket["id"], user["id"], now),
        )
        refresh_ticket_mentions_conn(
            conn,
            int(ticket["id"]),
            int(ticket["project_id"]),
            body,
            "comment",
            int(cur.lastrowid),
        )
        log_action(conn, ticket["project_id"], ticket["id"], user["id"], "commented")
        return row_to_dict(conn.execute("SELECT * FROM comments WHERE id = ?", (cur.lastrowid,)).fetchone()) or {}


def set_watch(user: Dict[str, Any], ticket_key: str, watch: bool = True) -> None:
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        require_project_access(user, int(ticket["project_id"]), write=False)
        if watch:
            conn.execute(
                "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
                (ticket["id"], user["id"], utcnow()),
            )
            action = "watching"
        else:
            conn.execute("DELETE FROM watchers WHERE ticket_id = ? AND user_id = ?", (ticket["id"], user["id"]))
            action = "unwatching"
        log_action(conn, ticket["project_id"], ticket["id"], user["id"], action)


def log_action(
    conn: Any,
    project_id: Optional[int],
    ticket_id: Optional[int],
    actor_id: Optional[int],
    action: str,
    field: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    now = utcnow()
    cur = conn.execute(
        """
        INSERT INTO action_log
            (project_id, ticket_id, actor_id, action, field, old_value, new_value, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (project_id, ticket_id, actor_id, action, field, old_value, new_value, json_dumps(metadata or {}), now),
    )
    action_id = int(cur.lastrowid)
    if ticket_id and action in NOTIFY_ACTIONS:
        enqueue_notifications(conn, action_id, project_id, ticket_id, actor_id, action)
    return action_id


def purge_expired_records(
    retention_days: Optional[int] = None,
    action_log_retention_days: Optional[int] = None,
) -> Dict[str, int]:
    """Delete rows that are safe to drop so service tables do not grow forever:
    expired sessions, expired/old-used telegram link tokens, and audit/history
    rows past the retention window. api_audit and action_log have separate
    retention because action_log backs the ticket activity history. Returns a
    count of rows removed per table."""
    audit_days = settings.audit_retention_days if retention_days is None else retention_days
    log_days = (
        settings.action_log_retention_days
        if action_log_retention_days is None
        else action_log_retention_days
    )
    now_dt = datetime.now(timezone.utc)
    now = now_dt.replace(microsecond=0).isoformat()
    used_cutoff = (now_dt - timedelta(days=1)).replace(microsecond=0).isoformat()
    audit_cutoff = (now_dt - timedelta(days=max(0, audit_days))).replace(microsecond=0).isoformat()
    log_cutoff = (now_dt - timedelta(days=max(0, log_days))).replace(microsecond=0).isoformat()
    with get_conn() as conn:
        sessions = conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,)).rowcount
        tokens = conn.execute(
            """
            DELETE FROM telegram_link_tokens
            WHERE expires_at <= ? OR (used_at IS NOT NULL AND used_at <= ?)
            """,
            (now, used_cutoff),
        ).rowcount
        audit = conn.execute("DELETE FROM api_audit WHERE created_at < ?", (audit_cutoff,)).rowcount
        actions = conn.execute("DELETE FROM action_log WHERE created_at < ?", (log_cutoff,)).rowcount
    return {
        "sessions": int(sessions or 0),
        "telegram_link_tokens": int(tokens or 0),
        "api_audit": int(audit or 0),
        "action_log": int(actions or 0),
    }


def record_api_audit(
    user_id: Optional[int],
    token_id: Optional[int],
    route: str,
    action: str,
    client: str = "",
    user_agent: str = "",
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO api_audit (user_id, token_id, route, action, client, user_agent, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, token_id, route, action, client[:200], user_agent[:300], utcnow()),
        )


def extract_ticket_keys(text: str) -> List[str]:
    return sorted(set(match.group(1).upper() for match in TICKET_KEY_RE.finditer(text or "")))


def link_github_ref(
    ticket_key: str,
    repo_full_name: str,
    ref_type: str,
    ref_name: str,
    url: str = "",
    sha: str = "",
    title: str = "",
    state: str = "",
    actor_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    now = utcnow()
    repo_full_name = normalize_github_repo(repo_full_name)
    ref_type = ref_type.strip()
    if ref_type not in GITHUB_REF_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid GitHub ref type")
    url = normalize_github_link_url(url)
    with get_conn() as conn:
        ticket = row_to_dict(
            conn.execute(
                """
                SELECT tickets.*, projects.github_repo_full_name AS project_github_repo_full_name
                FROM tickets
                JOIN projects ON projects.id = tickets.project_id
                WHERE tickets.key = ?
                """,
                (ticket_key.upper(),),
            ).fetchone()
        )
        if not ticket:
            return None
        project_repo = ticket.get("project_github_repo_full_name")
        if project_repo and project_repo != repo_full_name:
            return None
        conn.execute(
            """
            INSERT INTO github_links
                (ticket_id, repo_full_name, ref_type, ref_name, url, sha, title, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticket_id, repo_full_name, ref_type, ref_name)
            DO UPDATE SET
                url = excluded.url,
                sha = excluded.sha,
                title = excluded.title,
                state = excluded.state,
                updated_at = excluded.updated_at
            """,
            (ticket["id"], repo_full_name, ref_type, ref_name, url, sha, title, state, now, now),
        )
        log_action(
            conn,
            ticket["project_id"],
            ticket["id"],
            actor_id,
            "github_linked",
            metadata={"repo": repo_full_name, "type": ref_type, "name": ref_name, "url": url},
        )
        return get_ticket_by_id_conn(conn, ticket["id"])


def mark_github_delivery(delivery_id: str, event: str) -> bool:
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO github_deliveries (delivery_id, event, received_at) VALUES (?, ?, ?)",
                (delivery_id, event, utcnow()),
            )
            return True
        except Exception:
            return False


def create_test_notification(user: Dict[str, Any]) -> None:
    with get_conn() as conn:
        prefs = notification_preferences_conn(conn, user["id"])
        channels: List[str] = []
        if prefs.get("email_enabled") and user.get("email"):
            channels.append("email")
        if prefs.get("telegram_enabled"):
            telegram = row_to_dict(
                conn.execute("SELECT * FROM telegram_links WHERE user_id = ?", (user["id"],)).fetchone()
            )
            if telegram:
                channels.append("telegram")
        for channel in channels:
            now = utcnow()
            conn.execute(
                """
                INSERT OR IGNORE INTO notification_outbox
                    (user_id, channel, event_type, subject, body, next_attempt_at, dedupe_key, created_at)
                VALUES (?, ?, 'test', 'RoundTable test notification',
                        'This is a RoundTable test notification.', ?, ?, ?)
                """,
                (user["id"], channel, now, "test:%s:%s:%s" % (user["id"], channel, now), now),
            )


def create_mcp_token(user: Dict[str, Any], name: str) -> Dict[str, str]:
    clean_name = name.strip() or "MCP token"
    token = new_token("rt_")
    now = utcnow()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO mcp_tokens (user_id, name, token_hash, prefix, suffix, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user["id"], clean_name, hash_token(token), token[:10], token[-4:], now),
        )
    return {"token": token, "prefix": token[:10], "suffix": token[-4:], "name": clean_name}


def list_mcp_tokens(user_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        return rows_to_dicts(
            conn.execute(
                """
                SELECT id, name, prefix, suffix, last_used_at, revoked_at, created_at
                FROM mcp_tokens
                WHERE user_id = ? AND revoked_at IS NULL
                ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()
        )


def revoke_mcp_token(user_id: int, token_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE mcp_tokens SET revoked_at = ? WHERE user_id = ? AND id = ?",
            (utcnow(), user_id, token_id),
        )


def create_telegram_link_token(user: Dict[str, Any]) -> Dict[str, str]:
    token = new_token("tg_")
    now_dt = datetime.now(timezone.utc)
    expires_at = (now_dt + timedelta(minutes=20)).replace(microsecond=0).isoformat()
    now = now_dt.replace(microsecond=0).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO telegram_link_tokens (user_id, token_hash, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user["id"], hash_token(token), expires_at, now),
        )
    return {"token": token, "expires_at": expires_at}


def consume_telegram_link_token(token: str, chat_id: str, username: str = "") -> bool:
    now = utcnow()
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM telegram_link_tokens
            WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?
            """,
            (hash_token(token), now),
        ).fetchone()
        data = row_to_dict(row)
        if not data:
            return False
        conn.execute(
            """
            INSERT INTO telegram_links (user_id, chat_id, username, linked_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                chat_id = excluded.chat_id,
                username = excluded.username,
                linked_at = excluded.linked_at
            """,
            (data["user_id"], chat_id, username, now),
        )
        conn.execute("UPDATE telegram_link_tokens SET used_at = ? WHERE id = ?", (now, data["id"]))
        return True


def get_telegram_link(user_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        return row_to_dict(
            conn.execute("SELECT * FROM telegram_links WHERE user_id = ?", (user_id,)).fetchone()
        )


def unlink_telegram(user_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM telegram_links WHERE user_id = ?", (user_id,))
