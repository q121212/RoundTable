import threading

from app import notifications


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
