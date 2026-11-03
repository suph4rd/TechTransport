import hashlib
import logging
import secrets
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.db import get_session
from app.auth.models import AuthSession, LoginCode, User
from app.auth.schemas import PhoneInput, VerifyInput, ProfileInput
from app.auth.dependencies import current_session, login_csrf
from app.auth.utils import COOKIE, aware, now, profile, issue_session, lock_phone

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger("tech_transport.sms_stub")


@router.post("/code", dependencies=[Depends(login_csrf)])
def request_code(data: PhoneInput, db: Session = Depends(get_session)):
    lock_phone(db, data.phone)
    challenge = db.get(LoginCode, data.phone)
    timestamp = now()
    if challenge and aware(challenge.sent_at) + timedelta(minutes=1) > timestamp:
        raise HTTPException(429, "Повторный код можно запросить через минуту", headers={"Retry-After": "60"})
    code = f"{secrets.randbelow(1000000):06d}"
    salt = secrets.token_hex(16)
    hashed = salt + ":" + hashlib.scrypt(code.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=32).hex()
    if challenge is None:
        challenge = LoginCode(phone=data.phone)
        db.add(challenge)
    challenge.code_hash = hashed
    challenge.sent_at = timestamp
    challenge.expires_at = timestamp + timedelta(minutes=5)
    challenge.attempts = 0
    challenge.consumed = False
    db.commit()
    logger.info("LOCAL SMS phone=%s code=%s", data.phone, code)
    return {"expires_in": 300, "retry_after": 60}


@router.post("/verify", dependencies=[Depends(login_csrf)])
def verify_code(data: VerifyInput, response: Response, db: Session = Depends(get_session)):
    lock_phone(db, data.phone)
    challenge = db.get(LoginCode, data.phone)
    if not challenge or challenge.consumed or aware(challenge.expires_at) <= now() or challenge.attempts >= 5:
        raise HTTPException(400, "Код недействителен. Запросите новый код")
    salt, stored = challenge.code_hash.split(":")
    actual = hashlib.scrypt(data.code.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=32).hex()
    challenge.attempts += 1
    if not secrets.compare_digest(stored, actual):
        db.commit()  # Failed attempts must survive the HTTP error rollback.
        raise HTTPException(400, "Неверный код")
    challenge.consumed = True
    user = db.scalar(select(User).where(User.phone == data.phone))
    if user and not user.is_active:
        db.commit()
        raise HTTPException(403, "Аккаунт отключён")
    if user is None:
        user = User(phone=data.phone)
        db.add(user)
        db.flush()
    return issue_session(db, user, response)


@router.get("/me")
def me(response: Response, auth=Depends(current_session)):
    response.headers["Cache-Control"] = "no-store"
    return {"user": profile(auth[1]), "csrf_token": auth[0].csrf_token}


@router.patch("/me")
def update_profile(data: ProfileInput, response: Response, auth=Depends(current_session), db: Session = Depends(get_session)):
    auth[1].display_name = data.display_name
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"user": profile(auth[1]), "csrf_token": auth[0].csrf_token}


@router.post("/refresh")
def refresh(response: Response, auth=Depends(current_session), db: Session = Depends(get_session)):
    db.delete(auth[0])
    return issue_session(db, auth[1], response)


@router.post("/logout", status_code=204)
def logout(response: Response, auth=Depends(current_session), db: Session = Depends(get_session)):
    db.delete(auth[0])
    db.commit()
    response.delete_cookie(COOKIE, path="/api", httponly=True, samesite="lax", secure=get_settings().cookie_secure)
    response.headers["Cache-Control"] = "no-store"
