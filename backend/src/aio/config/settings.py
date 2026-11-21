"""Layered engine settings.

Resolution order, later overriding earlier: built-in defaults, the global
``config.toml``, then the project's ``.ai-office/project.yaml``.

Assumption: only the ``engine`` table in each file is read. Other keys are
project identity and are left untouched. Feature and per-task overrides from
the system design are not applied here; no caller needs them yet.
Environment variables are not a layer.

The global file is ``~/Library/Application Support/ai-office/config.toml``.
A missing file is an empty layer. A file that exists but is not valid, or
an ``engine`` table with an unknown key or a value that does not match the
setting, fails resolution and names the file.
"""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

# PyYAML ships no type information. The stub package is not an approved
# dependency of this task; the type-check setup belongs to TASK-0009.
import yaml  # type: ignore[import-untyped]
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

APP_DATA_DIR = Path.home() / "Library" / "Application Support" / "ai-office"
GLOBAL_CONFIG_PATH = APP_DATA_DIR / "config.toml"
_PROJECT_CONFIG_RELATIVE = Path(".ai-office") / "project.yaml"
_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class ConfigLayer(StrEnum):
    DEFAULT = "default"
    GLOBAL = "global"
    PROJECT = "project"


class ConfigurationError(Exception):
    """A configuration file could not be read or did not match the schema."""

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        super().__init__(f"{path}: {message}")


class EngineSettings(BaseSettings):
    """Validated engine settings.

    File layers are applied by :func:`resolve_settings`. Initialization is the
    only pydantic-settings source, so the process environment cannot override
    the three layers defined by FR-002.
    """

    model_config = SettingsConfigDict(extra="forbid")

    host: str = "127.0.0.1"
    port: int = Field(default=8765, ge=1, le=65535)
    log_level: str = "INFO"
    data_dir: Path = APP_DATA_DIR

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        del settings_cls, env_settings, dotenv_settings, file_secret_settings
        return (init_settings,)

    @field_validator("host")
    @classmethod
    def _host_not_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or any(character.isspace() for character in stripped):
            raise ValueError("must be a non-empty host without whitespace")
        return stripped

    @field_validator("log_level", mode="before")
    @classmethod
    def _canonical_log_level(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        canonical = value.upper()
        if canonical not in _LOG_LEVELS:
            allowed = ", ".join(sorted(_LOG_LEVELS))
            raise ValueError(f"must be one of: {allowed}")
        return canonical

    @field_validator("data_dir", mode="before")
    @classmethod
    def _absolute_data_dir(cls, value: object) -> object:
        if isinstance(value, str | Path):
            return Path(value).expanduser().resolve()
        return value


@dataclass(frozen=True)
class EffectiveValue:
    key: str
    value: Any
    layer: ConfigLayer


@dataclass(frozen=True)
class ResolvedSettings:
    settings: EngineSettings
    layers_by_key: dict[str, ConfigLayer]
    global_path: Path
    project_path: Path | None


def resolve_settings(
    *,
    global_path: Path | None = None,
    project_root: Path | None = None,
) -> ResolvedSettings:
    """Resolve settings from defaults, the global file, and one project file.

    ``project_root`` is the project directory that contains ``.ai-office/``.
    When it is omitted, the project layer is empty. The running process does
    not guess a project from the working directory; opening a project is a
    later task.
    """

    resolved_global = GLOBAL_CONFIG_PATH if global_path is None else global_path
    project_path = None if project_root is None else project_root / _PROJECT_CONFIG_RELATIVE
    global_table = _engine_table(resolved_global, _parse_toml)
    project_table = {} if project_path is None else _engine_table(project_path, _parse_yaml)

    merged: dict[str, Any] = {}
    layers = {name: ConfigLayer.DEFAULT for name in EngineSettings.model_fields}
    for layer, table in (
        (ConfigLayer.GLOBAL, global_table),
        (ConfigLayer.PROJECT, project_table),
    ):
        for key, value in table.items():
            merged[key] = value
            layers[key] = layer

    try:
        settings = EngineSettings.model_validate(merged)
    except ValidationError as exc:
        raise ConfigurationError(_source_of_invalid(exc, resolved_global, project_path, layers), str(exc)) from exc

    return ResolvedSettings(
        settings=settings,
        layers_by_key=layers,
        global_path=resolved_global,
        project_path=project_path,
    )


def effective_configuration(resolved: ResolvedSettings) -> tuple[EffectiveValue, ...]:
    """Return each effective setting and the layer that supplied it."""

    values = resolved.settings.model_dump()
    return tuple(
        EffectiveValue(key=key, value=values[key], layer=resolved.layers_by_key[key])
        for key in EngineSettings.model_fields
    )


def _engine_table(path: Path, parse: Callable[[str], object]) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(path, "could not be read") from exc
    try:
        loaded = parse(text)
    except ValueError as exc:
        raise ConfigurationError(path, str(exc)) from exc
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigurationError(path, "must contain a mapping")
    document: dict[str, Any] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            raise ConfigurationError(path, "mapping keys must be strings")
        document[key] = value
    if "engine" not in document:
        return {}
    engine = document["engine"]
    if engine is None:
        return {}
    if not isinstance(engine, dict):
        raise ConfigurationError(path, "engine must be a mapping")
    table: dict[str, Any] = {}
    for key, value in engine.items():
        if not isinstance(key, str):
            raise ConfigurationError(path, "engine keys must be strings")
        table[key] = value
    unknown = sorted(set(table) - set(EngineSettings.model_fields))
    if unknown:
        names = ", ".join(unknown)
        raise ConfigurationError(path, f"unknown engine settings: {names}")
    return table


def _parse_toml(text: str) -> object:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid TOML ({exc})") from exc


def _parse_yaml(text: str) -> object:
    try:
        loaded: object = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML ({exc})") from exc
    return loaded


def _source_of_invalid(
    exc: ValidationError,
    global_path: Path,
    project_path: Path | None,
    layers: dict[str, ConfigLayer],
) -> Path:
    errors = exc.errors()
    if errors:
        location = errors[0].get("loc", ())
        if location and isinstance(location[0], str):
            layer = layers.get(location[0], ConfigLayer.DEFAULT)
            if layer is ConfigLayer.PROJECT and project_path is not None:
                return project_path
            if layer is ConfigLayer.GLOBAL:
                return global_path
    return project_path or global_path
