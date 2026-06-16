"""User records and global-admin role syncing.

Imports downward only (_notification_outbox to seed preferences on create);
never the project/ticket layers.
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from ..config import settings
from ..db import get_conn, row_to_dict, rows_to_dicts, utcnow
from ._notification_outbox import ensure_notification_preferences


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


def list_users() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM users ORDER BY login").fetchall())
