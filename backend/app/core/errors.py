"""Contract error envelope: {"error":{"code","message","details"},"request_id"}.

Per CLAUDE.md "Reliability and integrity rules" — every HTTP error response
(including Pydantic validation failures) must use this shape, not FastAPI's
default error body.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Raised by service/repository code; translated to the contract error envelope."""

    def __init__(self, code: str, message: str, status_code: int, details: Any = None) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def _error_response(status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {"code": code, "message": message, "details": details},
            "request_id": str(uuid.uuid4()),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            "Request validation failed.",
            exc.errors(),
        )
