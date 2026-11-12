# Union representations

## R02 — Range-less unions fail before their alternatives are used

**P2 — defect.** The mapping advertises `any_of` / `exactly_one_of` storage as
`Variant`, but an unrelated enclosing range is currently required in practice.

### Evidence and reproduction

[`_value_type()`](../../../src/linkml_gdscript/mapping.py#L176) validates a copy of
the outer slot with its union removed before examining the alternatives. When
neither that slot nor the entry schema supplies a range, primitive resolution
fails on `None` instead of using the declared alternative ranges.

```yaml
id: https://example.org/review/range-union
name: range_union
prefixes:
  linkml: https://w3id.org/linkml/
imports: [linkml:types]
classes:
  Choice:
    attributes:
      value:
        any_of:
          - range: string
          - range: integer
```

Run the standalone YAML through `nix develop --command uv run gen-gdscript`.
Observed: `ValueError: No such type: "None"`. Replacing `any_of` with
`exactly_one_of` exercises the same path. Do **not** add `default_range: string`
to hide the failure.

The existing `tests/test_mapping.py::schema_view()` helper always adds
`default_range: string`, which masks this case. Use a genuinely range-less
schema in the regression, and cover the real CLI/imported-entry path as well as
mapping calls. Ordinary unresolved references must still fail.

### Acceptance

- [ ] Both operators work with valid scalar alternatives and no outer/default
      range, preserving the current nullable `Variant` contract.
- [ ] Referenced alternatives are still checked: unknown/cyclic types and
      unsupported shapes cannot hide behind `Variant`.
- [ ] Explicit enclosing ranges and supported nested-union/default/constraint
      cases retain their intended checks; do not fix this by skipping all checks.
- [ ] A small imported-schema case proves entry-level defaults do not accidentally
      decide whether a fully specified union works.
- [ ] CLI generation and a headless Godot assignment check pass for the new
      supported case. Permanent tests include the failure oracle above.

## R03 — Scalar-or-list alternatives are rejected as nested collections

**Compatibility limit, not a demand to support every LinkML shape.** A scalar/list
union is not inherently a nested collection, although the current mapper rejects
it through the nested-collection guard.

### Reproduce independently of R02

```yaml
id: https://example.org/review/scalar-or-list
name: scalar_or_list
prefixes:
  linkml: https://w3id.org/linkml/
imports: [linkml:types]
default_range: string
classes:
  Choice:
    attributes:
      value:
        any_of:
          - range: string
          - range: string
            multivalued: true
```

Observed: `Choice.value: nested collections are unsupported` from
[`_value_type()`](../../../src/linkml_gdscript/mapping.py#L189). The top-level
field is not multivalued; one alternative is. Real source records also use
`exactly_one_of: [{range: string, multivalued: true}]` for optional list shapes.
Fixing R02 alone does not add support for these alternatives.

### Required disposition and acceptance

- [ ] Retain the supported-subset restriction **or** obtain approval to support
      scalar/list unions. Do not flatten a list into text, invent a default,
      wrap a scalar in a singleton list or rewrite a consumer schema silently.
- [ ] If retaining it: add/reuse a regression for this exact shape and the
      single-list `exactly_one_of` case; document branch-local `multivalued`
      restrictions in `docs/MAPPING.md`, with an accurate slot-specific diagnostic.
- [ ] If extending it: define storage and missing/empty/scalar/list semantics;
      exercise scalar and list assignment in Godot and preserve nested-collection,
      keyed-union and invalid-reference rejection where still unsupported.
- [ ] Record the chosen existing/new contract and passing evidence in the README.
      Neither this item's closure nor R02 establishes full LinkML validation.
