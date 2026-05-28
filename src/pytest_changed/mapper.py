"""Map changed source files to test files."""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class SelectionResult:
    """Selected tests and changed sources that could not be matched."""

    tests: set[str]
    unmatched_sources: set[str]


def _normalise(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).as_posix()


def _is_under_root(path: str, roots: list[str]) -> bool:
    normalised = _normalise(path)
    return any(normalised == root or normalised.startswith(f"{root}/") for root in roots)


def _discover_candidates(path: str, source_roots: list[str], test_roots: list[str]) -> list[str]:
    parts = PurePosixPath(_normalise(path)).parts
    if not parts:
        return []

    relative_parts = parts
    for root in source_roots:
        root_parts = PurePosixPath(root).parts
        if parts[: len(root_parts)] == root_parts:
            relative_parts = parts[len(root_parts) :]
            break

    if not relative_parts:
        return []

    *directories, filename = relative_parts
    stem = PurePosixPath(filename).stem
    candidates: list[str] = []
    for test_root in test_roots:
        nested = PurePosixPath(test_root, *directories, f"test_{stem}.py").as_posix()
        flat = PurePosixPath(test_root, f"test_{stem}.py").as_posix()
        for candidate in (nested, flat):
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


def _select_tests_for_path(
    path: str,
    mapping: dict[str, list[str]],
    project: Path,
    source_roots: list[str],
    test_roots: list[str],
    selected: set[str],
    unmatched: set[str],
) -> None:
    if _is_under_root(path, test_roots):
        if (project / path).is_file():
            selected.add(path)
        return

    configured = mapping.get(path)
    if configured is not None:
        configured_matches = {
            _normalise(item) for item in configured if (project / item).is_file()
        }
        if configured_matches:
            selected.update(configured_matches)
        else:
            unmatched.add(path)
        return

    discovered = {
        candidate
        for candidate in _discover_candidates(path, source_roots, test_roots)
        if (project / candidate).is_file()
    }
    if discovered:
        selected.update(discovered)
    else:
        unmatched.add(path)


def _filter_py_files(changed: set[str]) -> set[str]:
    return {_normalise(p) for p in changed if p.endswith(".py")}


def target_tests(
    changed: set[str],
    mapping: dict[str, list[str]],
    project_root: str | Path,
    source_roots: list[str] | None = None,
    test_roots: list[str] | None = None,
) -> SelectionResult:
    project = Path(project_root)
    selected: set[str] = set()
    unmatched: set[str] = set()
    src_roots = source_roots or ["src"]
    tst_roots = test_roots or ["tests"]

    for path in _filter_py_files(changed):
        _select_tests_for_path(path, mapping, project, src_roots, tst_roots, selected, unmatched)

    return SelectionResult(tests=selected, unmatched_sources=unmatched)
