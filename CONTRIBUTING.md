# Contributing

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Implementing the mapping

Start with [docs/MAPPING.md](docs/MAPPING.md), the structural projection contract.
Keep domain logic in `mapping.py` and `templates/`, not the generator plumbing.
Add failing regression tests in `tests/test_mapping.py` before changing a mapping;
use `tests/test_godot.py` to verify that generated scripts parse and run.
The templates also use `string_literal` and `escape_description` helpers, shared
explicitly with the test-only naive mapper.

## Setup

```shell
uv sync
uv run pytest --ignore=tests/test_godot.py
uv run ruff check && uv run ruff format --check
```

Optionally `uvx pre-commit install` to run ruff on every commit.

### With Nix

`nix develop` gives a shell with uv, Python 3.14 and 3.11, ruff, pre-commit and
Godot 4 (`godot4`). On NixOS it is the supported way to work: there, call `ruff`
directly instead of `uv run ruff` (the ruff binary uv installs cannot run), and
test another interpreter with `uv run --isolated --python 3.11 pytest`.

Run the complete acceptance gates (including Godot) with:

```shell
nix develop --command uv run pytest
nix develop --command ruff check
nix develop --command ruff format --check
```

The engine test creates a temporary project, registers generated global classes,
checks diagnostics, and executes runtime assertions with a success sentinel.
It requires `godot4` and never skips a missing engine. CI covers Python 3.10/3.14
separately from the Nix-provisioned Godot job.

## Code conventions

These follow [linkml/linkml](https://linkml.io/linkml/maintainers/contributing.html),
so the generator can be proposed upstream later without rework:

- pytest in functional style, never `unittest`; `@pytest.mark.parametrize` for input combinations
- no mocks; do not weaken a test to make it pass
- doctests for small examples
- type hints and docstrings on every function and class
- fail fast: no `try`/`except` that could hide a bug

## Git conventions

- Work and commit directly on `master`; this is a single-developer repository.
- Do not create development branches or worktrees unless explicitly requested.
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:` ...

## Use of AI

This project follows the LinkML
[AI Covenant](https://github.com/linkml/linkml/blob/main/AI_COVENANT.md):
you own, understand and can defend everything you submit, whatever tools helped;
issues and discussion comments are written by humans; AI co-author trailers in
commits are discouraged.
