from app.db import get_conn
from app.store import create_project, create_ticket, project_statistics, upsert_user
from app.store._statistics import _format_duration, _status_time_groups

STATUSES = ["Backlog", "Todo", "In Progress", "Review", "Done", "Closed"]


def _by_value(groups):
    return {group["value"]: group for group in groups}


def test_status_time_groups_reconstructed_from_action_log(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    project = create_project(user, "TM", "Time")
    pid = int(project["id"])
    ticket = create_ticket(user, "TM", "Walk the board")
    tid = int(ticket["id"])

    t0 = "2026-01-01T00:00:00+00:00"
    t1 = "2026-01-02T00:00:00+00:00"  # +1 day in Backlog
    t2 = "2026-01-02T04:00:00+00:00"  # +4 hours in Todo
    with get_conn() as conn:
        conn.execute("UPDATE tickets SET created_at = ?, status = 'In Progress' WHERE id = ?", (t0, tid))
        conn.execute("DELETE FROM action_log WHERE ticket_id = ? AND field = 'status'", (tid,))
        for old, new, ts in [("Backlog", "Todo", t1), ("Todo", "In Progress", t2)]:
            conn.execute(
                "INSERT INTO action_log (project_id, ticket_id, actor_id, action, field, "
                "old_value, new_value, created_at) VALUES (?, ?, ?, 'status_changed', 'status', ?, ?, ?)",
                (pid, tid, int(user["id"]), old, new, ts),
            )

    with get_conn() as conn:
        groups = _by_value(_status_time_groups(conn, pid, STATUSES))

    assert groups["Backlog"]["avg_completed_seconds"] == 86400  # 1 day
    assert groups["Backlog"]["completed_count"] == 1
    assert groups["Backlog"]["avg_completed_label"] == "1d"
    assert groups["Todo"]["avg_completed_seconds"] == 14400  # 4 hours
    assert groups["Todo"]["avg_completed_label"] == "4h"
    # Still in progress: an open segment measured to now, no completed segment.
    assert groups["In Progress"]["completed_count"] == 0
    assert groups["In Progress"]["current_count"] == 1
    assert groups["In Progress"]["avg_current_seconds"] > 0
    # Bar width is relative to the largest average (Backlog here).
    assert groups["Backlog"]["completed_percent"] == 100


def test_project_statistics_includes_status_time_groups(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "TS", "TimeStats")
    create_ticket(user, "TS", "Fresh ticket")

    stats = project_statistics("TS", user)

    assert "status_time_groups" in stats
    values = [group["value"] for group in stats["status_time_groups"]]
    assert values == stats["statuses"]  # one row per enabled status, in order


def test_stats_page_renders_time_in_status_panel(temp_db):
    from fastapi.testclient import TestClient

    from app.main import app
    from app.security import SESSION_COOKIE, create_session

    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RP", "Render")
    create_ticket(user, "RP", "T1")
    session = create_session(int(user["id"]))
    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, session["token"])

    response = client.get("/p/RP/stats")

    assert response.status_code == 200
    assert 'data-i18n="stats.time_in_status"' in response.text
    assert 'data-i18n="stats.avg_time"' in response.text


def test_format_duration():
    assert _format_duration(30) == "30s"
    assert _format_duration(600) == "10m"
    assert _format_duration(3600) == "1h"
    assert _format_duration(3600 + 600) == "1h 10m"
    assert _format_duration(86400) == "1d"
    assert _format_duration(86400 + 3600) == "1d 1h"
