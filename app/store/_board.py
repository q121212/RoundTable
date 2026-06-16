"""Board view assembly: tickets grouped into status columns with sprint filtering."""

from typing import Any, Dict, List

from ..db import get_conn, row_to_dict, rows_to_dicts
from ._policies import project_role_for_user, require_project_access
from ._projects import get_project_by_key
from ._read_models import attach_ticket_link_summaries_conn
from ._sprints import list_project_sprints
from ._validation import project_statuses


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
