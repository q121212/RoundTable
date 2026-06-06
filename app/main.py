import asyncio
import json
import logging
import secrets
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .db import PRIORITIES, TICKET_STATUSES, get_conn, init_db
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
    create_telegram_link_token,
    create_test_notification,
    create_ticket,
    delete_project,
    get_project_by_key,
    get_telegram_link,
    get_ticket_bundle,
    list_mcp_tokens,
    list_projects,
    notification_preferences,
    normalize_github_repo,
    project_members,
    remove_project_member,
    reopen_ticket,
    require_project_access,
    require_project_admin,
    revoke_mcp_token,
    set_watch,
    sync_configured_admin_roles,
    unlink_telegram,
    update_notification_preferences,
    update_project_member,
    update_project_settings,
    update_ticket,
    upsert_user,
)


logger = logging.getLogger("roundtable")


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
        "statuses": TICKET_STATUSES,
        "priorities": PRIORITIES,
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


async def publish_ticket_event(ticket: Dict[str, Any], event_name: str = "ticket_changed") -> None:
    if not ticket:
        return
    await project_events.publish(
        str(ticket["project_key"]),
        {"event": event_name, "ticket": ticket},
    )


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
    board = board_for_project(project_key, user)
    members = project_members(int(board["project"]["id"]))
    return render(request, "board.html", {**board, "members": members})


@app.get("/events/projects/{project_key}")
async def project_events_stream(request: Request, project_key: str) -> StreamingResponse:
    user = require_page_user(request)
    project = get_project_by_key(project_key)
    require_project_access(user, int(project["id"]))

    async def stream() -> AsyncIterator[str]:
        queue = await project_events.subscribe(str(project["key"]))
        try:
            yield sse_message("ready", {"project_key": project["key"]})
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=25)
                    yield sse_message(str(item.get("event") or "ticket_changed"), item)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                if await request.is_disconnected():
                    break
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
        {"project": project, "members": members, "admin_count": admin_count, "can_delete": True, "error": error},
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
    )
    return redirect("/p/%s/settings" % project_key.upper())


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
    ticket = create_ticket(
        user,
        str(form.get("project_key") or ""),
        str(form.get("title") or ""),
        str(form.get("description") or ""),
        str(form.get("priority") or "Medium"),
        assignee_id,
    )
    await publish_ticket_event(ticket, "ticket_created")
    return redirect("/t/%s" % ticket["key"])


@app.get("/t/{ticket_key}", response_class=HTMLResponse)
async def ticket_page(request: Request, ticket_key: str) -> HTMLResponse:
    user = require_page_user(request)
    bundle = get_ticket_bundle(ticket_key)
    require_project_access(user, int(bundle["ticket"]["project_id"]))
    members = project_members(int(bundle["ticket"]["project_id"]))
    return render(request, "ticket.html", {**bundle, "members": members})


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
        status_value=str(form.get("status")) if "status" in form else None,
        priority=str(form.get("priority")) if "priority" in form else None,
        assignee_id=parse_optional_int(form.get("assignee_id")),
        assignee_touched=assignee_present,
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
        status_value=str(form.get("status")) if "status" in form else None,
        priority=str(form.get("priority")) if "priority" in form else None,
        assignee_id=parse_optional_int(form.get("assignee_id")),
        assignee_touched="assignee_id" in form,
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
    payload = await request.json()
    ticket = update_ticket(
        user,
        ticket_key,
        title=payload.get("title"),
        description=payload.get("description"),
        status_value=payload.get("status"),
        priority=payload.get("priority"),
        assignee_id=payload.get("assignee_id"),
        assignee_touched="assignee_id" in payload,
    )
    await publish_ticket_event(ticket)
    return JSONResponse(ticket)


@app.post("/api/tickets/{ticket_key}/comments")
async def api_add_comment(request: Request, ticket_key: str) -> RedirectResponse:
    user = await validate_csrf_request(request)
    form = await request.form()
    add_comment(user, ticket_key, str(form.get("body") or ""))
    await publish_ticket_event(get_ticket_bundle(ticket_key)["ticket"], "ticket_commented")
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
    if settings.github_webhook_secret:
        signature = request.headers.get("x-hub-signature-256", "")
        if not verify_hmac_signature(settings.github_webhook_secret, body, signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid GitHub signature")
    event = request.headers.get("x-github-event", "")
    delivery_id = request.headers.get("x-github-delivery", "")
    payload = json.loads(body.decode("utf-8") or "{}")
    result = handle_webhook(event, delivery_id, payload)
    return JSONResponse(result)


@app.post("/integrations/telegram/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    if settings.telegram_webhook_secret:
        provided = request.headers.get("x-telegram-bot-api-secret-token", "")
        if not secrets.compare_digest(provided, settings.telegram_webhook_secret):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram webhook secret")
    payload = await request.json()
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
    result = await handle_mcp(request)
    if result is None:
        # JSON-RPC notifications get an empty 202 (no response body).
        return Response(status_code=status.HTTP_202_ACCEPTED)
    return JSONResponse(result)


def parse_optional_int(value: Any) -> Optional[int]:
    if value is None or str(value).strip() == "":
        return None
    return int(value)
