# Contributing

Contributions are welcome if they keep the core promise: convention-first source→test discovery, explicit overrides where needed, and no hidden dependency database.

## Development setup

```bash
git clone https://github.com/mishmishb/pytest-changed.git
cd pytest-changed
uv pip install -e ".[dev]"
pre-commit install --install-hooks
```

## Quality gates

Run before opening a PR:

```bash
uv run pytest tests -q
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyright --project pyproject.toml src
uv run bandit -c pyproject.toml -r src -ll
uvx pip-audit
```

## Release process

Releases are tag-driven. The release workflow calls the full reusable test workflow first, then builds, creates a GitHub Release, and publishes to PyPI via trusted publishing.

```bash
git tag -a v0.1.0 -m "v0.1.0"
git push origin v0.1.0
```

PyPI trusted publishing must be configured once with:

- Owner: `mishmishb`
- Repository: `pytest-changed`
- Workflow filename: `release.yml`
