# linkml-gdscript

Generate structural GDScript data classes for **Godot 4.5+** from
[LinkML](https://linkml.io) schemas. Generated scripts extend `RefCounted` and
have no extra runtime dependencies.

## Usage

```shell
uv tool install git+https://github.com/M4jor-Tom/linkml-gdscript
gen-gdscript my_schema.yaml -d path/to/godot_project/generated/
```

One `.gd` file is written per class and static enum. For example, `Person`
becomes `LinkMLPerson` in `link_ml_person.gd`, slot `age` becomes `slot_age`,
and enum value `in limbo` becomes `VALUE_IN_LIMBO` with its original string value:

```gdscript
var person = LinkMLPerson.new()
assert(person.slot_age == null)
person.slot_age = 0
person.slot_status = LinkMLLifeStatus.VALUE_IN_LIMBO
```

Scalar values use `Variant` so absence remains distinct from zero, false and
empty strings. Objects keep nullable class hints; collections use typed arrays
or dictionaries. Decimal values preserve their exact lexical strings. Inheritance,
mixin fields, static enums and literal defaults are supported; incompatible
inherited storage, naming collisions and unsupported shapes fail generation.

This is **not a LinkML runtime**: validation, reference resolution, JSON/YAML
loading and saving, and Inspector integration remain the caller's responsibility.
Keep the source schema for validation. See [the mapping contract](docs/MAPPING.md)
for supported representations, explicit rejections and external metadata policies.

## Development

```shell
nix develop --command uv run pytest
nix develop --command ruff check
nix develop --command ruff format --check
```

The suite includes a real headless Godot import and runtime check, verified
locally on Godot 4.7.2 and the advertised 4.5 floor. Python-only tests can run with
`uv run pytest --ignore=tests/test_godot.py`; the engine test fails if Godot is
missing rather than silently skipping acceptance.

Mapping logic lives in `src/linkml_gdscript/mapping.py` and `templates/`;
`generator.py` handles loading, rendering, the CLI and file writing.
See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
