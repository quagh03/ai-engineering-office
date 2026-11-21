"""AC-003: project overrides global, global overrides the default."""

from pathlib import Path

import pytest

from aio.config.settings import (
    ConfigLayer,
    ConfigurationError,
    effective_configuration,
    resolve_settings,
)


def test_project_value_wins_and_query_reports_the_layer(tmp_path: Path) -> None:
    global_path = tmp_path / "config.toml"
    global_path.write_text(
        '[engine]\nport = 1111\nlog_level = "WARNING"\nhost = "localhost"\n',
        encoding="utf-8",
    )
    project_root = tmp_path / "project"
    office = project_root / ".ai-office"
    office.mkdir(parents=True)
    (office / "project.yaml").write_text(
        "name: example\nengine:\n  port: 2222\n",
        encoding="utf-8",
    )

    resolved = resolve_settings(global_path=global_path, project_root=project_root)
    by_key = {item.key: item for item in effective_configuration(resolved)}

    assert by_key["port"].value == 2222
    assert by_key["port"].layer is ConfigLayer.PROJECT
    assert by_key["log_level"].value == "WARNING"
    assert by_key["log_level"].layer is ConfigLayer.GLOBAL
    assert by_key["host"].value == "localhost"
    assert by_key["host"].layer is ConfigLayer.GLOBAL
    assert by_key["data_dir"].layer is ConfigLayer.DEFAULT


def test_global_value_wins_when_the_project_does_not_set_it(tmp_path: Path) -> None:
    global_path = tmp_path / "config.toml"
    global_path.write_text('[engine]\nport = 1111\n', encoding="utf-8")
    project_root = tmp_path / "project"
    office = project_root / ".ai-office"
    office.mkdir(parents=True)
    (office / "project.yaml").write_text("name: example\n", encoding="utf-8")

    resolved = resolve_settings(global_path=global_path, project_root=project_root)
    by_key = {item.key: item for item in effective_configuration(resolved)}

    assert by_key["port"].value == 1111
    assert by_key["port"].layer is ConfigLayer.GLOBAL
    assert by_key["host"].value == "127.0.0.1"
    assert by_key["host"].layer is ConfigLayer.DEFAULT


def test_environment_variables_are_not_a_layer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", "9")
    monkeypatch.setenv("AIO_PORT", "9")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    resolved = resolve_settings(global_path=tmp_path / "missing.toml")

    assert resolved.settings.port == 8765
    assert resolved.settings.log_level == "INFO"


def test_missing_files_use_defaults(tmp_path: Path) -> None:
    resolved = resolve_settings(
        global_path=tmp_path / "missing.toml",
        project_root=tmp_path / "absent-project",
    )
    by_key = {item.key: item for item in effective_configuration(resolved)}

    assert resolved.settings.port == 8765
    assert by_key["port"].layer is ConfigLayer.DEFAULT
    assert all(item.layer is ConfigLayer.DEFAULT for item in by_key.values())


def test_invalid_global_file_names_the_path(tmp_path: Path) -> None:
    global_path = tmp_path / "config.toml"
    global_path.write_text("engine = [\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match=str(global_path)) as raised:
        resolve_settings(global_path=global_path)

    assert raised.value.path == global_path


def test_unknown_engine_key_names_the_project_file(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    office = project_root / ".ai-office"
    office.mkdir(parents=True)
    project_path = office / "project.yaml"
    project_path.write_text("engine:\n  prot: 1\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="unknown engine settings: prot") as raised:
        resolve_settings(global_path=tmp_path / "missing.toml", project_root=project_root)

    assert raised.value.path == project_path


def test_repository_project_yaml_has_no_engine_overrides() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    resolved = resolve_settings(
        global_path=repo_root / "missing-global-config.toml",
        project_root=repo_root,
    )

    assert resolved.settings.host == "127.0.0.1"
    assert resolved.settings.port == 8765
    assert resolved.layers_by_key["port"] is ConfigLayer.DEFAULT
