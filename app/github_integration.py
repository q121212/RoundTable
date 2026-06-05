import time
from typing import Any, Dict, Iterable, List, Optional

import httpx
import jwt

from .config import settings
from .store import extract_ticket_keys, link_github_ref, mark_github_delivery


GITHUB_API = "https://api.github.com"


def github_oauth_configured() -> bool:
    return bool(settings.github_client_id and settings.github_client_secret)


async def exchange_oauth_code(code: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20) as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
        )
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise RuntimeError("GitHub OAuth did not return an access token")
        user_response = await client.get(
            "%s/user" % GITHUB_API,
            headers={"Authorization": "Bearer %s" % access_token, "Accept": "application/vnd.github+json"},
        )
        user_response.raise_for_status()
        user = user_response.json()
        email = user.get("email") or await fetch_primary_email(client, access_token)
        return {
            "github_id": str(user["id"]),
            "login": user["login"],
            "name": user.get("name"),
            "email": email,
            "avatar_url": user.get("avatar_url"),
        }


async def fetch_primary_email(client: httpx.AsyncClient, access_token: str) -> Optional[str]:
    response = await client.get(
        "%s/user/emails" % GITHUB_API,
        headers={"Authorization": "Bearer %s" % access_token, "Accept": "application/vnd.github+json"},
    )
    if response.status_code >= 400:
        return None
    for email in response.json():
        if email.get("primary") and email.get("verified"):
            return email.get("email")
    return None


def app_jwt() -> str:
    if not settings.github_app_id or not settings.github_app_private_key_path:
        raise RuntimeError("GitHub App credentials are not configured")
    with open(settings.github_app_private_key_path, "r", encoding="utf-8") as handle:
        private_key = handle.read()
    now = int(time.time())
    return jwt.encode(
        {"iat": now - 60, "exp": now + 540, "iss": settings.github_app_id},
        private_key,
        algorithm="RS256",
    )


async def installation_token(installation_id: str) -> str:
    token = app_jwt()
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "%s/app/installations/%s/access_tokens" % (GITHUB_API, installation_id),
            headers={"Authorization": "Bearer %s" % token, "Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        return response.json()["token"]


async def ensure_repo_autolink(
    repo_full_name: str, installation_id: str, project_key: str, base_url: str
) -> None:
    token = await installation_token(installation_id)
    key_prefix = "%s-" % project_key.upper()
    target_url = "%s/t/%s<num>" % (base_url.rstrip("/"), key_prefix)
    async with httpx.AsyncClient(timeout=20) as client:
        existing = await client.get(
            "%s/repos/%s/autolinks" % (GITHUB_API, repo_full_name),
            headers={"Authorization": "Bearer %s" % token, "Accept": "application/vnd.github+json"},
        )
        if existing.status_code == 200:
            for autolink in existing.json():
                if autolink.get("key_prefix") == key_prefix:
                    return
        response = await client.post(
            "%s/repos/%s/autolinks" % (GITHUB_API, repo_full_name),
            headers={"Authorization": "Bearer %s" % token, "Accept": "application/vnd.github+json"},
            json={"key_prefix": key_prefix, "url_template": target_url, "is_alphanumeric": True},
        )
        response.raise_for_status()


def handle_webhook(event: str, delivery_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if delivery_id and not mark_github_delivery(delivery_id, event):
        return {"ok": True, "duplicate": True, "linked": 0}
    linked = 0
    repo = (payload.get("repository") or {}).get("full_name", "")
    if event == "push":
        linked += link_push_refs(repo, payload)
    elif event == "pull_request":
        linked += link_pull_request_refs(repo, payload)
    elif event in {"create", "delete"}:
        linked += link_branch_event(repo, event, payload)
    return {"ok": True, "duplicate": False, "linked": linked}


def link_push_refs(repo: str, payload: Dict[str, Any]) -> int:
    count = 0
    branch = str(payload.get("ref", "")).replace("refs/heads/", "")
    compare_url = payload.get("compare", "")
    candidates = [branch]
    for commit in payload.get("commits") or []:
        candidates.append(commit.get("message") or "")
        keys = keys_from(candidates)
        for key in keys:
            if link_github_ref(
                key,
                repo,
                "commit",
                commit.get("id", ""),
                commit.get("url", compare_url),
                commit.get("id", ""),
                first_line(commit.get("message") or ""),
                "pushed",
            ):
                count += 1
    for key in keys_from([branch]):
        if link_github_ref(key, repo, "branch", branch, compare_url, "", branch, "active"):
            count += 1
    return count


def link_pull_request_refs(repo: str, payload: Dict[str, Any]) -> int:
    pr = payload.get("pull_request") or {}
    branch = ((pr.get("head") or {}).get("ref")) or ""
    text = " ".join([branch, pr.get("title") or "", pr.get("body") or ""])
    count = 0
    for key in extract_ticket_keys(text):
        if link_github_ref(
            key,
            repo,
            "pull_request",
            "#%s" % pr.get("number", ""),
            pr.get("html_url", ""),
            ((pr.get("head") or {}).get("sha")) or "",
            pr.get("title") or "",
            pr.get("state") or payload.get("action", ""),
        ):
            count += 1
    return count


def link_branch_event(repo: str, event: str, payload: Dict[str, Any]) -> int:
    if payload.get("ref_type") != "branch":
        return 0
    branch = payload.get("ref") or ""
    count = 0
    for key in extract_ticket_keys(branch):
        if link_github_ref(key, repo, "branch", branch, "", "", branch, event):
            count += 1
    return count


def keys_from(values: Iterable[str]) -> List[str]:
    keys: List[str] = []
    for value in values:
        keys.extend(extract_ticket_keys(value))
    return sorted(set(keys))


def first_line(value: str) -> str:
    return value.splitlines()[0] if value else ""

