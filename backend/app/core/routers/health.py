import logging
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.db import get_session
from app.core.errors import error_response

logger = logging.getLogger("tech_transport")
router = APIRouter(prefix="/api/health")


@router.get("/live")
def live():
    return {"status": "ok"}


@router.get("/ready")
def ready(session: Session = Depends(get_session)):
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("Database readiness check failed")
        return error_response(503, "database_unavailable", "База данных недоступна")
    return {"status": "ok", "database": "ok"}
