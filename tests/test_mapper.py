"""Tests for pytest_changed.mapper — the core source→test mapping logic."""

from pytest_changed.mapper import target_tests


class TestTargetTests:
    """Core mapping logic — given changed files and a mapping dict, return test files to run."""

    def test_empty_changed_returns_empty(self):
        """Empty changed set returns empty test set."""
        assert target_tests(set(), {}) == set()

    def test_non_python_files_ignored(self):
        """Only .py files are considered. Non-Python extensions are skipped."""
        changed = {"README.md", "pyproject.toml", "src/config.yaml"}
        mapping = {"src/config.yaml": ["tests/test_config.py"]}
        assert target_tests(changed, mapping) == set()

    def test_source_file_maps_to_single_test(self):
        """A changed source file with a mapping returns its mapped test file."""
        mapping = {"src/core.py": ["tests/test_core.py"]}
        assert target_tests({"src/core.py"}, mapping) == {"tests/test_core.py"}

    def test_source_file_maps_to_multiple_tests(self):
        """A source file can map to multiple test files — all are returned."""
        mapping = {"src/db.py": ["tests/test_db.py", "tests/test_db_integration.py"]}
        result = target_tests({"src/db.py"}, mapping)
        assert result == {"tests/test_db.py", "tests/test_db_integration.py"}

    def test_multiple_sources_deduplicate_tests(self):
        """When two source files map to the same test, it's only returned once."""
        mapping = {
            "src/a.py": ["tests/test_shared.py"],
            "src/b.py": ["tests/test_shared.py"],
        }
        result = target_tests({"src/a.py", "src/b.py"}, mapping)
        assert result == {"tests/test_shared.py"}

    def test_changed_test_file_always_included(self):
        """A changed file under tests/ is always included, even without a mapping."""
        result = target_tests({"tests/test_new.py"}, {})
        assert result == {"tests/test_new.py"}

    def test_changed_test_with_mapping_not_duplicated(self):
        """If a test file is both changed and mapped from a source, it appears once."""
        mapping = {"src/core.py": ["tests/test_core.py"]}
        result = target_tests({"src/core.py", "tests/test_core.py"}, mapping)
        assert result == {"tests/test_core.py"}

    def test_unknown_source_silently_ignored(self):
        """Source files with no mapping entry are silently skipped."""
        mapping = {"src/known.py": ["tests/test_known.py"]}
        result = target_tests({"src/unknown.py"}, mapping)
        assert result == set()

    def test_mixed_changed_files(self):
        """Integration: mix of mapped sources, unmapped sources, test files, and non-Python."""
        mapping = {
            "src/core.py": ["tests/test_core.py"],
            "src/utils.py": ["tests/test_utils.py", "tests/test_utils_edge.py"],
        }
        changed = {
            "src/core.py",  # mapped
            "src/utils.py",  # mapped to 2 files
            "src/unknown.py",  # no mapping
            "tests/test_new.py",  # auto-included
            "README.md",  # non-Python
        }
        result = target_tests(changed, mapping)
        assert result == {
            "tests/test_core.py",
            "tests/test_utils.py",
            "tests/test_utils_edge.py",
            "tests/test_new.py",
        }
