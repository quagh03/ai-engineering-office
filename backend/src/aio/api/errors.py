"""One error body for every API error.

An unhandled exception is answered with a fixed message and no internal
details. The correlation middleware logs that exception with its traceback
while the request's correlation id is still set.
"""

from __future__ import annotations

from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException

from aio.config.logging import get_correlation_id

_STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    500: "internal_error",
}


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    loc: str
    message: str
    type: str


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    correlation_id: str
    details: list[ErrorDetail]


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorBody


def error_response(
    status_code: int,
    *,
    code: str,
    message: str,
    correlation_id: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            correlation_id=correlation_id,
            details=details or [],
        )
    )
    response = JSONResponse(status_code=status_code, content=body.model_dump())
    response.headers["x-correlation-id"] = correlation_id
    return response


def register_exception_handlers(app: FastAPI) -> None:
    # The router raises starlette.exceptions.HTTPException. FastAPI's subclass
    # is registered separately by the framework and would not cover 404s.
    app.add_exception_handler(HTTPException, _http_exception)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unhandled_error)


async def _http_exception(request: Request, exc: Exception) -> JSONResponse:
    http_exc = cast(HTTPException, exc)
    message = http_exc.detail if isinstance(http_exc.detail, str) else "Request failed."
    return error_response(
        http_exc.status_code,
        code=_STATUS_CODES.get(http_exc.status_code, "error"),
        message=message,
        correlation_id=correlation_id_from(request),
    )


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    validation = cast(RequestValidationError, exc)
    details: list[ErrorDetail] = []
    for item in validation.errors():
        location = item.get("loc", ())
        loc = ".".join(str(part) for part in location)
        details.append(
            ErrorDetail(
                loc=loc,
                message=str(item.get("msg", "")),
                type=str(item.get("type", "")),
            )
        )
    return error_response(
        422,
        code="validation_error",
        message="Request validation failed.",
        correlation_id=correlation_id_from(request),
        details=details,
    )


async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    # The traceback is logged by the correlation middleware, which still has
    # the request's id. This handler only builds the response. It runs outside
    # that middleware, after the id has been reset.
    del exc
    return error_response(
        500,
        code="internal_error",
        message="An unexpected error occurred.",
        correlation_id=correlation_id_from(request),
    )


def correlation_id_from(request: Request) -> str:
    value = getattr(request.state, "correlation_id", None)
    if isinstance(value, str):
        return value
    current = get_correlation_id()
    if current is None:
        return "none"
    return current
