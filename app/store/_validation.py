"""Pure input validators, normalizers, and per-project config helpers.

This module is a leaf: it depends only on stdlib, FastAPI's HTTPException, and
db-level constants/helpers. It must not import the rest of app.store, so it can
be imported by any other store submodule without creating a cycle.
"""

import re
from datetime import date
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import HTTPException, status

from ..db import PRIORITIES, TICKET_LINK_TYPES, TICKET_STATUSES, TICKET_TYPES, json_loads


PROJECT_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")
GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
STATS_VISIBILITIES = {"viewer", "member", "admin"}
TICKET_DELETE_POLICIES = {"admin", "member", "viewer"}


def validate_project_key(key: str) -> str:
    normalized = key.strip().upper()
    if not PROJECT_KEY_RE.match(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project key must be 2-10 uppercase letters or digits, starting with a letter.",
        )
    return normalized


def validate_status(value: str) -> str:
    if value not in TICKET_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket status")
    return value


def normalize_project_statuses(values: List[str]) -> List[str]:
    seen = set()
    normalized = []
    for value in values:
        status_value = validate_status(str(value))
        if status_value not in seen:
            normalized.append(status_value)
            seen.add(status_value)
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select at least one status")
    return normalized


def project_statuses(project: Dict[str, Any]) -> List[str]:
    configured = normalize_project_statuses(json_loads(project.get("statuses_json"), TICKET_STATUSES))
    return configured


def validate_project_ticket_status(project: Dict[str, Any], value: str) -> str:
    status_value = validate_status(value)
    if status_value not in project_statuses(project):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status is not enabled for this project")
    return status_value


def validate_priority(value: str) -> str:
    if value not in PRIORITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid priority")
    return value


def validate_story_points(value: Any) -> int:
    try:
        points = int(value or 0)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Story points must be an integer") from exc
    if points < 0 or points > 999:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Story points must be between 0 and 999")
    return points


def validate_ticket_type(value: str) -> str:
    if value not in TICKET_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket type")
    return value


def normalize_project_ticket_types(values: List[str]) -> List[str]:
    seen = set()
    normalized = []
    for value in values:
        ticket_type = validate_ticket_type(str(value))
        if ticket_type not in seen:
            normalized.append(ticket_type)
            seen.add(ticket_type)
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select at least one ticket type")
    return normalized


def project_ticket_types(project: Dict[str, Any]) -> List[str]:
    return normalize_project_ticket_types(json_loads(project.get("ticket_types_json"), TICKET_TYPES))


def normalize_stats_visibility(value: Optional[str]) -> str:
    clean = (value or "all").strip().lower()
    if clean == "all":
        clean = "viewer"
    if clean not in STATS_VISIBILITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid statistics visibility")
    return clean


def project_stats_visibility(project: Dict[str, Any]) -> str:
    return normalize_stats_visibility(project.get("stats_visibility") or "all")


def normalize_ticket_delete_policy(value: Optional[str]) -> str:
    clean = (value or "admin").strip().lower()
    if clean not in TICKET_DELETE_POLICIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket delete policy")
    return clean


def project_ticket_delete_policy(project: Dict[str, Any]) -> str:
    return normalize_ticket_delete_policy(project.get("ticket_delete_policy") or "admin")


def project_ticket_delete_own_only(project: Dict[str, Any]) -> bool:
    return bool(int(project.get("ticket_delete_own_only") or 0))


def validate_project_ticket_type(project: Dict[str, Any], value: str) -> str:
    ticket_type = validate_ticket_type(value)
    if ticket_type not in project_ticket_types(project):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket type is not enabled for this project")
    return ticket_type


def validate_ticket_link_type(value: str) -> str:
    if value not in TICKET_LINK_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket link type")
    return value


def validate_date_string(value: str, label: str) -> str:
    clean = value.strip()
    if not clean:
        return ""
    try:
        date.fromisoformat(clean)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="%s must be YYYY-MM-DD" % label) from exc
    return clean


def normalize_github_repo(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""
    if raw.startswith("git@github.com:"):
        raw = raw.removeprefix("git@github.com:")
    elif "://" in raw:
        parsed = urlparse(raw)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub repository must be owner/repo or a github.com URL.",
            )
        raw = parsed.path.strip("/")
    raw = raw.removesuffix(".git").strip("/")
    parts = raw.split("/")
    if len(parts) >= 2:
        raw = "%s/%s" % (parts[0], parts[1])
    if not GITHUB_REPO_RE.match(raw):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub repository must be owner/repo or a github.com URL.",
        )
    return raw


def normalize_github_installation_id(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if not raw.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub installation id must be numeric.",
        )
    return raw


def normalize_github_link_url(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    if parsed.scheme != "https" or parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub link URL must be an https://github.com URL.",
        )
    return raw
