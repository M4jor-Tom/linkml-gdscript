# Regeneration safety

## R06 — Stale scripts can break a previously working project

**P2 — integration defect.** Generation into an existing directory overwrites
current filenames but leaves removed/renamed generated types behind.

### Evidence and cause

[`serialize()`](../../../src/linkml_gdscript/generator.py#L108) renders in memory,
then writes each current file. It has no obsolete-file ownership/cleanup policy.
`tests/test_generator.py::test_serialize_writes_the_rendered_files` covers a fresh
directory, not successive schema versions.

Reproduce with these two schemas, generating both into the **same temporary**
`generated/` directory.

Before:

```yaml
id: https://example.org/review/regeneration
name: regeneration
prefixes:
  linkml: https://w3id.org/linkml/
imports: [linkml:types]
default_range: string
classes:
  Parent: {}
  Child:
    is_a: Parent
    attributes:
      value: {}
```

After:

```yaml
id: https://example.org/review/regeneration
name: regeneration
prefixes:
  linkml: https://w3id.org/linkml/
imports: [linkml:types]
default_range: string
classes:
  Parent:
    attributes:
      value: {}
```

Observed: `link_ml_child.gd` remains. It declares `slot_value`, while the rewritten
parent now declares the same member. After a temporary project registers global
classes, explicitly compiling the stale child produces:

```text
Parse Error: The member "slot_value" already exists in parent class LinkMLParent.
```

Generating only the second schema into a fresh directory imports without errors.
Editor class scanning alone need not compile every stale file; force compilation
or instantiate it when reproducing.

### Select the smallest safe ownership policy

Possible remedies include tracking files owned by a previous generation, or an
explicit generated-only directory workflow that refuses unsafe reuse and clearly
documents replacement. Select and document one policy before implementing it.
Do not add a broad recursive deletion or assume every `.gd` file in an output
directory belongs to this generator. A warning or cleanup recipe alone does not
establish that existing unsafe reuse is prevented; if only that limitation is
accepted, record an explicit owner-approved disposition rather than a verified fix.

### Acceptance

- [ ] A permanent two-generation regression demonstrates the original stale-file
      failure, including a removed/renamed class or enum.
- [ ] Under the chosen supported workflow, the second generation either produces
      the correct owned file set or fails safely with an actionable diagnostic.
- [ ] Unrelated handwritten files and files from another generator are preserved.
      Symlinks/paths must not allow cleanup outside the authorized output scope.
- [ ] A schema/render failure leaves the previous output intact. Do not remove
      working files before the new schema has successfully rendered.
- [ ] Repeating an unchanged schema is safe and deterministic under the chosen
      policy. Test fresh and existing directories.
- [ ] Real Godot import/compilation is clean for the supported regenerated result;
      negative checks reject the known stale-child case for the intended reason.
- [ ] README usage and writer tests describe the ownership policy and any explicit
      user action. Follow the review README's evidence and deletion rules.
