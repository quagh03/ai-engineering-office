"""Structured JSON logs for the engine.

Every record is one JSON object. The correlation id is captured when the
record is created, so a line written while a request is in progress carries
that request's id. Outside a request the field is null.

Logs are written to stderr and to a rotating file, ``engine.log``, in the
configured data directory. Secret redaction is not done here; this task's
log records are the request line and the error traceback, and scanning
output for credentials belongs with secret handling.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, TextIO, cast

from aio.config.settings import ConfigurationError, EngineSettings

_correlation_id: ContextVar[str | None] = ContextVar("aio_correlation_id", default=None)
_factory_installed = False
_MAX_LOG_BYTES = 1_048_576
_LOG_BACKUPS = 3
_LOG_FILE_NAME = "engine.log"


class _CorrelatedRecord(logging.LogRecord):
    correlation_id: str | None


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def set_correlation_id(value: str) -> Token[str | None]:
    return _correlation_id.set(value)


def reset_correlation_id(token: Token[str | None]) -> None:
    _correlation_id.reset(token)


def _install_log_record_factory() -> None:
    """Stamp the correlation id onto every record when it is created.

    A filter on the root logger does not run for records that propagate up
    from a child logger. Creating the record is the one place that sees the
    context of the code that logged.
    """

    global _factory_installed
    if _factory_installed:
        return
    previous = logging.getLogRecordFactory()

    def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = previous(*args, **kwargs)
        # LogRecord has no declared correlation field; the formatter reads this back.
        correlated = cast(_CorrelatedRecord, record)
        correlated.correlation_id = get_correlation_id()
        return record

    logging.setLogRecordFactory(factory)
    _factory_installed = True


class JsonFormatter(logging.Formatter):
    """Format one log record as a single line of JSON."""

    def format(self, record: logging.LogRecord) -> str:
        correlation = getattr(record, "correlation_id", None)
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation if isinstance(correlation, str) else None,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class JsonStreamHandler(logging.StreamHandler[TextIO]):
    """Stderr handler installed by :func:`configure_logging`."""


class JsonFileHandler(RotatingFileHandler):
    """Rotating file handler installed by :func:`configure_logging`."""


def configure_logging(settings: EngineSettings) -> Path:
    """Send engine logs to stderr and to ``<data_dir>/engine.log``.

    Handlers previously installed by this function are replaced. Other
    handlers, including ones a test attached, are left in place.
    """

    log_dir = settings.data_dir
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigurationError(log_dir, "log directory could not be created") from exc

    _install_log_record_factory()
    root = logging.getLogger()
    root.setLevel(settings.log_level)

    for handler in list(root.handlers):
        if isinstance(handler, JsonStreamHandler | JsonFileHandler):
            root.removeHandler(handler)
            handler.close()

    formatter = JsonFormatter()
    stream = JsonStreamHandler(sys.stderr)
    stream.setFormatter(formatter)
    root.addHandler(stream)

    log_path = log_dir / _LOG_FILE_NAME
    file_handler = JsonFileHandler(
        log_path,
        maxBytes=_MAX_LOG_BYTES,
        backupCount=_LOG_BACKUPS,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    return log_path
