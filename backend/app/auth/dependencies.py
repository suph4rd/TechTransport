import secrets
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.db import get_session
from app.auth.models import AuthSession, User
from app.auth.utils import COOKIE, aware, digest, now


def check_origin(request: Request):
    origin = request.headers.get("origin")
    allowed = get_settings().allowed_origins.split(",")
    if origin is not None and origin not in allowed:
        raise HTTPException(403, "Недопустимый источник запроса")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Недопустимый источник запроса")


def login_csrf(request: Request):
    check_origin(request)
    # A custom header requires a CORS preflight; cross-origin access is disabled.
    if request.headers.get("x-csrf-token") != "login":
        raise HTTPException(403, "Отсутствует защита CSRF")


def current_session(request: Request, db: Session = Depends(get_session)):
    token = request.cookies.get(COOKIE, "")
    statement = select(AuthSession).where(AuthSession.token_hash == digest(token))
    if request.method != "GET":
        statement = statement.with_for_update()
    session = db.scalar(statement)
    if not session or aware(session.expires_at) <= now():
        raise HTTPException(401, "Войдите в аккаунт")
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(403, "Аккаунт отключён")
    if request.method != "GET":
        check_origin(request)
        if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), session.csrf_token):
            raise HTTPException(403, "Неверный токен CSRF")
    return session, user


def require_admin(auth=Depends(current_session)):
    if auth[1].role != "admin":
        raise HTTPException(403, "Требуются права администратора")
    return auth[1]
