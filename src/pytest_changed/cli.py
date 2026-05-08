"""Entry point for pytest-changed pre-commit hook."""

import subprocess
import sys
from pathlib import Path

PYTEST_NO_TESTS = 5  # exit code for "no tests collected"


def run_pytest(test_files: set[str], pytest_args: list[str] | None = None) -> int:
    """Run pytest on the given test files. Returns exit code.

    Treats pytest exit code 5 (no tests collected) as success — this is normal
    for scaffold repos or when test files exist but are empty.
    """
    if not test_files:
        return 0
    args = pytest_args if pytest_args is not None else ["-q"]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *sorted(test_files), *args],
        check=False,
    )
    if result.returncode == PYTEST_NO_TESTS:
        return 0
    return result.returncode


def _warn_unmatched(unmatched_sources: set[str]) -> None:
    for path in sorted(unmatched_sources):
        print(f"pytest-changed: no matching tests found for {path}", file=sys.stderr)


def main() -> int:
    """CLI entry point. Receives filenames from pre-commit or manual invocation."""
    from pytest_changed.config import load_settings
    from pytest_changed.mapper import target_tests

    if len(sys.argv) < 2:
        return 0

    changed = set(sys.argv[1:])
    py_files = {p for p in changed if p.endswith(".py")}
    if not py_files:
        return 0

    settings = load_settings()
    selection = target_tests(
        py_files,
        settings.mapping,
        Path.cwd(),
        settings.source_roots,
        settings.test_roots,
    )
    if settings.warn_on_missing and selection.unmatched_sources:
        _warn_unmatched(selection.unmatched_sources)
    if not selection.tests:
        return 0

    return run_pytest(selection.tests, settings.pytest_args)


if __name__ == "__main__":
    raise SystemExit(main())
