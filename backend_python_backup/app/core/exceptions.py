"""Domain exceptions and the global handlers that enforce the error envelope.

README "Error Response Format": EVERY error is ``{"detail": "..."}``.
Only 422 may carry a list of messages.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400
    default_detail = "Bad request"

    def __init__(self, detail: str | None = None, headers: dict[str, str] | None = None):
        self.detail = detail or self.default_detail
        self.headers = headers
        super().__init__(self.detail)


class BusinessRuleError(AppError):
    status_code = 400
    default_detail = "Business rule violated"


class AuthenticationError(AppError):
    status_code = 401
    default_detail = "Could not validate credentials"

    def __init__(self, detail: str | None = None):
        super().__init__(detail, headers={"WWW-Authenticate": "Bearer"})


class PermissionDenied(AppError):
    status_code = 403
    default_detail = "Insufficient permissions"


class NotFoundError(AppError):
    status_code = 404
    default_detail = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    default_detail = "Conflict"


class UnprocessableError(AppError):
    status_code = 422
    default_detail = "Unprocessable request"


def _validation_messages(exc: RequestValidationError) -> list[str]:
    ignored = {"body", "query", "path", "header", "cookie"}
    messages: list[str] = []
    for err in exc.errors():
        location = ".".join(str(part) for part in err.get("loc", ()) if part not in ignored)
        message = str(err.get("msg", "Invalid value"))
        if message.startswith("Value error, "):
            message = message[len("Value error, "):]
        messages.append(f"{location}: {message}" if location else message)
    return messages or ["Invalid request"]


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code, content={"detail": detail}, headers=exc.headers
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": _validation_messages(exc)})

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
        # Safety net: services check first, the database constraint has the last word.
        pgcode = getattr(exc.orig, "pgcode", None)
        if pgcode == "23505":
            detail = "Resource already exists"
        elif pgcode == "23503":
            detail = "Operation conflicts with related data"
        elif pgcode == "23P01":
            detail = "Resource conflicts with an existing one"
        else:
            detail = "Data integrity error"
        logger.warning("IntegrityError mapped to 409 (pgcode=%s)", pgcode)
        return JSONResponse(status_code=409, content={"detail": detail})

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
