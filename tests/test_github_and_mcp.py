from fastapi.testclient import TestClient

from app.db import get_conn, row_to_dict
from app.github_integration import handle_webhook
from app.main import app
from app.store import create_mcp_token, create_project, create_ticket, upsert_user


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
