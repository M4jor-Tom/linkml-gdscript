# LinkML → GDScript mapping

**Status: nothing decided, nothing implemented.** This document is the worklist
for the person designing the mapping. You do not need to know the Python
packaging, the CLI or the LinkML generator framework: all of that is done.

## Workflow

1. Decide a row of the tables below and write the decision down here.
2. Implement it in `src/linkml_gdscript/mapping.py` (one small function per
   topic, each documented) or in `src/linkml_gdscript/templates/*.gd.jinja`.
3. Remove the `@todo_mapping` marker of the matching test in
   `tests/test_mapping.py`, and add tests for the decision you made, using
   `tests/input/kitchen_sink.yaml` (it contains one example of every row below).
4. Run `uv run pytest`.

`rg 'TODO\(mapping\)'` lists every open point in the code. To try the generator:

```shell
uv run gen-gdscript tests/input/kitchen_sink.yaml -d /tmp/out
```

Two things to settle before anything else, because most rows depend on them:

- **TODO(mapping): minimum Godot version.** Typed `Dictionary[K, V]` needs 4.4, `@abstract` needs 4.5.
- **TODO(mapping): what the generated classes are for.** Editable `Resource`s
  with `@export`, plain `RefCounted` data objects, or something else.

## Naming

| LinkML | GDScript | Where | Status |
|---|---|---|---|
| class name | | `mapping.class_name` | TODO |
| slot name / `alias` | | `mapping.field_name` | TODO |
| enum name | | `mapping.enum_name` | TODO |
| permissible value (may not be an identifier: `in limbo`) | | `mapping.enum_member_name` | TODO |
| output file name | | `mapping.file_name` | TODO |
| collision with a reserved word or a Godot built-in (`Node`, `name` ...) | | all of the above | TODO |

## Classes

| LinkML | GDScript | Where | Status |
|---|---|---|---|
| class without `is_a` | `extends` what? | `mapping.base_class` | TODO |
| `is_a` | | `mapping.base_class` | TODO |
| `mixins` (no multiple inheritance in GDScript) | | `mapping.class_slots` | TODO |
| inherited slots: redeclare or rely on `extends`? | | `mapping.class_slots` | TODO |
| `abstract: true` | | `class.gd.jinja` | TODO |
| `tree_root: true` | | `class.gd.jinja` | TODO |
| `description` | `##` doc comment (skeleton does this) | `class.gd.jinja` | TODO: confirm |

## Slot types

All in `mapping.field_type` (type hint) and `mapping.field_default` (initialiser).

| LinkML | GDScript | Status |
|---|---|---|
| `string` | | TODO |
| `integer` | | TODO |
| `float`, `double` | | TODO |
| `decimal` (no native decimal) | | TODO |
| `boolean` | | TODO |
| `date`, `datetime`, `time` (no native types) | | TODO |
| `uri`, `uriorcurie`, `curie`, `ncname` | | TODO |
| custom `types` (`typeof`) | | TODO |
| enum range | | TODO |
| class range, inlined | | TODO |
| class range, reference by identifier | | TODO |
| `any_of` / unions (no union types) | | TODO |
| no range (`default_range`) | | TODO |

## Cardinality

| LinkML | GDScript | Status |
|---|---|---|
| optional scalar (`int`, `float`, `bool` cannot be `null`) | | TODO |
| `required: true` | | TODO |
| `multivalued: true` | | TODO |
| `multivalued` + `inlined: true` (dict keyed by identifier) | | TODO |
| `multivalued` + `inlined_as_list: true` | | TODO |
| `ifabsent` (default value) | | TODO |

## Enums

| LinkML | GDScript | Where | Status |
|---|---|---|---|
| enum definition (needs a host script) | skeleton: one script per enum, inner `enum Value` | `enum.gd.jinja` | TODO: confirm or change |
| string value of a permissible value (GDScript enums are ints) | | `enum.gd.jinja` | TODO |
| `meaning`, dynamic enums (`reachable_from` ...) | | | TODO |

## Constraints and behaviour

All in the templates.

| LinkML | GDScript | Status |
|---|---|---|
| `pattern`, `minimum_value`, `maximum_value`, `required` | generated `validate()`? ignored? | TODO |
| `identifier`, `key` | | TODO |
| loading / saving LinkML-conformant JSON or YAML | `from_dict` / `to_dict`? | TODO |
| `@export` and inspector hints | | TODO |
| `rules`, `unique_keys`, `slot_usage` refinements, `annotations` | | TODO |

## If the plumbing is in your way

If a decision cannot be expressed through the existing functions and template
variables (for example several classes per file, or all enums in one script),
that is a plumbing change: open an issue rather than working around it.
