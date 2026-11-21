"""Application factory.

Build the app with :func:`create_app` so a test can supply its own resolved
settings. The process entry point used by uvicorn is the same factory:

``uvicorn aio.main:create_app --factory``
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from aio import __version__
from aio.api.config import router as config_router
from aio.api.errors import register_exception_handlers
from aio.api.health import router as health_router
from aio.api.middleware import CorrelationIdMiddleware
from aio.config.logging import configure_logging
from aio.config.settings import ResolvedSettings, resolve_settings


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Uvicorn installs its own logging before the lifespan runs. Re-apply the
    # engine's JSON handlers so request logs stay structured after startup.
    resolved = app.state.resolved
    if isinstance(resolved, ResolvedSettings):
        configure_logging(resolved.settings)
    yield


def create_app(resolved: ResolvedSettings | None = None) -> FastAPI:
    """Create the FastAPI application.

    With no argument, settings are resolved from the built-in defaults, the
    global config file, and no project. Pass a :class:`ResolvedSettings` to
    point the app at a specific project and data directory.
    """

    settings = resolved if resolved is not None else resolve_settings()
    configure_logging(settings.settings)
    app = FastAPI(title="AI Engineering Office", version=__version__, lifespan=_lifespan)
    app.state.resolved = settings
    app.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(config_router, prefix="/api/v1")
    return app
