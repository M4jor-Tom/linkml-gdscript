"""Tests of the plumbing, independent of the real mapping (they use ``naive_mapping``)."""

import naive_mapping
import pytest
from click.testing import CliRunner
from conftest import KITCHEN_SINK

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
    GDScriptGenerator(KITCHEN_SINK, mapping=naive_mapping).serialize(directory=out)
    assert {p.name: p.read_text(encoding="utf-8") for p in out.iterdir()} == files


def test_colliding_file_names_are_rejected(monkeypatch):
    monkeypatch.setattr(naive_mapping, "file_name", lambda name: "same.gd")
    with pytest.raises(ValueError, match="same.gd"):
        GDScriptGenerator(KITCHEN_SINK, mapping=naive_mapping).render()


def test_cli_help():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--output-directory" in result.output
