"""Health endpoint and the effective-configuration query over HTTP."""

from pathlib import Path

from fastapi import FastAPI

from aio import __version__
from tests.support import api_client, resolved_for


async def test_health_returns_the_application_version(app: FastAPI) -> None:
    async with api_client(app) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}
    assert response.headers["x-correlation-id"]


async def test_effective_configuration_query_reports_the_winning_layer(tmp_path: Path) -> None:
    from aio.main import create_app

    resolved = resolved_for(
        tmp_path,
        global_body='port = 1111\nlog_level = "WARNING"\n',
        project_body="engine:\n  port: 2222\n",
    )
    app = create_app(resolved)

    async with api_client(app) as client:
        response = await client.get("/api/v1/config/effective")

    assert response.status_code == 200
    by_key = {item["key"]: item for item in response.json()["values"]}
    assert by_key["port"] == {"key": "port", "value": 2222, "layer": "project"}
    assert by_key["log_level"] == {"key": "log_level", "value": "WARNING", "layer": "global"}
    assert by_key["host"]["layer"] == "default"
    assert by_key["data_dir"]["layer"] == "global"
    assert by_key["data_dir"]["value"] == str((tmp_path / "data").resolve())


async def test_openapi_lists_the_system_routes(app: FastAPI) -> None:
    async with api_client(app) as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/config/effective" in paths
