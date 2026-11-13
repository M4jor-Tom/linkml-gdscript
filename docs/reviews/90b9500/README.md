# Review of `90b9500` — pending work

Reviewed commit: `90b9500c4f829c10ff96366b3ee2b5f48fd1eef9`  
Review date: 2026-11-12  
Scope: LinkML → GDScript generator correctness, integration safety and output contract.

**This is a disposable work queue, not permanent architecture documentation.** Resume
here in later sessions. Delete this directory when every item meets the closure
rules below. Creating this review does not mean its findings have been fixed.

## Findings and order

P1 = potential silent structural loss. P2 = generation/integration failure or a
verification gap. A compatibility limit is not automatically a defect or permission
to expand the supported subset.

| ID | Section / finding | Classification | State | Owner | Next action or resolution receipt |
|---|---|---|---|---|---|
| R01 | [Dynamic maps disappear](schema-fidelity.md#r01--dynamic-map-entries-have-no-generated-storage) | P1 defect | resolved | Task 3 + Task 7 | `test_dynamic_map_has_storage` was RED (missing extras field), then policy/storage, invalid-schema no-write, inheritance/mixin, collision, and Godot raw-key/value regressions passed. Task 7's `nix develop --command uv run pytest` passed (304 tests); both Godot 4.7.2 and 4.5 executed Unicode/punctuation raw keys in `DOMAIN_MODEL_OK`. Nix ruff and `git diff --check` passed. Commits `0d152fe4c7f5e426be08b3abd30c658e1549c429`, `0015a08`. |
| R02 | [Unions require an unrelated outer range](union-representations.md#r02--range-less-unions-fail-before-their-alternatives-are-used) | P2 defect | resolved | Task 2 implementation | `test_union_without_outer_range`, nested union, invalid range, imported CLI (fails before output), and Godot runtime regressions pass. Full suite: 179 passed; Godot 4.7.2 + 4.5 each pass with `MAPPING_RUNTIME_OK`; ruff checks and `git diff --check` pass. Commit `15d2aa6`. |
| R03 | [Scalar-or-list alternatives](union-representations.md#r03--scalar-or-list-alternatives-are-rejected-as-nested-collections) | Compatibility limit | resolved | Task 2 implementation | Extended scalar-position unions with preserved Variant array branches; defaults match only scalar leaves. Outer collection nesting/keyed class lists rejected, inline list accepted. Mapping regressions, Godot 4.7.2 + 4.5, full suite (179), Nix ruff, format and diff checks pass. Commit `15d2aa6`. |
| R04 | [Unicode-only enum values](naming-and-inheritance.md#r04--unicode-only-enum-values-stop-generation) | Compatibility limit | resolved | Task 4 + Task 7 | Existing `Unicode` Godot runtime covers Ω, café and emoji symbols. Task 7 domain CLI output has exact `VALUE__U03A9` and the executable usage asserts it stores `Ω`; both Godot 4.7.2 and 4.5 pass `DOMAIN_MODEL_OK`. Full suite 304 passed. Commits `20467f3`, `0015a08`. |
| R05 | [Inherited alias changes](naming-and-inheritance.md#r05--subclasses-cannot-rename-inherited-storage) | Compatibility limit | resolved | Task 5 + Task 7 | Forwarding properties share physical-owner storage/types; immediate-parent compatibility and all exposed-name collision checks remain. `nix develop --command uv run pytest tests/test_mapping.py -k inherited_alias_forwards -v`: RED incompatible storage, then GREEN. Range-only induced-union, three-level/reverted aliases, mixin ownership, scalar/reference/subtype narrowing, null/default and collection conflicts covered. Approved nested-list leaf guard: both union operators RED (did not raise), then GREEN. Full suite: 304 passed. Both Godot 4.7.2 and 4.5 pass Task 7 alias assertion (`slot_kind` forwards to `slot_category`) with `DOMAIN_MODEL_OK`; both engine suites pass. Nix ruff and `git diff --check` pass. Commits `8da0afe`, `0015a08`; simplify/ponytail self-review complete, independent review pending. |
| R06 | [Obsolete output survives regeneration](regeneration-safety.md#r06--stale-scripts-can-break-a-previously-working-project) | P2 integration defect | resolved | Task 6 implementation | `test_regeneration_removes_obsolete_child`: RED stale `link_ml_child.gd`, then GREEN with format-1 SHA256 ownership in `output.py`. Direct filesystem tests cover preflight refusal without writes, legacy/unmanaged collisions, duplicate keys, symlinks, staging failure, Unicode, repeat/empty output and preserved UID sidecars. Task 7 final full suite: 304 passed. Both engine checks pass regeneration and the exact stale-child duplicate `slot_value` diagnostic is confirmed in the negative project. Nix ruff check/format and `git diff --check` pass. README/CONTRIBUTING document migration and publication limits; commits `2c77c72`, `0015a08`; simplify/ponytail self-review complete, independent review pending. |
| R07 | [Minimum Godot version is unverified](engine-coverage.md#r07--testing-472-does-not-establish-45-support) | P2 evidence gap | resolved | Task 1 + Task 7 | Fresh Task 7 `nix develop --command uv run pytest tests/test_godot.py -s`: 4 passed on `4.7.2.stable.nixpkgs.ed1daf0bf`, including `DOMAIN_MODEL_OK` and `DOMAIN_SCRIPTS_COMPILE_OK`. Fresh `nix develop .#godot-floor --command uv run pytest tests/test_godot.py -s`: 4 passed on `4.5.stable.nixpkgs.876b29033`, same sentinels. Full pytest: 304 passed; Nix ruff check/format and `git diff --check` pass. Floor emits external Fontconfig warnings; no failures/diagnostics. Commits `22dd1cc`, `0015a08`. Remote CI (Python 3.10/3.14 and engine matrix) was not run; its evidence remains pending. |

Read [output-contract.md](output-contract.md) before changing behavior. It contains
scope guardrails and LinkML guidance, **not another feature backlog**. Suggested
order: R01 → R02 → R03–R05 dispositions → R06 → R07 → final verification.

## Baseline evidence and limits

- `nix develop --command uv run pytest`: **169 passed** on the reviewed revision;
  Nix `ruff check` and `ruff format --check` also passed. Existing green tests do
  not cover the newly reproduced gaps.
- A small CLI-generated model imported and executed in Godot
  `4.7.2.stable.nixpkgs.ed1daf0bf`, exercising inheritance, mixin flattening,
  nullable scalars, string enums, references, inline objects and typed containers.
- Reusing an output directory reproduced an inherited-member parse failure;
  generating the same final schema into a clean directory did not.
- A read-only Pixlnd snapshot taken at `2026-11-12T14:54:33Z` exposed additional
  compatibility cases. It included uncommitted work above
  `a2e557cb9bf0def4c187ae50599f15bebc0776d2`; that commit alone does not reproduce it.
  The resolved entry had 328 classes and 30 enums. Full generation stopped on
  `Ω`, with no files written. Subsequent per-class probes were **not** successful
  full-schema generation or whole-project Godot acceptance.
- Each section supplies a reduced reproduction independent of Pixlnd. Do not
  require a live external checkout, `/tmp` artifacts or earlier chat to proceed.
  Do not edit Pixlnd or weaken its schemas to make this generator pass.

## Resume protocol

1. Read this README, [the mapping contract](../../MAPPING.md) and
   [CONTRIBUTING.md](../../../CONTRIBUTING.md). Check the current revision and dirty
   files; `90b9500` is a historical baseline, not an instruction to reset Git.
2. Select an unowned item. Set its table state to `in-progress` and identify the
   owner/session before editing. Keep one writer per working directory; coordinate
   any shared `mapping.py` or test edits rather than overlapping them.
3. Reproduce the behavior on the current revision. Reuse a permanent regression
   if a previous session already added it; do not duplicate fixes or tests.
4. Implement only the selected remedy. Mapping decisions belong in `mapping.py`
   and templates; R06 concerns the actual writer in `generator.py`. Changes to
   previously approved semantics require owner approval, not an inferred mandate
   from this review.
5. Before yielding, update the table receipt with changed files/test names, exact
   commands and observed results, remaining next step, and commit SHA if one
   exists. For uncommitted work, say so and identify the diff. Release ownership
   or name the continuing owner. Use `blocked` for unanswered decisions/failures;
   a started or attempted check is not a passed check.
6. On resumption, recheck the receipt against current code. Passing evidence from
   a different revision or a truncated/failed invocation does not close an item.

States are `open`, `in-progress`, `blocked`, `resolved`. The table is the status
registry; section checklists describe acceptance, not a second state registry.

## What counts as handled

An item becomes `resolved` only through one of these explicit outcomes:

- **Fixed:** its acceptance checks pass; durable regression tests and relevant
  mapping/usage documentation are in the repository.
- **Already fixed:** reproduce against current code and cite the existing remedy
  and passing regression. No duplicate implementation is needed.
- **Retained supported-subset policy (R03–R05):** verify that rejection is explicit,
  tested and accurately documented; cite the existing approved contract. Keeping
  that contract does not require inventing new product requirements. Expanding
  it requires an approved decision and the corresponding runtime tests.
- **Owner-approved alternative or transfer:** record the actual approval and a
  durable destination containing the unresolved work/acceptance criteria. A
  transferred item is not a verified fix; report it separately at completion.

“Later”, a green unrelated test suite, or documenting silent data loss does not
resolve a defect. Do not unilaterally downgrade R01/R02 or mark an unanswered
policy choice resolved. Every resolved row needs a concrete receipt, not only a
check mark. Keep finished section files until the final cleanup so partial work
remains understandable across sessions.

## Final verification and mandatory deletion

After all seven rows are resolved:

- [ ] Check every item's acceptance/disposition receipt against the final code;
      rerun applicable regressions after the last implementation adjustment.
- [ ] Run `nix develop --command uv run pytest`.
- [ ] Run `nix develop --command ruff check` and
      `nix develop --command ruff format --check`.
- [ ] Record the actual Godot version(s); require clean diagnostics and the runtime
      success marker, not exit status alone. Apply R07's selected support policy.
- [ ] Run `/simplify`, then `/skill:ponytail-review`; apply justified adjustments
      and rerun affected checks. Do not add optional backends to close this review.
- [ ] Move lasting decisions/examples to `docs/MAPPING.md`, usage/development docs
      or tests as appropriate. No requirement or transferred work may survive
      only in this disposable directory. Record a concise completion receipt in
      the fixing/cleanup commit or final handoff, distinguishing fixes, retained
      limitations and transfers; creating a commit requires normal authority.
- [ ] Inspect `docs/reviews/90b9500/` for newly added/unowned files. Once everything
      here is accounted for, **delete this entire review directory, including this
      README**, and verify its removal with Git status/diff. Leave other reviews
      and unrelated work untouched; do not keep a permanent completed checklist.

If any item is still open, blocked, unverified or being edited by another owner,
**leave the review in place** and provide a precise next step.
