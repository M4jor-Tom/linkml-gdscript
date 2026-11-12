# Naming and inherited storage

These are **existing, deliberate compatibility limits**. They explain why a
valid consumer schema may not generate, but do not by themselves justify changing
the approved naming or inheritance policy. A verified retain-policy disposition
can close either item without a new backend or abstraction.

## R04 — Unicode-only enum values stop generation

### Evidence and reproduction

[`_words()`](../../../src/linkml_gdscript/mapping.py#L40) requires at least one
ASCII alphanumeric segment. [`enum_member_name()`](../../../src/linkml_gdscript/mapping.py#L336)
checks every member for usable, collision-free constant names. Thus this whole
enum fails, not merely access to the affected member:

```yaml
id: https://example.org/review/unicode-enum
name: unicode_enum
enums:
  SourceVersion:
    permissible_values:
      A: {}
      S: {}
      Ω: {}
      X: {}
```

Observed through the CLI: `ValueError: Name has no usable ASCII characters: 'Ω'`.
A full imported consumer schema stopped here before any output files were written.
The string-literal emitter can preserve Unicode values; the restriction is on
constructing the generated symbol, not quoting the value.

### Acceptance / disposition

- [ ] Reproduce the Unicode-only case and identify it explicitly as the documented
      ASCII naming restriction, not an inability to store Unicode strings.
- [ ] Retain that policy with a named regression and clear user-facing example,
      or obtain approval for a deterministic symbol-encoding/override policy.
      Existing coverage may be reused if it proves this exact boundary.
- [ ] If support is added, preserve the value `"Ω"` exactly; test deterministic
      symbols, collisions with ASCII/lookalike inputs, and actual Godot parsing.
      Do not silently rename the schema value to `"OMEGA"` or omit a member.
- [ ] Keep collision diagnostics and generation-before-write behavior intact.
      Record the selected policy and evidence in the README.

## R05 — Subclasses cannot rename inherited storage

### Evidence and reproduction

[`class_slots()`](../../../src/linkml_gdscript/mapping.py#L128) compares inherited
field names, representations and defaults before omitting duplicate declarations.
A subclass alias change therefore fails deliberately:

```yaml
id: https://example.org/review/inherited-alias
name: inherited_alias
prefixes:
  linkml: https://w3id.org/linkml/
imports: [linkml:types]
default_range: string
classes:
  Entity:
    attributes:
      species:
        range: string
  Player:
    is_a: Entity
    slot_usage:
      species:
        alias: race
```

Observed: an incompatible-inherited-storage error comparing `slot_species` with
`slot_race`. The consumer case also narrows the reference range from a species
union to race; the concrete rejection already occurs on the alias difference.
Separately, exact object-type comparison rejects inline subtype narrowing even
when the target class inherits from the broader target. That is also the current
storage contract, not proof that native GDScript inheritance itself is broken.

### Acceptance / disposition

- [ ] Verify/reuse `test_inherited_storage_conflicts` and the exact alias example;
      compatible constraint-only refinements must continue to work.
- [ ] Retain the rejection with a clear `slot_usage` example and a receipt citing
      the approved contract, or obtain approval for a different representation.
- [ ] If changing it, define how base and child access refer to one logical value;
      do not emit independent `species` and `race` fields that can diverge.
      Test base/child access and inheritance in real Godot.
- [ ] Do not remove the compatibility check to make generation pass. Preserve
      rejection of incompatible collection shapes/defaults/aliases outside the
      explicitly supported change. Record the disposition in the README.
