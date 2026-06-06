import pytest
from fastapi import HTTPException

from app.db import get_conn, row_to_dict
from app.store import (
    add_project_member,
    board_for_project,
    close_ticket,
    create_project,
    create_ticket,
    delete_project,
    get_ticket_bundle,
    upsert_user,
)


def test_project_prefixed_ticket_sequence(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "crm", "CRM")

    first = create_ticket(user, "CRM", "First ticket")
    second = create_ticket(user, "CRM", "Second ticket")

    assert first["key"] == "CRM-1"
    assert second["key"] == "CRM-2"
    assert board_for_project("CRM", user)["columns"]["Backlog"][0]["key"] == "CRM-2"


def test_project_accepts_github_repo_url(temp_db):
    user = upsert_user("alice", email="alice@example.com")

    project = create_project(user, "web", "Website", repo="https://github.com/acme/site.git")

    assert project["github_repo_full_name"] == "acme/site"


def test_close_ticket_logs_action(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "OPS", "Operations")
    ticket = create_ticket(user, "OPS", "Restart service")

    closed = close_ticket(user, ticket["key"])
    bundle = get_ticket_bundle(ticket["key"])

    assert closed["status"] == "Closed"
    assert bundle["actions"][0]["action"] == "closed"


def test_assignment_notification_outbox(temp_db):
    reporter = upsert_user("alice", email="alice@example.com")
    assignee = upsert_user("bob", email="bob@example.com")
    create_project(reporter, "AI", "AI Platform")

    create_ticket(reporter, "AI", "Wire model telemetry", assignee_id=assignee["id"])

    with get_conn() as conn:
        row = row_to_dict(conn.execute("SELECT * FROM notification_outbox").fetchone())
    assert row is not None
    assert row["user_id"] == assignee["id"]
    assert row["channel"] == "email"


def test_delete_project_cascades(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "GT", "GigaTool")
    ticket = create_ticket(user, "GT", "Some ticket")

    delete_project(user, "GT")

    with get_conn() as conn:
        assert conn.execute("SELECT COUNT(*) c FROM projects WHERE key = 'GT'").fetchone()["c"] == 0
        assert (
            conn.execute("SELECT COUNT(*) c FROM tickets WHERE key = ?", (ticket["key"],)).fetchone()["c"]
            == 0
        )


def test_delete_project_requires_admin(temp_db):
    from app.config import settings

    object.__setattr__(settings, "allow_dev_login", False)
    object.__setattr__(settings, "admin_github_logins", ["alice"])

    owner = upsert_user("alice", email="alice@example.com")
    project = create_project(owner, "OPS", "Operations")
    member = upsert_user("bob", email="bob@example.com")
    add_project_member(int(project["id"]), "bob", "member")

    with pytest.raises(HTTPException) as exc:
        delete_project(member, "OPS")
    assert exc.value.status_code == 403

    delete_project(owner, "OPS")
    with get_conn() as conn:
        assert conn.execute("SELECT COUNT(*) c FROM projects WHERE key = 'OPS'").fetchone()["c"] == 0
