"""Ticket records: creation, updates, comments, watching, links, search, and
board sort ordering. Top of the store layering — imports projects, sprints,
read models, policies, validation, action_log; nothing imports it.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from ..db import get_conn, row_to_dict, rows_to_dicts, utcnow
from ._action_log import log_action
from ._policies import require_project_access, require_ticket_delete_access
from ._projects import get_project_for_ticket_key, require_project_member_conn
from ._read_models import get_ticket_by_id_conn, get_ticket_by_key_conn
from ._sprints import validate_project_sprint_conn
from ._validation import (
    project_statuses,
    validate_priority,
    validate_project_key,
    validate_project_ticket_status,
    validate_project_ticket_type,
    validate_story_points,
    validate_ticket_link_type,
)


MENTION_RE = re.compile(r"(?<![\w.-])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?)")


def mentioned_user_ids_conn(conn: Any, project_id: int, text: str) -> List[int]:
    logins = {match.group(1).lower() for match in MENTION_RE.finditer(text or "")}
    if not logins:
        return []
    placeholders = ",".join("?" for _ in logins)
    rows = conn.execute(
        f"""
        SELECT users.id
        FROM users
        JOIN project_members ON project_members.user_id = users.id
        WHERE project_members.project_id = ?
          AND lower(users.login) IN ({placeholders})
        """,
        (project_id, *sorted(logins)),
    ).fetchall()
    return [int(row["id"]) for row in rows]


def refresh_ticket_mentions_conn(
    conn: Any,
    ticket_id: int,
    project_id: int,
    text: str,
    source_type: str,
    comment_id: Optional[int] = None,
) -> List[int]:
    if source_type not in {"description", "comment"}:
        raise ValueError("Unsupported mention source type")
    mentioned_ids = mentioned_user_ids_conn(conn, project_id, text)
    now = utcnow()
    if source_type == "description":
        conn.execute(
            "DELETE FROM ticket_mentions WHERE ticket_id = ? AND source_type = 'description'",
            (ticket_id,),
        )
    else:
        conn.execute(
            "DELETE FROM ticket_mentions WHERE ticket_id = ? AND comment_id = ? AND source_type = 'comment'",
            (ticket_id, comment_id),
        )
    for user_id in mentioned_ids:
        conn.execute(
            """
            INSERT OR IGNORE INTO ticket_mentions
                (ticket_id, comment_id, mentioned_user_id, source_type, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticket_id, comment_id, user_id, source_type, now),
        )
        conn.execute(
            "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
            (ticket_id, user_id, now),
        )
    return mentioned_ids


def next_ticket_sort_order_conn(conn: Any, project_id: int, status_value: str) -> float:
    value = conn.execute(
        "SELECT COALESCE(MAX(sort_order), 0) + 1000 FROM tickets WHERE project_id = ? AND status = ?",
        (project_id, status_value),
    ).fetchone()[0]
    return float(value)


def first_ticket_sort_order_conn(conn: Any, project_id: int, status_value: str) -> float:
    value = conn.execute(
        "SELECT COALESCE(MIN(sort_order), 1000) - 1000 FROM tickets WHERE project_id = ? AND status = ?",
        (project_id, status_value),
    ).fetchone()[0]
    return float(value)


def ticket_sort_order_after_conn(
    conn: Any,
    project_id: int,
    status_value: str,
    ticket_id: int,
    after_ticket_key: Optional[str],
) -> float:
    if not after_ticket_key:
        return first_ticket_sort_order_conn(conn, project_id, status_value)
    previous = row_to_dict(
        conn.execute(
            """
            SELECT id, sort_order
            FROM tickets
            WHERE project_id = ? AND status = ? AND key = ? AND id != ?
            """,
            (project_id, status_value, after_ticket_key, ticket_id),
        ).fetchone()
    )
    if not previous:
        return next_ticket_sort_order_conn(conn, project_id, status_value)
    next_row = conn.execute(
        """
        SELECT sort_order
        FROM tickets
        WHERE project_id = ?
          AND status = ?
          AND id != ?
          AND sort_order > ?
        ORDER BY sort_order ASC, updated_at DESC, number DESC
        LIMIT 1
        """,
        (project_id, status_value, ticket_id, previous["sort_order"]),
    ).fetchone()
    previous_order = float(previous["sort_order"] or 0)
    if not next_row:
        return previous_order + 1000
    next_order = float(next_row["sort_order"] or previous_order + 1000)
    if next_order <= previous_order:
        return previous_order + 1000
    return previous_order + ((next_order - previous_order) / 2)


def create_ticket(
    user: Dict[str, Any],
    project_key: str,
    title: str,
    description: str = "",
    priority: str = "Medium",
    ticket_type: str = "Task",
    assignee_id: Optional[int] = None,
    sprint_id: Optional[int] = None,
    story_points: int = 0,
) -> Dict[str, Any]:
    title = title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket title is required")
    priority = validate_priority(priority)
    story_points = validate_story_points(story_points)
    project_key = validate_project_key(project_key)
    now = utcnow()
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        project = row_to_dict(conn.execute("SELECT * FROM projects WHERE key = ?", (project_key,)).fetchone())
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        require_project_access(user, int(project["id"]), write=True)
        if assignee_id:
            require_project_member_conn(conn, int(project["id"]), assignee_id)
        sprint_id = validate_project_sprint_conn(conn, int(project["id"]), sprint_id)
        ticket_type = validate_project_ticket_type(project, ticket_type)
        initial_status = project_statuses(project)[0]
        sort_order = first_ticket_sort_order_conn(conn, int(project["id"]), initial_status)
        number = int(project["next_ticket_number"])
        ticket_key = "%s-%s" % (project["key"], number)
        conn.execute(
            "UPDATE projects SET next_ticket_number = next_ticket_number + 1 WHERE id = ?",
            (project["id"],),
        )
        cur = conn.execute(
            """
            INSERT INTO tickets
                (project_id, number, key, title, description, ticket_type, status, priority,
                 sprint_id, story_points, sort_order, assignee_id, reporter_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project["id"],
                number,
                ticket_key,
                title,
                description.strip(),
                ticket_type,
                initial_status,
                priority,
                sprint_id,
                story_points,
                sort_order,
                assignee_id,
                user["id"],
                now,
                now,
            ),
        )
        ticket_id = int(cur.lastrowid)
        conn.execute(
            "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
            (ticket_id, user["id"], now),
        )
        if assignee_id:
            conn.execute(
                "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
                (ticket_id, assignee_id, now),
            )
        refresh_ticket_mentions_conn(conn, ticket_id, int(project["id"]), description, "description")
        log_action(
            conn,
            project["id"],
            ticket_id,
            user["id"],
            "ticket_created",
            metadata={
                "key": ticket_key,
                "title": title,
                "ticket_type": ticket_type,
                "sprint_id": sprint_id,
                "story_points": story_points,
            },
        )
        if assignee_id:
            log_action(
                conn,
                project["id"],
                ticket_id,
                user["id"],
                "assigned",
                field="assignee",
                old_value="",
                new_value=str(assignee_id),
            )
        return get_ticket_by_id_conn(conn, ticket_id)


def update_ticket(
    user: Dict[str, Any],
    ticket_key: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    ticket_type: Optional[str] = None,
    status_value: Optional[str] = None,
    priority: Optional[str] = None,
    story_points: Optional[int] = None,
    story_points_touched: bool = False,
    assignee_id: Optional[int] = None,
    assignee_touched: bool = False,
    sprint_id: Optional[int] = None,
    sprint_touched: bool = False,
    position_after_key: Optional[str] = None,
    position_touched: bool = False,
) -> Dict[str, Any]:
    now = utcnow()
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        require_project_access(user, int(ticket["project_id"]), write=True)
        changes: List[Tuple[str, Any, Any]] = []
        if title is not None and title.strip() and title.strip() != ticket["title"]:
            changes.append(("title", ticket["title"], title.strip()))
        if description is not None and description.strip() != ticket["description"]:
            changes.append(("description", ticket["description"], description.strip()))
        if ticket_type is not None:
            project = row_to_dict(
                conn.execute("SELECT * FROM projects WHERE id = ?", (ticket["project_id"],)).fetchone()
            ) or {}
            ticket_type = validate_project_ticket_type(project, ticket_type)
            if ticket_type != ticket["ticket_type"]:
                changes.append(("ticket_type", ticket["ticket_type"], ticket_type))
        if status_value is not None:
            project = row_to_dict(
                conn.execute("SELECT * FROM projects WHERE id = ?", (ticket["project_id"],)).fetchone()
            ) or {}
            status_value = validate_project_ticket_status(project, status_value)
            if status_value != ticket["status"]:
                changes.append(("status", ticket["status"], status_value))
        if priority is not None:
            priority = validate_priority(priority)
            if priority != ticket["priority"]:
                changes.append(("priority", ticket["priority"], priority))
        if story_points_touched:
            story_points = validate_story_points(story_points)
            if story_points != int(ticket["story_points"] or 0):
                changes.append(("story_points", ticket["story_points"], story_points))
        if assignee_touched and assignee_id != ticket["assignee_id"]:
            if assignee_id:
                require_project_member_conn(conn, int(ticket["project_id"]), assignee_id)
            changes.append(("assignee_id", ticket["assignee_id"], assignee_id))
        if sprint_touched:
            sprint_id = validate_project_sprint_conn(conn, int(ticket["project_id"]), sprint_id)
            if sprint_id != ticket["sprint_id"]:
                changes.append(("sprint_id", ticket["sprint_id"], sprint_id))

        target_status = status_value if status_value is not None else ticket["status"]
        target_sort_order = ticket["sort_order"]
        if position_touched:
            target_sort_order = ticket_sort_order_after_conn(
                conn,
                int(ticket["project_id"]),
                str(target_status),
                int(ticket["id"]),
                position_after_key,
            )
        elif status_value is not None and status_value != ticket["status"]:
            target_sort_order = next_ticket_sort_order_conn(conn, int(ticket["project_id"]), str(target_status))
        sort_changed = target_sort_order != ticket["sort_order"]

        if not changes and not sort_changed:
            # Nothing actually changed (e.g. story points re-set to the same
            # value). Flag it so callers can skip broadcasting a no-op event.
            unchanged = get_ticket_by_id_conn(conn, ticket["id"])
            unchanged["_changed"] = False
            return unchanged

        values = {
            "title": ticket["title"],
            "description": ticket["description"],
            "ticket_type": ticket["ticket_type"],
            "status": ticket["status"],
            "priority": ticket["priority"],
            "story_points": int(ticket["story_points"] or 0),
            "assignee_id": ticket["assignee_id"],
            "sprint_id": ticket["sprint_id"],
            "closed_at": ticket["closed_at"],
            "sort_order": ticket["sort_order"],
        }
        for field, _old, new in changes:
            if field == "status":
                values["status"] = new
                values["closed_at"] = now if new == "Closed" else None
            elif field == "assignee_id":
                values["assignee_id"] = new
            elif field == "sprint_id":
                values["sprint_id"] = new
            else:
                values[field] = new

        conn.execute(
            """
            UPDATE tickets
            SET title = ?, description = ?, ticket_type = ?, status = ?, priority = ?, story_points = ?,
                sprint_id = ?, sort_order = ?, assignee_id = ?, closed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                values["title"],
                values["description"],
                values["ticket_type"],
                values["status"],
                values["priority"],
                values["story_points"],
                values["sprint_id"],
                target_sort_order,
                values["assignee_id"],
                values["closed_at"],
                now,
                ticket["id"],
            ),
        )
        if values["assignee_id"]:
            conn.execute(
                "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
                (ticket["id"], values["assignee_id"], now),
            )
        if any(field == "description" for field, _old, _new in changes):
            refresh_ticket_mentions_conn(
                conn,
                int(ticket["id"]),
                int(ticket["project_id"]),
                str(values["description"] or ""),
                "description",
            )
        for field, old, new in changes:
            action = "ticket_updated"
            if field == "status":
                action = "closed" if new == "Closed" else "status_changed"
            if field == "ticket_type":
                action = "type_changed"
            if field == "assignee_id":
                action = "assigned"
            if field == "sprint_id":
                action = "sprint_changed"
            log_action(
                conn,
                ticket["project_id"],
                ticket["id"],
                user["id"],
                action,
                field=field,
                old_value="" if old is None else str(old),
                new_value="" if new is None else str(new),
            )
        status_changed = any(field == "status" for field, _old, _new in changes)
        if sort_changed and not status_changed:
            log_action(
                conn,
                ticket["project_id"],
                ticket["id"],
                user["id"],
                "reordered",
                field="sort_order",
                old_value="" if ticket["sort_order"] is None else str(ticket["sort_order"]),
                new_value=str(target_sort_order),
            )
        result = get_ticket_by_id_conn(conn, ticket["id"])
        result["_changed"] = True
        return result


def close_ticket(user: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
    return update_ticket(user, ticket_key, status_value="Closed")


def reopen_ticket(user: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
    project = get_project_for_ticket_key(ticket_key)
    statuses = project_statuses(project)
    target = "Todo" if "Todo" in statuses else statuses[0]
    return update_ticket(user, ticket_key, status_value=target)


def delete_ticket(user: Dict[str, Any], ticket_key: str, confirmation: str = "") -> Dict[str, Any]:
    ticket_key = ticket_key.upper()
    if confirmation.strip().upper() != ticket_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type the ticket key to confirm deletion.")
    project = get_project_for_ticket_key(ticket_key)
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        if int(ticket["project_id"]) != int(project["id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        require_ticket_delete_access(user, project, ticket)
        deleted = dict(ticket)
        deleted["project_key"] = project["key"]
        log_action(
            conn,
            int(project["id"]),
            None,
            user["id"],
            "ticket_deleted",
            metadata={"key": ticket["key"], "title": ticket["title"], "status": ticket["status"]},
        )
        conn.execute("DELETE FROM tickets WHERE id = ?", (ticket["id"],))
        return deleted


def add_comment(user: Dict[str, Any], ticket_key: str, body: str) -> Dict[str, Any]:
    body = body.strip()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment body is required")
    now = utcnow()
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        require_project_access(user, int(ticket["project_id"]), write=True)
        cur = conn.execute(
            "INSERT INTO comments (ticket_id, user_id, body, created_at) VALUES (?, ?, ?, ?)",
            (ticket["id"], user["id"], body, now),
        )
        conn.execute("UPDATE tickets SET updated_at = ? WHERE id = ?", (now, ticket["id"]))
        conn.execute(
            "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
            (ticket["id"], user["id"], now),
        )
        refresh_ticket_mentions_conn(
            conn,
            int(ticket["id"]),
            int(ticket["project_id"]),
            body,
            "comment",
            int(cur.lastrowid),
        )
        log_action(conn, ticket["project_id"], ticket["id"], user["id"], "commented")
        return row_to_dict(conn.execute("SELECT * FROM comments WHERE id = ?", (cur.lastrowid,)).fetchone()) or {}


def set_watch(user: Dict[str, Any], ticket_key: str, watch: bool = True) -> None:
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        require_project_access(user, int(ticket["project_id"]), write=False)
        if watch:
            conn.execute(
                "INSERT OR IGNORE INTO watchers (ticket_id, user_id, created_at) VALUES (?, ?, ?)",
                (ticket["id"], user["id"], utcnow()),
            )
            action = "watching"
        else:
            conn.execute("DELETE FROM watchers WHERE ticket_id = ? AND user_id = ?", (ticket["id"], user["id"]))
            action = "unwatching"
        log_action(conn, ticket["project_id"], ticket["id"], user["id"], action)


def link_ticket(
    user: Dict[str, Any],
    source_key: str,
    target_key: str,
    link_type: str = "relates",
) -> Dict[str, Any]:
    link_type = validate_ticket_link_type(link_type)
    target_key = target_key.strip().upper()
    if not target_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target ticket is required")
    now = utcnow()
    with get_conn() as conn:
        source = get_ticket_by_key_conn(conn, source_key)
        target = get_ticket_by_key_conn(conn, target_key)
        require_project_access(user, int(source["project_id"]), write=True)
        require_project_access(user, int(target["project_id"]), write=False)
        if int(source["id"]) == int(target["id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A ticket cannot link to itself")
        if int(source["project_id"]) != int(target["project_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket links are project-scoped")
        existing = row_to_dict(
            conn.execute(
                """
                SELECT *
                FROM ticket_links
                WHERE
                    (source_ticket_id = ? AND target_ticket_id = ?)
                    OR (source_ticket_id = ? AND target_ticket_id = ?)
                """,
                (source["id"], target["id"], target["id"], source["id"]),
            ).fetchone()
        )
        if existing:
            conn.execute(
                """
                UPDATE ticket_links
                SET source_ticket_id = ?, target_ticket_id = ?, link_type = ?, created_by = ?, created_at = ?
                WHERE id = ?
                """,
                (source["id"], target["id"], link_type, user["id"], now, existing["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO ticket_links
                    (project_id, source_ticket_id, target_ticket_id, link_type, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source["project_id"], source["id"], target["id"], link_type, user["id"], now),
            )
        conn.execute("UPDATE tickets SET updated_at = ? WHERE id IN (?, ?)", (now, source["id"], target["id"]))
        log_action(
            conn,
            source["project_id"],
            source["id"],
            user["id"],
            "linked",
            field="ticket_link",
            old_value="",
            new_value=target["key"],
            metadata={"link_type": link_type, "updated_existing": bool(existing)},
        )
        return {
            "source_key": source["key"],
            "target_key": target["key"],
            "link_type": link_type,
        }


def update_ticket_link(
    user: Dict[str, Any],
    ticket_key: str,
    link_id: int,
    target_key: str,
    link_type: str,
) -> Dict[str, Any]:
    link_type = validate_ticket_link_type(link_type)
    target_key = target_key.strip().upper()
    if not target_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target ticket is required")
    now = utcnow()
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        target = get_ticket_by_key_conn(conn, target_key)
        require_project_access(user, int(ticket["project_id"]), write=True)
        require_project_access(user, int(target["project_id"]), write=False)
        if int(ticket["id"]) == int(target["id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A ticket cannot link to itself")
        if int(ticket["project_id"]) != int(target["project_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket links are project-scoped")
        link = row_to_dict(
            conn.execute(
                """
                SELECT ticket_links.*, target.key AS target_key, source.key AS source_key
                FROM ticket_links
                JOIN tickets target ON target.id = ticket_links.target_ticket_id
                JOIN tickets source ON source.id = ticket_links.source_ticket_id
                WHERE ticket_links.id = ?
                """,
                (link_id,),
            ).fetchone()
        )
        if not link or int(link["project_id"]) != int(ticket["project_id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket link not found")
        if int(ticket["id"]) not in {int(link["source_ticket_id"]), int(link["target_ticket_id"])}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket link not found")
        duplicate = row_to_dict(
            conn.execute(
                """
                SELECT id
                FROM ticket_links
                WHERE id != ?
                  AND (
                    (source_ticket_id = ? AND target_ticket_id = ?)
                    OR (source_ticket_id = ? AND target_ticket_id = ?)
                  )
                """,
                (link_id, ticket["id"], target["id"], target["id"], ticket["id"]),
            ).fetchone()
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="These tickets are already linked")
        old_other_key = link["target_key"] if int(link["source_ticket_id"]) == int(ticket["id"]) else link["source_key"]
        conn.execute(
            """
            UPDATE ticket_links
            SET source_ticket_id = ?, target_ticket_id = ?, link_type = ?, created_by = ?, created_at = ?
            WHERE id = ?
            """,
            (ticket["id"], target["id"], link_type, user["id"], now, link_id),
        )
        conn.execute(
            "UPDATE tickets SET updated_at = ? WHERE id IN (?, ?, ?)",
            (now, ticket["id"], target["id"], link["source_ticket_id"] if int(link["source_ticket_id"]) != int(ticket["id"]) else link["target_ticket_id"]),
        )
        log_action(
            conn,
            ticket["project_id"],
            ticket["id"],
            user["id"],
            "linked",
            field="ticket_link",
            old_value=old_other_key,
            new_value=target["key"],
            metadata={"link_type": link_type, "updated_existing": True, "link_id": link_id},
        )
        return {
            "source_key": ticket["key"],
            "target_key": target["key"],
            "link_type": link_type,
        }


def unlink_ticket(user: Dict[str, Any], ticket_key: str, link_id: int) -> None:
    now = utcnow()
    with get_conn() as conn:
        ticket = get_ticket_by_key_conn(conn, ticket_key)
        require_project_access(user, int(ticket["project_id"]), write=True)
        link = row_to_dict(
            conn.execute(
                """
                SELECT ticket_links.*, target.key AS target_key, source.key AS source_key
                FROM ticket_links
                JOIN tickets target ON target.id = ticket_links.target_ticket_id
                JOIN tickets source ON source.id = ticket_links.source_ticket_id
                WHERE ticket_links.id = ?
                """,
                (link_id,),
            ).fetchone()
        )
        if not link or int(link["project_id"]) != int(ticket["project_id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket link not found")
        if int(ticket["id"]) not in {int(link["source_ticket_id"]), int(link["target_ticket_id"])}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket link not found")
        other_key = link["target_key"] if int(link["source_ticket_id"]) == int(ticket["id"]) else link["source_key"]
        conn.execute("DELETE FROM ticket_links WHERE id = ?", (link_id,))
        conn.execute("UPDATE tickets SET updated_at = ? WHERE id IN (?, ?)", (now, link["source_ticket_id"], link["target_ticket_id"]))
        log_action(
            conn,
            ticket["project_id"],
            ticket["id"],
            user["id"],
            "unlinked",
            field="ticket_link",
            old_value=other_key,
            new_value="",
            metadata={"link_type": link["link_type"]},
        )


def search_linkable_tickets(project_id: int, current_ticket_key: str, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    normalized_query = query.strip()
    if not normalized_query:
        return []
    like_query = normalized_query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    with get_conn() as conn:
        current = get_ticket_by_key_conn(conn, current_ticket_key)
        if int(current["project_id"]) != int(project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        return rows_to_dicts(
            conn.execute(
                """
                SELECT id, key, title, ticket_type, status
                FROM tickets
                WHERE project_id = ?
                  AND id != ?
                  AND (
                    key LIKE ? ESCAPE '\\'
                    OR title LIKE ? ESCAPE '\\'
                  )
                ORDER BY
                  CASE
                    WHEN key = ? THEN 0
                    WHEN key LIKE ? ESCAPE '\\' THEN 1
                    ELSE 2
                  END,
                  number DESC
                LIMIT ?
                """,
                (
                    project_id,
                    current["id"],
                    f"{like_query}%",
                    f"%{like_query}%",
                    normalized_query.upper(),
                    f"{like_query}%",
                    limit,
                ),
            ).fetchall()
        )


def search_tickets(user: Dict[str, Any], query: str = "", project_key: str = "") -> List[Dict[str, Any]]:
    clean_query = query.strip()
    # Escape LIKE metacharacters so a user typing % or _ matches them literally
    # instead of turning the search into a wildcard over their whole scope.
    escaped = clean_query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    query_like = "%" + escaped + "%"
    params: List[Any] = []
    where = []
    if clean_query:
        where.append(
            "(tickets.key LIKE ? ESCAPE '\\' OR tickets.title LIKE ? ESCAPE '\\' "
            "OR tickets.description LIKE ? ESCAPE '\\')"
        )
        params.extend([query_like, query_like, query_like])
    if project_key.strip():
        where.append("projects.key = ?")
        params.append(project_key.strip().upper())
    if user.get("role") != "admin":
        where.append("project_members.user_id = ?")
        params.append(user["id"])
    sql = """
        SELECT tickets.*,
               projects.key AS project_key,
               projects.name AS project_name,
               assignee.login AS assignee_login,
               assignee.name AS assignee_name,
               assignee.avatar_url AS assignee_avatar_url
        FROM tickets
        JOIN projects ON projects.id = tickets.project_id
        LEFT JOIN users assignee ON assignee.id = tickets.assignee_id
    """
    if user.get("role") != "admin":
        sql += " JOIN project_members ON project_members.project_id = projects.id"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY tickets.updated_at DESC LIMIT 50"
    with get_conn() as conn:
        return rows_to_dicts(conn.execute(sql, tuple(params)).fetchall())
