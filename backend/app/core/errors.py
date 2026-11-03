import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger("tech_transport")


def error_response(status: int, code: str, message: str, details=None, headers=None):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "details": details or []}}, headers=headers)


async def http_error(request: Request, exc: HTTPException):
    return error_response(exc.status_code, f"http_{exc.status_code}", str(exc.detail), headers=exc.headers)


async def validation_error(request: Request, exc: RequestValidationError):
    details = [{"loc": list(e["loc"]), "type": e["type"], "message": e["msg"]} for e in exc.errors()]
    return error_response(422, "validation_error", "Некорректные данные запроса", details)


async def unexpected_error(request: Request, exc: Exception):
    # Do not serialize exceptions: they may contain credentials or SQL values.
    logger.error("Unhandled application error (%s)", type(exc).__name__)
    return error_response(500, "internal_error", "Внутренняя ошибка сервера")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_error)
    app.add_exception_handler(RequestValidationError, validation_error)
    app.add_exception_handler(Exception, unexpected_error)
