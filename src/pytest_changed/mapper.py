"""Map staged source changes to test files."""


def target_tests(changed: set[str], mapping: dict[str, list[str]]) -> set[str]:
    """Return set of test file paths to run for the given changed files.

    Rules:
    - Only .py files are considered (non-Python files ignored)
    - Any changed file under tests/ is auto-included
    - Source files with mapping entries contribute their mapped test files
    - Results are deduplicated
    """
    tests: set[str] = set()
    for path in changed:
        # Changed test files always run
        if path.startswith("tests/") and path.endswith(".py"):
            tests.add(path)
            continue
        # Map source files to their test files
        if path.endswith(".py"):
            mapped = mapping.get(path)
            if mapped:
                tests.update(mapped)
    return tests
