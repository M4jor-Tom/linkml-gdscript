# linkml-gdscript

Generate GDScript (Godot 4) classes from [LinkML](https://linkml.io) schemas.

> **Status: scaffold.** The tooling works; the LinkML → GDScript mapping itself is
> deliberately **not implemented yet**. Running `gen-gdscript` today fails with
> `NotImplementedError: TODO(mapping): ...`. See [docs/MAPPING.md](docs/MAPPING.md).

## Usage (once the mapping exists)

```shell
uv tool install git+https://github.com/M4jor-Tom/linkml-gdscript   # or: pip install
gen-gdscript my_schema.yaml -d path/to/godot_project/generated/
```

One `.gd` file is written per LinkML class and enum. The generator runs outside
Godot; the generated files have no dependency on it, so they work in any project.

## Layout

| Path | What | Who edits it |
|---|---|---|
| `src/linkml_gdscript/mapping.py` | Every LinkML → GDScript decision, as small functions | **GDScript / domain expert** |
| `src/linkml_gdscript/templates/` | Shape of the generated `.gd` files | **GDScript / domain expert** |
| `docs/MAPPING.md` | The decision table and the open questions | **GDScript / domain expert** |
| `tests/test_mapping.py` | Contract tests, `xfail` until each function is implemented | **GDScript / domain expert** |
| `src/linkml_gdscript/generator.py` | Schema loading, CLI, rendering, file writing | plumbing, done |
| `tests/test_generator.py`, `tests/naive_mapping.py` | Plumbing tests | plumbing, done |

## Development

```shell
uv sync
uv run pytest
uv run ruff check && uv run ruff format --check
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
