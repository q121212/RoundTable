"""Action log writes. log_action records an audit row and, for notifiable
actions, fans out via the outbox.

Direction: this module imports _notification_outbox (to enqueue) but must never
import _tickets. Ticket mutations import log_action from here, completing the
acyclic chain _tickets -> _action_log -> _notification_outbox -> _read_models.
"""

from typing import Any, Dict, Optional

from ..db import json_dumps, utcnow
from ._notification_outbox import enqueue_notifications


NOTIFY_ACTIONS = {"assigned", "status_changed", "commented", "closed", "reopened"}


def log_action(
    conn: Any,
    project_id: Optional[int],
    ticket_id: Optional[int],
    actor_id: Optional[int],
    action: str,
    field: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    now = utcnow()
    cur = conn.execute(
        """
        INSERT INTO action_log
            (project_id, ticket_id, actor_id, action, field, old_value, new_value, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (project_id, ticket_id, actor_id, action, field, old_value, new_value, json_dumps(metadata or {}), now),
    )
    action_id = int(cur.lastrowid)
    if ticket_id and action in NOTIFY_ACTIONS:
        enqueue_notifications(conn, action_id, project_id, ticket_id, actor_id, action)
    return action_id
