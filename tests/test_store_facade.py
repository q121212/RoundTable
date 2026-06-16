"""Locks that guard the store package split (R12).

These pin the two things most at risk when functions move between submodules:
the public app.store API surface, and the mutation -> action_log -> outbox chain
around the import cycle being broken.
"""

from app import store
from app.db import get_conn, row_to_dict
from app.store import add_comment, create_project, create_ticket, get_ticket_bundle, update_ticket, upsert_user


# Every name the rest of the app (main/mcp_server/notifications) and the tests
# import from app.store. The facade must keep re-exporting all of them.
PUBLIC_API = [
    "add_comment", "add_project_member", "board_for_project", "can_delete_ticket",
    "can_view_project_stats", "close_ticket", "consume_telegram_link_token", "create_mcp_token",
    "create_project", "create_sprint", "create_telegram_link_token", "create_test_notification",
    "create_ticket", "delete_project", "delete_ticket", "get_project_by_key", "get_telegram_link",
    "get_ticket_bundle", "link_github_ref", "link_ticket", "list_mcp_tokens", "list_project_sprints",
    "list_projects", "normalize_github_installation_id", "normalize_github_repo",
    "notification_preferences", "project_members", "project_statistics", "project_statuses",
    "project_ticket_types", "purge_expired_records", "record_api_audit", "remove_project_member",
    "reopen_ticket", "require_project_access", "require_project_admin", "revoke_mcp_token",
    "search_linkable_tickets", "search_project_users", "search_tickets", "set_watch",
    "sync_configured_admin_roles", "unlink_telegram", "unlink_ticket",
    "update_notification_preferences", "update_project_member", "update_project_settings",
    "update_sprint", "update_sprint_status", "update_ticket", "update_ticket_link", "upsert_user",
]


def test_store_facade_exposes_public_api():
    missing = [name for name in PUBLIC_API if not hasattr(store, name)]
    assert missing == [], "app.store stopped re-exporting: %s" % missing


def test_ticket_lifecycle_logs_actions_and_enqueues(temp_db):
    reporter = upsert_user("alice", email="alice@example.com")
    assignee = upsert_user("bob", email="bob@example.com")
    project = create_project(reporter, "LK", "Lock")
    from app.store import add_project_member

    add_project_member(int(project["id"]), "bob", "member")

    ticket = create_ticket(reporter, "LK", "Wire telemetry")
    update_ticket(reporter, ticket["key"], assignee_id=int(assignee["id"]), assignee_touched=True)

    with get_conn() as conn:
        actions = [
            r["action"]
            for r in conn.execute(
                "SELECT action FROM action_log WHERE ticket_id = ? ORDER BY id", (ticket["id"],)
            ).fetchall()
        ]
        outbox = row_to_dict(
            conn.execute("SELECT * FROM notification_outbox WHERE user_id = ?", (int(assignee["id"]),)).fetchone()
        )
    assert "ticket_created" in actions      # create path logs
    assert "assigned" in actions            # update path logs
    assert outbox is not None               # action_log -> enqueue -> outbox
    assert outbox["user_id"] == int(assignee["id"])  # recipient unchanged


def test_get_ticket_bundle_output_shape_is_stable(temp_db):
    reporter = upsert_user("alice", email="alice@example.com")
    create_project(reporter, "BN", "Bundle")
    ticket = create_ticket(reporter, "BN", "Read me")

    bundle = get_ticket_bundle(ticket["key"])

    assert set(bundle.keys()) == {
        "ticket", "comments", "actions", "links", "ticket_links",
        "linkable_tickets", "watchers", "watcher_ids",
    }
    assert bundle["ticket"]["key"] == ticket["key"]
    assert bundle["ticket"]["project_key"] == "BN"

    add_comment(reporter, ticket["key"], "first")
    assert get_ticket_bundle(ticket["key"])["comments"][0]["body"] == "first"
