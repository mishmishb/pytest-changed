"""Entry point for pytest-changed pre-commit hook."""

import subprocess
import sys

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


def main() -> int:
    """CLI entry point. Receives filenames from pre-commit or manual invocation.

    Reads mapping config from pyproject.toml, maps staged files to test files,
    and runs pytest on the result.
    """
    from pytest_changed.config import load_mapping, load_pytest_args
    from pytest_changed.mapper import target_tests

    if len(sys.argv) < 2:
        return 0

    changed = set(sys.argv[1:])
    py_files = {p for p in changed if p.endswith(".py")}
    if not py_files:
        return 0

    mapping = load_mapping()
    tests = target_tests(py_files, mapping)
    if not tests:
        return 0

    pytest_args = load_pytest_args()
    return run_pytest(tests, pytest_args)


if __name__ == "__main__":
    raise SystemExit(main())
