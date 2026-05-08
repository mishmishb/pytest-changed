"""Config loading for pytest-changed."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # pragma: no cover

ENV_CONFIG = "PYTEST_CHANGED_CONFIG"
CANONICAL_TOOL_KEY = "pytest-changed"
LEGACY_TOOL_KEY = "pytest_changed"
DEFAULT_PYTEST_ARGS = ["-q"]
DEFAULT_SOURCE_ROOTS = ["src"]
DEFAULT_TEST_ROOTS = ["tests"]


@dataclass(frozen=True)
class Settings:
    """Runtime settings for discovery and pytest invocation."""

    mapping: dict[str, list[str]]
    pytest_args: list[str]
    source_roots: list[str]
    test_roots: list[str]
    warn_on_missing: bool


def _find_config_file(project_root: Path) -> Path | None:
    """Find the TOML config file to use.

    PYTEST_CHANGED_CONFIG points directly at a TOML file. Relative override paths
    are resolved against project_root/current working directory.
    """
    override = os.environ.get(ENV_CONFIG)
    if override:
        override_path = Path(override).expanduser()
        if not override_path.is_absolute():
            override_path = project_root / override_path
        return override_path if override_path.is_file() else None

    pyproject = project_root / "pyproject.toml"
    return pyproject if pyproject.is_file() else None


def _load_tool_config(project_root: str | Path | None = None) -> dict[str, Any]:
    """Load [tool.pytest-changed] config, with underscore alias support."""
    root = Path(project_root) if project_root else Path.cwd()
    config_file = _find_config_file(root)
    if config_file is None:
        return {}

    data = tomllib.loads(config_file.read_text())
    tool = data.get("tool", {})
    if not isinstance(tool, dict):
        return {}

    canonical = tool.get(CANONICAL_TOOL_KEY)
    if isinstance(canonical, dict):
        return canonical

    legacy = tool.get(LEGACY_TOOL_KEY)
    if isinstance(legacy, dict):
        return legacy

    return {}


def _string_list(value: Any, default: list[str]) -> list[str]:
    if not isinstance(value, list):
        return default.copy()
    result = [item.strip("/") for item in value if isinstance(item, str) and item.strip("/")]
    return result or default.copy()


def _mapping(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}

    result: dict[str, list[str]] = {}
    for key, item in value.items():
        if isinstance(key, str) and isinstance(item, list):
            result[key] = [str(entry) for entry in item if isinstance(entry, str)]
    return result


def load_settings(project_root: str | Path | None = None) -> Settings:
    """Load all runtime settings from TOML config."""
    tool_cfg = _load_tool_config(project_root)

    pytest_args = tool_cfg.get("pytest_args", DEFAULT_PYTEST_ARGS)
    if not (isinstance(pytest_args, list) and all(isinstance(arg, str) for arg in pytest_args)):
        pytest_args = DEFAULT_PYTEST_ARGS

    warn_on_missing = tool_cfg.get("warn_on_missing", True)
    if not isinstance(warn_on_missing, bool):
        warn_on_missing = True

    return Settings(
        mapping=_mapping(tool_cfg.get("mapping", {})),
        pytest_args=list(pytest_args),
        source_roots=_string_list(tool_cfg.get("source_roots"), DEFAULT_SOURCE_ROOTS),
        test_roots=_string_list(tool_cfg.get("test_roots"), DEFAULT_TEST_ROOTS),
        warn_on_missing=warn_on_missing,
    )


def load_mapping(project_root: str | Path | None = None) -> dict[str, list[str]]:
    """Load source→test mapping from [tool.pytest-changed.mapping]."""
    return load_settings(project_root).mapping


def load_pytest_args(project_root: str | Path | None = None) -> list[str]:
    """Load pytest args from [tool.pytest-changed.pytest_args]."""
    return load_settings(project_root).pytest_args
