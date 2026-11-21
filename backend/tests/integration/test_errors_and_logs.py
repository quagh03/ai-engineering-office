"""AC-017: correlation ids on request logs, and the uniform error body."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import FastAPI

from aio.config.logging import JsonFormatter
from aio.main import create_app
from tests.support import api_client, resolved_for

_SENTINEL = "sentinel-internal-detail-do-not-leak"


class _CollectHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self.setFormatter(JsonFormatter())

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


def _app_with_probes(tmp_path: Path) -> FastAPI:
    app = create_app(resolved_for(tmp_path, global_body='log_level = "INFO"\n'))

    @app.get("/api/v1/_test/log")
    async def log_something() -> dict[str, bool]:
        logging.getLogger("aio.api.test").info("handled test request")
        logging.getLogger("aio.api.test").info("handled test request again")
        return {"ok": True}

    @app.get("/api/v1/_test/boom")
    async def boom() -> dict[str, bool]:
        raise RuntimeError(_SENTINEL)

    @app.get("/api/v1/_test/needs-int")
    async def needs_int(count: int) -> dict[str, int]:
        return {"count": count}

    return app


def _parsed(handler: _CollectHandler) -> list[dict[str, object]]:
    records = [json.loads(line) for line in handler.lines]
    return [record for record in records if str(record["logger"]).startswith("aio.")]


async def test_request_log_lines_carry_the_correlation_id(tmp_path: Path) -> None:
    app = _app_with_probes(tmp_path)
    handler = _CollectHandler()
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        async with api_client(app) as client:
            handler.lines.clear()
            response = await client.get(
                "/api/v1/_test/log",
                headers={"x-correlation-id": "request-1"},
            )
            recorded = _parsed(handler)
    finally:
        root.removeHandler(handler)

    assert response.status_code == 200
    assert response.headers["x-correlation-id"] == "request-1"
    assert recorded
    assert {line["correlation_id"] for line in recorded} == {"request-1"}
    assert any(line["message"] == "handled test request" for line in recorded)
    assert any(line["message"] == "handled test request again" for line in recorded)

    log_path = tmp_path / "data" / "engine.log"
    file_records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line]
    request_records = [record for record in file_records if record["correlation_id"] == "request-1"]
    assert request_records
    assert all("\n" not in line for line in log_path.read_text(encoding="utf-8").splitlines())


async def test_unhandled_error_hides_internals_and_logs_the_traceback(tmp_path: Path) -> None:
    app = _app_with_probes(tmp_path)
    handler = _CollectHandler()
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        async with api_client(app) as client:
            handler.lines.clear()
            response = await client.get("/api/v1/_test/boom")
            recorded = _parsed(handler)
    finally:
        root.removeHandler(handler)

    assert response.status_code == 500
    body = response.json()
    assert body == {
        "error": {
            "code": "internal_error",
            "message": "An unexpected error occurred.",
            "correlation_id": response.headers["x-correlation-id"],
            "details": [],
        }
    }
    leaked = response.text
    assert _SENTINEL not in leaked
    assert "Traceback" not in leaked
    assert "RuntimeError" not in leaked

    correlation_id = response.headers["x-correlation-id"]
    traced = [
        line
        for line in recorded
        if line["correlation_id"] == correlation_id and "exception" in line
    ]
    assert len(traced) == 1
    exception = traced[0]["exception"]
    assert isinstance(exception, str)
    assert "Traceback" in exception
    assert "RuntimeError" in exception
    assert _SENTINEL in exception
    assert all(line["correlation_id"] == correlation_id for line in recorded)


async def test_http_and_validation_errors_use_the_same_body(tmp_path: Path) -> None:
    app = _app_with_probes(tmp_path)
    async with api_client(app) as client:
        missing = await client.get("/api/v1/does-not-exist")
        invalid = await client.get("/api/v1/_test/needs-int?count=abc")
        method = await client.post("/api/v1/health")

    for response, code in (
        (missing, "not_found"),
        (invalid, "validation_error"),
        (method, "method_not_allowed"),
    ):
        body = response.json()
        assert set(body) == {"error"}
        assert set(body["error"]) == {"code", "message", "correlation_id", "details"}
        assert body["error"]["code"] == code
        assert body["error"]["correlation_id"] == response.headers["x-correlation-id"]
        assert "Traceback" not in response.text

    assert "abc" not in invalid.text
    assert invalid.json()["error"]["details"]
