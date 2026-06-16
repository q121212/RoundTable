"""Notification fan-out: turning an action into per-recipient outbox rows, plus
notification preference storage.

Direction: this module may import _read_models (to read the ticket being
notified about) but must never import _action_log or _tickets — that is what
keeps the action_log -> outbox -> reads chain acyclic.
"""

from typing import Any, Dict, List, Optional

from ..config import settings
from ..db import get_conn, json_loads, row_to_dict, rows_to_dicts, utcnow
from ._read_models import get_ticket_by_id_conn


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
            UNION
            SELECT mentioned_user_id FROM ticket_mentions WHERE ticket_id = ?
        )
        """,
        (ticket_id, ticket_id, ticket_id, ticket_id),
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
