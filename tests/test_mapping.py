"""Contract tests for the real mapping in ``linkml_gdscript.mapping``.

Every test is marked ``@todo_mapping`` while its function is unimplemented.
The marker is strict: once a function works, its test "unexpectedly passes" and
the suite fails until the marker is removed. That is the progress tracker.

These tests only check what any sane mapping must satisfy (valid identifiers,
nothing lost). Add tests for the actual decisions next to them as you make them.
"""

import pytest
from click.testing import CliRunner
from conftest import KITCHEN_SINK
from linkml_runtime.utils.schemaview import SchemaView

from linkml_gdscript import mapping
from linkml_gdscript.generator import cli

todo_mapping = pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="TODO(mapping)")


def all_slots(sv: SchemaView) -> list[tuple]:
    """Every (class, induced slot) pair of the schema."""
    return [(cls, slot) for cn, cls in sv.all_classes().items() for slot in sv.class_induced_slots(cn)]


@todo_mapping
def test_class_names_are_unique_identifiers(sv):
    names = [mapping.class_name(sv, cls) for cls in sv.all_classes().values()]
    assert all(name.isidentifier() for name in names)
    assert len(set(names)) == len(names)


@todo_mapping
def test_base_classes_are_identifiers(sv):
    assert all(mapping.base_class(sv, cls).isidentifier() for cls in sv.all_classes().values())


@todo_mapping
def test_class_slots_are_induced_slots_of_the_class(sv):
    for cn, cls in sv.all_classes().items():
        induced = {slot.name for slot in sv.class_induced_slots(cn)}
        assert {slot.name for slot in mapping.class_slots(sv, cls)} <= induced


@todo_mapping
def test_field_names_are_identifiers(sv):
    assert all(mapping.field_name(sv, cls, slot).isidentifier() for cls, slot in all_slots(sv))


@todo_mapping
def test_field_types_are_never_empty(sv):
    assert all(mapping.field_type(sv, cls, slot).strip() for cls, slot in all_slots(sv))


@todo_mapping
def test_field_defaults_are_expressions_or_none(sv):
    for cls, slot in all_slots(sv):
        default = mapping.field_default(sv, cls, slot)
        assert default is None or default.strip()


@todo_mapping
def test_enum_names_are_identifiers(sv):
    assert all(mapping.enum_name(sv, enum).isidentifier() for enum in sv.all_enums().values())


@todo_mapping
def test_enum_member_names_are_unique_identifiers(sv):
    for enum in sv.all_enums().values():
        names = [mapping.enum_member_name(sv, enum, pv) for pv in enum.permissible_values.values()]
        assert all(name.isidentifier() for name in names)
        assert len(set(names)) == len(names)


@todo_mapping
def test_file_names_end_with_gd():
    assert mapping.file_name("Person").endswith(".gd")


@todo_mapping
def test_cli_generates_the_kitchen_sink(sv, tmp_path):
    result = CliRunner().invoke(cli, [str(KITCHEN_SINK), "-d", str(tmp_path)], catch_exceptions=False)
    assert result.exit_code == 0
    assert len(list(tmp_path.glob("*.gd"))) == len(sv.all_classes()) + len(sv.all_enums())
    # TODO(mapping): parse-check each file with Godot once the output is real:
    #   godot --headless --check-only --script <file.gd>
