"""Assign a correlation id for the duration of one HTTP request."""

from __future__ import annotations

import logging
import re
import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from aio.config.logging import reset_correlation_id, set_correlation_id

logger = logging.getLogger("aio.api.access")

_CORRELATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_HEADER = "x-correlation-id"


class CorrelationIdMiddleware:
    """Set the correlation id, echo it, and log one line for the request.

    A client id is reused when it matches a short token shape. Anything else,
    including an empty or over-long value, is replaced so it cannot break the
    response header. The query string is not logged.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        correlation_id = _correlation_id(Headers(scope=scope).get(_HEADER))
        state = scope.setdefault("state", {})
        if isinstance(state, dict):
            state["correlation_id"] = correlation_id
        token = set_correlation_id(correlation_id)
        status_code = 500

        async def send_with_correlation(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = MutableHeaders(scope=message)
                headers[_HEADER] = correlation_id
            await send(message)

        try:
            try:
                await self.app(scope, receive, send_with_correlation)
            except Exception:
                # Logged here, before the id is reset. The outer server-error
                # middleware turns the same exception into the response.
                logging.getLogger("aio.api.errors").exception("Unhandled error")
                raise
        finally:
            try:
                method = str(scope.get("method", ""))
                path = str(scope.get("path", ""))
                logger.info("%s %s %s", method, path, status_code)
            finally:
                reset_correlation_id(token)


def _correlation_id(raw: str | None) -> str:
    if raw is not None and _CORRELATION_ID.fullmatch(raw) is not None:
        return raw
    return str(uuid.uuid4())
