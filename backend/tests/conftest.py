"""Fixtures shared by the backend tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI

from aio.main import create_app
from tests.support import resolved_for


@pytest.fixture
def app(tmp_path: Path) -> Iterator[FastAPI]:
    yield create_app(resolved_for(tmp_path))
