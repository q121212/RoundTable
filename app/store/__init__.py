from typing import Any, Dict, List

from ..db import (
    PRIORITIES,
    get_conn,
    row_to_dict,
    rows_to_dicts,
)

# log_action (action_log writes + notify fan-out) lives in _action_log.py.
from ._action_log import log_action as log_action  # noqa: E402

# Validators, normalizers, and per-project config helpers now live in
# _validation.py. Re-exported here so app.store stays the single public facade
# (the `as` aliases mark them as intentional re-exports for linters).
from ._validation import (  # noqa: E402
    STATS_VISIBILITIES as STATS_VISIBILITIES,
    TICKET_DELETE_POLICIES as TICKET_DELETE_POLICIES,
    normalize_github_installation_id as normalize_github_installation_id,
    normalize_github_link_url as normalize_github_link_url,
    normalize_github_repo as normalize_github_repo,
    normalize_project_statuses as normalize_project_statuses,
    normalize_project_ticket_types as normalize_project_ticket_types,
    normalize_stats_visibility as normalize_stats_visibility,
    normalize_ticket_delete_policy as normalize_ticket_delete_policy,
    project_stats_visibility as project_stats_visibility,
    project_statuses as project_statuses,
    project_ticket_delete_own_only as project_ticket_delete_own_only,
    project_ticket_delete_policy as project_ticket_delete_policy,
    project_ticket_types as project_ticket_types,
    validate_date_string as validate_date_string,
    validate_priority as validate_priority,
    validate_project_key as validate_project_key,
    validate_project_ticket_status as validate_project_ticket_status,
    validate_project_ticket_type as validate_project_ticket_type,
    validate_status as validate_status,
    validate_story_points as validate_story_points,
    validate_ticket_link_type as validate_ticket_link_type,
    validate_ticket_type as validate_ticket_type,
)


# User records and global-admin role syncing live in _users.py.
from ._users import (  # noqa: E402
    list_users as list_users,
    sync_configured_admin_roles as sync_configured_admin_roles,
    upsert_user as upsert_user,
)


# Notification fan-out and preference storage live in _notification_outbox.py
# (imports _read_models, never _tickets/_action_log). Re-exported from facade.
from ._notification_outbox import (  # noqa: E402
    describe_action as describe_action,
    enqueue_notifications as enqueue_notifications,
    ensure_notification_preferences as ensure_notification_preferences,
    notification_preferences as notification_preferences,
    notification_preferences_conn as notification_preferences_conn,
    notification_recipients as notification_recipients,
    update_notification_preferences as update_notification_preferences,
)


# Project records, membership, and settings live in _projects.py.
from ._projects import (  # noqa: E402
    add_project_member as add_project_member,
    create_project as create_project,
    delete_project as delete_project,
    get_project_by_key as get_project_by_key,
    get_project_for_ticket_key as get_project_for_ticket_key,
    list_projects as list_projects,
    project_members as project_members,
    remove_project_member as remove_project_member,
    require_project_member_conn as require_project_member_conn,
    search_project_users as search_project_users,
    update_project_member as update_project_member,
    update_project_settings as update_project_settings,
)


# Project authorization policies live in _policies.py (cycle-free: db + the
# validation helpers only). Re-exported so app.store stays the public facade.
from ._policies import (  # noqa: E402
    can_delete_ticket as can_delete_ticket,
    can_view_project_stats as can_view_project_stats,
    project_role_for_user as project_role_for_user,
    require_project_access as require_project_access,
    require_project_admin as require_project_admin,
    require_project_stats_access as require_project_stats_access,
    require_ticket_delete_access as require_ticket_delete_access,
)


# Sprint records and lifecycle live in _sprints.py.
from ._sprints import (  # noqa: E402
    create_sprint as create_sprint,
    list_project_sprints as list_project_sprints,
    update_sprint as update_sprint,
    update_sprint_status as update_sprint_status,
    validate_project_sprint_conn as validate_project_sprint_conn,
)


# Ticket records, updates, comments, links, and search live in _tickets.py.
from ._tickets import (  # noqa: E402
    add_comment as add_comment,
    close_ticket as close_ticket,
    create_ticket as create_ticket,
    delete_ticket as delete_ticket,
    link_ticket as link_ticket,
    reopen_ticket as reopen_ticket,
    search_linkable_tickets as search_linkable_tickets,
    search_tickets as search_tickets,
    set_watch as set_watch,
    unlink_ticket as unlink_ticket,
    update_ticket as update_ticket,
    update_ticket_link as update_ticket_link,
)


# Read-only ticket helpers and row mappers live in _read_models.py — the seam
# that breaks the notifications<->tickets cycle (reads import nothing from
# tickets/action_log/notifications). Re-exported from the facade.
from ._read_models import (  # noqa: E402
    attach_ticket_link_summaries_conn as attach_ticket_link_summaries_conn,
    get_ticket as get_ticket,
    get_ticket_by_id_conn as get_ticket_by_id_conn,
    get_ticket_by_key_conn as get_ticket_by_key_conn,
    get_ticket_bundle as get_ticket_bundle,
    list_linkable_tickets_conn as list_linkable_tickets_conn,
    list_ticket_links_conn as list_ticket_links_conn,
)


def board_for_project(project_key: str, user: Dict[str, Any], sprint_filter: str = "") -> Dict[str, Any]:
    project = get_project_by_key(project_key)
    require_project_access(user, int(project["id"]))
    statuses = project_statuses(project)
    with get_conn() as conn:
        where = ["tickets.project_id = ?"]
        params: List[Any] = [project["id"]]
        current_sprint = None
        if sprint_filter == "none":
            where.append("tickets.sprint_id IS NULL")
        elif sprint_filter == "active":
            active_sprints = rows_to_dicts(
                conn.execute(
                    "SELECT * FROM sprints WHERE project_id = ? AND status = 'active' ORDER BY starts_on DESC, created_at DESC",
                    (project["id"],),
                ).fetchall()
            )
            if active_sprints:
                placeholders = ",".join("?" for _ in active_sprints)
                where.append("tickets.sprint_id IN (%s)" % placeholders)
                params.extend([sprint["id"] for sprint in active_sprints])
            else:
                where.append("1 = 0")
        elif sprint_filter:
            current_sprint = row_to_dict(
                conn.execute(
                    "SELECT * FROM sprints WHERE project_id = ? AND id = ?",
                    (project["id"], sprint_filter),
                ).fetchone()
            )
            if current_sprint:
                where.append("tickets.sprint_id = ?")
                params.append(current_sprint["id"])
        rows = rows_to_dicts(
            conn.execute(
                """
                SELECT tickets.*,
                       sprints.name AS sprint_name,
                       sprints.status AS sprint_status,
                       sprints.starts_on AS sprint_starts_on,
                       sprints.ends_on AS sprint_ends_on,
                       assignee.login AS assignee_login,
                       assignee.name AS assignee_name,
                       assignee.avatar_url AS assignee_avatar_url,
                       reporter.login AS reporter_login,
                       reporter.name AS reporter_name,
                       reporter.avatar_url AS reporter_avatar_url
                FROM tickets
                LEFT JOIN sprints ON sprints.id = tickets.sprint_id
                LEFT JOIN users assignee ON assignee.id = tickets.assignee_id
                LEFT JOIN users reporter ON reporter.id = tickets.reporter_id
                WHERE %s
                ORDER BY
                    CASE tickets.status
                        WHEN 'Backlog' THEN 1
                        WHEN 'Todo' THEN 2
                        WHEN 'In Progress' THEN 3
                        WHEN 'Review' THEN 4
                        WHEN 'Done' THEN 5
                        ELSE 6
                    END,
                    tickets.sort_order ASC,
                    tickets.updated_at DESC,
                    tickets.number DESC
                """
                % " AND ".join(where),
                tuple(params),
            ).fetchall()
        )
        attach_ticket_link_summaries_conn(conn, rows)
    columns = {status_name: [] for status_name in statuses}
    for ticket in rows:
        columns.setdefault(ticket["status"], []).append(ticket)
    return {
        "project": project,
        "project_role": project_role_for_user(user, int(project["id"])),
        "statuses": statuses,
        "columns": columns,
        "sprints": list_project_sprints(int(project["id"])),
        "sprint_filter": sprint_filter,
        "current_sprint": current_sprint,
    }


def _stats_assignee_key(row: Dict[str, Any]) -> str:
    return str(row["assignee_id"]) if row["assignee_id"] is not None else "unassigned"


def _stats_sprint_key(row: Dict[str, Any]) -> str:
    return str(row["sprint_id"]) if row["sprint_id"] is not None else "none"


def _stats_aggregate(rows: List[Dict[str, Any]], key_fn) -> Dict[str, Dict[str, Any]]:
    """Count and sum story points per group value, in one pass over rows.
    Replaces a per-dimension SQL GROUP BY scan."""
    aggregates: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        value = key_fn(row)
        slot = aggregates.setdefault(value, {"group_value": value, "count": 0, "story_points": 0})
        slot["count"] += 1
        slot["story_points"] += int(row["story_points"] or 0)
    return aggregates


def _stats_previews(sorted_rows: List[Dict[str, Any]], key_fn, limit: int = 8) -> Dict[str, List[Dict[str, Any]]]:
    """Top-`limit` preview tickets per group value. `sorted_rows` must already be
    ordered (updated_at DESC, number DESC); taking the first `limit` per group in
    that order reproduces the per-partition ROW_NUMBER window."""
    previews: Dict[str, List[Dict[str, Any]]] = {}
    for row in sorted_rows:
        value = key_fn(row)
        bucket = previews.setdefault(value, [])
        if len(bucket) < limit:
            bucket.append(
                {
                    "group_value": value,
                    "key": row["key"],
                    "title": row["title"],
                    "story_points": row["story_points"],
                }
            )
    return previews


def _stats_group_from_maps(
    value: str,
    label: str,
    aggregates: Dict[str, Dict[str, Any]],
    previews: Dict[str, List[Dict[str, Any]]],
    href: str = "",
) -> Dict[str, Any]:
    aggregate = aggregates.get(value, {})
    count = int(aggregate.get("count") or 0)
    tickets = previews.get(value, [])
    return {
        "value": value,
        "label": label,
        "count": count,
        "story_points": int(aggregate.get("story_points") or 0),
        "tickets": tickets,
        "ticket_more": max(0, count - len(tickets)),
        "href": href,
    }


def project_statistics(project_key: str, user: Dict[str, Any]) -> Dict[str, Any]:
    project = get_project_by_key(project_key)
    require_project_stats_access(user, project)
    statuses = project_statuses(project)
    ticket_types = project_ticket_types(project)
    sprints = list_project_sprints(int(project["id"]))
    # Single scan over the project's tickets; all summaries, per-dimension
    # aggregates, and previews are then computed in Python. This replaces the
    # previous 12 separate SQL scans (1 summary + 5 group-bys + 5 windowed
    # previews + 1 assignee-label query) with one query.
    with get_conn() as conn:
        rows = rows_to_dicts(
            conn.execute(
                """
                SELECT tickets.status,
                       tickets.priority,
                       tickets.ticket_type,
                       tickets.assignee_id,
                       tickets.sprint_id,
                       tickets.story_points,
                       tickets.key,
                       tickets.title,
                       tickets.updated_at,
                       tickets.number,
                       users.name AS assignee_name,
                       users.login AS assignee_login,
                       users.avatar_url AS assignee_avatar_url
                FROM tickets
                LEFT JOIN users ON users.id = tickets.assignee_id
                WHERE tickets.project_id = ?
                """,
                (project["id"],),
            ).fetchall()
        )

    sorted_rows = sorted(rows, key=lambda row: (row["updated_at"], row["number"]), reverse=True)

    status_aggregates = _stats_aggregate(rows, lambda row: row["status"])
    priority_aggregates = _stats_aggregate(rows, lambda row: row["priority"])
    type_aggregates = _stats_aggregate(rows, lambda row: row["ticket_type"])
    assignee_aggregates = _stats_aggregate(rows, _stats_assignee_key)
    sprint_aggregates = _stats_aggregate(rows, _stats_sprint_key)
    status_previews = _stats_previews(sorted_rows, lambda row: row["status"])
    priority_previews = _stats_previews(sorted_rows, lambda row: row["priority"])
    type_previews = _stats_previews(sorted_rows, lambda row: row["ticket_type"])
    assignee_previews = _stats_previews(sorted_rows, _stats_assignee_key)
    sprint_previews = _stats_previews(sorted_rows, _stats_sprint_key)

    # Distinct assignees that have tickets (matches GROUP BY tickets.assignee_id).
    assignee_rows = []
    seen_assignees = set()
    for row in rows:
        value = _stats_assignee_key(row)
        if value in seen_assignees:
            continue
        seen_assignees.add(value)
        assignee_rows.append(
            {
                "value": value,
                "label": row["assignee_name"] or row["assignee_login"] or "Unassigned",
                "login": row["assignee_login"] or "",
                "avatar_url": row["assignee_avatar_url"] or "",
            }
        )

    open_statuses = ("Done", "Closed")
    summary_row = {
        "total_tickets": len(rows),
        "story_points": sum(int(row["story_points"] or 0) for row in rows),
        "open_tickets": sum(1 for row in rows if row["status"] not in open_statuses),
        "open_story_points": sum(
            int(row["story_points"] or 0) for row in rows if row["status"] not in open_statuses
        ),
        "done_tickets": sum(1 for row in rows if row["status"] == "Done"),
        "closed_tickets": sum(1 for row in rows if row["status"] == "Closed"),
    }

    total_points = int(summary_row.get("story_points") or 0)
    status_groups = [
        _stats_group_from_maps(
            status_name,
            status_name,
            status_aggregates,
            status_previews,
            "#status-%s" % status_name.lower().replace(" ", "-"),
        )
        for status_name in statuses
    ]
    max_count = max([1, *[int(group["count"]) for group in status_groups]])
    max_points = max(1, total_points)
    for group in status_groups:
        group["count_percent"] = int(round((group["count"] / max_count) * 100)) if max_count else 0
        group["points_percent"] = int(round((group["story_points"] / max_points) * 100)) if max_points else 0

    priority_groups = [
        _stats_group_from_maps(priority, priority, priority_aggregates, priority_previews)
        for priority in PRIORITIES
    ]
    type_groups = [
        _stats_group_from_maps(ticket_type, ticket_type, type_aggregates, type_previews)
        for ticket_type in ticket_types
    ]

    assignee_groups = sorted(
        [
            {
                **_stats_group_from_maps(str(group["value"]), str(group["label"]), assignee_aggregates, assignee_previews),
                "login": group["login"],
                "avatar_url": group["avatar_url"],
            }
            for group in assignee_rows
        ],
        key=lambda item: (-int(item["story_points"]), -int(item["count"]), item["label"].lower()),
    )

    sprint_groups = [
        {
            **_stats_group_from_maps(
                "none",
                "No sprint",
                sprint_aggregates,
                sprint_previews,
                "/p/%s/board?sprint=none" % project["key"],
            ),
            "status": "",
            "starts_on": "",
            "ends_on": "",
        }
    ]
    for sprint_item in sprints:
        sprint_key = str(sprint_item["id"])
        sprint_groups.append(
            {
                **_stats_group_from_maps(
                    sprint_key,
                    sprint_item["name"],
                    sprint_aggregates,
                    sprint_previews,
                    "/p/%s/board?sprint=%s" % (project["key"], sprint_item["id"]),
                ),
                "status": sprint_item.get("status") or "",
                "starts_on": sprint_item.get("starts_on") or "",
                "ends_on": sprint_item.get("ends_on") or "",
            }
        )

    return {
        "project": project,
        "project_role": project_role_for_user(user, int(project["id"])),
        "statuses": statuses,
        "ticket_types": ticket_types,
        "summary": {
            "total_tickets": int(summary_row.get("total_tickets") or 0),
            "open_tickets": int(summary_row.get("open_tickets") or 0),
            "done_tickets": int(summary_row.get("done_tickets") or 0),
            "closed_tickets": int(summary_row.get("closed_tickets") or 0),
            "story_points": total_points,
            "open_story_points": int(summary_row.get("open_story_points") or 0),
        },
        "status_groups": status_groups,
        "priority_groups": priority_groups,
        "type_groups": type_groups,
        "assignee_groups": assignee_groups,
        "sprint_groups": sprint_groups,
        "active_sprints": [sprint for sprint in sprints if sprint.get("status") == "active"],
    }


# GitHub linking helpers live in _integrations.py (imports _validation,
# _read_models, _action_log). Re-exported from the facade.
from ._integrations import (  # noqa: E402
    GITHUB_REF_TYPES as GITHUB_REF_TYPES,
    TICKET_KEY_RE as TICKET_KEY_RE,
    extract_ticket_keys as extract_ticket_keys,
    link_github_ref as link_github_ref,
    mark_github_delivery as mark_github_delivery,
)

# Per-user account peripherals (MCP tokens, Telegram links/tokens, api_audit,
# retention pruning, test notification) live in _accounts.py.
from ._accounts import (  # noqa: E402
    consume_telegram_link_token as consume_telegram_link_token,
    create_mcp_token as create_mcp_token,
    create_telegram_link_token as create_telegram_link_token,
    create_test_notification as create_test_notification,
    get_telegram_link as get_telegram_link,
    list_mcp_tokens as list_mcp_tokens,
    purge_expired_records as purge_expired_records,
    record_api_audit as record_api_audit,
    revoke_mcp_token as revoke_mcp_token,
    unlink_telegram as unlink_telegram,
)
