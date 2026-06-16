from app.live import project_events
from app.main import publish_ticket_event
from app.store import create_project, create_ticket, update_ticket, upsert_user


async def test_noop_update_is_not_broadcast(temp_db):
    """A no-op edit (story points re-set to the same value) must not publish a
    live event, so connected clients do not play a notification sound for a
    change that did not happen."""
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "NO", "NoOp")
    ticket = create_ticket(user, "NO", "Telemetry", story_points=3)

    queue = await project_events.subscribe("NO")
    try:
        noop = update_ticket(user, ticket["key"], story_points=3, story_points_touched=True)
        assert noop["_changed"] is False
        action = await publish_ticket_event(noop)
        assert action is None
        assert queue.empty()  # nothing broadcast

        changed = update_ticket(user, ticket["key"], story_points=8, story_points_touched=True)
        assert changed["_changed"] is True
        await publish_ticket_event(changed)
        assert not queue.empty()  # real change broadcast
    finally:
        await project_events.unsubscribe("NO", queue)


def test_update_ticket_marks_change_state(temp_db):
    user = upsert_user("alice", email="alice@example.com")
    create_project(user, "CH", "Change")
    ticket = create_ticket(user, "CH", "Item", story_points=1)

    assert update_ticket(user, ticket["key"], story_points=1, story_points_touched=True)["_changed"] is False
    assert update_ticket(user, ticket["key"], priority="High")["_changed"] is True
    # priority already High now -> no-op again
    assert update_ticket(user, ticket["key"], priority="High")["_changed"] is False
