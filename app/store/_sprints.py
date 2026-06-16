"""Sprint records and lifecycle.

Imports downward only (_projects, _policies, _action_log, _validation).
"""

import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from ..db import get_conn, row_to_dict, rows_to_dicts, utcnow
from ._action_log import log_action
from ._policies import require_project_admin
from ._projects import get_project_by_key
from ._validation import validate_date_string


SPRINT_STATUSES = {"planned", "active", "closed"}


def list_project_sprints(project_id: int, include_closed: bool = True) -> List[Dict[str, Any]]:
    where = "sprints.project_id = ?"
    params: List[Any] = [project_id]
    if not include_closed:
        where += " AND sprints.status != 'closed'"
    with get_conn() as conn:
        sprints = rows_to_dicts(
            conn.execute(
                """
                SELECT sprints.*,
                       COUNT(tickets.id) AS ticket_count
                FROM sprints
                LEFT JOIN tickets ON tickets.sprint_id = sprints.id
                WHERE %s
                GROUP BY sprints.id
                ORDER BY
                  CASE sprints.status
                    WHEN 'active' THEN 1
                    WHEN 'planned' THEN 2
                    ELSE 3
                  END,
                  sprints.starts_on IS NULL,
                  sprints.starts_on DESC,
                  sprints.created_at DESC
                """
                % where,
                tuple(params),
            ).fetchall()
        )
        if not sprints:
            return sprints
        sprint_ids = [int(sprint["id"]) for sprint in sprints]
        placeholders = ",".join("?" for _ in sprint_ids)
        ticket_rows = rows_to_dicts(
            conn.execute(
                """
                SELECT sprint_id, key, title
                FROM (
                    SELECT sprint_id,
                           key,
                           title,
                           ROW_NUMBER() OVER (
                               PARTITION BY sprint_id
                               ORDER BY sort_order ASC, updated_at DESC, number DESC
                           ) AS row_number
                    FROM tickets
                    WHERE project_id = ?
                      AND sprint_id IN (%s)
                )
                WHERE row_number <= 8
                ORDER BY sprint_id, row_number
                """
                % placeholders,
                (project_id, *sprint_ids),
            ).fetchall()
        )
        tickets_by_sprint: Dict[int, List[Dict[str, Any]]] = {sprint_id: [] for sprint_id in sprint_ids}
        for ticket in ticket_rows:
            tickets_by_sprint.setdefault(int(ticket["sprint_id"]), []).append(ticket)
        for sprint in sprints:
            preview = tickets_by_sprint.get(int(sprint["id"]), [])[:8]
            sprint["ticket_preview"] = preview
            remaining = max(0, int(sprint.get("ticket_count") or 0) - len(preview))
            sprint["ticket_preview_more"] = remaining
        return sprints


def validate_project_sprint_conn(conn: Any, project_id: int, sprint_id: Optional[int]) -> Optional[int]:
    if not sprint_id:
        return None
    sprint = row_to_dict(
        conn.execute("SELECT * FROM sprints WHERE id = ? AND project_id = ?", (sprint_id, project_id)).fetchone()
    )
    if not sprint:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint does not belong to this project")
    return int(sprint_id)


def create_sprint(
    user: Dict[str, Any],
    project_key: str,
    name: str,
    goal: str = "",
    starts_on: str = "",
    ends_on: str = "",
    status_value: str = "planned",
) -> Dict[str, Any]:
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    name = name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint name is required")
    status_value = status_value if status_value in SPRINT_STATUSES else "planned"
    starts_on = validate_date_string(starts_on, "Sprint start date")
    ends_on = validate_date_string(ends_on, "Sprint end date")
    if starts_on and ends_on and ends_on < starts_on:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint end date cannot be before start date")
    now = utcnow()
    with get_conn() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO sprints
                    (project_id, name, goal, status, starts_on, ends_on, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project["id"],
                    name,
                    goal.strip(),
                    status_value,
                    starts_on or None,
                    ends_on or None,
                    user["id"],
                    now,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint name already exists") from exc
        log_action(conn, int(project["id"]), None, user["id"], "sprint_created", metadata={"name": name})
        return row_to_dict(conn.execute("SELECT * FROM sprints WHERE id = ?", (cur.lastrowid,)).fetchone()) or {}


def update_sprint(
    user: Dict[str, Any],
    project_key: str,
    sprint_id: int,
    name: str,
    goal: str = "",
    starts_on: str = "",
    ends_on: str = "",
) -> Dict[str, Any]:
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    name = name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint name is required")
    starts_on = validate_date_string(starts_on, "Sprint start date")
    ends_on = validate_date_string(ends_on, "Sprint end date")
    if starts_on and ends_on and ends_on < starts_on:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint end date cannot be before start date")
    with get_conn() as conn:
        sprint = row_to_dict(
            conn.execute("SELECT * FROM sprints WHERE id = ? AND project_id = ?", (sprint_id, project["id"])).fetchone()
        )
        if not sprint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
        try:
            conn.execute(
                """
                UPDATE sprints
                SET name = ?, goal = ?, starts_on = ?, ends_on = ?
                WHERE id = ?
                """,
                (name, goal.strip(), starts_on or None, ends_on or None, sprint_id),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint name already exists") from exc
        changes = {
            "name": [sprint["name"], name],
            "goal": [sprint["goal"] or "", goal.strip()],
            "starts_on": [sprint["starts_on"] or "", starts_on or ""],
            "ends_on": [sprint["ends_on"] or "", ends_on or ""],
        }
        log_action(
            conn,
            int(project["id"]),
            None,
            user["id"],
            "sprint_updated",
            field="sprint_details",
            old_value=sprint["name"],
            new_value=name,
            metadata={"changes": changes},
        )
        return row_to_dict(conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()) or {}


def update_sprint_status(user: Dict[str, Any], project_key: str, sprint_id: int, status_value: str) -> Dict[str, Any]:
    if status_value not in SPRINT_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sprint status")
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    now = utcnow()
    with get_conn() as conn:
        sprint = row_to_dict(
            conn.execute("SELECT * FROM sprints WHERE id = ? AND project_id = ?", (sprint_id, project["id"])).fetchone()
        )
        if not sprint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
        conn.execute(
            "UPDATE sprints SET status = ?, closed_at = ? WHERE id = ?",
            (status_value, now if status_value == "closed" else None, sprint_id),
        )
        log_action(
            conn,
            int(project["id"]),
            None,
            user["id"],
            "sprint_updated",
            field="sprint_status",
            old_value=sprint["status"],
            new_value=status_value,
        )
        return row_to_dict(conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()) or {}
