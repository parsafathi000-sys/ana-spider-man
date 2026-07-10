"""
Web API Router - authentication, subscription, and session endpoints.

This module performs NO server-side HTML rendering.
The UI is a static single-page app served from main.py (static/index.html).
Only the API endpoints that the static frontend depends on live here.
"""
import asyncio
import hashlib
import secrets

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, Response, JSONResponse
from pydantic import BaseModel

from config import logger, SESSION_COOKIE, SESSION_TTL, AUTH
from core.state import (
    LINKS, LINKS_LOCK, SUBS, SUBS_LOCK,
    SESSIONS, SESSIONS_LOCK,
    is_link_allowed,
)
from services.xray_service import generate_vless_link as svc_generate_vless_link

router = APIRouter()

# ── Public Subscription API ──────────────────────────────────────────────────
@router.get("/api/public/sub/{uuid_key}")
async def public_subscription(uuid_key: str, request: Request, pw: str = None):
    async with SUBS_LOCK:
        sub = SUBS.get(uuid_key)
    if not sub:
        raise HTTPException(status_code=404, detail="اشتراک یافت نشد")
    if sub.get("password") and pw != sub.get("password"):
        return HTMLResponse(
            "<html><body><h1>رمز عبور مورد نیاز</h1>"
            "<form method='get'><input name='pw' placeholder='رمز عبور'>"
            "<button type='submit'>ورود</button></form></body></html>"
        )
    return HTMLResponse(
        f"<html><body><h1>اشتراک {uuid_key}</h1>"
        "<p>Welcome to Spider Panel</p></body></html>"
    )


@router.get("/sub-group/{uuid_key}")
async def subscription_group(uuid_key: str, pw: str = None):
    async with SUBS_LOCK:
        sub = SUBS.get(uuid_key)
    if not sub:
        raise HTTPException(status_code=404, detail="اشتراک یافت نشد")
    if sub.get("password") and pw != sub.get("password"):
        raise HTTPException(status_code=401, detail="رمز عبور اشتباه است")
    links = []
    for link_id in sub.get("links", []):
        async with LINKS_LOCK:
            link = LINKS.get(link_id)
        if link and is_link_allowed(link):
            try:
                config = svc_generate_vless_link(
                    uuid=link_id,
                    remark=link.get("label", "Spider"),
                    inbound_id=link.get("inbound_id"),
                    user=link,
                )
                links.append(config)
            except Exception:
                pass
    return Response(content="\n".join(links), media_type="text/plain")


# ── Login / Logout / Session API ─────────────────────────────────────────────
class LoginRequest(BaseModel):
    password: str = ""


@router.post("/api/login")
async def api_login(request: Request, body: LoginRequest):
    expected_hash = AUTH.get("password_hash")
    if expected_hash:
        provided_hash = hashlib.sha256(
            f"{body.password}{AUTH.get('secret', 'spider-panel-secret-key-v2')}".encode()
        ).hexdigest()
        if provided_hash != expected_hash:
            return JSONResponse({"detail": "رمز عبور اشتباه است"}, status_code=401)
    token = secrets.token_urlsafe(32)
    async with SESSIONS_LOCK:
        SESSIONS[token] = asyncio.get_event_loop().time() + SESSION_TTL
    response = JSONResponse({"success": True})
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        max_age=SESSION_TTL,
        samesite="lax",
    )
    return response


@router.post("/api/logout")
async def api_logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        async with SESSIONS_LOCK:
            SESSIONS.pop(token, None)
    response = JSONResponse({"success": True})
    response.delete_cookie(SESSION_COOKIE)
    return response


@router.get("/api/me")
async def api_me(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        async with SESSIONS_LOCK:
            exp = SESSIONS.get(token)
            if exp and exp > asyncio.get_event_loop().time():
                return {"authenticated": True}
    return {"authenticated": False}
