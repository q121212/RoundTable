import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.db import get_conn, row_to_dict
from app.main import app
from app.security import SESSION_COOKIE, create_session
from app.store import (
    add_project_member,
    board_for_project,
    close_ticket,
    create_project,
    create_sprint,
    create_ticket,
    delete_project,
    get_project_by_key,
    get_ticket_bundle,
    list_project_sprints,
    link_ticket,
    project_members,
    project_ticket_types,
    remove_project_member,
    search_linkable_tickets,
    sync_configured_admin_roles,
    update_project_member,
    update_project_settings,
    update_sprint_status,
    update_ticket,
    upsert_user,
    unlink_ticket,
)


def test_project_prefixed_ticket_sequence(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "crm", "CRM")

    first = create_ticket(user, "CRM", "First ticket")
    second = create_ticket(user, "CRM", "Second ticket")

    assert first["key"] == "CRM-1"
    assert second["key"] == "CRM-2"
    assert board_for_project("CRM", user)["columns"]["Backlog"][0]["key"] == "CRM-2"


def test_ticket_board_order_can_be_changed_within_status(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    first = create_ticket(user, "RT", "First")
    second = create_ticket(user, "RT", "Second")
    third = create_ticket(user, "RT", "Third")

    assert [ticket["key"] for ticket in board_for_project("RT", user)["columns"]["Backlog"]] == [
        third["key"],
        second["key"],
        first["key"],
    ]

    update_ticket(user, first["key"], position_after_key="", position_touched=True)
    update_ticket(user, third["key"], position_after_key=first["key"], position_touched=True)

    assert [ticket["key"] for ticket in board_for_project("RT", user)["columns"]["Backlog"]] == [
        first["key"],
        third["key"],
        second["key"],
    ]


def test_ticket_board_order_can_be_changed_via_api(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    first = create_ticket(user, "RT", "First")
    second = create_ticket(user, "RT", "Second")
    third = create_ticket(user, "RT", "Third")
    session = create_session(int(user["id"]))

    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, session["token"])
    response = client.patch(
        f"/api/tickets/{first['key']}",
        json={"status": "Backlog", "position_after_key": third["key"]},
        headers={"x-csrf-token": session["csrf"]},
    )

    assert response.status_code == 200
    assert [ticket["key"] for ticket in board_for_project("RT", user)["columns"]["Backlog"]] == [
        third["key"],
        first["key"],
        second["key"],
    ]


def test_project_sprints_filter_board_and_update_tickets(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    sprint = create_sprint(user, "RT", "Sprint 1", status_value="active")
    sprint_ticket = create_ticket(user, "RT", "Scoped work", sprint_id=sprint["id"])
    backlog_ticket = create_ticket(user, "RT", "Later work")

    active_board = board_for_project("RT", user, sprint_filter="active")
    no_sprint_board = board_for_project("RT", user, sprint_filter="none")

    assert [ticket["key"] for ticket in active_board["columns"]["Backlog"]] == [sprint_ticket["key"]]
    assert [ticket["key"] for ticket in no_sprint_board["columns"]["Backlog"]] == [backlog_ticket["key"]]

    updated = update_ticket(user, backlog_ticket["key"], sprint_id=sprint["id"], sprint_touched=True)

    assert updated["sprint_id"] == sprint["id"]
    assert updated["sprint_name"] == "Sprint 1"


def test_only_one_sprint_can_be_active_per_project(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    first = create_sprint(user, "RT", "Sprint 1", status_value="active")
    second = create_sprint(user, "RT", "Sprint 2")

    update_sprint_status(user, "RT", int(second["id"]), "active")
    sprints = {sprint["name"]: sprint["status"] for sprint in list_project_sprints(int(first["project_id"]))}

    assert sprints["Sprint 1"] == "planned"
    assert sprints["Sprint 2"] == "active"


def test_project_accepts_github_repo_url(temp_db):
    user = upsert_user("alice", email="alice@example.com")

    project = create_project(user, "web", "Website", repo="https://github.com/acme/site.git")

    assert project["github_repo_full_name"] == "acme/site"


def test_project_status_settings_control_board_and_ticket_updates(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "OPS", "Operations")

    update_project_settings(user, "OPS", "Operations", statuses=["Todo", "Review", "Done"])
    ticket = create_ticket(user, "OPS", "Custom workflow")
    board = board_for_project("OPS", user)

    assert list(board["columns"]) == ["Todo", "Review", "Done"]
    assert ticket["status"] == "Todo"
    assert update_ticket(user, ticket["key"], status_value="Review")["status"] == "Review"
    with pytest.raises(HTTPException) as exc:
        update_ticket(user, ticket["key"], status_value="Closed")
    assert exc.value.status_code == 400


def test_project_status_with_tickets_cannot_be_disabled(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "WEB", "Website")
    create_ticket(user, "WEB", "Keep visible")

    with pytest.raises(HTTPException) as exc:
        update_project_settings(user, "WEB", "Website", statuses=["Todo", "Review"])

    assert exc.value.status_code == 400
    assert "Backlog" in exc.value.detail


def test_project_ticket_type_settings_and_updates(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    project = create_project(user, "RT", "RoundTable")

    update_project_settings(user, "RT", "RoundTable", ticket_types=["Task", "Epic"])
    project = get_project_by_key("RT")

    ticket = create_ticket(user, "RT", "Planning", ticket_type="Epic")
    updated = update_ticket(user, ticket["key"], ticket_type="Task")

    assert project_ticket_types(project) == ["Task", "Epic"]
    assert ticket["ticket_type"] == "Epic"
    assert updated["ticket_type"] == "Task"
    with pytest.raises(HTTPException) as exc:
        create_ticket(user, "RT", "Broken type", ticket_type="Bug")
    assert exc.value.status_code == 400


def test_project_ticket_type_in_use_cannot_be_disabled(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "BUG", "Bugs")
    create_ticket(user, "BUG", "Fix login", ticket_type="Bug")

    with pytest.raises(HTTPException) as exc:
        update_project_settings(user, "BUG", "Bugs", ticket_types=["Task", "Epic"])

    assert exc.value.status_code == 400
    assert "Bug" in exc.value.detail


def test_ticket_links_are_project_scoped_and_logged(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    first = create_ticket(user, "RT", "Epic", ticket_type="Epic")
    second = create_ticket(user, "RT", "Task")

    link_ticket(user, first["key"], second["key"], "parent")
    bundle = get_ticket_bundle(first["key"])

    assert bundle["ticket_links"][0]["other_key"] == second["key"]
    assert bundle["ticket_links"][0]["link_type"] == "parent"
    assert bundle["actions"][0]["action"] == "linked"

    unlink_ticket(user, first["key"], int(bundle["ticket_links"][0]["id"]))
    assert get_ticket_bundle(first["key"])["ticket_links"] == []


def test_board_includes_ticket_link_summary(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    first = create_ticket(user, "RT", "Epic", ticket_type="Epic")
    second = create_ticket(user, "RT", "Task")

    link_ticket(user, first["key"], second["key"], "relates")
    board = board_for_project("RT", user)
    tickets = {ticket["key"]: ticket for column in board["columns"].values() for ticket in column}

    assert tickets[first["key"]]["linked_ticket_count"] == 1
    assert tickets[first["key"]]["linked_tickets"][0]["other_key"] == second["key"]
    assert tickets[second["key"]]["linked_tickets"][0]["other_key"] == first["key"]


def test_ticket_link_pair_is_unique_even_when_reversed(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    first = create_ticket(user, "RT", "Epic", ticket_type="Epic")
    second = create_ticket(user, "RT", "Task")

    link_ticket(user, first["key"], second["key"], "relates")
    link_ticket(user, second["key"], first["key"], "blocks")
    board = board_for_project("RT", user)
    tickets = {ticket["key"]: ticket for column in board["columns"].values() for ticket in column}

    assert tickets[first["key"]]["linked_ticket_count"] == 1
    assert tickets[second["key"]]["linked_ticket_count"] == 1
    assert get_ticket_bundle(first["key"])["ticket_links"][0]["link_type"] == "blocks"


def test_ticket_links_reject_self_and_cross_project(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "ONE", "One")
    create_project(user, "TWO", "Two")
    one = create_ticket(user, "ONE", "One task")
    two = create_ticket(user, "TWO", "Two task")

    with pytest.raises(HTTPException) as self_exc:
        link_ticket(user, one["key"], one["key"])
    assert self_exc.value.status_code == 400

    with pytest.raises(HTTPException) as cross_exc:
        link_ticket(user, one["key"], two["key"])
    assert cross_exc.value.status_code == 400


def test_search_linkable_tickets_filters_by_key_and_title(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    project = create_project(user, "RT", "RoundTable")
    current = create_ticket(user, "RT", "Current")
    by_title = create_ticket(user, "RT", "OAuth callback fails", ticket_type="Bug")
    by_key = create_ticket(user, "RT", "Plain work")

    title_results = search_linkable_tickets(int(project["id"]), current["key"], "oauth")
    key_results = search_linkable_tickets(int(project["id"]), current["key"], by_key["key"].lower())

    assert [ticket["key"] for ticket in title_results] == [by_title["key"]]
    assert key_results[0]["key"] == by_key["key"]
    assert current["key"] not in {ticket["key"] for ticket in title_results + key_results}


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
    project = create_project(reporter, "AI", "AI Platform")
    add_project_member(int(project["id"]), "bob", "member")

    create_ticket(reporter, "AI", "Wire model telemetry", assignee_id=assignee["id"])

    with get_conn() as conn:
        row = row_to_dict(conn.execute("SELECT * FROM notification_outbox").fetchone())
    assert row is not None
    assert row["user_id"] == assignee["id"]
    assert row["channel"] == "email"


def test_assignee_must_be_project_member(temp_db):
    reporter = upsert_user("alice", email="alice@example.com")
    outsider = upsert_user("mallory", email="mallory@example.com")
    create_project(reporter, "SEC", "Security")
    ticket = create_ticket(reporter, "SEC", "Harden project")

    with pytest.raises(HTTPException) as create_exc:
        create_ticket(reporter, "SEC", "Leak notifications", assignee_id=outsider["id"])
    assert create_exc.value.status_code == 400

    with pytest.raises(HTTPException) as update_exc:
        update_ticket(reporter, ticket["key"], assignee_id=outsider["id"], assignee_touched=True)
    assert update_exc.value.status_code == 400


def test_project_members_exposes_safe_profile_fields(temp_db):
    user = upsert_user("alice", email="alice@example.com", github_id="1")
    project = create_project(user, "CRM", "CRM")

    member = project_members(int(project["id"]))[0]

    assert set(member) == {"id", "login", "name", "avatar_url", "project_role"}


def test_project_member_can_be_invited_before_first_login(temp_db):
    owner = upsert_user("alice", email="alice@example.com")
    project = create_project(owner, "INV", "Invites")

    add_project_member(int(project["id"]), "octocat", "viewer")

    invited = project_members(int(project["id"]))
    assert any(member["login"] == "octocat" and member["project_role"] == "viewer" for member in invited)

    upsert_user("octocat", github_id="42", name="The Octocat", avatar_url="https://example.com/a.png")
    updated = {member["login"]: member for member in project_members(int(project["id"]))}
    assert updated["octocat"]["name"] == "The Octocat"
    assert updated["octocat"]["avatar_url"] == "https://example.com/a.png"
    assert updated["octocat"]["project_role"] == "viewer"


def test_delete_project_cascades(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "GT", "GigaTool")
    ticket = create_ticket(user, "GT", "Some ticket")

    # Wrong confirmation is rejected.
    with pytest.raises(HTTPException) as exc:
        delete_project(user, "GT", "nope")
    assert exc.value.status_code == 400

    delete_project(user, "GT", "GT")

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
        delete_project(member, "OPS", "OPS")
    assert exc.value.status_code == 403

    delete_project(owner, "OPS", "OPS")
    with get_conn() as conn:
        assert conn.execute("SELECT COUNT(*) c FROM projects WHERE key = 'OPS'").fetchone()["c"] == 0


def test_member_cannot_create_project(temp_db):
    from app.config import settings

    object.__setattr__(settings, "allow_dev_login", False)
    object.__setattr__(settings, "admin_github_logins", ["alice"])

    member = upsert_user("bob", email="bob@example.com")
    session = create_session(int(member["id"]))

    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, session["token"])
    response = client.post(
        "/api/projects",
        data={"csrf_token": session["csrf"], "key": "NOPE", "name": "Nope"},
        follow_redirects=False,
    )

    assert response.status_code == 403


def test_member_management_role_change_and_remove(temp_db):
    owner = upsert_user("alice", email="alice@example.com")
    project = create_project(owner, "WEB", "Website")
    bob = upsert_user("bob", email="bob@example.com")
    add_project_member(int(project["id"]), "bob", "member")

    # Promote and demote a regular member.
    update_project_member(int(project["id"]), int(bob["id"]), "admin")
    update_project_member(int(project["id"]), int(bob["id"]), "viewer")
    roles = {m["login"]: m["project_role"] for m in project_members(int(project["id"]))}
    assert roles["bob"] == "viewer"

    # The sole admin (owner) cannot be demoted or removed.
    with pytest.raises(HTTPException) as exc:
        update_project_member(int(project["id"]), int(owner["id"]), "member")
    assert exc.value.status_code == 400
    with pytest.raises(HTTPException):
        remove_project_member(int(project["id"]), int(owner["id"]))

    # A non-admin member can be removed.
    remove_project_member(int(project["id"]), int(bob["id"]))
    assert "bob" not in {m["login"] for m in project_members(int(project["id"]))}


def test_configured_admins_override_stale_dev_admins(temp_db):
    from app.config import settings

    object.__setattr__(settings, "allow_dev_login", True)
    object.__setattr__(settings, "admin_github_logins", [])

    stale_admin = upsert_user("admin")
    assert stale_admin["role"] == "admin"

    object.__setattr__(settings, "admin_github_logins", ["alice"])

    alice = upsert_user("alice")
    admin_again = upsert_user("admin")
    sync_configured_admin_roles()

    assert alice["role"] == "admin"
    assert admin_again["role"] == "member"
    with get_conn() as conn:
        rows = {
            row["login"]: row["role"]
            for row in conn.execute("SELECT login, role FROM users ORDER BY login").fetchall()
        }
    assert rows == {"admin": "member", "alice": "admin"}


def test_member_cannot_manage_project_members_via_api(temp_db):
    from app.config import settings

    object.__setattr__(settings, "allow_dev_login", False)
    object.__setattr__(settings, "admin_github_logins", ["alice"])

    owner = upsert_user("alice", email="alice@example.com")
    project = create_project(owner, "WEB", "Website")
    member = upsert_user("bob", email="bob@example.com")
    outsider = upsert_user("mallory", email="mallory@example.com")
    add_project_member(int(project["id"]), "bob", "member")
    session = create_session(int(member["id"]))

    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, session["token"])
    response = client.post(
        "/api/projects/WEB/members",
        data={"csrf_token": session["csrf"], "login": outsider["login"], "role": "admin"},
        follow_redirects=False,
    )

    assert response.status_code == 403
