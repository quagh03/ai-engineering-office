"""Query the effective engine configuration and the layer each value came from."""

from pathlib import Path
from typing import cast

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from aio.config.settings import ConfigLayer, ResolvedSettings, effective_configuration

router = APIRouter()


class EffectiveSettingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    value: str | int
    layer: ConfigLayer


class EffectiveConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    values: list[EffectiveSettingResponse]


@router.get(
    "/config/effective",
    response_model=EffectiveConfigResponse,
    summary="Effective configuration and its sources",
)
async def read_effective_config(request: Request) -> EffectiveConfigResponse:
    resolved = _resolved(request)
    values: list[EffectiveSettingResponse] = []
    for item in effective_configuration(resolved):
        values.append(
            EffectiveSettingResponse(
                key=item.key,
                value=_json_value(item.value),
                layer=item.layer,
            )
        )
    return EffectiveConfigResponse(values=values)


def _resolved(request: Request) -> ResolvedSettings:
    resolved = cast(object, request.app.state.resolved)
    if not isinstance(resolved, ResolvedSettings):
        raise TypeError("application settings are not configured")
    return resolved


def _json_value(value: object) -> str | int:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, str | int):
        return value
    raise TypeError(f"setting value cannot be reported: {type(value).__name__}")
