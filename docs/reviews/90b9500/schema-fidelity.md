# Schema fidelity

## R01 — Dynamic map entries have no generated storage

**P1 — defect.** Class-level `extra_slots` describes actual data structure, not
merely a constraint that can be left to external validation.

### Evidence and cause

At the reviewed revision,
[`class_slots()`](../../../src/linkml_gdscript/mapping.py#L128) returns named
`SchemaView.class_induced_slots()` entries. Neither it nor the
[class template](../../../src/linkml_gdscript/templates/class.gd.jinja) represents
or rejects `ClassDefinition.extra_slots`.

Consequently, a class consisting entirely of dynamic map entries becomes an
empty `RefCounted` class. A class with both fixed fields and `extra_slots` retains
only its fixed fields. Successful parsing would not detect this structural loss.
Six such classes occurred in the inspected consumer schema; no consumer-specific
behavior is needed to reproduce the defect.

### Reproduce

Save this standalone schema as a temporary `dynamic-map.yaml`:

```yaml
id: https://example.org/review/dynamic-map
name: dynamic_map
prefixes:
  linkml: https://w3id.org/linkml/
imports: [linkml:types]
classes:
  TextMap:
    extra_slots:
      range_expression:
        range: string
        required: true
```

From the repository root:

```sh
nix develop --command uv run gen-gdscript /absolute/path/dynamic-map.yaml
```

Observed: successful generation of `LinkMLTextMap` extending `RefCounted`, with
no fields or dictionary storage. The input's map cannot be represented by that
output. This was also reproduced through `GDScriptGenerator(...).render()`.

### Required action

The smallest safe fix is an explicit, class-specific generation error for
unsupported `extra_slots`. Supporting maps instead is acceptable only with an
explicit representation and tests; this review does not require that extension.
Keep the decision in mapping code, not a Pixlnd-specific filter. Check inherited
and mixed fixed/dynamic shapes so a local guard does not leave sibling paths lossy.

### Acceptance

- [ ] A permanent regression fails on `90b9500` for the missing guard/storage.
- [ ] Dynamic-only and fixed-plus-dynamic classes are represented faithfully or
      rejected with the class name and unsupported feature in the diagnostic.
- [ ] Effective inherited dynamic structure is covered, or explicitly rejected;
      an ordinary fixed-field sibling remains unaffected.
- [ ] Rejection occurs before writing generated files. Test both a fresh output
      directory and preservation of existing files on a mapping failure.
- [ ] If supported, Godot checks prove multiple keys/values survive in distinct
      instances, including fixed fields; an empty parseable class is not success.
- [ ] `docs/MAPPING.md` states the selected behavior. Existing scalar/container
      tests still pass. Follow the README closure/deletion protocol.
