"""The factory starts under uvicorn and the health endpoint responds."""

from __future__ import annotations

import socket
import threading
import time
from pathlib import Path

import httpx
import uvicorn

from aio import __version__
from aio.main import create_app
from tests.support import resolved_for


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_application_starts_and_health_responds(tmp_path: Path) -> None:
    port = _free_port()
    app = create_app(resolved_for(tmp_path))
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_config=None,
        access_log=False,
    )
    server = uvicorn.Server(config)
    # Uvicorn skips signal handlers when Server.run is not on the main thread.
    thread = threading.Thread(target=server.run, name="aio-test-server")
    thread.start()
    url = f"http://127.0.0.1:{port}/api/v1/health"
    response: httpx.Response | None = None
    last_error: Exception | None = None
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if server.started:
                try:
                    response = httpx.get(url, timeout=1)
                    break
                except httpx.HTTPError as exc:
                    last_error = exc
            time.sleep(0.05)
        assert response is not None, f"server did not respond: {last_error}"
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "version": __version__}
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        assert not thread.is_alive()
