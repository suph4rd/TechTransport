from fastapi import Query
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from app.core.db import get_session
from app.main import app


def test_live_and_error_contract():
    with TestClient(app) as client:
        assert client.get('/api/health/live').json() == {'status': 'ok'}
        response = client.get('/missing')
        assert response.status_code == 404
        assert response.json()['error']['code'] == 'http_404'


def test_database_failure_does_not_expose_credentials():
    class BrokenSession:
        def execute(self, statement):
            raise OperationalError('secret-query', {}, Exception('secret-password'))

    app.dependency_overrides[get_session] = lambda: BrokenSession()
    try:
        with TestClient(app) as client:
            response = client.get('/api/health/ready')
            assert response.status_code == 503
            assert response.json()['error']['code'] == 'database_unavailable'
            assert 'secret' not in response.text
    finally:
        app.dependency_overrides.clear()


def test_validation_does_not_echo_input():
    from fastapi import FastAPI
    from fastapi.exceptions import RequestValidationError
    from app.core.errors import validation_error
    test_app = FastAPI()
    test_app.add_exception_handler(RequestValidationError, validation_error)

    @test_app.get('/validate')
    def validate(value: int = Query()):
        return value

    with TestClient(test_app) as client:
        response = client.get('/validate?value=secret-code')
        assert response.status_code == 422
        assert response.json()['error']['code'] == 'validation_error'
        assert 'secret-code' not in response.text


def test_database_ready():
    class HealthySession:
        def execute(self, statement):
            assert str(statement) == 'SELECT 1'

    app.dependency_overrides[get_session] = lambda: HealthySession()
    try:
        with TestClient(app) as client:
            response = client.get('/api/health/ready')
            assert response.status_code == 200
            assert response.json() == {'status': 'ok', 'database': 'ok'}
    finally:
        app.dependency_overrides.clear()


def test_lifespan_disposes_engine(monkeypatch):
    import asyncio
    import pytest
    from app.core.lifespan import Lifespan, engine

    calls = []
    monkeypatch.setattr(engine, 'dispose', lambda: calls.append(True))

    async def run():
        async with Lifespan(app):
            assert calls == []
        assert len(calls) == 1
        with pytest.raises(RuntimeError, match='test failure'):
            async with Lifespan(app):
                raise RuntimeError('test failure')
        assert len(calls) == 2

    asyncio.run(run())
