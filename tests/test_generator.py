"""Generator plumbing with a naive mapper, plus real-mapping regeneration regressions."""

import json
from hashlib import sha256
from pathlib import Path

import naive_mapping
import pytest
from click.testing import CliRunner
from conftest import KITCHEN_SINK
from linkml_runtime.linkml_model.meta import ClassDefinition
from linkml_runtime.utils.schemaview import SchemaView

from linkml_gdscript.generator import GDScriptGenerator, cli

EXPECTED_FILES = {
    "LifeStatus.gd",
    "HasAliases.gd",
    "NamedThing.gd",
    "Person.gd",
    "Pet.gd",
    "Address.gd",
    "Event.gd",
    "Dataset.gd",
}


@pytest.fixture(scope="module")
def files() -> dict[str, str]:
    return GDScriptGenerator(KITCHEN_SINK, mapping=naive_mapping).render()


def test_render_emits_one_file_per_class_and_enum(files):
    assert set(files) == EXPECTED_FILES


def test_class_file_uses_mapping_results(files):
    person = files["Person.gd"]
    assert "class_name Person\nextends RefCounted\n" in person
    assert "var age: Variant\n" in person
    assert "var friends: Variant = []\n" in person
    assert "var aliases: Variant = []\n" in person, "class_slots() decides which slots appear, mixins included"


def test_descriptions_become_doc_comments(files):
    assert "## Anything with an identity.\n## This description spans two lines.\n" in files["NamedThing.gd"]
    assert "## An inlined object.\nvar address: Variant\n" in files["Person.gd"]


def test_enum_file_lists_members(files):
    status = files["LifeStatus.gd"]
    assert "class_name LifeStatus\n" in status
    assert '## Still going.\nconst ALIVE: String = "ALIVE"\n' in status
    assert 'const DEAD: String = "DEAD"\n' in status
    assert 'const IN_LIMBO: String = "in limbo"\n' in status


def test_no_template_syntax_leaks_into_output(files):
    for source in files.values():
        assert "{#" not in source and "{{" not in source and "TODO" not in source


def test_serialize_writes_the_rendered_files(files, tmp_path):
    out = tmp_path / "nested" / "out"
    generator = GDScriptGenerator(KITCHEN_SINK, mapping=naive_mapping)
    source = generator.serialize(directory=out)
    assert {p.name: p.read_text(encoding="utf-8") for p in out.glob("*.gd")} == files
    assert source == generator.serialize() == "\n".join(files.values())
    assert json.loads((out / ".linkml-gdscript.json").read_text()) == {
        "format": 1,
        "schema_id": str(generator.schemaview.schema.id),
        "files": {name: sha256(text.encode("utf-8")).hexdigest() for name, text in files.items()},
    }


def test_regeneration_removes_obsolete_child(tmp_path: Path) -> None:
    """Retire the child before its former field moves into the parent."""
    before = SchemaView("""id: https://example.org/review/regeneration
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
""")
    after = SchemaView("""id: https://example.org/review/regeneration
name: regeneration
prefixes:
  linkml: https://w3id.org/linkml/
imports: [linkml:types]
default_range: string
classes:
  Parent:
    attributes:
      value: {}
""")
    GDScriptGenerator(before.schema).serialize(directory=tmp_path)
    GDScriptGenerator(after.schema).serialize(directory=tmp_path)
    assert not (tmp_path / "link_ml_child.gd").exists()


def test_colliding_file_names_are_rejected(monkeypatch):
    monkeypatch.setattr(naive_mapping, "file_name", lambda name: "same.gd")
    with pytest.raises(ValueError, match="same.gd"):
        GDScriptGenerator(KITCHEN_SINK, mapping=naive_mapping).render()


@pytest.mark.parametrize("invalid", ["range", "collision"])
def test_generation_failure_preserves_owned_output(tmp_path: Path, invalid: str) -> None:
    """Invalid schema references and render collisions precede writer mutation."""
    schema = SchemaView("""id: urn:test
name: failure
prefixes:
  linkml: https://w3id.org/linkml/
imports: [linkml:types]
classes:
  Model:
    attributes:
      value:
        range: string
""").schema
    out = tmp_path / "generated"
    GDScriptGenerator(schema).serialize(directory=out)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    if invalid == "range":
        schema.classes["Model"].attributes["value"].range = "Missing"
        generator = GDScriptGenerator(schema)
        with pytest.raises(ValueError, match="Missing"):
            generator.serialize(directory=out)
    else:
        schema.classes["model"] = ClassDefinition(name="model")
        with pytest.raises(ValueError, match="collision"):
            GDScriptGenerator(schema).serialize(directory=out)
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


def test_cli_help():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--output-directory" in result.output


def test_cli_generates_domain_import_closure(tmp_path: Path) -> None:
    """The real CLI generates the modular example from its single entry schema."""
    root = Path(__file__).parents[1] / "examples" / "domain" / "domain.yaml"
    generated = tmp_path / "generated"
    result = CliRunner().invoke(cli, [str(root), "-d", str(generated)])
    assert result.exit_code == 0, result.output
    files = GDScriptGenerator(root).render()
    assert {path.name: path.read_text(encoding="utf-8") for path in generated.glob("*.gd")} == files
    assert "var slot_items: Dictionary[String, LinkMLItem] = {}" in files["link_ml_catalog.gd"]
    assert "var slot_featured: Variant = null" in files["link_ml_catalog.gd"]
    assert "var slot_labels: Variant = null" in files["link_ml_item.gd"]
    assert "var linkml_extra_slots: Dictionary[String, Variant] = {}" in files["link_ml_metadata.gd"]
    assert "var slot_kind: Variant:" in files["link_ml_item.gd"]


def test_cli_imported_union_without_entry_default_range(tmp_path):
    """Imported alternatives generate Variant before creating output on failure."""
    choices = tmp_path / "choices.yaml"
    choices.write_text(
        """id: https://example.org/choices
name: choices
prefixes:
  linkml: https://w3id.org/linkml/
classes:
  Choice:
    attributes:
      value:
        any_of:
          - range: integer
          - range: string
""",
        encoding="utf-8",
    )
    entry = tmp_path / "entry.yaml"
    entry.write_text(
        """id: https://example.org/entry
name: entry
prefixes:
  linkml: https://w3id.org/linkml/
imports: [linkml:types, choices]
""",
        encoding="utf-8",
    )
    out = tmp_path / "generated"
    result = CliRunner().invoke(cli, [str(entry), "-d", str(out)])
    assert result.exit_code == 0, result.output
    assert any("var slot_value: Variant = null" in path.read_text(encoding="utf-8") for path in out.glob("*.gd"))

    choices.write_text(choices.read_text(encoding="utf-8").replace("range: string", "range: Missing"), encoding="utf-8")
    failed_out = tmp_path / "failed"
    failure = CliRunner().invoke(cli, [str(entry), "-d", str(failed_out)])
    assert failure.exit_code != 0
    assert "Missing" in str(failure.exception)
    assert not failed_out.exists()
