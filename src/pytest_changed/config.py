"""Config loading for pytest-changed."""

import os
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # pragma: no cover

ENV_CONFIG = "PYTEST_CHANGED_CONFIG"
CANONICAL_TOOL_KEY = "pytest-changed"
LEGACY_TOOL_KEY = "pytest_changed"


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


def load_mapping(project_root: str | Path | None = None) -> dict[str, list[str]]:
    """Load source→test mapping from [tool.pytest-changed.mapping]."""
    tool_cfg = _load_tool_config(project_root)
    mapping = tool_cfg.get("mapping", {})
    if not isinstance(mapping, dict):
        return {}

    result: dict[str, list[str]] = {}
    for key, value in mapping.items():
        if isinstance(key, str) and isinstance(value, list):
            result[key] = [str(v) for v in value if isinstance(v, str)]
    return result


def load_pytest_args(project_root: str | Path | None = None) -> list[str]:
    """Load pytest args from [tool.pytest-changed.pytest_args]."""
    tool_cfg = _load_tool_config(project_root)
    args = tool_cfg.get("pytest_args", ["-q"])
    if isinstance(args, list) and all(isinstance(a, str) for a in args):
        return args
    return ["-q"]
