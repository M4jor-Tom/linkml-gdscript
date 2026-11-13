# Modular domain example

This small LinkML schema closure demonstrates imported classes and an enum,
identifier references, inline objects, range-less unions, a scalar/list value,
an inherited alias and dynamic extra slots. The application-owned boundary is
shown in [`usage.gd`](usage.gd): it selects fixed properties, maps extra keys,
and supplies identifier references. No loader, admission service or validation
facade is generated.

From the repository root, create and run a fresh temporary Godot project:

```sh
tmp_project=$(mktemp -d)
printf 'config_version=5\n[application]\nconfig/name="LinkML domain example"\n' > "$tmp_project/project.godot"
uv run gen-gdscript examples/domain/domain.yaml -d "$tmp_project/generated"
cp examples/domain/usage.gd "$tmp_project/usage.gd"
godot4 --headless --path "$tmp_project" --editor --quit
godot4 --headless --path "$tmp_project" --script usage.gd
```

The final command prints `DOMAIN_MODEL_OK`. This requires the documented Godot
4.5+ engine; it does not launch a consumer game. `domain.yaml` is the single
entry point and imports `types.yaml`.

Generated classes provide structural storage, not complete LinkML semantics.
Constraints, requiredness, enum membership and uniqueness are not enforced;
unsupported schema constructs fail generation. Source-schema validation and
admission of untrusted data remain the caller's responsibility. There is no
JSON/YAML codec, automatic reference resolution, Inspector integration or
gameplay behavior. See [the mapping contract](../../docs/MAPPING.md).
