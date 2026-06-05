from app.db import get_conn, row_to_dict
from app.store import (
    board_for_project,
    close_ticket,
    create_project,
    create_ticket,
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
