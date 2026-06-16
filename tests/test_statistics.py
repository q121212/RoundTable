"""Golden tests for project_statistics.

These assert hand-computed expected values for a fixed fixture so they pin the
exact output contract. They are written against the original multi-query SQL
implementation and must keep passing after the single-scan refactor (C2),
proving the optimization does not change any returned value.
"""

from app.store import (
    add_project_member,
    create_project,
    create_sprint,
    create_ticket,
    project_statistics,
    update_ticket,
    upsert_user,
)


def _by_value(groups):
    return {g["value"]: g for g in groups}


def test_project_statistics_golden_values(temp_db):
    alice = upsert_user("alice", email="alice@example.com")
    bob = upsert_user("bob")
    upsert_user("carol")
    create_project(alice, "ST", "Stats")
    add_project_member(get_pid("ST"), "bob", "member")
    add_project_member(get_pid("ST"), "carol", "member")  # member with no tickets
    sprint = create_sprint(alice, "ST", "S1", status_value="active")
    a, b = int(alice["id"]), int(bob["id"])
    s1 = int(sprint["id"])

    # title, priority, type, assignee, sprint, story_points, final_status
    plan = [
        ("T1", "High", "Bug", a, s1, 3, "Backlog"),
        ("T2", "High", "Task", a, None, 2, "Backlog"),
        ("T3", "Low", "Task", b, s1, 5, "Todo"),
        ("T4", "Medium", "Story", b, None, 8, "Done"),
        ("T5", "Urgent", "Bug", None, s1, 1, "Closed"),
        ("T6", "Medium", "Task", None, None, 0, "Backlog"),
    ]
    keys = {}
    for title, prio, ttype, assignee, sprint_id, sp, status in plan:
        ticket = create_ticket(alice, "ST", title, priority=prio, ticket_type=ttype,
                               assignee_id=assignee, sprint_id=sprint_id, story_points=sp)
        keys[title] = ticket["key"]
        if status != "Backlog":
            update_ticket(alice, ticket["key"], status_value=status)

    stats = project_statistics("ST", alice)

    # --- summary ---
    assert stats["summary"] == {
        "total_tickets": 6,
        "open_tickets": 4,      # Backlog x3 + Todo x1
        "done_tickets": 1,
        "closed_tickets": 1,
        "story_points": 19,
        "open_story_points": 10,  # 3 + 2 + 5 + 0
    }

    # --- status (count, story_points) ---
    status = _by_value(stats["status_groups"])
    assert (status["Backlog"]["count"], status["Backlog"]["story_points"]) == (3, 5)
    assert (status["Todo"]["count"], status["Todo"]["story_points"]) == (1, 5)
    assert (status["In Progress"]["count"], status["In Progress"]["story_points"]) == (0, 0)
    assert (status["Done"]["count"], status["Done"]["story_points"]) == (1, 8)
    assert (status["Closed"]["count"], status["Closed"]["story_points"]) == (1, 1)

    # --- priority ---
    prio = _by_value(stats["priority_groups"])
    assert (prio["Low"]["count"], prio["Low"]["story_points"]) == (1, 5)
    assert (prio["Medium"]["count"], prio["Medium"]["story_points"]) == (2, 8)
    assert (prio["High"]["count"], prio["High"]["story_points"]) == (2, 5)
    assert (prio["Urgent"]["count"], prio["Urgent"]["story_points"]) == (1, 1)

    # --- type ---
    types = _by_value(stats["type_groups"])
    assert (types["Task"]["count"], types["Task"]["story_points"]) == (3, 7)
    assert (types["Bug"]["count"], types["Bug"]["story_points"]) == (2, 4)
    assert (types["Story"]["count"], types["Story"]["story_points"]) == (1, 8)
    assert (types["Epic"]["count"], types["Epic"]["story_points"]) == (0, 0)

    # --- assignee (sorted by -story_points, -count, label) ---
    assignees = stats["assignee_groups"]
    assert [(g["value"], g["count"], g["story_points"]) for g in assignees] == [
        (str(b), 2, 13),          # bob: T3 + T4
        (str(a), 2, 5),           # alice: T1 + T2
        ("unassigned", 2, 1),     # T5 + T6
    ]
    assert _by_value(assignees)[str(b)]["login"] == "bob"
    assert _by_value(assignees)["unassigned"]["label"] == "Unassigned"

    # --- sprint (none first, then S1) ---
    sprints = stats["sprint_groups"]
    sprint_map = _by_value(sprints)
    assert (sprint_map["none"]["count"], sprint_map["none"]["story_points"]) == (3, 10)
    assert (sprint_map[str(s1)]["count"], sprint_map[str(s1)]["story_points"]) == (3, 9)
    assert sprints[0]["value"] == "none"  # "No sprint" group is first

    # --- previews: all groups <= 8, so full membership and ticket_more == 0 ---
    assert {t["key"] for t in status["Backlog"]["tickets"]} == {keys["T1"], keys["T2"], keys["T6"]}
    assert status["Backlog"]["ticket_more"] == 0
    assert {t["key"] for t in sprint_map[str(s1)]["tickets"]} == {keys["T1"], keys["T3"], keys["T5"]}


def test_project_statistics_preview_caps_at_eight(temp_db):
    alice = upsert_user("alice", email="alice@example.com")
    create_project(alice, "CAP", "Cap")
    created = [create_ticket(alice, "CAP", "T%d" % i, story_points=1) for i in range(1, 11)]  # 10 Backlog

    stats = project_statistics("CAP", alice)
    backlog = _by_value(stats["status_groups"])["Backlog"]

    assert backlog["count"] == 10
    assert backlog["story_points"] == 10
    assert len(backlog["tickets"]) == 8          # capped
    assert backlog["ticket_more"] == 2
    # Order is updated_at DESC, number DESC; tickets created in order => number DESC.
    expected_top8 = [t["key"] for t in reversed(created)][:8]
    assert [t["key"] for t in backlog["tickets"]] == expected_top8


def get_pid(project_key):
    from app.store import get_project_by_key

    return int(get_project_by_key(project_key)["id"])
