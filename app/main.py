import asyncio
import html
import json
import logging
import os
import re
import secrets
from contextlib import asynccontextmanager
from json import JSONDecodeError
from typing import Any, AsyncIterator, Dict, Optional
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from .config import settings
from .db import PRIORITIES, TICKET_LINK_TYPES, TICKET_STATUSES, TICKET_TYPES, get_conn, init_db
from .github_integration import exchange_oauth_code, github_oauth_configured, handle_webhook
from .live import project_events, sse_message
from .mcp_server import handle_mcp
from .notifications import notification_worker
from .security import (
    SESSION_COOKIE,
    delete_session,
    get_user_by_session,
    login_response,
    new_token,
    require_admin,
    validate_csrf_request,
    verify_hmac_signature,
)
from .store import (
    add_comment,
    add_project_member,
    board_for_project,
    close_ticket,
    consume_telegram_link_token,
    create_mcp_token,
    create_project,
    create_sprint,
    create_telegram_link_token,
    create_test_notification,
    create_ticket,
    delete_project,
    get_project_by_key,
    get_telegram_link,
    get_ticket_bundle,
    link_ticket,
    list_mcp_tokens,
    list_project_sprints,
    list_projects,
    notification_preferences,
    normalize_github_repo,
    project_members,
    project_ticket_types,
    project_statuses,
    remove_project_member,
    reopen_ticket,
    require_project_access,
    require_project_admin,
    revoke_mcp_token,
    search_linkable_tickets,
    search_project_users,
    set_watch,
    sync_configured_admin_roles,
    unlink_ticket,
    unlink_telegram,
    update_notification_preferences,
    update_project_member,
    update_project_settings,
    update_sprint,
    update_sprint_status,
    update_ticket,
    update_ticket_link,
    upsert_user,
)


logger = logging.getLogger("roundtable")

TICKET_TYPE_ICONS = {
    "Task": "circle-check",
    "Epic": "layers-3",
    "Bug": "bug",
    "Story": "book-open",
}

PRIORITY_ICONS = {
    "Low": "arrow-down",
    "Medium": "minus",
    "High": "arrow-up",
    "Urgent": "flame",
}


def static_version() -> str:
    candidates = ("app/static/app.js", "app/static/styles.css", "app/static/favicon.svg")
    try:
        return str(int(max(os.path.getmtime(path) for path in candidates if os.path.exists(path))))
    except ValueError:
        return "dev"


def warn_insecure_config() -> None:
    """Loud warnings for config that is dangerous on a public deployment."""
    is_https = settings.base_url.lower().startswith("https")
    if settings.allow_dev_login:
        logger.warning(
            "ALLOW_DEV_LOGIN is ON: anyone can sign in as any user (and becomes admin "
            "when no ADMIN_GITHUB_LOGINS are set). Turn it OFF for any internet-facing deploy."
        )
        if is_https:
            logger.warning(
                "ALLOW_DEV_LOGIN is ON together with an https BASE_URL (%s) — this looks "
                "like production. Disable dev login.",
                settings.base_url,
            )
    if is_https and not settings.session_cookie_secure:
        logger.warning("BASE_URL is https but SESSION_COOKIE_SECURE is off; session cookies may leak.")
    if is_https and not settings.github_webhook_secret:
        logger.warning("BASE_URL is https but GITHUB_WEBHOOK_SECRET is empty; GitHub webhooks will be disabled.")
    if is_https and settings.telegram_bot_token and not settings.telegram_webhook_secret:
        logger.warning("BASE_URL is https but TELEGRAM_WEBHOOK_SECRET is empty; Telegram webhooks will be disabled.")


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    init_db()
    sync_configured_admin_roles()
    warn_insecure_config()
    fastapi_app.state.notification_stop = asyncio.Event()
    fastapi_app.state.notification_task = asyncio.create_task(
        notification_worker(fastapi_app.state.notification_stop)
    )
    yield
    stop_event = getattr(fastapi_app.state, "notification_stop", None)
    task = getattr(fastapi_app.state, "notification_task", None)
    if stop_event:
        stop_event.set()
    if task:
        await task


app = FastAPI(title=settings.app_name, lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

MENTION_RE = re.compile(r"(?<![\w.-])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?)")


CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        # inline style attributes are used for drag previews and avatars.
        "style-src 'self' 'unsafe-inline'",
        # avatars come from GitHub/arbitrary https hosts.
        "img-src 'self' https: data:",
        "connect-src 'self'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
    if settings.session_cookie_secure:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


def page_user(request: Request) -> Optional[Dict[str, Any]]:
    return get_user_by_session(request.cookies.get(SESSION_COOKIE))


def require_page_user(request: Request) -> Dict[str, Any]:
    user = page_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user


def render(
    request: Request,
    template: str,
    context: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
) -> HTMLResponse:
    data: Dict[str, Any] = {
        "request": request,
        "user": page_user(request),
        "base_url": settings.base_url,
        "static_version": static_version(),
        "statuses": TICKET_STATUSES,
        "priorities": PRIORITIES,
        "ticket_types": TICKET_TYPES,
        "ticket_link_types": TICKET_LINK_TYPES,
        "ticket_type_icons": TICKET_TYPE_ICONS,
        "priority_icons": PRIORITY_ICONS,
    }
    data.update(context or {})
    project_key = None
    if isinstance(data.get("project"), dict):
        project_key = data["project"].get("key")
    if not project_key and isinstance(data.get("ticket"), dict):
        project_key = data["ticket"].get("project_key")
    data["current_project_url"] = "/p/%s/board" % project_key if project_key else ""
    # Modern Starlette signature (request, name, context); works across the
    # version range we target and avoids the deprecated (name, context) form.
    return templates.TemplateResponse(
        request=request, name=template, context=data, status_code=status_code
    )


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)


def render_mentions(text: str, members: list[Dict[str, Any]]) -> Markup:
    member_by_login = {str(member.get("login") or "").lower(): member for member in members}
    pieces: list[str] = []
    last = 0
    for match in MENTION_RE.finditer(text or ""):
        pieces.append(html.escape((text or "")[last:match.start()]))
        login = match.group(1)
        member = member_by_login.get(login.lower())
        if member:
            label = "@%s" % html.escape(str(member.get("login") or login))
            title = html.escape(str(member.get("name") or member.get("login") or login))
            pieces.append('<span class="mention" title="%s">%s</span>' % (title, label))
        else:
            pieces.append(html.escape(match.group(0)))
        last = match.end()
    pieces.append(html.escape((text or "")[last:]))
    return Markup("".join(pieces))


async def publish_ticket_event(
    ticket: Dict[str, Any], event_name: str = "ticket_changed"
) -> Optional[Dict[str, Any]]:
    if not ticket:
        return None
    bundle = get_ticket_bundle(str(ticket["key"]))
    action = bundle["actions"][0] if bundle.get("actions") else None
    await project_events.publish(
        str(ticket["project_key"]),
        {"event": event_name, "ticket": ticket, "action": action},
    )
    return action


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request) -> HTMLResponse:
    if page_user(request):
        return redirect("/")  # type: ignore[return-value]
    return render(
        request,
        "login.html",
        {"github_enabled": github_oauth_configured(), "allow_dev_login": settings.allow_dev_login},
    )


@app.post("/auth/dev")
async def auth_dev(request: Request) -> RedirectResponse:
    if not settings.allow_dev_login:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local login is disabled")
    form = await request.form()
    user = upsert_user(
        str(form.get("login") or ""),
        name=str(form.get("login") or ""),
        email=str(form.get("email") or "") or None,
    )
    return login_response(int(user["id"]), "/")


@app.get("/auth/github/start")
async def auth_github_start() -> RedirectResponse:
    if not github_oauth_configured():
        return redirect("/login")
    state_token = new_token("gh_")
    params = urlencode(
        {
            "client_id": settings.github_client_id,
            "scope": "read:user user:email",
            "state": state_token,
            "redirect_uri": "%s/auth/github/callback" % settings.base_url,
        }
    )
    response = RedirectResponse("https://github.com/login/oauth/authorize?%s" % params)
    response.set_cookie(
        "github_oauth_state",
        state_token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=600,
    )
    return response


@app.get("/auth/github/callback")
async def auth_github_callback(request: Request, code: str = "", state: str = "") -> RedirectResponse:
    expected = request.cookies.get("github_oauth_state")
    if not expected or not secrets.compare_digest(expected, state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid GitHub OAuth state")
    profile = await exchange_oauth_code(code)
    user = upsert_user(**profile)
    response = login_response(int(user["id"]), "/")
    response.delete_cookie("github_oauth_state")
    return response


@app.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    await validate_csrf_request(request)
    delete_session(request.cookies.get(SESSION_COOKIE))
    response = redirect("/login")
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/", response_class=HTMLResponse)
@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request) -> HTMLResponse:
    user = require_page_user(request)
    return render(
        request,
        "projects.html",
        {"projects": list_projects(user), "can_create_project": user.get("role") == "admin"},
    )


@app.post("/api/projects")
async def api_create_project(request: Request) -> RedirectResponse:
    user = await validate_csrf_request(request)
    require_admin(user)
    form = await request.form()
    project = create_project(
        user,
        str(form.get("key") or ""),
        str(form.get("name") or ""),
        str(form.get("description") or ""),
        str(form.get("repo") or ""),
    )
    return redirect("/p/%s/board" % project["key"])


@app.get("/p/{project_key}/board", response_class=HTMLResponse)
async def board_page(request: Request, project_key: str) -> HTMLResponse:
    user = require_page_user(request)
    sprint_filter = str(request.query_params.get("sprint") or "")
    board = board_for_project(project_key, user, sprint_filter=sprint_filter)
    members = project_members(int(board["project"]["id"]))
    return render(
        request,
        "board.html",
        {**board, "members": members, "ticket_types": project_ticket_types(board["project"])},
    )


@app.get("/events/projects/{project_key}")
async def project_events_stream(request: Request, project_key: str) -> StreamingResponse:
    user = require_page_user(request)
    project = get_project_by_key(project_key)
    require_project_access(user, int(project["id"]))

    async def stream() -> AsyncIterator[str]:
        queue = await project_events.subscribe(str(project["key"]))
        try:
            yield sse_message("ready", {"project_key": project["key"]})
            while not await request.is_disconnected():
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=10)
                    yield sse_message(str(item.get("event") or "ticket_changed"), item)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            await project_events.unsubscribe(str(project["key"]), queue)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/p/{project_key}/settings", response_class=HTMLResponse)
async def project_settings_page(request: Request, project_key: str, error: str = "") -> HTMLResponse:
    user = require_page_user(request)
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    members = project_members(int(project["id"]))
    admin_count = sum(1 for member in members if member.get("project_role") == "admin")
    return render(
        request,
        "project_settings.html",
        {
            "project": project,
            "members": members,
            "admin_count": admin_count,
            "can_delete": True,
            "error": error,
            "all_statuses": TICKET_STATUSES,
            "active_statuses": project_statuses(project),
            "all_ticket_types": TICKET_TYPES,
            "active_ticket_types": project_ticket_types(project),
            "sprints": list_project_sprints(int(project["id"])),
        },
    )


@app.get("/p/{project_key}/sprints", response_class=HTMLResponse)
async def project_sprints_page(request: Request, project_key: str) -> HTMLResponse:
    user = require_page_user(request)
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    return render(
        request,
        "project_sprints.html",
        {
            "project": project,
            "sprints": list_project_sprints(int(project["id"])),
        },
    )


@app.post("/api/projects/{project_key}/delete")
async def api_delete_project(request: Request, project_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    delete_project(user, project_key, str(form.get("confirm") or ""))
    return redirect("/projects")


@app.post("/api/projects/{project_key}/settings")
async def api_update_project_settings(request: Request, project_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    update_project_settings(
        user,
        project_key,
        str(form.get("name") or ""),
        str(form.get("description") or ""),
        str(form.get("repo") or ""),
        [str(value) for value in form.getlist("statuses")],
        [str(value) for value in form.getlist("ticket_types")],
    )
    return redirect("/p/%s/settings" % project_key.upper())


@app.post("/api/projects/{project_key}/sprints")
async def api_create_sprint(request: Request, project_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    create_sprint(
        user,
        project_key,
        str(form.get("name") or ""),
        str(form.get("goal") or ""),
        str(form.get("starts_on") or ""),
        str(form.get("ends_on") or ""),
        str(form.get("status") or "planned"),
    )
    return redirect("/p/%s/sprints" % project_key.upper())


@app.post("/api/projects/{project_key}/sprints/{sprint_id}/status")
async def api_update_sprint_status(request: Request, project_key: str, sprint_id: int) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    update_sprint_status(user, project_key, sprint_id, str(form.get("status") or "planned"))
    return redirect(str(request.headers.get("referer") or "/p/%s/sprints" % project_key.upper()))


@app.post("/api/projects/{project_key}/sprints/{sprint_id}")
async def api_update_sprint(request: Request, project_key: str, sprint_id: int) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    update_sprint(
        user,
        project_key,
        sprint_id,
        str(form.get("name") or ""),
        str(form.get("goal") or ""),
        str(form.get("starts_on") or ""),
        str(form.get("ends_on") or ""),
    )
    return redirect(str(request.headers.get("referer") or "/p/%s/sprints" % project_key.upper()))


@app.post("/api/projects/{project_key}/members")
async def api_add_member(request: Request, project_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    form = await request.form()
    add_project_member(int(project["id"]), str(form.get("login") or ""), str(form.get("role") or "member"))
    return redirect(str(request.headers.get("referer") or "/p/%s/settings" % project["key"]))


@app.post("/api/projects/{project_key}/members/{member_id}")
async def api_update_member(request: Request, project_key: str, member_id: int) -> RedirectResponse:
    user = await validate_csrf_request(request)
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    form = await request.form()
    try:
        update_project_member(int(project["id"]), member_id, str(form.get("role") or "member"))
    except HTTPException as exc:
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            return redirect("/p/%s/settings?error=last_admin" % project["key"])
        raise
    return redirect("/p/%s/settings" % project["key"])


@app.post("/api/projects/{project_key}/members/{member_id}/remove")
async def api_remove_member(request: Request, project_key: str, member_id: int) -> RedirectResponse:
    user = await validate_csrf_request(request)
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    try:
        remove_project_member(int(project["id"]), member_id)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            return redirect("/p/%s/settings?error=last_admin" % project["key"])
        raise
    return redirect("/p/%s/settings" % project["key"])


@app.post("/api/projects/{project_key}/github")
async def api_project_github(request: Request, project_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    project = get_project_by_key(project_key)
    require_project_admin(user, int(project["id"]))
    form = await request.form()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE projects
            SET github_repo_full_name = ?, github_installation_id = ?
            WHERE id = ?
            """,
            (
                normalize_github_repo(str(form.get("repo") or "")) or None,
                str(form.get("installation_id") or "").strip() or None,
                project["id"],
            ),
        )
    return redirect("/integrations/github")


@app.post("/api/tickets")
async def api_create_ticket(request: Request) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    assignee_id = parse_optional_int(form.get("assignee_id"))
    sprint_id = parse_optional_int(form.get("sprint_id"))
    story_points = parse_optional_int(form.get("story_points")) or 0
    ticket = create_ticket(
        user,
        str(form.get("project_key") or ""),
        str(form.get("title") or ""),
        str(form.get("description") or ""),
        str(form.get("priority") or "Medium"),
        str(form.get("ticket_type") or "Task"),
        assignee_id,
        sprint_id,
        story_points,
    )
    await publish_ticket_event(ticket, "ticket_created")
    return redirect("/t/%s" % ticket["key"])


@app.get("/t/{ticket_key}", response_class=HTMLResponse)
async def ticket_page(request: Request, ticket_key: str) -> HTMLResponse:
    user = require_page_user(request)
    bundle = get_ticket_bundle(ticket_key)
    require_project_access(user, int(bundle["ticket"]["project_id"]))
    members = project_members(int(bundle["ticket"]["project_id"]))
    for comment in bundle["comments"]:
        comment["body_html"] = render_mentions(str(comment.get("body") or ""), members)
    project = get_project_by_key(str(bundle["ticket"]["project_key"]))
    sprints = [
        sprint
        for sprint in list_project_sprints(int(project["id"]))
        if sprint.get("status") != "closed" or sprint.get("id") == bundle["ticket"].get("sprint_id")
    ]
    return render(
        request,
        "ticket.html",
        {
            **bundle,
            "members": members,
            "statuses": project_statuses(project),
            "ticket_types": project_ticket_types(project),
            "sprints": sprints,
            "link_types": TICKET_LINK_TYPES,
        },
    )


@app.get("/api/projects/{project_key}/tickets/search")
async def api_search_project_tickets(request: Request, project_key: str, q: str = "", exclude: str = "") -> JSONResponse:
    user = require_page_user(request)
    project = get_project_by_key(project_key)
    require_project_access(user, int(project["id"]))
    tickets = search_linkable_tickets(int(project["id"]), exclude, q)
    return JSONResponse({"tickets": tickets})


@app.get("/api/projects/{project_key}/users/search")
async def api_search_project_users(request: Request, project_key: str, q: str = "") -> JSONResponse:
    user = require_page_user(request)
    project = get_project_by_key(project_key)
    require_project_access(user, int(project["id"]))
    users = search_project_users(int(project["id"]), q)
    return JSONResponse({"users": users})


@app.post("/api/tickets/{ticket_key}")
async def api_update_ticket_form(request: Request, ticket_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    assignee_present = "assignee_id" in form
    ticket = update_ticket(
        user,
        ticket_key,
        title=str(form.get("title")) if "title" in form else None,
        description=str(form.get("description")) if "description" in form else None,
        ticket_type=str(form.get("ticket_type")) if "ticket_type" in form else None,
        status_value=str(form.get("status")) if "status" in form else None,
        priority=str(form.get("priority")) if "priority" in form else None,
        story_points=parse_optional_int(form.get("story_points")),
        story_points_touched="story_points" in form,
        assignee_id=parse_optional_int(form.get("assignee_id")),
        assignee_touched=assignee_present,
        sprint_id=parse_optional_int(form.get("sprint_id")),
        sprint_touched="sprint_id" in form,
    )
    await publish_ticket_event(ticket)
    return redirect(str(request.headers.get("referer") or "/t/%s" % ticket_key))


@app.post("/api/tickets/{ticket_key}/quick-update")
async def api_quick_update_ticket(request: Request, ticket_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    ticket = update_ticket(
        user,
        ticket_key,
        ticket_type=str(form.get("ticket_type")) if "ticket_type" in form else None,
        status_value=str(form.get("status")) if "status" in form else None,
        priority=str(form.get("priority")) if "priority" in form else None,
        story_points=parse_optional_int(form.get("story_points")),
        story_points_touched="story_points" in form,
        assignee_id=parse_optional_int(form.get("assignee_id")),
        assignee_touched="assignee_id" in form,
        sprint_id=parse_optional_int(form.get("sprint_id")),
        sprint_touched="sprint_id" in form,
    )
    comment = str(form.get("comment") or "").strip()
    if comment:
        add_comment(user, ticket_key, comment)
        ticket = get_ticket_bundle(ticket_key)["ticket"]
    await publish_ticket_event(ticket, "ticket_changed")
    return redirect(str(request.headers.get("referer") or "/t/%s" % ticket_key))


@app.patch("/api/tickets/{ticket_key}")
async def api_update_ticket_json(request: Request, ticket_key: str) -> JSONResponse:
    user = await validate_csrf_request(request)
    try:
        payload = await request.json()
    except JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body") from exc
    ticket = update_ticket(
        user,
        ticket_key,
        title=payload.get("title"),
        description=payload.get("description"),
        ticket_type=payload.get("ticket_type"),
        status_value=payload.get("status"),
        priority=payload.get("priority"),
        story_points=parse_optional_int(payload.get("story_points")),
        story_points_touched="story_points" in payload,
        assignee_id=parse_optional_int(payload.get("assignee_id")),
        assignee_touched="assignee_id" in payload,
        sprint_id=parse_optional_int(payload.get("sprint_id")),
        sprint_touched="sprint_id" in payload,
        position_after_key=payload.get("position_after_key"),
        position_touched="position_after_key" in payload,
    )
    action = await publish_ticket_event(ticket)
    return JSONResponse({**ticket, "_action": action})


@app.post("/api/tickets/{ticket_key}/comments")
async def api_add_comment(request: Request, ticket_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    add_comment(user, ticket_key, str(form.get("body") or ""))
    await publish_ticket_event(get_ticket_bundle(ticket_key)["ticket"], "ticket_commented")
    return redirect("/t/%s" % ticket_key)


@app.post("/api/tickets/{ticket_key}/links")
async def api_link_ticket(request: Request, ticket_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    link_ticket(
        user,
        ticket_key,
        str(form.get("target_key") or ""),
        str(form.get("link_type") or "relates"),
    )
    await publish_ticket_event(get_ticket_bundle(ticket_key)["ticket"], "ticket_linked")
    return redirect("/t/%s" % ticket_key)


@app.post("/api/tickets/{ticket_key}/links/{link_id}/delete")
async def api_unlink_ticket(request: Request, ticket_key: str, link_id: int) -> RedirectResponse:
    user = await validate_csrf_request(request)
    unlink_ticket(user, ticket_key, link_id)
    await publish_ticket_event(get_ticket_bundle(ticket_key)["ticket"], "ticket_unlinked")
    return redirect("/t/%s" % ticket_key)


@app.post("/api/tickets/{ticket_key}/links/{link_id}")
async def api_update_ticket_link(request: Request, ticket_key: str, link_id: int) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    update_ticket_link(
        user,
        ticket_key,
        link_id,
        str(form.get("target_key") or ""),
        str(form.get("link_type") or "relates"),
    )
    await publish_ticket_event(get_ticket_bundle(ticket_key)["ticket"], "ticket_linked")
    return redirect("/t/%s" % ticket_key)


@app.post("/api/tickets/{ticket_key}/close")
async def api_close_ticket(request: Request, ticket_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    ticket = close_ticket(user, ticket_key)
    await publish_ticket_event(ticket)
    return redirect("/t/%s" % ticket_key)


@app.post("/api/tickets/{ticket_key}/reopen")
async def api_reopen_ticket(request: Request, ticket_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    ticket = reopen_ticket(user, ticket_key)
    await publish_ticket_event(ticket)
    return redirect("/t/%s" % ticket_key)


@app.post("/api/tickets/{ticket_key}/watch")
async def api_watch_ticket(request: Request, ticket_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    set_watch(user, ticket_key, str(form.get("watch") or "true").lower() == "true")
    await publish_ticket_event(get_ticket_bundle(ticket_key)["ticket"])
    return redirect("/t/%s" % ticket_key)


@app.get("/settings/mcp", response_class=HTMLResponse)
async def mcp_settings(request: Request) -> HTMLResponse:
    user = require_page_user(request)
    return render(request, "settings_mcp.html", {"tokens": list_mcp_tokens(int(user["id"]))})


@app.post("/settings/mcp/tokens", response_class=HTMLResponse)
async def create_mcp_token_page(request: Request) -> HTMLResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    created = create_mcp_token(user, str(form.get("name") or "MCP token"))
    return render(
        request,
        "settings_mcp.html",
        {"tokens": list_mcp_tokens(int(user["id"])), "created_token": created["token"]},
    )


@app.post("/settings/mcp/tokens/{token_id}/revoke")
async def revoke_mcp_token_page(request: Request, token_id: int) -> RedirectResponse:
    user = await validate_csrf_request(request)
    revoke_mcp_token(int(user["id"]), token_id)
    return redirect("/settings/mcp")


@app.get("/settings/notifications", response_class=HTMLResponse)
async def notification_settings(request: Request) -> HTMLResponse:
    user = require_page_user(request)
    return render(
        request,
        "settings_notifications.html",
        {
            "prefs": notification_preferences(int(user["id"])),
            "telegram_link": get_telegram_link(int(user["id"])),
        },
    )


@app.post("/api/me/notification-preferences")
async def api_notification_preferences(request: Request) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    update_notification_preferences(
        int(user["id"]),
        email_enabled=False,
        telegram_enabled=str(form.get("telegram_enabled") or "").lower() == "true",
    )
    return redirect("/settings/notifications")


@app.post("/api/me/notifications/test")
async def api_test_notification(request: Request) -> RedirectResponse:
    user = await validate_csrf_request(request)
    create_test_notification(user)
    return redirect("/settings/notifications")


@app.post("/api/me/telegram/link", response_class=HTMLResponse)
async def api_telegram_link(request: Request) -> HTMLResponse:
    user = await validate_csrf_request(request)
    token = create_telegram_link_token(user)
    return render(
        request,
        "settings_notifications.html",
        {
            "prefs": notification_preferences(int(user["id"])),
            "telegram_link": get_telegram_link(int(user["id"])),
            "telegram_token": token["token"],
        },
    )


@app.post("/api/me/telegram/unlink")
async def api_telegram_unlink(request: Request) -> RedirectResponse:
    user = await validate_csrf_request(request)
    unlink_telegram(int(user["id"]))
    return redirect("/settings/notifications")


@app.delete("/api/me/telegram/link")
async def api_telegram_unlink_delete(request: Request) -> JSONResponse:
    user = await validate_csrf_request(request)
    unlink_telegram(int(user["id"]))
    return JSONResponse({"ok": True})


@app.patch("/api/me/notification-preferences")
async def api_notification_preferences_patch(request: Request) -> JSONResponse:
    user = await validate_csrf_request(request)
    payload = await request.json()
    prefs = update_notification_preferences(
        int(user["id"]),
        False,
        bool(payload.get("telegram_enabled")),
    )
    return JSONResponse(prefs)


@app.get("/integrations/github", response_class=HTMLResponse)
async def github_settings(request: Request) -> HTMLResponse:
    user = require_page_user(request)
    return render(request, "integrations_github.html", {"projects": list_projects(user)})


@app.post("/integrations/github/webhook")
async def github_webhook(request: Request) -> JSONResponse:
    body = await request.body()
    if not settings.github_webhook_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub webhook secret is not configured")
    signature = request.headers.get("x-hub-signature-256", "")
    if not verify_hmac_signature(settings.github_webhook_secret, body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid GitHub signature")
    event = request.headers.get("x-github-event", "")
    delivery_id = request.headers.get("x-github-delivery", "")
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid GitHub webhook JSON") from exc
    result = handle_webhook(event, delivery_id, payload)
    # GitHub webhook linking is stored by the data layer. Clients will see the
    # resulting GitHub links on refresh; per-ticket live publication is handled
    # for direct RoundTable mutations where we already have the changed ticket.
    return JSONResponse(result)


@app.post("/integrations/telegram/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    if not settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram webhook secret is not configured")
    provided = request.headers.get("x-telegram-bot-api-secret-token", "")
    if not secrets.compare_digest(provided, settings.telegram_webhook_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram webhook secret")
    try:
        payload = await request.json()
    except JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Telegram webhook JSON") from exc
    message = payload.get("message") or {}
    text = message.get("text") or ""
    chat = message.get("chat") or {}
    from_user = message.get("from") or {}
    if text.startswith("/start "):
        token = text.split(" ", 1)[1].strip()
        linked = consume_telegram_link_token(
            token,
            str(chat.get("id") or ""),
            str(from_user.get("username") or ""),
        )
        return JSONResponse({"ok": True, "linked": linked})
    return JSONResponse({"ok": True, "linked": False})


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> Response:
    result = await handle_mcp(request, on_ticket_changed=publish_ticket_event)
    if result is None:
        # JSON-RPC notifications get an empty 202 (no response body).
        return Response(status_code=status.HTTP_202_ACCEPTED)
    # Streamable HTTP transport: when the client advertises text/event-stream,
    # frame the single JSON-RPC reply as one SSE event so SSE-style MCP clients
    # parse it. Otherwise fall back to a plain JSON body.
    accept = request.headers.get("accept", "")
    if "text/event-stream" in accept:
        body = "event: message\ndata: %s\n\n" % json.dumps(result)

        async def event_stream():
            yield body

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    return JSONResponse(result)


@app.get("/mcp")
async def mcp_endpoint_get() -> Response:
    # We have no server-initiated messages, so the optional GET SSE stream of
    # the Streamable HTTP transport is not offered. 405 is the spec-compliant
    # answer and tells clients to use POST only.
    return Response(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, headers={"Allow": "POST"})


def parse_optional_int(value: Any) -> Optional[int]:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expected an integer value") from exc
