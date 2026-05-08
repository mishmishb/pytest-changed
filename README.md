# pytest-changed

Run pytest for tests related to staged Python files in pre-commit.

`pytest-changed` is a small, deterministic selector for commit-time feedback. It takes the Python filenames passed in by pre-commit, turns source-file changes into test-file paths using simple conventions, applies optional explicit overrides, and runs pytest on the resulting test files.

If `src/foo/bar.py` changes, `pytest-changed` looks for:

- `tests/foo/test_bar.py`
- `tests/test_bar.py`

Any changed test file under your configured test roots is always run directly.

## What it is for

Use `pytest-changed` when you want a staged-file-aware pre-commit hook that:

- runs fast enough to sit on the commit path
- behaves predictably from filenames alone
- is easy to debug when selection looks wrong
- does not rely on stored state, import graphs, or runtime tracing

This tool is intentionally file-level and convention-driven. It is for commit-time test selection, not whole-project impact analysis.

## Install

```bash
pip install pytest-changed
```

`pytest` is installed as a runtime dependency because `pytest-changed` invokes pytest directly.

## Quick start

The default convention assumes source files live under `src/` and tests live under `tests/`.

```toml
[tool.pytest-changed]
pytest_args = ["-q"]
```

With that config:

```text
src/foo/bar.py   -> tests/foo/test_bar.py
src/foo/bar.py   -> tests/test_bar.py
```

Run manually:

```bash
pytest-changed src/foo/bar.py tests/test_other.py
```

If `src/foo/bar.py` has no matching tests, `pytest-changed` exits `0` but warns on stderr by default.

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
| `source_roots` | `["src"]` | Source roots stripped before convention matching |
| `test_roots` | `["tests"]` | Test roots searched for matching tests |
| `warn_on_missing` | `true` | Warn on stderr when a changed source file has no match |
| `mapping` | `{}` | Optional explicit overrides for individual source files |

### Convention matching

For each changed Python source file, `pytest-changed` tries these paths under each configured `test_root`:

```text
<test_root>/<relative_dir>/test_<module>.py
<test_root>/test_<module>.py
```

Example with defaults:

```text
src/core.py           -> tests/test_core.py
src/utils/helpers.py  -> tests/utils/test_helpers.py
src/utils/helpers.py  -> tests/test_helpers.py
```

If both convention matches exist, both run.

### Explicit overrides

Use `[tool.pytest-changed.mapping]` when a file needs something more specific than the naming convention. Explicit mappings override convention discovery for that source file.

```toml
[tool.pytest-changed]
pytest_args = ["-q"]
warn_on_missing = true

[tool.pytest-changed.mapping]
"src/db.py" = ["tests/test_db.py", "tests/test_db_integration.py"]
"src/core.py" = ["tests/custom/test_special_core.py"]
```

### Custom roots

If your project uses different layout conventions, configure them explicitly:

```toml
[tool.pytest-changed]
source_roots = ["lib", "pkg"]
test_roots = ["spec", "tests"]
warn_on_missing = true
```

### Environment override

Set `PYTEST_CHANGED_CONFIG` to point at a TOML config file. This is useful when you cannot or do not want to put configuration in the project `pyproject.toml`.

```bash
PYTEST_CHANGED_CONFIG=pytest-changed.toml pytest-changed src/core.py
```

The override file uses the same table structure:

```toml
[tool.pytest-changed]
pytest_args = ["-q", "--tb=short"]
source_roots = ["src"]
test_roots = ["tests"]
warn_on_missing = true

[tool.pytest-changed.mapping]
"src/core.py" = ["tests/custom/test_special_core.py"]
```

The canonical table name is hyphenated (`pytest-changed`) because it matches the package/distribution name. The Python import package remains underscored (`pytest_changed`), as normal for Python modules. The early underscore table (`[tool.pytest_changed]`) is accepted as a compatibility alias, but new projects should use `[tool.pytest-changed]`.

## How it works

1. Receives changed filenames from pre-commit or CLI arguments
2. Filters to Python files only
3. Auto-includes changed files under configured test roots
4. Applies an explicit mapping override if one exists for a changed source file
5. Otherwise tries nested and flat convention matches
6. Warns about unmatched source files unless disabled
7. Deduplicates selected tests
8. Runs `python -m pytest <selected tests> <pytest_args>`
9. Returns exit code `0` if no tests match, or if pytest exits with code `5` (`no tests collected`)

## Scope and limits

These are current scope boundaries, not laws of nature:

- **Staged filenames in, test files out** — the current contract is commit-time file selection
- **File-level selection** — it selects test files, not individual test functions or classes
- **No hidden state** — no database, baseline run, or runtime trace cache
- **No dependency graph inference** — selection is based on configured conventions and explicit overrides
- **CI still matters** — this speeds up local commit feedback; it does not replace the full suite

## Design principles

- **Pre-commit first** — designed around staged filenames passed by the hook
- **Convention first** — useful with minimal config
- **Explicit overrides when needed** — config is the escape hatch, not the baseline
- **Changed tests always run** — edited tests do not need source mapping
- **Warnings over silent misses** — unmatched sources should be visible
- **Deterministic local feedback** — selection should be understandable from paths alone

## License

MIT
