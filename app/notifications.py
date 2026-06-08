import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, Optional

import httpx

from .config import settings
from .db import get_conn, row_to_dict, rows_to_dicts, utcnow


logger = logging.getLogger("roundtable.notifications")


async def notification_worker(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            await process_due_notifications()
        except Exception:
            logger.exception("notification worker iteration failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=5)
        except asyncio.TimeoutError:
            continue


async def process_due_notifications(limit: int = 20) -> None:
    with get_conn() as conn:
        rows = rows_to_dicts(
            conn.execute(
                """
                SELECT * FROM notification_outbox
                WHERE status = 'pending' AND next_attempt_at <= ?
                ORDER BY created_at
                LIMIT ?
                """,
                (utcnow(), limit),
            ).fetchall()
        )
    for item in rows:
        await send_outbox_item(item)


async def send_outbox_item(item: Dict[str, Any]) -> None:
    try:
        if item["channel"] == "email":
            send_email(item)
        elif item["channel"] == "telegram":
            await send_telegram(item)
        else:
            raise RuntimeError("Unsupported notification channel: %s" % item["channel"])
    except Exception as exc:
        mark_notification_failed(item, str(exc))
        return
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE notification_outbox
            SET status = 'sent', sent_at = ?, last_error = NULL
            WHERE id = ?
            """,
            (utcnow(), item["id"]),
        )


def mark_notification_failed(item: Dict[str, Any], error: str) -> None:
    attempts = int(item["attempts"]) + 1
    status = "failed" if attempts >= 5 else "pending"
    delay_seconds = min(3600, 30 * (2 ** max(0, attempts - 1)))
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE notification_outbox
            SET attempts = ?,
                status = ?,
                last_error = ?,
                next_attempt_at = datetime('now', ?)
            WHERE id = ?
            """,
            (attempts, status, error[:500], "+%s seconds" % delay_seconds, item["id"]),
        )


def send_email(item: Dict[str, Any]) -> None:
    if not settings.smtp_host:
        raise RuntimeError("SMTP_HOST is not configured")
    user = load_user(item["user_id"])
    if not user or not user.get("email"):
        raise RuntimeError("Recipient has no email")
    message = EmailMessage()
    message["Subject"] = item["subject"]
    message["From"] = settings.smtp_from
    message["To"] = user["email"]
    message.set_content(item["body"])
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


async def send_telegram(item: Dict[str, Any]) -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    link = load_telegram_link(item["user_id"])
    if not link:
        raise RuntimeError("Recipient has no Telegram link")
    url = "https://api.telegram.org/bot%s/sendMessage" % settings.telegram_bot_token
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            url,
            json={
                "chat_id": link["chat_id"],
                "text": "%s\n\n%s" % (item["subject"], item["body"]),
                "disable_web_page_preview": True,
            },
        )
        response.raise_for_status()


def load_user(user_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        return row_to_dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())


def load_telegram_link(user_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        return row_to_dict(
            conn.execute("SELECT * FROM telegram_links WHERE user_id = ?", (user_id,)).fetchone()
        )
