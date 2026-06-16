import json
import logging
import uuid
from json import JSONDecodeError
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import HTTPException, Request, status

from .db import get_conn, row_to_dict, utcnow
from .security import hash_token
from .rate_limit import client_identity
from .store import (
    add_comment,
    board_for_project,
    close_ticket,
    create_sprint,
    create_ticket,
    get_project_by_key,
    get_ticket_bundle,
    link_ticket,
    link_github_ref,
    list_project_sprints,
    list_projects,
    record_api_audit,
    reopen_ticket,
    require_project_access,
    search_tickets,
    unlink_ticket,
    update_sprint_status,
    update_ticket,
)


logger = logging.getLogger("roundtable.mcp")

TicketChangedCallback = Callable[[Dict[str, Any], str], Awaitable[Any]]


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


async def handle_mcp(request: Request, on_ticket_changed: Optional[TicketChangedCallback] = None) -> Optional[Any]:
    user = authenticate_bearer(request)
    try:
        payload = await request.json()
    except JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body") from exc
    try:
        if isinstance(payload, list):
            responses = []
            for entry in payload:
                item = await dispatch_rpc(entry, user, on_ticket_changed)
                if item is not None:
                    responses.append(item)
            return responses or None
        return await dispatch_rpc(payload, user, on_ticket_changed)
    finally:
        if isinstance(payload, list):
            methods = ",".join(
                str(entry.get("method") or "")
                for entry in payload
                if isinstance(entry, dict)
            )
        elif isinstance(payload, dict):
            methods = str(payload.get("method") or "")
        else:
            methods = "invalid"
        record_api_audit(
            int(user["id"]),
            int(user["token_id"]),
            "/mcp",
            methods[:120] or "unknown",
            client_identity(request),
            request.headers.get("user-agent", ""),
        )


async def dispatch_rpc(
    payload: Dict[str, Any],
    user: Dict[str, Any],
    on_ticket_changed: Optional[TicketChangedCallback] = None,
) -> Optional[Dict[str, Any]]:
    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}
    # JSON-RPC notifications (e.g. notifications/initialized) carry no id and get no response.
    if method and method.startswith("notifications/"):
        return None
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": "RoundTable", "version": "0.1.0"},
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": tool_specs()}
        elif method == "tools/call":
            result = await call_tool(user, params.get("name"), params.get("arguments") or {}, on_ticket_changed)
        elif method == "resources/list":
            result = {"resources": resource_list(user)}
        elif method == "resources/read":
            result = read_resource(user, params.get("uri", ""))
        else:
            raise ValueError("Unsupported MCP method: %s" % method)
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except (HTTPException, ValueError) as exc:
        # Expected, user-facing errors (validation, authz, unknown tool/argument).
        # These messages are the same ones the web UI shows, so they are safe.
        message = exc.detail if isinstance(exc, HTTPException) else str(exc)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(message)},
        }
    except Exception:
        # Unexpected errors may carry internal detail (SQL text, KeyError field
        # names). Log the real exception with a reference and return only the ref.
        error_ref = uuid.uuid4().hex[:12]
        logger.exception("MCP method %s failed [ref %s]", method, error_ref)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": "Internal error (ref %s)" % error_ref},
        }


def _required_tool_args() -> Dict[str, List[str]]:
    return {spec["name"]: spec["inputSchema"].get("required", []) for spec in tool_specs()}


def tool_specs() -> List[Dict[str, Any]]:
    def schema(properties: Dict[str, Any], required: Optional[List[str]] = None) -> Dict[str, Any]:
        return {"type": "object", "properties": properties, "required": required or []}

    return [
        {
            "name": "list_projects",
            "description": (
                "List projects visible to this token's user. Use the returned project key explicitly "
                "when creating tickets or narrowing searches."
            ),
            "inputSchema": schema({}),
        },
        {
            "name": "search_tickets",
            "description": "Search tickets by key, title, or description. Pass project_key to search one project.",
            "inputSchema": schema({"query": {"type": "string"}, "project_key": {"type": "string"}}),
        },
        {
            "name": "get_ticket",
            "description": "Read a ticket with comments, actions, ticket links, and GitHub links.",
            "inputSchema": schema({"ticket_key": {"type": "string"}}, ["ticket_key"]),
        },
        {
            "name": "create_ticket",
            "description": "Create a ticket in a project. project_key is required; get it from list_projects.",
            "inputSchema": schema(
                {
                    "project_key": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "ticket_type": {"type": "string"},
                    "priority": {"type": "string"},
                    "story_points": {"type": "integer"},
                    "sprint_id": {"type": "integer"},
                },
                ["project_key", "title"],
            ),
        },
        {
            "name": "update_ticket",
            "description": "Update title, description, type, status, priority, story points, assignee, or sprint.",
            "inputSchema": schema(
                {
                    "ticket_key": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "ticket_type": {"type": "string"},
                    "status": {"type": "string"},
                    "priority": {"type": "string"},
                    "story_points": {"type": "integer"},
                    "assignee_id": {"type": "integer"},
                    "sprint_id": {"type": "integer"},
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
            "name": "link_ticket",
            "description": "Create a project-scoped relationship between two RoundTable tickets.",
            "inputSchema": schema(
                {
                    "source_ticket_key": {"type": "string"},
                    "target_ticket_key": {"type": "string"},
                    "link_type": {
                        "type": "string",
                        "description": "One of relates, blocks, blocked_by, duplicates, parent.",
                    },
                },
                ["source_ticket_key", "target_ticket_key"],
            ),
        },
        {
            "name": "list_sprints",
            "description": "List sprints for a project visible to this token's user.",
            "inputSchema": schema({"project_key": {"type": "string"}, "include_closed": {"type": "boolean"}}, ["project_key"]),
        },
        {
            "name": "create_sprint",
            "description": "Create a sprint. Requires project admin access.",
            "inputSchema": schema(
                {
                    "project_key": {"type": "string"},
                    "name": {"type": "string"},
                    "goal": {"type": "string"},
                    "starts_on": {"type": "string"},
                    "ends_on": {"type": "string"},
                    "status": {"type": "string", "description": "planned or active"},
                },
                ["project_key", "name"],
            ),
        },
        {
            "name": "update_sprint_status",
            "description": "Set a sprint status to planned, active, or closed. Requires project admin access.",
            "inputSchema": schema(
                {
                    "project_key": {"type": "string"},
                    "sprint_id": {"type": "integer"},
                    "status": {"type": "string"},
                },
                ["project_key", "sprint_id", "status"],
            ),
        },
        {
            "name": "unlink_ticket",
            "description": "Remove a RoundTable ticket relationship by link id from get_ticket.",
            "inputSchema": schema({"ticket_key": {"type": "string"}, "link_id": {"type": "integer"}}, ["ticket_key", "link_id"]),
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
            "description": (
                "Link a ticket to a GitHub branch, commit, tag, or pull request. repo_full_name is optional; "
                "when omitted, RoundTable uses the GitHub repository configured on the ticket's project."
            ),
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
                ["ticket_key", "ref_type", "ref_name"],
            ),
        },
    ]


async def call_tool(
    user: Dict[str, Any],
    name: str,
    args: Dict[str, Any],
    on_ticket_changed: Optional[TicketChangedCallback] = None,
) -> Dict[str, Any]:
    tools: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Any]] = {
        "list_projects": lambda u, a: list_projects(u),
        "search_tickets": lambda u, a: search_tickets(u, a.get("query", ""), a.get("project_key", "")),
        "get_ticket": lambda u, a: read_ticket_checked(u, a["ticket_key"]),
        "create_ticket": lambda u, a: create_ticket(
            user=u,
            project_key=a["project_key"],
            title=a["title"],
            description=a.get("description", ""),
            priority=a.get("priority", "Medium"),
            ticket_type=a.get("ticket_type", "Task"),
            sprint_id=a.get("sprint_id"),
            story_points=a.get("story_points", 0),
        ),
        "update_ticket": lambda u, a: update_ticket(
            u,
            a["ticket_key"],
            title=a.get("title"),
            description=a.get("description"),
            ticket_type=a.get("ticket_type"),
            status_value=a.get("status"),
            priority=a.get("priority"),
            story_points=a.get("story_points"),
            story_points_touched="story_points" in a,
            assignee_id=a.get("assignee_id"),
            assignee_touched="assignee_id" in a,
            sprint_id=a.get("sprint_id"),
            sprint_touched="sprint_id" in a,
        ),
        "move_ticket": lambda u, a: update_ticket(u, a["ticket_key"], status_value=a["status"]),
        "assign_ticket": lambda u, a: update_ticket(
            u, a["ticket_key"], assignee_id=a.get("assignee_id"), assignee_touched=True
        ),
        "add_comment": lambda u, a: add_comment(u, a["ticket_key"], a["body"]),
        "link_ticket": lambda u, a: link_ticket(
            u, a["source_ticket_key"], a["target_ticket_key"], a.get("link_type", "relates")
        ),
        "list_sprints": lambda u, a: list_sprints_for_mcp(u, a["project_key"], bool(a.get("include_closed", True))),
        "create_sprint": lambda u, a: create_sprint(
            u,
            a["project_key"],
            a["name"],
            a.get("goal", ""),
            a.get("starts_on", ""),
            a.get("ends_on", ""),
            a.get("status", "planned"),
        ),
        "update_sprint_status": lambda u, a: update_sprint_status(u, a["project_key"], int(a["sprint_id"]), a["status"]),
        "unlink_ticket": lambda u, a: (unlink_ticket(u, a["ticket_key"], int(a["link_id"])) or {"ok": True}),
        "close_ticket": lambda u, a: close_ticket(u, a["ticket_key"]),
        "reopen_ticket": lambda u, a: reopen_ticket(u, a["ticket_key"]),
        "link_github_ref": link_github_ref_for_mcp,
    }
    if name not in tools:
        raise ValueError("Unknown tool: %s" % name)
    missing = [
        arg
        for arg in _required_tool_args().get(name, [])
        if args.get(arg) is None or args.get(arg) == ""
    ]
    if missing:
        raise ValueError(
            "Missing required argument(s) for %s: %s" % (name, ", ".join(missing))
        )
    result = tools[name](user, args)
    if on_ticket_changed:
        event_name = {
            "create_ticket": "ticket_created",
            "update_ticket": "ticket_changed",
            "move_ticket": "ticket_changed",
            "assign_ticket": "ticket_changed",
            "add_comment": "ticket_commented",
            "link_ticket": "ticket_linked",
            "unlink_ticket": "ticket_unlinked",
            "close_ticket": "ticket_changed",
            "reopen_ticket": "ticket_changed",
            "link_github_ref": "ticket_changed",
        }.get(name)
        if event_name:
            ticket = result if isinstance(result, dict) and result.get("key") else None
            if not ticket and name == "add_comment":
                ticket = get_ticket_bundle(args["ticket_key"])["ticket"]
            if not ticket and name == "link_ticket":
                ticket = get_ticket_bundle(args["source_ticket_key"])["ticket"]
            if not ticket and name == "unlink_ticket":
                ticket = get_ticket_bundle(args["ticket_key"])["ticket"]
            if ticket:
                await on_ticket_changed(ticket, event_name)
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}]}


def list_sprints_for_mcp(user: Dict[str, Any], project_key: str, include_closed: bool = True) -> Dict[str, Any]:
    project = get_project_by_key(project_key)
    require_project_access(user, int(project["id"]))
    return {
        "project": project,
        "sprints": list_project_sprints(int(project["id"]), include_closed=include_closed),
    }


def link_github_ref_for_mcp(user: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    bundle = read_ticket_checked(user, args["ticket_key"])
    ticket = bundle["ticket"]
    repo_full_name = str(args.get("repo_full_name") or ticket.get("project_github_repo_full_name") or "")
    if not repo_full_name:
        raise ValueError(
            "This ticket's project has no GitHub repository configured; configure the project or pass repo_full_name."
        )
    linked = link_github_ref(
        args["ticket_key"],
        repo_full_name,
        args["ref_type"],
        args["ref_name"],
        args.get("url", ""),
        args.get("sha", ""),
        args.get("title", ""),
        args.get("state", ""),
        actor_id=user["id"],
    )
    if not linked:
        raise ValueError("GitHub repository does not match the ticket's project.")
    return linked


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
        board = board_for_project(project_key, user)
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(board, ensure_ascii=False, default=str),
                }
            ]
        }
    raise ValueError("Unknown resource URI")


def read_ticket_checked(user: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
    bundle = get_ticket_bundle(ticket_key)
    require_project_access(user, int(bundle["ticket"]["project_id"]))
    return bundle
