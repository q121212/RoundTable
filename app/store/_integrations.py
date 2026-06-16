"""GitHub linking helpers: parsing ticket keys from text, recording github_links
from refs, and webhook delivery de-duplication.

Imports downward only (_validation, _read_models, _action_log); never _tickets.
"""

import re
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from ..db import get_conn, row_to_dict, utcnow
from ._action_log import log_action
from ._read_models import get_ticket_by_id_conn
from ._validation import normalize_github_link_url, normalize_github_repo


TICKET_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d+)\b")
GITHUB_REF_TYPES = {"branch", "commit", "pull_request", "tag"}


def extract_ticket_keys(text: str) -> List[str]:
    return sorted(set(match.group(1).upper() for match in TICKET_KEY_RE.finditer(text or "")))


def link_github_ref(
    ticket_key: str,
    repo_full_name: str,
    ref_type: str,
    ref_name: str,
    url: str = "",
    sha: str = "",
    title: str = "",
    state: str = "",
    actor_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    now = utcnow()
    repo_full_name = normalize_github_repo(repo_full_name)
    ref_type = ref_type.strip()
    if ref_type not in GITHUB_REF_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid GitHub ref type")
    url = normalize_github_link_url(url)
    with get_conn() as conn:
        ticket = row_to_dict(
            conn.execute(
                """
                SELECT tickets.*, projects.github_repo_full_name AS project_github_repo_full_name
                FROM tickets
                JOIN projects ON projects.id = tickets.project_id
                WHERE tickets.key = ?
                """,
                (ticket_key.upper(),),
            ).fetchone()
        )
        if not ticket:
            return None
        project_repo = ticket.get("project_github_repo_full_name")
        if project_repo and project_repo != repo_full_name:
            return None
        conn.execute(
            """
            INSERT INTO github_links
                (ticket_id, repo_full_name, ref_type, ref_name, url, sha, title, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticket_id, repo_full_name, ref_type, ref_name)
            DO UPDATE SET
                url = excluded.url,
                sha = excluded.sha,
                title = excluded.title,
                state = excluded.state,
                updated_at = excluded.updated_at
            """,
            (ticket["id"], repo_full_name, ref_type, ref_name, url, sha, title, state, now, now),
        )
        log_action(
            conn,
            ticket["project_id"],
            ticket["id"],
            actor_id,
            "github_linked",
            metadata={"repo": repo_full_name, "type": ref_type, "name": ref_name, "url": url},
        )
        return get_ticket_by_id_conn(conn, ticket["id"])


def mark_github_delivery(delivery_id: str, event: str) -> bool:
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO github_deliveries (delivery_id, event, received_at) VALUES (?, ?, ?)",
                (delivery_id, event, utcnow()),
            )
            return True
        except Exception:
            return False
