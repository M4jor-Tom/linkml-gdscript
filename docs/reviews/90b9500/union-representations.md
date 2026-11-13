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

- [x] Both operators work with valid scalar alternatives and no outer/default
      range, preserving the current nullable `Variant` contract (`test_union_without_outer_range`).
- [x] Referenced alternatives are still checked: missing alternatives, outer ranges,
      and unsupported shapes remain covered (`test_union_alternatives_validate_unknown_and_unsupported_shapes`,
      `test_union_base_range_reference_is_validated`).
- [x] Explicit enclosing ranges and supported nested-union/default/constraint
      cases retain their intended checks (`test_nested_union_without_outer_range`,
      `test_constraints_preserve_enclosing_union`, and union default regressions).
- [x] Imported CLI generation has no entry `default_range`; a missing imported branch
      fails before output creation (`test_cli_imported_union_without_entry_default_range`).
- [x] Current Godot 4.7.2 and floor Godot 4.5 parse and execute generated `Choice`
      assignments; regression suite prints `MAPPING_RUNTIME_OK`.

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

- [x] Extended scalar-position unions to preserve list alternatives as values inside
      `Variant`; empty/default semantics remain `null`, with no implicit wrapping or flattening.
- [x] `test_union_without_outer_range` covers scalar/list alternatives for both
      operators; `test_single_list_union_has_null_default_and_rejects_scalar_default`
      checks the list-only case and default mismatch. `docs/MAPPING.md` records the boundary.
- [x] Outer multivalued list alternatives and keyed class-list alternatives remain
      rejected contextually; inlined class lists with `inlined_as_list` are accepted.
      Missing types remain rejected by the ordinary type resolver.
- [x] Engine tests assign null, integer, empty array and string array to a generated
      `LinkMLChoice`; both engine shells passed without script/parse errors.
- [x] R02/R03 evidence and exact acceptance commands are recorded in the review README.
