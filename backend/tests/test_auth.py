import logging
import re
from datetime import timedelta
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.auth.utils import digest, now
from app.auth.validators import normalize_phone
from app.auth.dependencies import require_admin
from app.auth.endpoints import router
from app.core.db import Base, get_session
from app.core.errors import register_exception_handlers
from app.auth.models import AuthSession, LoginCode, User

PHONE = '+375291234567'
HEADERS = {'X-CSRF-Token': 'login', 'Origin': 'http://localhost:5173'}


@pytest.fixture
def context(caplog):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)

    @app.get('/api/admin')
    def admin(user=Depends(require_admin)):
        return {'role': user.role}

    def session():
        with Session(engine, expire_on_commit=False) as db:
            yield db
    app.dependency_overrides[get_session] = session
    caplog.set_level(logging.INFO, logger='tech_transport.sms_stub')
    try:
        with TestClient(app) as client, Session(engine) as db:
            yield client, db, caplog
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def send(context):
    client, db, caplog = context
    response = client.post('/api/auth/code', json={'phone': PHONE}, headers=HEADERS)
    assert response.status_code == 200
    code = re.findall(r'code=(\d{6})', caplog.text)[-1]
    assert code not in response.text
    db.expire_all()
    stored = db.get(LoginCode, PHONE).code_hash
    assert code not in stored
    return code


def login(context):
    code = send(context)
    response = context[0].post('/api/auth/verify', json={'phone': PHONE, 'code': code}, headers=HEADERS)
    assert response.status_code == 200
    assert 'HttpOnly' in response.headers['set-cookie']
    assert 'SameSite=lax' in response.headers['set-cookie']
    return {'X-CSRF-Token': response.json()['csrf_token']}


@pytest.mark.parametrize('value', ['+375 (29) 123-45-67', '80291234567', '291234567', '375291234567'])
def test_phone_normalization(value):
    assert normalize_phone(value) == PHONE


@pytest.mark.parametrize('value', ['+74951234567', '+375171234567', 'abc291234567', '+37529123456'])
def test_invalid_phone(value):
    with pytest.raises(ValueError):
        normalize_phone(value)


def test_profile_refresh_logout_and_replay(context):
    client, db, _ = context
    assert client.get('/api/auth/me').status_code == 401
    headers = login(context)
    assert client.get('/api/auth/me').headers['cache-control'] == 'no-store'
    assert client.patch('/api/auth/me', json={'display_name': 'Owner'}).status_code == 403
    assert client.patch('/api/auth/me', json={'display_name': ' Owner '}, headers=headers).json()['user']['display_name'] == 'Owner'
    assert client.patch('/api/auth/me', json={'phone': PHONE}, headers=headers).status_code == 422
    assert client.patch('/api/auth/me', json={'display_name': '  '}, headers=headers).status_code == 422
    old_cookie = client.cookies.get('tt_session')
    refreshed = client.post('/api/auth/refresh', headers=headers)
    assert refreshed.status_code == 200
    assert old_cookie != client.cookies.get('tt_session')
    db.expire_all()
    assert db.get(AuthSession, digest(old_cookie)) is None
    headers = {'X-CSRF-Token': refreshed.json()['csrf_token']}
    assert client.post('/api/auth/logout', headers=headers).status_code == 204
    assert client.get('/api/auth/me').status_code == 401
    client.cookies.set('tt_session', old_cookie)
    assert client.get('/api/auth/me').status_code == 401


def test_limits_expiry_and_single_use(context):
    client, db, _ = context
    code = send(context)
    assert client.post('/api/auth/code', json={'phone': PHONE}, headers=HEADERS).status_code == 429
    wrong = '000000' if code != '000000' else '111111'
    for _ in range(5):
        assert client.post('/api/auth/verify', json={'phone': PHONE, 'code': wrong}, headers=HEADERS).status_code == 400
    assert client.post('/api/auth/verify', json={'phone': PHONE, 'code': code}, headers=HEADERS).status_code == 400
    db.expire_all()
    challenge = db.get(LoginCode, PHONE)
    assert challenge.attempts == 5
    challenge.sent_at = now() - timedelta(minutes=2)
    db.commit()
    code = send(context)
    challenge = db.get(LoginCode, PHONE)
    challenge.expires_at = now() - timedelta(seconds=1)
    db.commit()
    assert client.post('/api/auth/verify', json={'phone': PHONE, 'code': code}, headers=HEADERS).status_code == 400
    challenge.sent_at = now() - timedelta(minutes=2)
    db.commit()
    code = send(context)
    payload = {'phone': PHONE, 'code': code}
    assert client.post('/api/auth/verify', json=payload, headers=HEADERS).status_code == 200
    assert client.post('/api/auth/verify', json=payload, headers=HEADERS).status_code == 400
    assert len(db.scalars(select(User)).all()) == 1


def test_csrf_and_disabled_user(context):
    client, db, _ = context
    assert client.post('/api/auth/code', json={'phone': PHONE}).status_code == 403
    assert client.post('/api/auth/code', json={'phone': PHONE}, headers={**HEADERS, 'Origin': 'https://evil.example'}).status_code == 403
    headers = login(context)
    assert client.post('/api/auth/logout', headers={**headers, 'Origin': 'https://evil.example'}).status_code == 403
    assert client.get('/api/admin').status_code == 403
    user = db.scalar(select(User))
    user.role = 'admin'
    db.commit()
    assert client.get('/api/admin').status_code == 200
    user.is_active = False
    challenge = db.get(LoginCode, PHONE)
    challenge.sent_at = now() - timedelta(minutes=2)
    db.commit()
    assert client.get('/api/auth/me').status_code == 403
    assert client.post('/api/auth/refresh', headers=headers).status_code == 403
    code = send(context)
    assert client.post('/api/auth/verify', json={'phone': PHONE, 'code': code}, headers=HEADERS).status_code == 403
    assert len(db.scalars(select(User)).all()) == 1


def test_expired_session(context):
    client, db, _ = context
    headers = login(context)
    session = db.scalar(select(AuthSession))
    session.expires_at = now() - timedelta(seconds=1)
    db.commit()
    assert client.get('/api/auth/me').status_code == 401
    assert client.post('/api/auth/refresh', headers=headers).status_code == 401
