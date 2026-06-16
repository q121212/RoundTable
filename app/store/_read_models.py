"""Read-only ticket helpers and row mappers shared by mutations and
notifications. This is the seam that breaks the import cycle: it must depend
only on db access and never import _tickets, _action_log, or _notification_outbox.
"""

from typing import Any, Dict, List

from fastapi import HTTPException, status

from ..db import get_conn, row_to_dict, rows_to_dicts


def get_ticket_by_id_conn(conn: Any, ticket_id: int) -> Dict[str, Any]:
    ticket = row_to_dict(
        conn.execute(
            """
            SELECT tickets.*,
                   projects.key AS project_key,
                   projects.name AS project_name,
                   projects.github_repo_full_name AS project_github_repo_full_name,
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
            JOIN projects ON projects.id = tickets.project_id
            LEFT JOIN sprints ON sprints.id = tickets.sprint_id
            LEFT JOIN users assignee ON assignee.id = tickets.assignee_id
            LEFT JOIN users reporter ON reporter.id = tickets.reporter_id
            WHERE tickets.id = ?
            """,
            (ticket_id,),
        ).fetchone()
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    attach_ticket_link_summaries_conn(conn, [ticket])
    return ticket


def get_ticket(ticket_key: str) -> Dict[str, Any]:
    with get_conn() as conn:
        ticket = row_to_dict(
            conn.execute(
                """
                SELECT tickets.*,
                       projects.key AS project_key,
                       projects.name AS project_name,
                       projects.github_repo_full_name AS project_github_repo_full_name,
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
                JOIN projects ON projects.id = tickets.project_id
                LEFT JOIN sprints ON sprints.id = tickets.sprint_id
                LEFT JOIN users assignee ON assignee.id = tickets.assignee_id
                LEFT JOIN users reporter ON reporter.id = tickets.reporter_id
                WHERE tickets.key = ?
                """,
                (ticket_key.upper(),),
            ).fetchone()
        )
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        return ticket


def get_ticket_by_key_conn(conn: Any, ticket_key: str) -> Dict[str, Any]:
    ticket = row_to_dict(conn.execute("SELECT * FROM tickets WHERE key = ?", (ticket_key.upper(),)).fetchone())
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


def list_linkable_tickets_conn(conn: Any, project_id: int, current_ticket_id: int) -> List[Dict[str, Any]]:
    return rows_to_dicts(
        conn.execute(
            """
            SELECT id, key, title, ticket_type, status
            FROM tickets
            WHERE project_id = ? AND id != ?
            ORDER BY number DESC
            LIMIT 200
            """,
            (project_id, current_ticket_id),
        ).fetchall()
    )


def list_ticket_links_conn(conn: Any, ticket_id: int) -> List[Dict[str, Any]]:
    rows = rows_to_dicts(
        conn.execute(
            """
            SELECT ticket_links.*,
                   source.key AS source_key,
                   source.title AS source_title,
                   source.ticket_type AS source_ticket_type,
                   source.status AS source_status,
                   target.key AS target_key,
                   target.title AS target_title,
                   target.ticket_type AS target_ticket_type,
                   target.status AS target_status,
                   users.login AS created_by_login,
                   users.name AS created_by_name,
                   users.avatar_url AS created_by_avatar_url
            FROM ticket_links
            JOIN tickets source ON source.id = ticket_links.source_ticket_id
            JOIN tickets target ON target.id = ticket_links.target_ticket_id
            LEFT JOIN users ON users.id = ticket_links.created_by
            WHERE ticket_links.source_ticket_id = ? OR ticket_links.target_ticket_id = ?
            ORDER BY ticket_links.created_at DESC
            """,
            (ticket_id, ticket_id),
        ).fetchall()
    )
    for row in rows:
        outgoing = int(row["source_ticket_id"]) == ticket_id
        row["direction"] = "out" if outgoing else "in"
        row["other_ticket_id"] = row["target_ticket_id"] if outgoing else row["source_ticket_id"]
        row["other_key"] = row["target_key"] if outgoing else row["source_key"]
        row["other_title"] = row["target_title"] if outgoing else row["source_title"]
        row["other_ticket_type"] = row["target_ticket_type"] if outgoing else row["source_ticket_type"]
        row["other_status"] = row["target_status"] if outgoing else row["source_status"]
    return rows


def attach_ticket_link_summaries_conn(conn: Any, tickets: List[Dict[str, Any]]) -> None:
    ids = [int(ticket["id"]) for ticket in tickets if ticket.get("id")]
    for ticket in tickets:
        ticket["linked_tickets"] = []
        ticket["linked_ticket_count"] = 0
    if not ids:
        return
    placeholders = ",".join("?" for _ in ids)
    rows = rows_to_dicts(
        conn.execute(
            """
            SELECT ticket_links.source_ticket_id AS ticket_id,
                   target.key AS other_key,
                   target.title AS other_title,
                   target.ticket_type AS other_ticket_type,
                   ticket_links.link_type AS link_type
            FROM ticket_links
            JOIN tickets target ON target.id = ticket_links.target_ticket_id
            WHERE ticket_links.source_ticket_id IN (%s)
            UNION ALL
            SELECT ticket_links.target_ticket_id AS ticket_id,
                   source.key AS other_key,
                   source.title AS other_title,
                   source.ticket_type AS other_ticket_type,
                   ticket_links.link_type AS link_type
            FROM ticket_links
            JOIN tickets source ON source.id = ticket_links.source_ticket_id
            WHERE ticket_links.target_ticket_id IN (%s)
            ORDER BY other_key
            """
            % (placeholders, placeholders),
            tuple(ids + ids),
        ).fetchall()
    )
    by_id: Dict[int, List[Dict[str, Any]]] = {ticket_id: [] for ticket_id in ids}
    for row in rows:
        by_id.setdefault(int(row["ticket_id"]), []).append(row)
    for ticket in tickets:
        linked = by_id.get(int(ticket["id"]), [])
        ticket["linked_tickets"] = linked
        ticket["linked_ticket_count"] = len(linked)


def get_ticket_bundle(ticket_key: str) -> Dict[str, Any]:
    with get_conn() as conn:
        ticket_row = conn.execute("SELECT id FROM tickets WHERE key = ?", (ticket_key.upper(),)).fetchone()
        if not ticket_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        ticket = get_ticket_by_id_conn(conn, int(ticket_row["id"]))
        comments = rows_to_dicts(
            conn.execute(
                """
                SELECT comments.*, users.login AS user_login,
                       users.name AS user_name,
                       users.avatar_url AS user_avatar_url
                FROM comments
                LEFT JOIN users ON users.id = comments.user_id
                WHERE comments.ticket_id = ?
                ORDER BY comments.created_at
                """,
                (ticket["id"],),
            ).fetchall()
        )
        actions = rows_to_dicts(
            conn.execute(
                """
                SELECT action_log.*,
                       users.login AS actor_login,
                       users.name AS actor_name,
                       users.avatar_url AS actor_avatar_url
                FROM action_log
                LEFT JOIN users ON users.id = action_log.actor_id
                WHERE action_log.ticket_id = ?
                ORDER BY action_log.created_at DESC
                LIMIT 100
                """,
                (ticket["id"],),
            ).fetchall()
        )
        links = rows_to_dicts(
            conn.execute(
                """
                SELECT * FROM github_links
                WHERE ticket_id = ?
                ORDER BY updated_at DESC
                """,
                (ticket["id"],),
            ).fetchall()
        )
        watchers = rows_to_dicts(
            conn.execute(
                """
                SELECT users.id, users.login, users.name, users.avatar_url
                FROM watchers
                JOIN users ON users.id = watchers.user_id
                WHERE watchers.ticket_id = ?
                ORDER BY users.login
                """,
                (ticket["id"],),
            ).fetchall()
        )
        ticket_links = list_ticket_links_conn(conn, int(ticket["id"]))
        linkable_tickets = list_linkable_tickets_conn(conn, int(ticket["project_id"]), int(ticket["id"]))
        return {
            "ticket": ticket,
            "comments": comments,
            "actions": actions,
            "links": links,
            "ticket_links": ticket_links,
            "linkable_tickets": linkable_tickets,
            "watchers": watchers,
            "watcher_ids": [int(watcher["id"]) for watcher in watchers],
        }
