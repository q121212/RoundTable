import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.db import get_conn, row_to_dict
from app.main import app
from app.security import SESSION_COOKIE, create_session
from app.store import (
    add_project_member,
    add_comment,
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
    search_project_users,
    sync_configured_admin_roles,
    update_project_member,
    update_project_settings,
    update_sprint,
    update_sprint_status,
    update_ticket,
    update_ticket_link,
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
    with get_conn() as conn:
        row = row_to_dict(
            conn.execute(
                "SELECT action, field FROM action_log WHERE action = 'reordered' ORDER BY id DESC LIMIT 1",
            ).fetchone()
        )
    assert row == {"action": "reordered", "field": "sort_order"}


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


def test_ticket_story_points_create_update_and_validate(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    ticket = create_ticket(user, "RT", "Estimate work", story_points=5)

    assert ticket["story_points"] == 5
    updated = update_ticket(user, ticket["key"], story_points=8, story_points_touched=True)
    assert updated["story_points"] == 8

    with get_conn() as conn:
        row = row_to_dict(
            conn.execute(
                "SELECT action, field, old_value, new_value FROM action_log WHERE field = 'story_points' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        )
    assert row == {"action": "ticket_updated", "field": "story_points", "old_value": "5", "new_value": "8"}

    with pytest.raises(HTTPException):
        update_ticket(user, ticket["key"], story_points=-1, story_points_touched=True)
    with pytest.raises(HTTPException):
        create_ticket(user, "RT", "Too large", story_points=1000)


def test_active_sprint_filter_is_empty_without_active_sprint(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    ticket = create_ticket(user, "RT", "Unscoped work")

    active_board = board_for_project("RT", user, sprint_filter="active")
    no_sprint_board = board_for_project("RT", user, sprint_filter="none")

    assert active_board["columns"]["Backlog"] == []
    assert [item["key"] for item in no_sprint_board["columns"]["Backlog"]] == [ticket["key"]]


def test_board_sprint_filter_page_hides_no_sprint_tickets(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    ticket = create_ticket(user, "RT", "Unscoped work")
    session = create_session(int(user["id"]))

    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, session["token"])

    active_response = client.get("/p/RT/board?sprint=active")
    no_sprint_response = client.get("/p/RT/board?sprint=none")

    assert active_response.status_code == 200
    assert ticket["key"] not in active_response.text
    assert ticket["key"] in no_sprint_response.text


def test_board_page_exposes_stable_counts_filter_and_priority_picker(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    sprint = create_sprint(user, "RT", "Sprint 1", starts_on="2026-06-10", ends_on="2026-06-24")
    create_ticket(user, "RT", "High priority", priority="High", sprint_id=sprint["id"], story_points=3)
    session = create_session(int(user["id"]))

    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, session["token"])
    response = client.get("/p/RT/board")

    assert response.status_code == 200
    assert 'class="column-count"' in response.text
    assert "column-points" in response.text
    assert "data-column-points>3</span>" in response.text
    assert 'data-sprint-filter-select' in response.text
    assert 'data-priority-picker' in response.text
    assert 'data-priority-value="High"' in response.text
    assert 'data-edit="story_points"' in response.text
    assert "3 SP" in response.text
    assert 'data-sprint-start="2026-06-10"' in response.text
    assert 'data-sprint-end="2026-06-24"' in response.text
    assert '<select name="priority"' not in response.text


def test_ticket_page_uses_priority_picker_contract(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    ticket = create_ticket(user, "RT", "Urgent work", priority="Urgent")
    session = create_session(int(user["id"]))

    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, session["token"])
    response = client.get(f"/t/{ticket['key']}")

    assert response.status_code == 200
    assert 'name="priority" value="Urgent"' in response.text
    assert 'name="story_points"' in response.text
    assert 'data-priority-picker' in response.text
    assert 'data-selected-priority-icon' in response.text
    assert 'data-priority-value="Urgent"' in response.text
    assert '<select name="priority"' not in response.text


def test_sprint_page_is_project_admin_only_and_actions_return_there(temp_db):
    admin = upsert_user("alice", email="alice@example.com")
    member = upsert_user("bob", email="bob@example.com")
    project = create_project(admin, "SPR", "Sprint Project")
    add_project_member(int(project["id"]), "bob", "member")
    with get_conn() as conn:
        conn.execute("UPDATE users SET role = 'member' WHERE id = ?", (member["id"],))
    member = {**member, "role": "member"}
    sprint = create_sprint(admin, "SPR", "Sprint 1", status_value="closed")
    admin_session = create_session(int(admin["id"]))
    member_session = create_session(int(member["id"]))
    client = TestClient(app)

    client.cookies.set(SESSION_COOKIE, admin_session["token"])
    page = client.get("/p/SPR/sprints")
    reopen = client.post(
        f"/api/projects/SPR/sprints/{sprint['id']}/status",
        data={"csrf_token": admin_session["csrf"], "status": "planned"},
        follow_redirects=False,
    )
    assert page.status_code == 200
    assert "Sprint 1" in page.text
    assert reopen.status_code == 303
    assert reopen.headers["location"] == "/p/SPR/sprints"

    client.cookies.set(SESSION_COOKIE, member_session["token"])
    forbidden = client.get("/p/SPR/sprints")
    assert forbidden.status_code == 403


def test_only_one_sprint_can_be_active_per_project(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    first = create_sprint(user, "RT", "Sprint 1", status_value="active")
    second = create_sprint(user, "RT", "Sprint 2")

    update_sprint_status(user, "RT", int(second["id"]), "active")
    sprints = {sprint["name"]: sprint["status"] for sprint in list_project_sprints(int(first["project_id"]))}

    assert sprints["Sprint 1"] == "planned"
    assert sprints["Sprint 2"] == "active"


def test_project_admin_can_reopen_closed_sprint(temp_db):
    admin = upsert_user("alice")
    member = upsert_user("bob")
    project = create_project(admin, "SPR", "Sprints")
    add_project_member(int(project["id"]), "bob", "member")
    with get_conn() as conn:
        conn.execute("UPDATE users SET role = 'member' WHERE id = ?", (member["id"],))
    member = {**member, "role": "member"}
    sprint = create_sprint(admin, "SPR", "Sprint 1", status_value="active")

    closed = update_sprint_status(admin, "SPR", int(sprint["id"]), "closed")
    reopened = update_sprint_status(admin, "SPR", int(sprint["id"]), "planned")
    active = update_sprint_status(admin, "SPR", int(sprint["id"]), "active")

    assert closed["status"] == "closed"
    assert closed["closed_at"] is not None
    assert reopened["status"] == "planned"
    assert reopened["closed_at"] is None
    assert active["status"] == "active"

    with pytest.raises(HTTPException) as exc:
        update_sprint_status(member, "SPR", int(sprint["id"]), "closed")
    assert exc.value.status_code == 403


def test_project_admin_can_edit_sprint_details(temp_db):
    admin = upsert_user("alice")
    member = upsert_user("bob")
    project = create_project(admin, "SPR", "Sprints")
    add_project_member(int(project["id"]), "bob", "member")
    with get_conn() as conn:
        conn.execute("UPDATE users SET role = 'member' WHERE id = ?", (member["id"],))
    member = {**member, "role": "member"}
    sprint = create_sprint(admin, "SPR", "Sprint 1", goal="Old", starts_on="2026-06-10", ends_on="2026-06-17")

    updated = update_sprint(
        admin,
        "SPR",
        int(sprint["id"]),
        "Sprint 2",
        "New goal",
        "2026-06-11",
        "2026-06-18",
    )

    assert updated["name"] == "Sprint 2"
    assert updated["goal"] == "New goal"
    assert updated["starts_on"] == "2026-06-11"
    assert updated["ends_on"] == "2026-06-18"

    with pytest.raises(HTTPException) as bad_order:
        update_sprint(admin, "SPR", int(sprint["id"]), "Sprint 2", starts_on="2026-06-20", ends_on="2026-06-10")
    assert bad_order.value.status_code == 400

    with pytest.raises(HTTPException) as forbidden:
        update_sprint(member, "SPR", int(sprint["id"]), "Nope")
    assert forbidden.value.status_code == 403


def test_sprint_details_can_be_edited_via_page(temp_db):
    admin = upsert_user("alice", email="alice@example.com")
    create_project(admin, "SPR", "Sprints")
    sprint = create_sprint(admin, "SPR", "Sprint 1", goal="Old", starts_on="2026-06-10", ends_on="2026-06-17")
    session = create_session(int(admin["id"]))
    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, session["token"])

    page = client.get("/p/SPR/sprints")
    response = client.post(
        f"/api/projects/SPR/sprints/{sprint['id']}",
        data={
            "csrf_token": session["csrf"],
            "name": "Renamed sprint",
            "goal": "Updated",
            "starts_on": "2026-06-11",
            "ends_on": "2026-06-18",
        },
        follow_redirects=False,
    )

    assert page.status_code == 200
    assert 'action="/api/projects/SPR/sprints/' in page.text
    assert 'data-local-date="2026-06-10"' in page.text
    assert 'data-local-date="2026-06-17"' in page.text
    assert response.status_code == 303
    assert response.headers["location"] == "/p/SPR/sprints"
    edited = list_project_sprints(int(get_project_by_key("SPR")["id"]))[0]
    assert edited["name"] == "Renamed sprint"
    assert edited["goal"] == "Updated"


def test_sprint_dates_are_validated(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")

    with pytest.raises(HTTPException) as bad_format:
        create_sprint(user, "RT", "Sprint 1", starts_on="tomorrow")
    assert bad_format.value.status_code == 400

    with pytest.raises(HTTPException) as bad_order:
        create_sprint(user, "RT", "Sprint 2", starts_on="2026-06-20", ends_on="2026-06-10")
    assert bad_order.value.status_code == 400


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


def test_ticket_links_can_be_edited_without_duplicates(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "RT", "RoundTable")
    first = create_ticket(user, "RT", "Epic", ticket_type="Epic")
    second = create_ticket(user, "RT", "Task")
    third = create_ticket(user, "RT", "Bug", ticket_type="Bug")

    link_ticket(user, first["key"], second["key"], "relates")
    link = get_ticket_bundle(first["key"])["ticket_links"][0]
    update_ticket_link(user, first["key"], int(link["id"]), third["key"], "blocks")
    edited = get_ticket_bundle(first["key"])["ticket_links"][0]

    assert edited["other_key"] == third["key"]
    assert edited["link_type"] == "blocks"
    assert len(get_ticket_bundle(first["key"])["ticket_links"]) == 1

    link_ticket(user, first["key"], second["key"], "parent")
    with pytest.raises(HTTPException) as exc:
        update_ticket_link(user, first["key"], int(edited["id"]), second["key"], "relates")
    assert exc.value.status_code == 400


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


def test_comment_mentions_project_member_by_login_or_name(temp_db):
    reporter = upsert_user("alice", email="alice@example.com")
    mentioned = upsert_user("bob", name="Robert Builder", email="bob@example.com")
    project = create_project(reporter, "MEN", "Mentions")
    add_project_member(int(project["id"]), "bob", "member")
    ticket = create_ticket(reporter, "MEN", "Wire mentions")

    add_comment(reporter, ticket["key"], "Can you check this, @bob?")

    with get_conn() as conn:
        mention = row_to_dict(conn.execute("SELECT * FROM ticket_mentions").fetchone())
        watcher = row_to_dict(
            conn.execute(
                "SELECT * FROM watchers WHERE ticket_id = ? AND user_id = ?",
                (ticket["id"], mentioned["id"]),
            ).fetchone()
        )
        notification = row_to_dict(
            conn.execute("SELECT * FROM notification_outbox WHERE user_id = ?", (mentioned["id"],)).fetchone()
        )
    assert mention is not None
    assert mention["mentioned_user_id"] == mentioned["id"]
    assert mention["source_type"] == "comment"
    assert watcher is not None
    assert notification is not None

    by_name = search_project_users(int(project["id"]), "Builder")
    assert by_name[0]["login"] == "bob"


def test_empty_mention_search_lists_small_project_members_only(temp_db):
    owner = upsert_user("alice", name="Alice")
    project = create_project(owner, "AT", "At Mentions")
    upsert_user("bob", name="Bob")
    add_project_member(int(project["id"]), "bob", "member")

    small = search_project_users(int(project["id"]), "")
    assert [user["login"] for user in small] == ["alice", "bob"]

    for index in range(13):
        login = f"user{index}"
        upsert_user(login)
        add_project_member(int(project["id"]), login, "member")

    assert search_project_users(int(project["id"]), "") == []
    assert search_project_users(int(project["id"]), "user1")


def test_description_mentions_are_refreshed_on_update(temp_db):
    reporter = upsert_user("alice", email="alice@example.com")
    upsert_user("bob", name="Bob Stone")
    upsert_user("carol", name="Carol Stone")
    project = create_project(reporter, "TXT", "Text")
    add_project_member(int(project["id"]), "bob", "member")
    add_project_member(int(project["id"]), "carol", "member")
    ticket = create_ticket(reporter, "TXT", "Describe", description="@bob please")

    update_ticket(reporter, ticket["key"], description="@carol now")

    with get_conn() as conn:
        rows = [
            row["login"]
            for row in conn.execute(
                """
                SELECT users.login
                FROM ticket_mentions
                JOIN users ON users.id = ticket_mentions.mentioned_user_id
                WHERE ticket_mentions.ticket_id = ? AND ticket_mentions.source_type = 'description'
                ORDER BY users.login
                """,
                (ticket["id"],),
            ).fetchall()
        ]
    assert rows == ["carol"]


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


def test_board_hides_project_admin_actions_for_members(temp_db):
    from app.config import settings

    object.__setattr__(settings, "allow_dev_login", False)
    object.__setattr__(settings, "admin_github_logins", ["alice"])

    owner = upsert_user("alice", email="alice@example.com")
    project = create_project(owner, "WEB", "Website")
    member = upsert_user("bob", email="bob@example.com")
    add_project_member(int(project["id"]), "bob", "member")

    client = TestClient(app)
    member_session = create_session(int(member["id"]))
    client.cookies.set(SESSION_COOKIE, member_session["token"])
    member_page = client.get("/p/WEB/board")

    assert member_page.status_code == 200
    assert "/p/WEB/settings" not in member_page.text
    assert "/p/WEB/sprints" not in member_page.text
    assert client.get("/p/WEB/settings").status_code == 403
    assert client.get("/p/WEB/sprints").status_code == 403

    admin_session = create_session(int(owner["id"]))
    client.cookies.set(SESSION_COOKIE, admin_session["token"])
    admin_page = client.get("/p/WEB/board")

    assert admin_page.status_code == 200
    assert "/p/WEB/settings" in admin_page.text
    assert "/p/WEB/sprints" in admin_page.text


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
