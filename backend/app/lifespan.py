import logging
from fastapi import FastAPI
from app.config import get_settings
from app.db import engine

logger = logging.getLogger("tech_transport")


class Lifespan:
    def __init__(self, app: FastAPI) -> None:
        self.app = app

    async def __aenter__(self) -> None:
        logging.basicConfig(level=get_settings().log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
        # SQL parameters, request bodies, cookies and query strings are never logged.
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logger.info("Backend started")

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        engine.dispose()
        logger.info("Backend stopped")
