import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from app.core.config import get_settings
from app.auth.models import AuthSession

COOKIE = "tt_session"
SESSION_SECONDS = 7 * 24 * 3600


def now():
    return datetime.now(timezone.utc)


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def digest(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


def profile(user):
    return {"id": user.id, "phone": user.phone, "display_name": user.display_name,
            "role": user.role, "created_at": user.created_at}


def issue_session(db, user, response):
    token = secrets.token_urlsafe(32)
    session = AuthSession(token_hash=digest(token), user_id=user.id,
                          csrf_token=secrets.token_urlsafe(32), expires_at=now() + timedelta(seconds=SESSION_SECONDS))
    db.add(session)
    db.commit()
    response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=get_settings().cookie_secure, samesite="lax", path="/api")
    response.headers["Cache-Control"] = "no-store"
    return {"user": profile(user), "csrf_token": session.csrf_token}


def lock_phone(db, phone):
    # Serializes requests even before the first challenge row exists.
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"),
                   {"key": int.from_bytes(hashlib.sha256(phone.encode()).digest()[:8], "big", signed=True)})
