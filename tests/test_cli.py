"""Tests for pytest_changed.cli — entry point, pytest runner, and main flow."""

import sys
from pathlib import Path

from pytest_changed.cli import main, run_pytest


class TestRunPytest:
    """Running pytest on selected test files."""

    def test_empty_test_set_returns_zero(self):
        """No test files to run → exit code 0."""
        assert run_pytest(set()) == 0

    def test_passes_custom_args(self, tmp_path: Path, monkeypatch):
        """Pytest receives custom args from config."""
        test_file = tmp_path / "test_dummy.py"
        test_file.write_text("def test_pass(): assert True\n")
        result = run_pytest({str(test_file)}, pytest_args=["--tb=short"])
        assert result == 0

    def test_runs_mapped_tests_and_passes(self, tmp_path: Path):
        """Pytest runs the mapped test files successfully."""
        test_file = tmp_path / "test_pass.py"
        test_file.write_text("def test_pass(): assert True\n")
        result = run_pytest({str(test_file)})
        assert result == 0

    def test_returns_nonzero_on_failure(self, tmp_path: Path):
        """Pytest returns non-zero exit code when a test fails."""
        test_file = tmp_path / "test_fail.py"
        test_file.write_text("def test_fail(): assert False\n")
        result = run_pytest({str(test_file)})
        assert result != 0

    def test_pytest_no_tests_collected_is_zero(self, tmp_path: Path):
        """Exit code 5 (no tests collected) is treated as success."""
        test_file = tmp_path / "test_empty.py"
        test_file.write_text("# no test functions\n")
        result = run_pytest({str(test_file)})
        assert result == 0


class TestMain:
    """CLI entry point — argv parsing and orchestration."""

    def test_no_argv_returns_zero(self, monkeypatch):
        """When called with no arguments, exits 0 silently."""
        monkeypatch.setattr(sys, "argv", ["pytest-changed"])
        assert main() == 0

    def test_no_python_files_returns_zero(self, monkeypatch):
        """Non-Python staged files are ignored, exits 0."""
        monkeypatch.setattr(sys, "argv", ["pytest-changed", "README.md", "pyproject.toml"])
        assert main() == 0

    def test_source_with_mapping_runs_test(self, tmp_path: Path, monkeypatch):
        """When a staged source file has a mapping, the mapped test is run."""
        # Set up a pretend project with pyproject.toml and a passing test
        src_file = tmp_path / "src" / "core.py"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_text("x = 1\n")

        test_file = tmp_path / "tests" / "test_core.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("def test_pass(): assert True\n")

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.pytest-changed.mapping]
"src/core.py" = ["tests/test_core.py"]
""")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["pytest-changed", "src/core.py"])

        assert main() == 0

    def test_changed_test_file_runs_without_mapping(self, tmp_path: Path, monkeypatch):
        """A changed file under tests/ runs even without a mapping entry."""
        test_file = tmp_path / "tests" / "test_standalone.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("def test_standalone(): assert True\n")

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.pytest_changed]
""")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["pytest-changed", "tests/test_standalone.py"])

        assert main() == 0
