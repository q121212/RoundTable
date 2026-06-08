import json
from urllib.parse import parse_qs, unquote, urlparse

from fastapi.testclient import TestClient

from app.db import get_conn, row_to_dict
from app.github_integration import handle_webhook
from app.main import app
from app.store import create_mcp_token, create_project, create_ticket, upsert_user


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
            "compare": "https://github.test/compare",
            "repository": {"full_name": "acme/app"},
            "commits": [
                {
                    "id": "abc123",
                    "message": "ENG-1 implement server",
                    "url": "https://github.test/commit/abc123",
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


def test_mcp_token_exposes_prefix_and_suffix(temp_db):
    user = upsert_user("alice")
    created = create_mcp_token(user, "laptop")
    assert created["token"].startswith(created["prefix"])
    assert created["token"].endswith(created["suffix"])


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
