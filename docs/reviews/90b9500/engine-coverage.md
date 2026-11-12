# Engine compatibility and acceptance evidence

## R07 — Testing 4.7.2 does not establish 4.5 support

**P2 — evidence gap, not an observed Godot 4.5 failure.** README and the mapping
contract target Godot 4.5+, while the recorded real-engine acceptance uses 4.7.2.

### Evidence and affected files

- [README.md](../../../README.md): minimum-version claim and explicit test caveat.
- [flake.nix](../../../flake.nix): `nixpkgs.godot_4` from the locked Nix input;
  the reviewed environment reports `4.7.2.stable.nixpkgs.ed1daf0bf`.
- [CI](../../../.github/workflows/ci.yaml): one Nix-provisioned Godot job, no
  minimum-engine test matrix.
- [tests/test_godot.py](../../../tests/test_godot.py): correctly registers classes,
  checks diagnostics and requires `MAPPING_RUNTIME_OK` after runtime assertions.
- The [class template](../../../src/linkml_gdscript/templates/class.gd.jinja)
  emits `@abstract`; typed dictionaries and global-class dependencies also deserve
  qualification on the actual supported floor.

The existing documentation is candid about the gap. Do not turn this finding
into a claim that generated code is known to fail on 4.5.

### Required action

Choose one with the owner:

1. Keep the 4.5 minimum and provision a reproducible minimum-version engine check
   alongside the current-engine check; or
2. Change the advertised support policy to a verified version after approval,
   updating README, `docs/MAPPING.md` and CI consistently.

No unapproved engine upgrade or undocumented system dependency is implied.
An unavailable engine is an unmet verification requirement, not a passing skip.

### Acceptance

- [ ] Record the selected support policy and exact engine version(s).
- [ ] Run the generated-code integration test on the selected supported floor.
      The check must be reproducible outside one developer's local installation.
- [ ] Exercise abstract inheritance, global-class registration, typed arrays and
      dictionaries, nullable values and escaped literals on that floor.
- [ ] Require exit status, clean combined diagnostics and the explicit runtime
      sentinel. Godot can report script errors while exiting zero.
- [ ] Update the public support claim and CI to match the evidence; do not label
      a 4.7.2-only run as 4.5 acceptance.
- [ ] Preserve the full Python suite and the currently verified engine checks.
      Record commands/results in the review README before resolving R07.

## Checks shared by all sections

Follow the existing test helpers rather than introducing another runner. Generate
into a temporary project, run `godot4 --headless --path <project> --editor --quit`
to register global types, then execute a bounded `SceneTree` check. Inspect
stdout/stderr and require a marker printed only after assertions. Do not launch a
consumer game, modify its actual project, or rely on source-fragment matching
alone when the emitted representation changes.

The final repository-wide commands and review removal gate are in [README.md](README.md).
