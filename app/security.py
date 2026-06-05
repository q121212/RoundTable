import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Cookie, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from .db import get_conn, row_to_dict, utcnow


SESSION_COOKIE = "roundtable_session"


def new_token(prefix: str = "") -> str:
    token = secrets.token_urlsafe(32)
    if prefix:
        return prefix + token
    return token


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_hmac_signature(secret: str, body: bytes, signature_header: str) -> bool:
    if not secret or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def create_session(user_id: int) -> Dict[str, str]:
    token = new_token()
    csrf = new_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).replace(microsecond=0).isoformat()
    now = utcnow()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO sessions (user_id, token_hash, csrf_token, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, hash_token(token), csrf, expires_at, now),
        )
    return {"token": token, "csrf": csrf, "expires_at": expires_at}


def delete_session(token: Optional[str]) -> None:
    if not token:
        return
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (hash_token(token),))


def get_user_by_session(token: Optional[str]) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    now = utcnow()
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT users.*, sessions.csrf_token, sessions.expires_at
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.expires_at > ?
            """,
            (hash_token(token), now),
        ).fetchone()
        return row_to_dict(row)


def login_response(user_id: int, url: str = "/") -> RedirectResponse:
    session = create_session(user_id)
    response = RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        SESSION_COOKIE,
        session["token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
    )
    return response


async def current_user(
    request: Request, roundtable_session: Optional[str] = Cookie(default=None)
) -> Dict[str, Any]:
    user = get_user_by_session(roundtable_session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    request.state.user = user
    return user


async def current_user_or_none(
    request: Request, roundtable_session: Optional[str] = Cookie(default=None)
) -> Optional[Dict[str, Any]]:
    user = get_user_by_session(roundtable_session)
    request.state.user = user
    return user


def require_login_page(request: Request) -> Dict[str, Any]:
    token = request.cookies.get(SESSION_COOKIE)
    user = get_user_by_session(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    request.state.user = user
    return user


async def validate_csrf_request(request: Request) -> Dict[str, Any]:
    token = request.cookies.get(SESSION_COOKIE)
    user = get_user_by_session(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    provided = request.headers.get("x-csrf-token")
    if not provided:
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            provided = str(form.get("csrf_token") or "")
    if not provided or not hmac.compare_digest(provided, user["csrf_token"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
    request.state.user = user
    return user


async def require_csrf(request: Request) -> None:
    await validate_csrf_request(request)


def require_admin(user: Dict[str, Any]) -> None:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
