import json
from typing import Any, Callable, Dict, List, Optional

from fastapi import HTTPException, Request, status

from .db import get_conn, row_to_dict, rows_to_dicts, utcnow
from .security import hash_token
from .store import (
    add_comment,
    close_ticket,
    create_ticket,
    get_ticket_bundle,
    link_github_ref,
    list_projects,
    reopen_ticket,
    require_project_access,
    search_tickets,
    update_ticket,
)


def authenticate_bearer(request: Request) -> Dict[str, Any]:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    token = auth.split(" ", 1)[1].strip()
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT users.*, mcp_tokens.id AS token_id
            FROM mcp_tokens
            JOIN users ON users.id = mcp_tokens.user_id
            WHERE mcp_tokens.token_hash = ? AND mcp_tokens.revoked_at IS NULL
            """,
            (hash_token(token),),
        ).fetchone()
        user = row_to_dict(row)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MCP token")
        conn.execute("UPDATE mcp_tokens SET last_used_at = ? WHERE id = ?", (utcnow(), user["token_id"]))
        return user


async def handle_mcp(request: Request) -> Dict[str, Any]:
    user = authenticate_bearer(request)
    payload = await request.json()
    if isinstance(payload, list):
        return [dispatch_rpc(item, user) for item in payload]  # type: ignore[return-value]
    return dispatch_rpc(payload, user)


def dispatch_rpc(payload: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": "RoundTable", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": tool_specs()}
        elif method == "tools/call":
            result = call_tool(user, params.get("name"), params.get("arguments") or {})
        elif method == "resources/list":
            result = {"resources": resource_list(user)}
        elif method == "resources/read":
            result = read_resource(user, params.get("uri", ""))
        else:
            raise ValueError("Unsupported MCP method: %s" % method)
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def tool_specs() -> List[Dict[str, Any]]:
    def schema(properties: Dict[str, Any], required: Optional[List[str]] = None) -> Dict[str, Any]:
        return {"type": "object", "properties": properties, "required": required or []}

    return [
        {"name": "list_projects", "description": "List visible projects.", "inputSchema": schema({})},
        {
            "name": "search_tickets",
            "description": "Search tickets by key, title, or description.",
            "inputSchema": schema({"query": {"type": "string"}, "project_key": {"type": "string"}}),
        },
        {
            "name": "get_ticket",
            "description": "Read a ticket with comments, actions, and GitHub links.",
            "inputSchema": schema({"ticket_key": {"type": "string"}}, ["ticket_key"]),
        },
        {
            "name": "create_ticket",
            "description": "Create a ticket in a project.",
            "inputSchema": schema(
                {
                    "project_key": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string"},
                },
                ["project_key", "title"],
            ),
        },
        {
            "name": "update_ticket",
            "description": "Update title, description, status, priority, or assignee.",
            "inputSchema": schema(
                {
                    "ticket_key": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string"},
                    "priority": {"type": "string"},
                    "assignee_id": {"type": "integer"},
                },
                ["ticket_key"],
            ),
        },
        {
            "name": "move_ticket",
            "description": "Move a ticket to another status.",
            "inputSchema": schema({"ticket_key": {"type": "string"}, "status": {"type": "string"}}, ["ticket_key", "status"]),
        },
        {
            "name": "assign_ticket",
            "description": "Assign a ticket to a user id.",
            "inputSchema": schema({"ticket_key": {"type": "string"}, "assignee_id": {"type": "integer"}}, ["ticket_key"]),
        },
        {
            "name": "add_comment",
            "description": "Add a comment to a ticket.",
            "inputSchema": schema({"ticket_key": {"type": "string"}, "body": {"type": "string"}}, ["ticket_key", "body"]),
        },
        {
            "name": "close_ticket",
            "description": "Close a ticket.",
            "inputSchema": schema({"ticket_key": {"type": "string"}}, ["ticket_key"]),
        },
        {
            "name": "reopen_ticket",
            "description": "Reopen a ticket into Todo.",
            "inputSchema": schema({"ticket_key": {"type": "string"}}, ["ticket_key"]),
        },
        {
            "name": "link_github_ref",
            "description": "Link a ticket to a GitHub branch, commit, or pull request.",
            "inputSchema": schema(
                {
                    "ticket_key": {"type": "string"},
                    "repo_full_name": {"type": "string"},
                    "ref_type": {"type": "string"},
                    "ref_name": {"type": "string"},
                    "url": {"type": "string"},
                    "sha": {"type": "string"},
                    "title": {"type": "string"},
                    "state": {"type": "string"},
                },
                ["ticket_key", "repo_full_name", "ref_type", "ref_name"],
            ),
        },
    ]


def call_tool(user: Dict[str, Any], name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    tools: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Any]] = {
        "list_projects": lambda u, a: list_projects(u),
        "search_tickets": lambda u, a: search_tickets(u, a.get("query", ""), a.get("project_key", "")),
        "get_ticket": lambda u, a: read_ticket_checked(u, a["ticket_key"]),
        "create_ticket": lambda u, a: create_ticket(
            u,
            a["project_key"],
            a["title"],
            a.get("description", ""),
            a.get("priority", "Medium"),
        ),
        "update_ticket": lambda u, a: update_ticket(
            u,
            a["ticket_key"],
            title=a.get("title"),
            description=a.get("description"),
            status_value=a.get("status"),
            priority=a.get("priority"),
            assignee_id=a.get("assignee_id"),
            assignee_touched="assignee_id" in a,
        ),
        "move_ticket": lambda u, a: update_ticket(u, a["ticket_key"], status_value=a["status"]),
        "assign_ticket": lambda u, a: update_ticket(
            u, a["ticket_key"], assignee_id=a.get("assignee_id"), assignee_touched=True
        ),
        "add_comment": lambda u, a: add_comment(u, a["ticket_key"], a["body"]),
        "close_ticket": lambda u, a: close_ticket(u, a["ticket_key"]),
        "reopen_ticket": lambda u, a: reopen_ticket(u, a["ticket_key"]),
        "link_github_ref": lambda u, a: link_github_ref(
            a["ticket_key"],
            a["repo_full_name"],
            a["ref_type"],
            a["ref_name"],
            a.get("url", ""),
            a.get("sha", ""),
            a.get("title", ""),
            a.get("state", ""),
            actor_id=u["id"],
        ),
    }
    if name not in tools:
        raise ValueError("Unknown tool: %s" % name)
    result = tools[name](user, args)
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}]}


def resource_list(user: Dict[str, Any]) -> List[Dict[str, Any]]:
    resources = []
    for project in list_projects(user):
        resources.append(
            {
                "uri": "roundtable://projects/%s/board" % project["key"],
                "name": "%s board" % project["key"],
                "mimeType": "application/json",
            }
        )
    return resources


def read_resource(user: Dict[str, Any], uri: str) -> Dict[str, Any]:
    if uri.startswith("roundtable://tickets/"):
        ticket_key = uri.rsplit("/", 1)[-1]
        bundle = read_ticket_checked(user, ticket_key)
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(bundle, ensure_ascii=False, default=str),
                }
            ]
        }
    if uri.startswith("roundtable://projects/") and uri.endswith("/board"):
        project_key = uri.replace("roundtable://projects/", "").replace("/board", "")
        with get_conn() as conn:
            project = row_to_dict(conn.execute("SELECT * FROM projects WHERE key = ?", (project_key,)).fetchone())
            if not project:
                raise ValueError("Project not found")
            require_project_access(user, project["id"])
            tickets = rows_to_dicts(
                conn.execute("SELECT * FROM tickets WHERE project_id = ? ORDER BY updated_at DESC", (project["id"],)).fetchall()
            )
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps({"project": project, "tickets": tickets}, ensure_ascii=False, default=str),
                }
            ]
        }
    raise ValueError("Unknown resource URI")


def read_ticket_checked(user: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
    bundle = get_ticket_bundle(ticket_key)
    require_project_access(user, int(bundle["ticket"]["project_id"]))
    return bundle
