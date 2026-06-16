import hashlib
import hmac
import json
from urllib.parse import parse_qs, unquote, urlparse

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.db import get_conn, row_to_dict
from app.github_integration import handle_webhook
from app.main import app
from app.store import create_mcp_token, create_project, create_ticket, list_mcp_tokens, revoke_mcp_token, upsert_user


def test_github_oauth_start_includes_base_url_redirect_uri(temp_db):
    from app.config import settings

    object.__setattr__(settings, "base_url", "https://rt.example.test")
    object.__setattr__(settings, "github_client_id", "client-id")
    object.__setattr__(settings, "github_client_secret", "client-secret")

    client = TestClient(app)
    response = client.get("/auth/github/start", follow_redirects=False)

    assert response.status_code == 307
    params = parse_qs(urlparse(response.headers["location"]).query)
    assert unquote(params["redirect_uri"][0]) == "https://rt.example.test/auth/github/callback"


def test_github_push_links_commit_to_ticket(temp_db):
    user = upsert_user("alice")
    create_project(user, "ENG", "Engineering")
    ticket = create_ticket(user, "ENG", "Build MCP")

    result = handle_webhook(
        "push",
        "delivery-1",
        {
            "ref": "refs/heads/ENG-1-mcp",
            "compare": "https://github.com/acme/app/compare/main...ENG-1-mcp",
            "repository": {"full_name": "acme/app"},
            "commits": [
                {
                    "id": "abc123",
                    "message": "ENG-1 implement server",
                    "url": "https://github.com/acme/app/commit/abc123",
                }
            ],
        },
    )

    with get_conn() as conn:
        link = row_to_dict(conn.execute("SELECT * FROM github_links WHERE ticket_id = ?", (ticket["id"],)).fetchone())
    assert result["linked"] >= 1
    assert link["repo_full_name"] == "acme/app"


def test_mcp_requires_bearer_token(temp_db):
    client = TestClient(app)
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert response.status_code == 401


def test_mcp_lists_projects_with_token(temp_db):
    user = upsert_user("alice")
    create_project(user, "WEB", "Website")
    token = create_mcp_token(user, "test")["token"]

    client = TestClient(app)
    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer %s" % token},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "list_projects"}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["content"][0]["type"] == "text"
    assert "WEB" in payload["result"]["content"][0]["text"]
    with get_conn() as conn:
        audit = row_to_dict(conn.execute("SELECT * FROM api_audit WHERE route = '/mcp'").fetchone())
    assert audit is not None
    assert audit["action"] == "tools/call"


def test_mcp_link_github_ref_uses_project_repo_by_default(temp_db):
    user = upsert_user("alice")
    create_project(user, "GT", "GigaTool", repo="https://github.com/acme/app")
    ticket = create_ticket(user, "GT", "Wire GitHub")
    token = create_mcp_token(user, "test")["token"]

    client = TestClient(app)
    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer %s" % token},
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "link_github_ref",
                "arguments": {
                    "ticket_key": ticket["key"],
                    "ref_type": "pull_request",
                    "ref_name": "#12",
                    "url": "https://github.com/acme/app/pull/12",
                },
            },
        },
    )

    assert response.status_code == 200
    assert "error" not in response.json()
    with get_conn() as conn:
        link = row_to_dict(conn.execute("SELECT * FROM github_links WHERE ticket_id = ?", (ticket["id"],)).fetchone())
    assert link["repo_full_name"] == "acme/app"


def test_mcp_link_github_ref_rejects_wrong_project_repo(temp_db):
    user = upsert_user("alice")
    create_project(user, "GT", "GigaTool", repo="https://github.com/acme/app")
    ticket = create_ticket(user, "GT", "Wire GitHub")
    token = create_mcp_token(user, "test")["token"]

    client = TestClient(app)
    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer %s" % token},
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "link_github_ref",
                "arguments": {
                    "ticket_key": ticket["key"],
                    "repo_full_name": "other/repo",
                    "ref_type": "pull_request",
                    "ref_name": "#12",
                    "url": "https://github.com/other/repo/pull/12",
                },
            },
        },
    )

    assert response.status_code == 200
    assert "does not match" in response.json()["error"]["message"]


def test_mcp_can_create_ticket_in_sprint(temp_db):
    user = upsert_user("alice")
    project = create_project(user, "GT", "GigaTool")
    token = create_mcp_token(user, "test")["token"]

    client = TestClient(app)
    sprint_response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer %s" % token},
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "create_sprint",
                "arguments": {"project_key": "GT", "name": "Sprint 1", "status": "active"},
            },
        },
    )
    sprint_payload = json.loads(sprint_response.json()["result"]["content"][0]["text"])
    sprint_id = sprint_payload["id"]

    ticket_response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer %s" % token},
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "create_ticket",
                "arguments": {"project_key": "GT", "title": "Scoped via MCP", "sprint_id": sprint_id, "story_points": 13},
            },
        },
    )

    assert sprint_response.status_code == 200
    assert ticket_response.status_code == 200
    assert sprint_payload["project_id"] == project["id"]
    ticket_payload = json.loads(ticket_response.json()["result"]["content"][0]["text"])
    assert ticket_payload["sprint_id"] == sprint_id
    assert ticket_payload["story_points"] == 13


def test_mcp_token_exposes_prefix_and_suffix(temp_db):
    user = upsert_user("alice")
    created = create_mcp_token(user, "laptop")
    assert created["token"].startswith(created["prefix"])
    assert created["token"].endswith(created["suffix"])


def test_revoked_mcp_tokens_are_hidden(temp_db):
    user = upsert_user("alice")
    create_mcp_token(user, "old laptop")
    token = list_mcp_tokens(int(user["id"]))[0]

    revoke_mcp_token(int(user["id"]), int(token["id"]))

    assert list_mcp_tokens(int(user["id"])) == []


def test_mcp_notification_returns_no_body(temp_db):
    user = upsert_user("alice")
    token = create_mcp_token(user, "test")["token"]

    client = TestClient(app)
    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer %s" % token},
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
    )

    assert response.status_code == 202
    assert response.content == b""


def test_mcp_streams_sse_when_accept_event_stream(temp_db):
    user = upsert_user("alice")
    create_project(user, "WEB", "Website")
    token = create_mcp_token(user, "test")["token"]

    client = TestClient(app)
    response = client.post(
        "/mcp",
        headers={
            "Authorization": "Bearer %s" % token,
            "Accept": "application/json, text/event-stream",
        },
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "list_projects"}},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert body.startswith("event: message\ndata: ")
    data_line = body.split("data: ", 1)[1].strip()
    payload = json.loads(data_line)
    assert "WEB" in payload["result"]["content"][0]["text"]


def test_mcp_get_returns_405(temp_db):
    client = TestClient(app)
    response = client.get("/mcp")
    assert response.status_code == 405
    assert response.headers.get("allow") == "POST"


def test_telegram_webhook_secret_is_checked_when_configured(temp_db):
    from app.config import settings

    object.__setattr__(settings, "telegram_webhook_secret", "telegram-secret")
    client = TestClient(app)
    payload = {"message": {"text": "/start nope", "chat": {"id": 123}, "from": {"username": "alice"}}}

    denied = client.post("/integrations/telegram/webhook", json=payload)
    allowed = client.post(
        "/integrations/telegram/webhook",
        json=payload,
        headers={"X-Telegram-Bot-Api-Secret-Token": "telegram-secret"},
    )

    assert denied.status_code == 401
    assert allowed.status_code == 200


def test_webhooks_are_disabled_without_secrets(temp_db):
    client = TestClient(app)

    github = client.post("/integrations/github/webhook", json={"repository": {"full_name": "acme/app"}})
    telegram = client.post("/integrations/telegram/webhook", json={"message": {"text": "/start nope"}})

    assert github.status_code == 503
    assert telegram.status_code == 503


def test_github_webhook_signature_is_checked(temp_db):
    from app.config import settings

    object.__setattr__(settings, "github_webhook_secret", "github-secret")
    body = json.dumps({"repository": {"full_name": "acme/app"}}).encode("utf-8")
    signature = "sha256=" + hmac.new(b"github-secret", body, hashlib.sha256).hexdigest()
    client = TestClient(app)

    denied = client.post("/integrations/github/webhook", content=body, headers={"X-GitHub-Event": "push"})
    allowed = client.post(
        "/integrations/github/webhook",
        content=body,
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": signature},
    )

    assert denied.status_code == 401
    assert allowed.status_code == 200


def test_github_installation_id_must_be_numeric(temp_db):
    from app.store import normalize_github_installation_id

    assert normalize_github_installation_id("") == ""
    assert normalize_github_installation_id("  12345 ") == "12345"
    with pytest.raises(HTTPException):
        normalize_github_installation_id("../../evil")
    with pytest.raises(HTTPException):
        normalize_github_installation_id("123abc")


def test_mcp_internal_error_is_masked(temp_db, monkeypatch):
    from app import mcp_server

    user = upsert_user("alice")
    create_project(user, "WEB", "Website")
    token = create_mcp_token(user, "test")["token"]

    def boom(_user):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(mcp_server, "list_projects", boom)

    client = TestClient(app)
    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer %s" % token},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "list_projects"}},
    )

    message = response.json()["error"]["message"]
    assert "secret internal detail" not in message
    assert "Internal error" in message
    assert "ref" in message


def test_mcp_missing_required_argument_is_reported_cleanly(temp_db):
    user = upsert_user("alice")
    token = create_mcp_token(user, "test")["token"]

    client = TestClient(app)
    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer %s" % token},
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "get_ticket", "arguments": {}},
        },
    )

    message = response.json()["error"]["message"]
    assert "Missing required argument" in message
    assert "ticket_key" in message
