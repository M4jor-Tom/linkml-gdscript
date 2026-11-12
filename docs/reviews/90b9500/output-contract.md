# Output contract and scope guardrails

**Assessment, not an additional open item.** The actionable queue is R01–R07 in
[README.md](README.md). This section prevents fixes from becoming an unrequested
runtime rewrite or a consumer-specific compatibility layer.

## Viable purpose

The existing `SchemaView` → mapping → Jinja → one-file-per-type pipeline is a
reasonable foundation for standalone runtime data holders. `RefCounted` is an
appropriate base for that purpose. The current tests and real-engine demo show
that representative generated classes can parse and execute; they do not prove
support for arbitrary schemas or exact equivalence to handwritten applications.

Keep the approved distinctions explicit:

| Existing output policy | Consequence, not automatically a defect |
|---|---|
| `RefCounted`, not `Resource`/`Node` | No promised Inspector asset workflow or scene-tree lifecycle. |
| `LinkML`, `slot_`, `VALUE_` prefixes | Predictable collision avoidance, not a handwritten consumer API. |
| Nullable scalar `Variant` | Preserves missing values versus zero/false/empty string; sacrifices scalar static typing. It does not distinguish every possible wire-level omission/null state. |
| String enum constants | Preserve lexical values; do not enforce membership or reproduce native integer enums. |
| Typed objects/containers, flattened mixins | Some static typing, but no mixin subtype identity or multiple inheritance. |
| No codecs or runtime validation | Callers own admission, serialized-name mapping, references, constraints and persistence. |
| No generated domain methods | Formulas, lifecycle behavior and application-specific transformations remain handwritten responsibilities. |

A `required` field is not currently constructor-enforced. Strengthening typing
must not silently convert missing values to `0`, `false` or `""`. An alias-derived
GDScript name is not automatically a JSON codec. R01's missing dynamic-map storage
is qualitatively different from leaving constraints to external validation.

## Consumer drift is not a target-language mandate

The inspected Pixlnd model uses inner Resource classes, exported properties,
`StringName`, numeric enums, loader conversions, raw-row retention, diagnostics
and formulas. Its schema also separates logical definitions, source documents
and saves. These are not a one-to-one description of that handwritten API.

Accordingly:

- Generating into a separate directory does not automatically migrate existing
  consumers. Replacing their model would require explicit API/data conversion
  and behavioral ownership work, not just this generator's fixes.
- Keeping independently authored schema and runtime mirrors creates ongoing
  drift risk. Fixed schema/generator/dependency inputs are instead expected to
  yield reproducible output or a reproducible rejection.
- Scope tests to this generator's declared representation. Do not require exact
  source-text parity with Pixlnd, invent gameplay defaults, or alter that active
  worktree. Its current C# migration contract is a separate project decision.

## Fit with LinkML guidance

The official [porting guide](https://linkml.io/linkml/howtos/port-linkml.html)
([source](https://github.com/linkml/linkml/blob/main/docs/howtos/port-linkml.md)),
consulted on 2026-11-12, recommends starting with **simple standalone classes**.
It describes the classes primarily as data holders and treats runtime dependencies,
target-language constructs, JSON parsing/serialization, validation and imports as
backend design decisions. URI annotations, introspection and JSON generation may
be separate concerns initially. It recommends `SchemaView`-based generators and
opening an issue to coordinate new language support.

Therefore neither Resource output, codecs nor a complete LinkML runtime is a
prerequisite for this project's legitimate scope. Upstream acceptance is still a
maintainer decision, not guaranteed by following that guidance. Explicit subset
limits are acceptable; silently pretending to represent discarded structure is
not a correct implementation of this project's stated contract.

## Do not add these merely to close the review

Resource/Inspector output, more idiomatic naming, constructor-enforced typing,
JSON codecs, C# output and richer validation may be useful future products. They
require actual user needs and explicit decisions. This review authorizes none of
them by implication and makes no claim of measured developer preference.

Use `docs/MAPPING.md` and permanent tests for any accepted lasting contract change.
This file is deleted with the review; it must not become the only authority for
new behavior.
