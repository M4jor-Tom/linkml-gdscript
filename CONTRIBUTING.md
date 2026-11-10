# Contributing

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Implementing the mapping

This is the main open work. Start with [docs/MAPPING.md](docs/MAPPING.md); it
explains the workflow and you should not need to touch anything outside
`mapping.py`, `templates/`, `docs/MAPPING.md` and `tests/test_mapping.py`.
`rg 'TODO\(mapping\)'` lists what is left.

## Setup

```shell
uv sync
uv run pytest
uv run ruff check && uv run ruff format --check
```

Optionally `uvx pre-commit install` to run ruff on every commit.

### With Nix

`nix develop` gives a shell with uv, Python 3.14 and 3.11, ruff, pre-commit and
Godot 4 (`godot4`). On NixOS it is the supported way to work: there, call `ruff`
directly instead of `uv run ruff` (the ruff binary uv installs cannot run), and
test another interpreter with `uv run --isolated --python 3.11 pytest`.

## Code conventions

These follow [linkml/linkml](https://linkml.io/linkml/maintainers/contributing.html),
so the generator can be proposed upstream later without rework:

- pytest in functional style, never `unittest`; `@pytest.mark.parametrize` for input combinations
- no mocks; do not weaken a test to make it pass
- doctests for small examples
- type hints and docstrings on every function and class
- fail fast: no `try`/`except` that could hide a bug

## Git conventions

- Gitflow: branch `feature/*` or `fix/*` from `develop`; `main` only receives releases
- merge with `--no-ff`, never fast-forward
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:` ...

## Use of AI

This project follows the LinkML
[AI Covenant](https://github.com/linkml/linkml/blob/main/AI_COVENANT.md):
you own, understand and can defend everything you submit, whatever tools helped;
issues and discussion comments are written by humans; AI co-author trailers in
commits are discouraged.
