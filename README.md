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
See the [modular domain example](examples/domain/README.md) for a runnable import,
generation and Godot runtime demonstration.

## Regenerating files

Use a dedicated generated subdirectory for each schema ID. The generator records
its `.gd` filenames and SHA256 hashes in `.linkml-gdscript.json` (format 1).
Regeneration verifies **all** previously owned scripts, replaces current scripts,
and removes only verified obsolete scripts. Keep the manifest with the output;
missing or edited owned files, another schema ID, unsafe paths/symlinks, and
collisions with unmanaged filenames (including case variants) refuse generation
before writing. Generated scripts are not intended for handwritten edits.

Legacy output without a manifest is unmanaged: generate into a **fresh directory**
and deliberately replace the old generated directory after preserving any manual
work. There is no adopt/force option. Unrelated files, subdirectories, `.godot/`
and Godot-created `.gd.uid` sidecars are retained, even for retired scripts.

Rendering and preflight finish before publication, and staging failures leave old
scripts intact. Use one writer at a time. Individual replacements are atomic, but
multi-file publication is **not a transaction**: an I/O failure or power loss may
leave partial output. Errors propagate; recover by generating into a fresh
directory, not by deleting the manifest to bypass checks. Stdout remains source
only, without a manifest.

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

### View a schema

From the repository root, generate a diagram and open it in the Nix-provided
Surf browser:

```shell
nix develop --command view-schema tests/input/kitchen_sink.yaml
```

This opens a temporary local `file://` HTML page, not a server or your default
browser. Internet access is required to load the pinned Mermaid renderer from
jsDelivr. The command waits for Surf to close, then deletes the temporary page.
Generation failures stop before opening the browser.

### Golden output

Committed examples live in `tests/golden/<input-name>/`: generated `.gd` files
and a `README.md` with one whole-schema Mermaid ER diagram. GitHub renders the
Markdown diagram directly; see the [kitchen-sink diagram](tests/golden/kitchen_sink/README.md).
Like `view-schema`, it includes disconnected classes, not only those reachable
from a `tree_root`. It depicts the LinkML schema, not GDScript storage details.
Every top-level `tests/input/*.yaml` or `*.yml` schema is discovered automatically;
use distinct filename stems. From the repository root:

```shell
nix develop --command golden                   # Read-only comparison
nix develop --command golden --update-goldens  # Accept intentional generation changes
```

Checks generate into temporary directories and compare exact bytes and the complete
`.gd` and `.md` file set, including missing, extra and retired-fixture files.
Updates replace expectations and retire obsolete generated source/Markdown files
only after every input and diagram generates successfully. This directory is
reserved for generated expectations, without ownership manifests or Godot caches.

After an intentional change, regenerate, review `git diff -- tests/golden/`, and
commit the expectations together with the input or generator change. For newly
created goldens, stage them with `git add tests/golden/` to include them in the diff
(`git diff --cached -- tests/golden/`). Never update goldens automatically in hooks
or CI: normal pytest runs check them, and the pre-commit hook runs the same read-only
check before every commit. Install the hooks with:

```shell
nix develop --command pre-commit install
```

Mapping logic lives in `src/linkml_gdscript/mapping.py` and `templates/`;
`generator.py` handles loading, rendering and the CLI; `output.py` owns file
preflight, staging and publication.
See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
