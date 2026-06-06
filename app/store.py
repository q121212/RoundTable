import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from fastapi import HTTPException, status

from .config import settings
from .db import (
    PRIORITIES,
    TICKET_STATUSES,
    get_conn,
    json_dumps,
    json_loads,
    row_to_dict,
    rows_to_dicts,
    utcnow,
)
from .security import hash_token, new_token


PROJECT_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")
TICKET_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d+)\b")
GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
NOTIFY_ACTIONS = {"assigned", "status_changed", "commented", "closed", "reopened"}


def validate_project_key(key: str) -> str:
    normalized = key.strip().upper()
    if not PROJECT_KEY_RE.match(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project key must be 2-10 uppercase letters or digits, starting with a letter.",
        )
    return normalized


def validate_status(value: str) -> str:
    if value not in TICKET_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket status")
    return value


def validate_priority(value: str) -> str:
    if value not in PRIORITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid priority")
    return value


def normalize_github_repo(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""
    if raw.startswith("git@github.com:"):
        raw = raw.removeprefix("git@github.com:")
    elif "://" in raw:
        parsed = urlparse(raw)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub repository must be owner/repo or a github.com URL.",
            )
        raw = parsed.path.strip("/")
    raw = raw.removesuffix(".git").strip("/")
    parts = raw.split("/")
    if len(parts) >= 2:
        raw = "%s/%s" % (parts[0], parts[1])
    if not GITHUB_REPO_RE.match(raw):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub repository must be owner/repo or a github.com URL.",
        )
    return raw


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
            role = user["role"] if user["role"] == "admin" else role
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


def ensure_notification_preferences(conn: Any, user_id: int) -> None:
    now = utcnow()
    conn.execute(
        """
        INSERT OR IGNORE INTO notification_preferences
            (user_id, email_enabled, telegram_enabled, muted_projects_json, created_at, updated_at)
        VALUES (?, 1, 1, '[]', ?, ?)
        """,
        (user_id, now, now),
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


def delete_project(user: Dict[str, Any], project_key: str) -> None:
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    with get_conn() as conn:
        # foreign_keys=ON cascades tickets, members, comments, action_log, links.
        conn.execute("DELETE FROM projects WHERE id = ?", (project["id"],))


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
                (key, name, description, created_by, github_repo_full_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (key, name, description.strip(), user["id"], normalize_github_repo(repo) or None, now),
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
    with get_conn() as conn:
        user = conn.execute("SELECT id FROM users WHERE login = ?", (login.strip(),)).fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        conn.execute(
            """
            INSERT INTO project_members (project_id, user_id, role, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(project_id, user_id) DO UPDATE SET role = excluded.role
            """,
            (project_id, user["id"], role, utcnow()),
        )


def create_ticket(
    user: Dict[str, Any],
    project_key: str,
    title: str,
    description: str = "",
    priority: str = "Medium",
    assignee_id: Optional[int] = None,
) -> Dict[str, Any]:
    title = title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket title is required")
    priority = validate_priority(priority)
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
        number = int(project["next_ticket_number"])
        ticket_key = "%s-%s" % (project["key"], number)
        conn.execute(
            "UPDATE projects SET next_ticket_number = next_ticket_number + 1 WHERE id = ?",
            (project["id"],),
        )
        cur = conn.execute(
            """
            INSERT INTO tickets
                (project_id, number, key, title, description, priority,
                 assignee_id, reporter_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project["id"],
                number,
                ticket_key,
                title,
                description.strip(),
                priority,
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
        log_action(
            conn,
            project["id"],
            ticket_id,
            user["id"],
            "ticket_created",
            metadata={"key": ticket_key, "title": title},
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


def get_ticket_by_id_conn(conn: Any, ticket_id: int) -> Dict[str, Any]:
    ticket = row_to_dict(
        conn.execute(
            """
            SELECT tickets.*,
                   projects.key AS project_key,
                   projects.name AS project_name,
                   assignee.login AS assignee_login,
                   assignee.name AS assignee_name,
                   assignee.avatar_url AS assignee_avatar_url,
                   reporter.login AS reporter_login,
                   reporter.name AS reporter_name,
                   reporter.avatar_url AS reporter_avatar_url
            FROM tickets
            JOIN projects ON projects.id = tickets.project_id
            LEFT JOIN users assignee ON assignee.id = tickets.assignee_id
            LEFT JOIN users reporter ON reporter.id = tickets.reporter_id
            WHERE tickets.id = ?
            """,
            (ticket_id,),
        ).fetchone()
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


def get_ticket(ticket_key: str) -> Dict[str, Any]:
    with get_conn() as conn:
        ticket = row_to_dict(
            conn.execute(
                """
                SELECT tickets.*,
                       projects.key AS project_key,
                       projects.name AS project_name,
                       assignee.login AS assignee_login,
                       assignee.name AS assignee_name,
                       assignee.avatar_url AS assignee_avatar_url,
                       reporter.login AS reporter_login,
                       reporter.name AS reporter_name,
                       reporter.avatar_url AS reporter_avatar_url
                FROM tickets
                JOIN projects ON projects.id = tickets.project_id
                LEFT JOIN users assignee ON assignee.id = tickets.assignee_id
                LEFT JOIN users reporter ON reporter.id = tickets.reporter_id
                WHERE tickets.key = ?
                """,
                (ticket_key.upper(),),
            ).fetchone()
        )
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        return ticket


def get_ticket_bundle(ticket_key: str) -> Dict[str, Any]:
    with get_conn() as conn:
        ticket_row = conn.execute("SELECT id FROM tickets WHERE key = ?", (ticket_key.upper(),)).fetchone()
        if not ticket_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        ticket = get_ticket_by_id_conn(conn, int(ticket_row["id"]))
        comments = rows_to_dicts(
            conn.execute(
                """
                SELECT comments.*, users.login AS user_login,
                       users.name AS user_name,
                       users.avatar_url AS user_avatar_url
                FROM comments
                LEFT JOIN users ON users.id = comments.user_id
                WHERE comments.ticket_id = ?
                ORDER BY comments.created_at
                """,
                (ticket["id"],),
            ).fetchall()
        )
        actions = rows_to_dicts(
            conn.execute(
                """
                SELECT action_log.*, users.login AS actor_login
                FROM action_log
                LEFT JOIN users ON users.id = action_log.actor_id
                WHERE action_log.ticket_id = ?
                ORDER BY action_log.created_at DESC
                LIMIT 100
                """,
                (ticket["id"],),
            ).fetchall()
        )
        links = rows_to_dicts(
            conn.execute(
                """
                SELECT * FROM github_links
                WHERE ticket_id = ?
                ORDER BY updated_at DESC
                """,
                (ticket["id"],),
            ).fetchall()
        )
        watchers = rows_to_dicts(
            conn.execute(
                """
                SELECT users.id, users.login, users.name, users.avatar_url
                FROM watchers
                JOIN users ON users.id = watchers.user_id
                WHERE watchers.ticket_id = ?
                ORDER BY users.login
                """,
                (ticket["id"],),
            ).fetchall()
        )
        return {"ticket": ticket, "comments": comments, "actions": actions, "links": links, "watchers": watchers}


def board_for_project(project_key: str, user: Dict[str, Any]) -> Dict[str, Any]:
    project = get_project_by_key(project_key)
    require_project_access(user, int(project["id"]))
    with get_conn() as conn:
        rows = rows_to_dicts(
            conn.execute(
                """
                SELECT tickets.*,
                       assignee.login AS assignee_login,
                       assignee.name AS assignee_name,
                       assignee.avatar_url AS assignee_avatar_url,
                       reporter.login AS reporter_login,
                       reporter.name AS reporter_name,
                       reporter.avatar_url AS reporter_avatar_url
                FROM tickets
                LEFT JOIN users assignee ON assignee.id = tickets.assignee_id
                LEFT JOIN users reporter ON reporter.id = tickets.reporter_id
                WHERE project_id = ?
                ORDER BY
                    CASE status
                        WHEN 'Backlog' THEN 1
                        WHEN 'Todo' THEN 2
                        WHEN 'In Progress' THEN 3
                        WHEN 'Review' THEN 4
                        WHEN 'Done' THEN 5
                        ELSE 6
                    END,
                    updated_at DESC,
                    number DESC
                """,
                (project["id"],),
            ).fetchall()
        )
    columns = {status_name: [] for status_name in TICKET_STATUSES}
    for ticket in rows:
        columns.setdefault(ticket["status"], []).append(ticket)
    return {"project": project, "statuses": TICKET_STATUSES, "columns": columns}


def search_tickets(user: Dict[str, Any], query: str = "", project_key: str = "") -> List[Dict[str, Any]]:
    query_like = "%" + query.strip() + "%"
    params: List[Any] = []
    where = []
    if query.strip():
        where.append("(tickets.key LIKE ? OR tickets.title LIKE ? OR tickets.description LIKE ?)")
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
    status_value: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[int] = None,
    assignee_touched: bool = False,
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
        if status_value is not None:
            status_value = validate_status(status_value)
            if status_value != ticket["status"]:
                changes.append(("status", ticket["status"], status_value))
        if priority is not None:
            priority = validate_priority(priority)
            if priority != ticket["priority"]:
                changes.append(("priority", ticket["priority"], priority))
        if assignee_touched and assignee_id != ticket["assignee_id"]:
            if assignee_id:
                require_project_member_conn(conn, int(ticket["project_id"]), assignee_id)
            changes.append(("assignee_id", ticket["assignee_id"], assignee_id))

        if not changes:
            return get_ticket_by_id_conn(conn, ticket["id"])

        values = {
            "title": ticket["title"],
            "description": ticket["description"],
            "status": ticket["status"],
            "priority": ticket["priority"],
            "assignee_id": ticket["assignee_id"],
            "closed_at": ticket["closed_at"],
        }
        for field, _old, new in changes:
            if field == "status":
                values["status"] = new
                values["closed_at"] = now if new == "Closed" else None
            elif field == "assignee_id":
                values["assignee_id"] = new
            else:
                values[field] = new

        conn.execute(
            """
            UPDATE tickets
            SET title = ?, description = ?, status = ?, priority = ?,
                assignee_id = ?, closed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                values["title"],
                values["description"],
                values["status"],
                values["priority"],
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
        for field, old, new in changes:
            action = "ticket_updated"
            if field == "status":
                action = "closed" if new == "Closed" else "status_changed"
            if field == "assignee_id":
                action = "assigned"
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
        return get_ticket_by_id_conn(conn, ticket["id"])


def close_ticket(user: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
    return update_ticket(user, ticket_key, status_value="Closed")


def reopen_ticket(user: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
    return update_ticket(user, ticket_key, status_value="Todo")


def get_ticket_by_key_conn(conn: Any, ticket_key: str) -> Dict[str, Any]:
    ticket = row_to_dict(conn.execute("SELECT * FROM tickets WHERE key = ?", (ticket_key.upper(),)).fetchone())
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


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


def enqueue_notifications(
    conn: Any,
    action_id: int,
    project_id: Optional[int],
    ticket_id: int,
    actor_id: Optional[int],
    action: str,
) -> None:
    ticket = get_ticket_by_id_conn(conn, ticket_id)
    recipients = notification_recipients(conn, ticket_id)
    actor = row_to_dict(conn.execute("SELECT login FROM users WHERE id = ?", (actor_id,)).fetchone())
    actor_name = actor["login"] if actor else "Someone"
    subject = "[%s] %s" % (ticket["key"], ticket["title"])
    body = "%s %s %s\n\n%s/t/%s" % (
        actor_name,
        describe_action(action),
        ticket["key"],
        settings.base_url,
        ticket["key"],
    )
    for recipient in recipients:
        if actor_id and recipient["id"] == actor_id:
            continue
        prefs = notification_preferences_conn(conn, recipient["id"])
        muted = json_loads(prefs.get("muted_projects_json"), [])
        if project_id in muted or str(project_id) in muted:
            continue
        channels: List[str] = []
        if prefs.get("email_enabled") and recipient.get("email"):
            channels.append("email")
        telegram = row_to_dict(
            conn.execute("SELECT * FROM telegram_links WHERE user_id = ?", (recipient["id"],)).fetchone()
        )
        if prefs.get("telegram_enabled") and telegram:
            channels.append("telegram")
        for channel in channels:
            conn.execute(
                """
                INSERT OR IGNORE INTO notification_outbox
                    (user_id, channel, event_type, subject, body, next_attempt_at, dedupe_key, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recipient["id"],
                    channel,
                    action,
                    subject,
                    body,
                    utcnow(),
                    "%s:%s:%s" % (action_id, recipient["id"], channel),
                    utcnow(),
                ),
            )


def describe_action(action: str) -> str:
    return {
        "assigned": "assigned",
        "status_changed": "moved",
        "commented": "commented on",
        "closed": "closed",
        "reopened": "reopened",
    }.get(action, "updated")


def notification_recipients(conn: Any, ticket_id: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT DISTINCT users.*
        FROM users
        WHERE users.id IN (
            SELECT assignee_id FROM tickets WHERE id = ? AND assignee_id IS NOT NULL
            UNION
            SELECT reporter_id FROM tickets WHERE id = ? AND reporter_id IS NOT NULL
            UNION
            SELECT user_id FROM watchers WHERE ticket_id = ?
        )
        """,
        (ticket_id, ticket_id, ticket_id),
    ).fetchall()
    return rows_to_dicts(rows)


def notification_preferences_conn(conn: Any, user_id: int) -> Dict[str, Any]:
    ensure_notification_preferences(conn, user_id)
    return row_to_dict(
        conn.execute("SELECT * FROM notification_preferences WHERE user_id = ?", (user_id,)).fetchone()
    ) or {}


def notification_preferences(user_id: int) -> Dict[str, Any]:
    with get_conn() as conn:
        return notification_preferences_conn(conn, user_id)


def update_notification_preferences(
    user_id: int, email_enabled: bool, telegram_enabled: bool
) -> Dict[str, Any]:
    with get_conn() as conn:
        ensure_notification_preferences(conn, user_id)
        conn.execute(
            """
            UPDATE notification_preferences
            SET email_enabled = ?, telegram_enabled = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (1 if email_enabled else 0, 1 if telegram_enabled else 0, utcnow(), user_id),
        )
        return notification_preferences_conn(conn, user_id)


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
    with get_conn() as conn:
        ticket = row_to_dict(conn.execute("SELECT * FROM tickets WHERE key = ?", (ticket_key.upper(),)).fetchone())
        if not ticket:
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
            INSERT INTO mcp_tokens (user_id, name, token_hash, prefix, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user["id"], clean_name, hash_token(token), token[:10], now),
        )
    return {"token": token, "prefix": token[:10], "name": clean_name}


def list_mcp_tokens(user_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        return rows_to_dicts(
            conn.execute(
                """
                SELECT id, name, prefix, last_used_at, revoked_at, created_at
                FROM mcp_tokens
                WHERE user_id = ?
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
