import threading
from datetime import datetime, timedelta, timezone

from app import notifications
from app.db import get_conn
from app.security import create_session, get_user_by_session
from app.store import create_telegram_link_token, purge_expired_records, upsert_user


def _iso(days_ago):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).replace(microsecond=0).isoformat()


async def test_email_send_runs_off_the_event_loop(temp_db, monkeypatch):
    """smtplib is blocking, so send_outbox_item must offload it to a worker
    thread. If it ran inline on the event loop, a slow SMTP server would stall
    every HTTP request and SSE stream."""
    seen = {}

    def fake_send_email(item):
        seen["thread"] = threading.get_ident()

    monkeypatch.setattr(notifications, "send_email", fake_send_email)

    # id 999 does not exist; the post-send UPDATE is a harmless no-op.
    await notifications.send_outbox_item({"id": 999, "channel": "email"})

    assert "thread" in seen
    assert seen["thread"] != threading.get_ident()


async def test_telegram_send_failure_is_marked_for_retry(temp_db, monkeypatch):
    """A failing channel must not raise out of send_outbox_item; it records the
    error and schedules a retry via mark_notification_failed."""
    recorded = {}

    async def boom(item):
        raise RuntimeError("telegram down")

    def fake_mark_failed(item, error):
        recorded["error"] = error

    monkeypatch.setattr(notifications, "send_telegram", boom)
    monkeypatch.setattr(notifications, "mark_notification_failed", fake_mark_failed)

    await notifications.send_outbox_item({"id": 1, "channel": "telegram", "attempts": 0})

    assert recorded["error"] == "telegram down"


def test_purge_removes_expired_sessions_keeps_active(temp_db):
    user = upsert_user("alice")
    active = create_session(int(user["id"]))  # expires in 30 days
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO sessions (user_id, token_hash, csrf_token, expires_at, created_at)
            VALUES (?, 'expired-hash', 'csrf', ?, ?)
            """,
            (int(user["id"]), _iso(1), _iso(40)),
        )

    removed = purge_expired_records()

    assert removed["sessions"] == 1
    assert get_user_by_session(active["token"]) is not None  # active session untouched


def test_purge_audit_and_action_log_have_separate_retention(temp_db):
    user = upsert_user("alice")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO api_audit (user_id, route, action, created_at) VALUES (?, '/mcp', 'old', ?)",
            (int(user["id"]), _iso(120)),
        )
        conn.execute(
            "INSERT INTO api_audit (user_id, route, action, created_at) VALUES (?, '/mcp', 'recent', ?)",
            (int(user["id"]), _iso(5)),
        )
        conn.execute("INSERT INTO action_log (action, created_at) VALUES ('old', ?)", (_iso(120),))
        conn.execute("INSERT INTO action_log (action, created_at) VALUES ('recent', ?)", (_iso(5),))

    # Default: api_audit pruned at 90d, but action_log keeps its long history.
    removed = purge_expired_records()

    assert removed["api_audit"] == 1
    assert removed["action_log"] == 0
    with get_conn() as conn:
        audit_actions = [r["action"] for r in conn.execute("SELECT action FROM api_audit").fetchall()]
        log_actions = sorted(r["action"] for r in conn.execute("SELECT action FROM action_log").fetchall())
    assert audit_actions == ["recent"]
    assert log_actions == ["old", "recent"]  # 120-day history retained by default


def test_action_log_is_pruned_when_its_retention_is_short(temp_db):
    with get_conn() as conn:
        conn.execute("INSERT INTO action_log (action, created_at) VALUES ('old', ?)", (_iso(120),))
        conn.execute("INSERT INTO action_log (action, created_at) VALUES ('recent', ?)", (_iso(5),))

    removed = purge_expired_records(action_log_retention_days=90)

    assert removed["action_log"] == 1
    with get_conn() as conn:
        log_actions = [r["action"] for r in conn.execute("SELECT action FROM action_log").fetchall()]
    assert log_actions == ["recent"]


def test_purge_removes_expired_and_old_used_telegram_tokens(temp_db):
    user = upsert_user("alice")
    active = create_telegram_link_token(user)  # expires in 20 minutes, unused
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO telegram_link_tokens (user_id, token_hash, expires_at, created_at) "
            "VALUES (?, 'expired', ?, ?)",
            (int(user["id"]), _iso(1), _iso(1)),
        )
        conn.execute(
            "INSERT INTO telegram_link_tokens (user_id, token_hash, expires_at, used_at, created_at) "
            "VALUES (?, 'old-used', ?, ?, ?)",
            (int(user["id"]), _iso(-1), _iso(2), _iso(3)),
        )

    removed = purge_expired_records()

    assert removed["telegram_link_tokens"] == 2
    with get_conn() as conn:
        remaining = conn.execute("SELECT COUNT(*) AS c FROM telegram_link_tokens").fetchone()["c"]
    assert remaining == 1  # the active, unused, unexpired token survives
    assert active["token"]
