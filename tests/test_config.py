"""Tests for pytest_changed.config — loading configuration from TOML files."""

import tempfile
from pathlib import Path

from pytest_changed.config import load_mapping, load_pytest_args


class TestLoadMapping:
    """Loading source→test mapping from pyproject.toml."""

    def test_loads_mapping_from_canonical_hyphenated_tool_table(self):
        """Canonical config lives under [tool.pytest-changed.mapping]."""
        pyproject = """
[tool.pytest-changed]
pytest_args = ["-q"]

[tool.pytest-changed.mapping]
"src/core.py" = ["tests/test_core.py"]
"src/utils.py" = ["tests/test_utils.py", "tests/test_utils_edge.py"]
"""
        with _temp_pyproject(pyproject) as root:
            result = load_mapping(root)
            assert result == {
                "src/core.py": ["tests/test_core.py"],
                "src/utils.py": ["tests/test_utils.py", "tests/test_utils_edge.py"],
            }

    def test_supports_legacy_underscore_tool_table(self):
        """Underscore table remains supported as an alias for early adopters."""
        pyproject = """
[tool.pytest_changed.mapping]
"src/app.py" = ["tests/test_app.py"]
"""
        with _temp_pyproject(pyproject) as root:
            result = load_mapping(root)
            assert result == {"src/app.py": ["tests/test_app.py"]}

    def test_hyphenated_table_takes_precedence_over_underscore_alias(self):
        """If both forms exist, the canonical hyphenated form wins."""
        pyproject = """
[tool.pytest-changed.mapping]
"src/canonical.py" = ["tests/test_canonical.py"]

[tool.pytest_changed.mapping]
"src/legacy.py" = ["tests/test_legacy.py"]
"""
        with _temp_pyproject(pyproject) as root:
            result = load_mapping(root)
            assert result == {"src/canonical.py": ["tests/test_canonical.py"]}

    def test_empty_mapping_when_section_missing(self):
        """Returns empty dict when [tool.pytest-changed] section doesn't exist."""
        pyproject = """
[project]
name = "test"
"""
        with _temp_pyproject(pyproject) as root:
            result = load_mapping(root)
            assert result == {}

    def test_empty_mapping_when_mapping_section_missing(self):
        """Returns empty dict when tool config exists but mapping section doesn't."""
        pyproject = """
[tool.pytest-changed]
pytest_args = ["-x"]
"""
        with _temp_pyproject(pyproject) as root:
            result = load_mapping(root)
            assert result == {}

    def test_uses_cwd_when_no_root_specified(self, monkeypatch):
        """When project_root is None, uses current working directory."""
        pyproject = """
[tool.pytest-changed.mapping]
"src/app.py" = ["tests/test_app.py"]
"""
        with _temp_pyproject(pyproject) as root:
            monkeypatch.chdir(root)
            result = load_mapping()
            assert result == {"src/app.py": ["tests/test_app.py"]}

    def test_env_config_override_loads_specific_toml_file(self, tmp_path: Path, monkeypatch):
        """PYTEST_CHANGED_CONFIG points directly at the config TOML file to use."""
        config = tmp_path / "pytest-changed.toml"
        config.write_text(
            """
[tool.pytest-changed.mapping]
"src/env.py" = ["tests/test_env.py"]
""".strip()
            + "\n"
        )
        monkeypatch.setenv("PYTEST_CHANGED_CONFIG", str(config))

        result = load_mapping(tmp_path / "different-root")

        assert result == {"src/env.py": ["tests/test_env.py"]}


class TestLoadPytestArgs:
    """Loading pytest args from TOML config."""

    def test_loads_args_from_canonical_hyphenated_tool_table(self):
        """Pytest args are loaded from [tool.pytest-changed.pytest_args]."""
        pyproject = """
[tool.pytest-changed]
pytest_args = ["-x", "--tb=long"]
"""
        with _temp_pyproject(pyproject) as root:
            result = load_pytest_args(root)
            assert result == ["-x", "--tb=long"]

    def test_supports_legacy_underscore_tool_table(self):
        """Underscore table remains supported as an alias for early adopters."""
        pyproject = """
[tool.pytest_changed]
pytest_args = ["--tb=short"]
"""
        with _temp_pyproject(pyproject) as root:
            result = load_pytest_args(root)
            assert result == ["--tb=short"]

    def test_defaults_to_minus_q_when_missing(self):
        """Defaults to ['-q'] when no pytest_args configured."""
        pyproject = """
[tool.pytest-changed]
"""
        with _temp_pyproject(pyproject) as root:
            result = load_pytest_args(root)
            assert result == ["-q"]

    def test_env_config_override_loads_pytest_args(self, tmp_path: Path, monkeypatch):
        """PYTEST_CHANGED_CONFIG affects pytest_args as well as mapping."""
        config = tmp_path / "pytest-changed.toml"
        config.write_text(
            """
[tool.pytest-changed]
pytest_args = ["-q", "--disable-warnings"]
""".strip()
            + "\n"
        )
        monkeypatch.setenv("PYTEST_CHANGED_CONFIG", str(config))

        result = load_pytest_args(tmp_path / "different-root")

        assert result == ["-q", "--disable-warnings"]


def _temp_pyproject(content: str) -> tempfile.TemporaryDirectory:
    """Create a temporary directory with a pyproject.toml file."""
    tmp = tempfile.TemporaryDirectory()
    (Path(tmp.name) / "pyproject.toml").write_text(content.strip() + "\n")
    return tmp
