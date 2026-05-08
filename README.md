# pytest-changed

Run only the pytest tests mapped to changed source files. Explicit mapping, no heuristics by default — you define which source files map to which test files.

## Why

Running the full test suite on every commit is slow. `pytest-picked` only runs test files that themselves changed. **pytest-changed** maps source changes to their corresponding test files, giving fast targeted feedback on pre-commit while your full suite still runs on pre-push or CI.

## Install

```bash
pip install pytest-changed
```

`pytest` is installed as a runtime dependency because `pytest-changed` invokes pytest directly.

## Quick start

Add mappings to `pyproject.toml`:

```toml
[tool.pytest-changed]
pytest_args = ["-q"]

[tool.pytest-changed.mapping]
"src/my_module.py" = ["tests/test_my_module.py"]
"src/utils.py" = ["tests/test_utils.py"]
```

Run manually:

```bash
pytest-changed src/my_module.py tests/test_my_module.py
```

Any changed test file under `tests/` is always run, even without an explicit mapping.

## Pre-commit usage

Use this repository as a normal pre-commit hook:

```yaml
repos:
  - repo: https://github.com/mishmishb/pytest-changed
    rev: v0.1.0
    hooks:
      - id: pytest-changed
```

For local development before the first release:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-changed
        name: pytest-changed
        entry: pytest-changed
        language: system
        pass_filenames: true
        always_run: false
        stages: [pre-commit]
```

## Configuration

All configuration lives in `pyproject.toml` under `[tool.pytest-changed]`:

| Option | Default | Description |
|--------|---------|-------------|
| `pytest_args` | `["-q"]` | Extra args passed to pytest |
| `mapping` | `{}` | Source file → test file(s) mapping |

### Mapping format

Each key is a source file path relative to the repo root. Each value is a list of test file paths:

```toml
[tool.pytest-changed.mapping]
"src/core.py" = ["tests/test_core.py"]
"src/utils/helpers.py" = ["tests/utils/test_helpers.py"]
"src/db.py" = ["tests/test_db.py", "tests/test_db_integration.py"]
```

The canonical table name is hyphenated (`pytest-changed`) because it matches the package/distribution name. The Python import package remains underscored (`pytest_changed`), as normal for Python modules. The early underscore table (`[tool.pytest_changed]`) is accepted as a compatibility alias, but new projects should use `[tool.pytest-changed]`.

### Environment override

Set `PYTEST_CHANGED_CONFIG` to point at a TOML config file. This is useful when you cannot or do not want to put configuration in the project `pyproject.toml`.

```bash
PYTEST_CHANGED_CONFIG=pytest-changed.toml pytest-changed src/core.py
```

The override file uses the same table structure:

```toml
[tool.pytest-changed]
pytest_args = ["-q", "--tb=short"]

[tool.pytest-changed.mapping]
"src/core.py" = ["tests/test_core.py"]
```

## How it works

1. Receives changed filenames from pre-commit or CLI arguments
2. Filters to Python files only
3. Looks up each source file in the explicit mapping
4. Auto-includes changed files under `tests/`
5. Deduplicates selected test files
6. Runs `python -m pytest <selected tests> <pytest_args>`
7. Returns exit code 0 if no tests match, or if pytest exits with code 5 (`no tests collected`)

## Relationship to pytest

The goal is to feel like pytest with one extra selection layer. The current release is intentionally small: a pre-commit-friendly wrapper that selects test files before invoking pytest.

A deeper pytest-like interface is best implemented as a pytest plugin, not as a patch to pytest core. Pytest core already provides hooks and plugin APIs for collection and selection behaviour; VCS-aware changed-test selection is better suited to a plugin because projects disagree on Git vs Mercurial, explicit mapping vs coverage tracing, and strictness around implicit selection.

## Roadmap and limits

These are not inevitable limits; they are deliberate v0.1 scope boundaries:

- **Dependency graph / import graph selection** — fixable, but likely belongs behind an explicit opt-in because import graphs can over-select and miss dynamic imports.
- **Heuristic source→test discovery** — fixable, but not enabled by default because naming heuristics produce false confidence. Explicit mapping remains the safe baseline.
- **Coverage/test-trace based selection** — fixable and powerful, but it requires a first full run and stored state. Existing tools such as `pytest-testmon` cover part of this space.
- **Full pytest CLI parity** — fixable. The likely v0.2 direction is a pytest plugin or a richer wrapper that passes arbitrary pytest options through cleanly.

## Design principles

- **Explicit mapping by default** — no surprise heuristics
- **Changed tests always run** — edited tests do not need mappings
- **Silent skip** — no Python files or no mapped tests exits 0
- **Deduplication** — shared mapped tests run once
- **CI still matters** — this speeds up local feedback; it does not replace full-suite CI

## License

MIT
