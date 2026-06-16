"""Per-user account peripherals: MCP tokens, Telegram link tokens/links, the
API audit log, retention pruning, and the test-notification helper.

Imports downward only (_notification_outbox for the test notification); never
_tickets/_projects.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ..config import settings
from ..db import get_conn, row_to_dict, rows_to_dicts, utcnow
from ..security import hash_token, new_token
from ._notification_outbox import notification_preferences_conn


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
