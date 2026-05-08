"""Tests for pytest_changed.mapper — source→test discovery and overrides."""

from pathlib import Path

from pytest_changed.mapper import target_tests


class TestTargetTests:
    """Core mapping logic — given changed files, discover test files to run."""

    def test_empty_changed_returns_empty_result(self, tmp_path: Path):
        result = target_tests(set(), {}, tmp_path)
        assert result.tests == set()
        assert result.unmatched_sources == set()

    def test_non_python_files_ignored(self, tmp_path: Path):
        changed = {"README.md", "pyproject.toml", "src/config.yaml"}
        result = target_tests(changed, {}, tmp_path)
        assert result.tests == set()
        assert result.unmatched_sources == set()

    def test_source_file_discovers_nested_convention_match(self, tmp_path: Path):
        _write(tmp_path, "tests/foo/test_bar.py")

        result = target_tests({"src/foo/bar.py"}, {}, tmp_path)

        assert result.tests == {"tests/foo/test_bar.py"}
        assert result.unmatched_sources == set()

    def test_source_file_discovers_flat_convention_match(self, tmp_path: Path):
        _write(tmp_path, "tests/test_bar.py")

        result = target_tests({"src/foo/bar.py"}, {}, tmp_path)

        assert result.tests == {"tests/test_bar.py"}
        assert result.unmatched_sources == set()

    def test_source_file_includes_all_existing_convention_matches(self, tmp_path: Path):
        _write(tmp_path, "tests/foo/test_bar.py")
        _write(tmp_path, "tests/test_bar.py")

        result = target_tests({"src/foo/bar.py"}, {}, tmp_path)

        assert result.tests == {"tests/foo/test_bar.py", "tests/test_bar.py"}
        assert result.unmatched_sources == set()

    def test_explicit_mapping_overrides_convention_discovery(self, tmp_path: Path):
        _write(tmp_path, "tests/test_core.py")
        _write(tmp_path, "tests/custom/test_special_core.py")
        mapping = {"src/core.py": ["tests/custom/test_special_core.py"]}

        result = target_tests({"src/core.py"}, mapping, tmp_path)

        assert result.tests == {"tests/custom/test_special_core.py"}
        assert result.unmatched_sources == set()

    def test_multiple_sources_deduplicate_tests(self, tmp_path: Path):
        _write(tmp_path, "tests/test_shared.py")
        result = target_tests({"src/pkg/shared.py", "src/other/shared.py"}, {}, tmp_path)
        assert result.tests == {"tests/test_shared.py"}

    def test_changed_test_file_always_included(self, tmp_path: Path):
        _write(tmp_path, "tests/test_new.py")
        result = target_tests({"tests/test_new.py"}, {}, tmp_path)
        assert result.tests == {"tests/test_new.py"}

    def test_changed_test_with_mapping_not_duplicated(self, tmp_path: Path):
        _write(tmp_path, "tests/test_core.py")
        mapping = {"src/core.py": ["tests/test_core.py"]}
        result = target_tests({"src/core.py", "tests/test_core.py"}, mapping, tmp_path)
        assert result.tests == {"tests/test_core.py"}

    def test_unknown_source_is_reported_as_unmatched(self, tmp_path: Path):
        result = target_tests({"src/unknown.py"}, {}, tmp_path)
        assert result.tests == set()
        assert result.unmatched_sources == {"src/unknown.py"}

    def test_mixed_changed_files(self, tmp_path: Path):
        _write(tmp_path, "tests/test_core.py")
        _write(tmp_path, "tests/utils/test_helpers.py")
        _write(tmp_path, "tests/test_helpers.py")
        _write(tmp_path, "tests/test_new.py")

        mapping = {"src/override.py": ["tests/test_core.py"]}
        changed = {
            "src/core.py",
            "src/utils/helpers.py",
            "src/override.py",
            "src/unknown.py",
            "tests/test_new.py",
            "README.md",
        }
        result = target_tests(changed, mapping, tmp_path)
        assert result.tests == {
            "tests/test_core.py",
            "tests/utils/test_helpers.py",
            "tests/test_helpers.py",
            "tests/test_new.py",
        }
        assert result.unmatched_sources == {"src/unknown.py"}


def _write(
    root: Path, relative_path: str, content: str = "def test_pass(): assert True\n"
) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
