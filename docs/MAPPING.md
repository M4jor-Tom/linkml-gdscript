# LinkML → GDScript mapping

## Contract

Generate **structural data classes for Godot 4.5+**, not a LinkML runtime.
The classes extend `RefCounted`, not `Resource` or `Node`. One script is emitted
per class and static enum. There are no extra runtime dependencies.

Validation, JSON/YAML loading and saving, Inspector integration, and reference
resolution belong to the caller. Keep the source schema for semantic validation.
A generated object is not automatically a valid LinkML instance.

The following decisions are approved; implementation and verification are tracked
in `docs/superpowers/plans/2026-11-12-mapping.md`.

## Naming

- Generated global types use `LinkML` plus PascalCase; fields use `slot_` plus
  snake_case; enum constants use `VALUE_` plus UPPER_SNAKE_CASE. Fixed prefixes
  avoid native Godot class/member/keyword collisions without depending on a
  running Godot installation or a maintained built-in blacklist.
- Slot `alias` takes precedence over the original slot name. A new inherited alias
  forwards to the original storage property; earlier exposed names stay available.
  Reusing an ancestor name for the same logical slot emits no new property.
- Class and slot names are normalized to ASCII identifiers. Enum constants
  preserve existing ASCII normalization; permissible values containing any
  non-ASCII character use `VALUE__` plus uppercase `U`-prefixed code points
  joined by underscores (for example, `Ω` becomes `VALUE__U03A9`). Stored values
  remain unchanged. This intentional generated-API migration does not
  transliterate, normalize, or hash Unicode values. Punctuation separates words;
  leading digits are safe behind the prefixes. Names with no usable characters
  are rejected rather than silently assigned a meaningless identifier.
- Output filenames are snake_case with `.gd`.
- Reject collisions after normalization: class and enum names share a namespace;
  filenames are compared case-insensitively; fields include inherited fields;
  enum constants are checked within their host. Name both conflicting elements.
- Collisions with arbitrary user-defined global types, or with independently
  generated schemas, are the integrating project's responsibility.

## Classes

| LinkML | GDScript |
|---|---|
| no `is_a` | `extends RefCounted` |
| `is_a` | Extend the corresponding generated class |
| `mixins` | Flatten effective mixin slots, without multiple inheritance |
| inherited slots | Rely on `extends`; do not redeclare fields |
| `abstract: true` | Native `@abstract` annotation (Godot 4.5+) |
| `tree_root: true` | Schema metadata, no different Godot base class |
| `description` | Documentation comments, with literal BBCode escaped |

A locally open `extra_slots` policy emits `linkml_extra_slots: Dictionary[String,
Variant]` unless an actual `is_a` ancestor already owns that storage. Mixins do
not pass permission to consumers. Descendants inherit physical storage even when
their local policy is closed; external validation must still enforce each class's
local policy. Applications route fixed names and aliases to `slot_*` fields and
preserve dynamic names as raw string keys in `linkml_extra_slots` (including
Unicode and punctuation); generation does not route or validate assignments.
`allowed` plus `range_expression` is unsupported. A range expression is checked
for a resolvable supported value shape, but its constraints are not enforced in
GDScript; keep the source schema for external validation.

Use induced slots from `SchemaView` so mixins and `slot_usage` are resolved.
Before suppressing inherited declarations, compare value/storage representations
and initializers against the immediate `is_a` parent. The earliest actual ancestor
introducing a slot owns its storage, including slots flattened from mixins. New
aliases are native getter/setter properties forwarding directly to that owner's
property, with its physical type hint, no cast and no second initializer. Thus
three-level aliases share one value; unchanged collection aliases share one
container, independently initialized per instance. All still-exposed ancestor
names participate in collision checks, even when current induced aliases differ.

Allow equal representations and bounded scalar refinements: supported union
alternatives may narrow to compatible scalar leaves, and inline objects may narrow
to actual `is_a` subtypes. Keep the broader physical hint for aliases rather than
filtering values assigned through base references. For example, an inherited
`species` aliased to `race` forwards `slot_race` to `slot_species`; nullable values
stay null until assigned. Reject changed defaults, primitive representations,
scalar/container shapes, keyed storage or typed collection element hints with a
class/slot-specific error. A mixin does not create Godot subtype identity.

These checks establish representation compatibility, not full logical implication
or enforcement of child constraints. LinkML may retain inherited union alternatives
under a range-only `slot_usage` refinement; map that actual induced expression, not
an assumed subset. Compatible constraints remain external validation concerns;
the source schema is authoritative. Reject cycles and inheritance that cannot be
represented, including missing parents or cycles introduced by effective
`slot_usage` ancestry.

## Values and cardinality

| LinkML value | GDScript representation |
|---|---|
| `string` | `String` value |
| `integer` | `int` value (signed 64-bit) |
| `boolean` | `bool` value |
| `float`, `double` | `float` value |
| `decimal` | Exact lexical `String`, not binary floating point |
| `date`, `datetime`, `time`, `date_or_datetime` | Lexical `String` |
| URI/CURIE, NCName, identifier and path types | Lexical `String` |
| custom `types` | Resolve `typeof` to its primitive representation |
| static enum | Original permissible-value `String` |
| inlined class | Generated object type |
| non-inlined class | Identifier's value representation, not an object lookup |
| `any_of`, `exactly_one_of` | `Variant`; range alternatives are externally validated |
| omitted range | Induced `default_range` |

All scalar **value** declarations use `Variant`, including required values and
fields with defaults. Without an explicit default they use `Variant = null`;
this allows absent values to stay distinct from `0`, `false` and `""`. Explicit
literal defaults initialize that same Variant declaration with the represented
value. This deliberately gives up scalar static typing. Object-valued fields
keep nullable object type hints. `required` does not invent a default.

Multivalued fields use `Array[T] = []`, with the primitive/object representation
as `T`. Inlined multivalued classes with an identifier or key use
`Dictionary[K, T] = {}` unless `inlined_as_list` is true. Unkeyed inline classes
use arrays. Empty collection defaults intentionally collapse absent and empty.
Nested typed collections are not emitted (GDScript does not support them).
Range unions (`any_of`, `exactly_one_of`) use `Variant` in scalar positions and
`Array[Variant] = []` for outer multivalued scalar unions. Branch-local
`multivalued` alternatives preserve their array shape inside a scalar `Variant`,
including a single list alternative; list alternatives inside an outer multivalued
union and keyed class-list alternatives are rejected. Inlined class-list
alternatives with `inlined_as_list: true` are supported. Unions resolve every
alternative even without an outer or schema `default_range`; an explicit outer
range is still validated. Literal defaults must match a scalar union leaf, and a
list alternative's element type does not authorize a scalar default. Reject
ambiguous keyed-union storage rather than inventing keys or converting references
silently. Slot `union_of` references other slots, not range types, and is explicitly
rejected as unsupported slot composition. `all_of` and `none_of` remain external
constraints on the existing effective range, preserving enclosing union storage
under compatible constraints: their references are checked, and branches that
change storage representation are rejected. `range_expression`, inline `enum_range`
and `array` expressions are explicitly unsupported structural shapes.

Use `SchemaView.is_inlined(slot)` for effective inlining. In the installed
LinkML runtime, an ordinary external reference requires an **identifier**;
a key alone does not make it a reference. Use
`get_identifier_slot(range, use_key=True)` when choosing inline dictionary keys.

Unknown/cyclic types, unsupported collection shapes, non-representable defaults
and unresolved schema references are generation-time errors, never silent
fallbacks. Godot's integer range and floating-point precision remain limitations
for values supplied by callers; no decimal arithmetic or JSON-number round-trip
compatibility is promised.

## Defaults

Support literal `ifabsent` forms for scalar primitives and their custom-type
aliases, including `string(dog)`, integers, finite floats, booleans, lexical
strings and exact decimal strings. Quote strings safely for GDScript, preserve
Unicode and escapes, and check compatibility with the slot's representation,
descending through nested range unions to their leaf value representations.
Reject nonliteral expressions, incompatible defaults, out-of-range integer
literals and collection/object defaults that cannot be represented faithfully.
Do not evaluate Python or GDScript code from a schema.

Only explicit `type(raw payload)` literals are supported. Outer-quoted payloads
such as `string("dog")` or `integer('7')` are rejected, not emitted with their
quote delimiters as data. Payloads beginning with a quote (after whitespace)
are rejected as unsupported quoted syntax; quotes inside a raw payload such as
`string(é "hi")` remain literal characters. Symbolic payload names `default_range`,
`class_uri`, `slot_uri`, `class_curie`, `slot_curie`, `bnode` and `default_ns` are
reserved and rejected across default types, rather than incorrectly emitted as
literal text. No LinkML default-expression evaluator is generated.

## Enums

Each static enum gets a `RefCounted` host with named string constants, for example
`LinkMLLifeStatus.VALUE_IN_LIMBO == "in limbo"`. There is no integer conversion
layer and no claim that these constants enforce membership at assignment time.
Descriptions are emitted as documentation. `meaning` and other semantic metadata
remain in the schema. Reject unresolved dynamic enums (`reachable_from`, code
sets, queries or compositional enum definitions), rather than emitting an
apparently complete but truncated set of values. This includes `is_a`, `mixins`,
`inherits`, `values_from`, `include`, `minus`, `matches`, `concepts`, `pv_formula`
and code-set metadata; external enumeration resolution is not performed.

## External behavior (deliberately not generated)

| LinkML concern | Policy |
|---|---|
| `required`, pattern, min/max, cardinality constraints | Validate against the source schema outside Godot |
| `identifier`, `key` | Select storage/reference shapes; uniqueness remains external |
| `rules`, `unique_keys` | External validation |
| `slot_usage` | Apply induced storage mapping; constraints stay external |
| `annotations`, semantic metadata | Retained in source schema, no generated behavior |
| JSON/YAML loading and saving | No `from_dict`, `to_dict` or custom codec |
| Inspector annotations/hints | No `@export` or editor behavior |

## Implementation boundaries and verification

Language/domain logic stays in `mapping.py` and `templates/`; keep the generator's
load/render/write plumbing unchanged. Template-shape tests and the test-only
naive mapping may change to match the new template contract.

Use `nix develop --command uv run pytest` and Nix's `ruff` directly. Tests must
exercise naming failures, null/default semantics, custom types, reference versus
inline/list/dict shapes, inheritance/refinement failures and static/dynamic enums.
A headless Godot project must register generated global classes, parse the scripts
and run representative assignments/default checks, not just grep generated text.
Godot 4.7.2 and 4.5 passed the headless import and runtime tests locally. CI
runs Python 3.10/3.14 tests separately from Nix-provisioned Godot 4.7.2 and 4.5
jobs. Missing Godot fails the integration test.

The templates additionally call `mapping.string_literal(text)` for safe source
literals and `mapping.escape_description(text)` before the existing `doc_comment`
filter. The class template also consumes `emits_extra_slots` to emit dynamic
storage when policy allows, and `field_aliases(sv, cls)` for ordered
`(alias_name, backing_name, physical_type_hint)` forwarding properties.
`class_slots` returns only fixed slots needing storage; `field_name` remains the
effective public name, not a storage resolver. The test-only naive mapper
deliberately reuses the literal helpers and emits no forwarding aliases;
generator contexts remain unchanged.
