"""Project statistics: single-scan aggregation and previews by status,
priority, type, assignee, and sprint."""

from typing import Any, Dict, List

from ..db import PRIORITIES, get_conn, rows_to_dicts
from ._policies import project_role_for_user, require_project_stats_access
from ._projects import get_project_by_key
from ._sprints import list_project_sprints
from ._validation import project_statuses, project_ticket_types


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
