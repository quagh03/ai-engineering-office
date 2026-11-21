"""Helpers that tests import directly."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aio.config.settings import ResolvedSettings, resolve_settings


def resolved_for(
    tmp_path: Path,
    *,
    global_body: str = "",
    project_body: str | None = None,
) -> ResolvedSettings:
    """Resolve settings against files under ``tmp_path``.

    The data directory is always the temp tree, so tests do not create
    ``~/Library/Application Support/ai-office``.
    """

    data_dir = tmp_path / "data"
    global_path = tmp_path / "config.toml"
    global_path.write_text(
        f'[engine]\ndata_dir = "{data_dir.as_posix()}"\n{global_body}',
        encoding="utf-8",
    )
    project_root = None
    if project_body is not None:
        project_root = tmp_path / "project"
        office = project_root / ".ai-office"
        office.mkdir(parents=True)
        (office / "project.yaml").write_text(project_body, encoding="utf-8")
    return resolve_settings(global_path=global_path, project_root=project_root)


@asynccontextmanager
async def api_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    # Starlette re-raises after it has written the 500 body. The client still
    # receives that body; the test transport must not hide it behind the exception.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
