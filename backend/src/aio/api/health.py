"""Application health.

The database schema revision is added by TASK-0002. This response stays
limited to liveness and the application version until then.
"""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from aio import __version__

router = APIRouter()


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    version: str


@router.get("/health", response_model=HealthResponse, summary="Application health")
async def read_health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)
