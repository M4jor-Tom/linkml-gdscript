"""Parse and execute generated classes in the real Nix-provided Godot engine."""

import os
import re
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest
from linkml_runtime.linkml_model.meta import ClassDefinition, EnumDefinition
from linkml_runtime.utils.schemaview import SchemaView

from linkml_gdscript.generator import GDScriptGenerator


def run_godot(engine: str, project: Path, *arguments: str) -> str:
    """Require a successful process and clean diagnostics (Godot may exit zero on errors)."""
    result = subprocess.run(
        [engine, "--headless", "--path", str(project), *arguments],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert not re.search(r"\b(?:SCRIPT ERROR|Parse Error|ERROR)\b", output, re.IGNORECASE), output
    return output


@pytest.fixture
def engine(tmp_path: Path) -> str:
    """Require the selected shell's engine and record its exact version."""
    executable = shutil.which("godot4")
    assert executable is not None, "Godot is required; use the documented Nix shell"
    version = run_godot(executable, tmp_path, "--version").strip()
    expected = os.environ.get("GODOT_EXPECTED_VERSION")
    if expected is not None:
        assert version.startswith(expected + "."), (expected, version)
    print(f"GODOT_VERSION={version}")
    return executable


def test_generated_scripts_run_in_godot(sv: SchemaView, tmp_path: Path, engine: str) -> None:
    """Register global classes, then exercise nullable values, defaults and containers."""
    schema = deepcopy(sv.schema)
    schema.classes["Choice"] = ClassDefinition(
        name="Choice",
        attributes={"value": {"exactly_one_of": [{"range": "integer"}, {"range": "string", "multivalued": True}]}},
    )
    schema.classes["LiteralValues"] = ClassDefinition(
        name="LiteralValues",
        description="Literal [b]BBCode[/b].\nSecond line.",
        attributes={
            "exact": {"range": "decimal", "ifabsent": "decimal(12345678901234567890.00100)"},
            "minimum": {"range": "integer", "ifabsent": "integer(-9223372036854775808)"},
            "escaped": {"ifabsent": 'string(é "hi"\\\n\t)'},
            "truth": {"range": "boolean", "ifabsent": "boolean(true)"},
            "number": {"range": "float", "ifabsent": "float(1.25)"},
            "choices": {
                "any_of": [{"range": "string"}, {"range": "integer"}],
                "multivalued": True,
                "all_of": [{"required": True}],
                "none_of": [{"pattern": "^forbidden"}],
            },
            "nested_choice": {
                "any_of": [{"exactly_one_of": [{"range": "integer"}, {"range": "string"}]}],
                "ifabsent": "integer(7)",
                "all_of": [{"required": True}],
            },
        },
    )
    schema.enums["Escapes"] = EnumDefinition(name="Escapes", permissible_values={'quote"\\\n': {}})
    GDScriptGenerator(schema).serialize(directory=tmp_path)
    (tmp_path / "project.godot").write_text(
        'config_version=5\n[application]\nconfig/name="Mapping acceptance"\n',
        encoding="utf-8",
    )
    # Import before writing the runner, so its references use the registered global class cache.
    print(run_godot(engine, tmp_path, "--editor", "--quit"))
    (tmp_path / "check.gd").write_text(
        """extends SceneTree
func _initialize() -> void:
    var person = LinkMLPerson.new()
    assert(person.slot_age == null and person.slot_name == null)
    assert(person.slot_is_player == null and person.slot_address == null)
    person.slot_age = 0
    person.slot_is_player = false
    person.slot_name = ""
    assert(person.slot_age == 0 and person.slot_is_player == false and person.slot_name == "")
    assert(LinkMLLifeStatus.VALUE_IN_LIMBO == "in limbo")
    assert(LinkMLPet.new().slot_species == "dog")
    person.slot_pets["pet:1"] = LinkMLPet.new()
    assert(person.slot_pets["pet:1"] is LinkMLPet)
    assert(LinkMLPerson.new().slot_pets.is_empty())
    person.slot_friends.append("person:2")
    person.slot_history.append(LinkMLEvent.new())
    person.slot_aliases.append("alias")
    person.slot_address = LinkMLAddress.new()
    assert(person is LinkMLNamedThing)
    var choice = LinkMLChoice.new()
    assert(choice.slot_value == null)
    choice.slot_value = 0
    assert(choice.slot_value == 0)
    choice.slot_value = []
    assert(choice.slot_value is Array and choice.slot_value.is_empty())
    choice.slot_value = ["text"]
    assert(choice.slot_value == ["text"])
    var values = LinkMLLiteralValues.new()
    assert(values.slot_exact == "12345678901234567890.00100")
    assert(values.slot_minimum == -9223372036854775808)
    assert(values.slot_escaped == "é \\"hi\\"\\\\\\n\\t")
    assert(values.slot_truth == true and values.slot_number == 1.25)
    assert(LinkMLEscapes.VALUE_QUOTE == "quote\\"\\\\\\n")
    values.slot_choices.append("text")
    values.slot_choices.append(1)
    assert(values.slot_choices == ["text", 1])
    assert(values.slot_nested_choice == 7)
    values.slot_nested_choice = "text"
    assert(values.slot_nested_choice == "text")
    print("MAPPING_RUNTIME_OK")
    quit()
""",
        encoding="utf-8",
    )
    output = run_godot(engine, tmp_path, "--script", "check.gd")
    assert "MAPPING_RUNTIME_OK" in output, output
    print(output)
