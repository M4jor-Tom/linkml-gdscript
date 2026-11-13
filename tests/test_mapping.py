"""Executable structural mapping contracts, including rejected lossy mappings."""

import pytest
import yaml
from click.testing import CliRunner
from conftest import KITCHEN_SINK
from linkml_runtime.utils.schemaview import SchemaView

from linkml_gdscript import mapping
from linkml_gdscript.generator import GDScriptGenerator, cli


def all_slots(sv: SchemaView) -> list[tuple]:
    """Every (class, induced slot) pair of the schema."""
    return [(cls, slot) for cn, cls in sv.all_classes().items() for slot in sv.class_induced_slots(cn)]


def test_class_names_are_unique_identifiers(sv):
    names = [mapping.class_name(sv, cls) for cls in sv.all_classes().values()]
    assert all(name.isidentifier() for name in names)
    assert len(set(names)) == len(names)


def test_base_classes_are_identifiers(sv):
    assert all(mapping.base_class(sv, cls).isidentifier() for cls in sv.all_classes().values())


def test_class_slots_are_induced_slots_of_the_class(sv):
    for cn, cls in sv.all_classes().items():
        induced = {slot.name for slot in sv.class_induced_slots(cn)}
        assert {slot.name for slot in mapping.class_slots(sv, cls)} <= induced


def test_field_names_are_identifiers(sv):
    assert all(mapping.field_name(sv, cls, slot).isidentifier() for cls, slot in all_slots(sv))


def test_field_types_are_never_empty(sv):
    assert all(mapping.field_type(sv, cls, slot).strip() for cls, slot in all_slots(sv))


def test_field_defaults_are_expressions_or_none(sv):
    for cls, slot in all_slots(sv):
        default = mapping.field_default(sv, cls, slot)
        assert default is None or default.strip()


def test_enum_names_are_identifiers(sv):
    assert all(mapping.enum_name(sv, enum).isidentifier() for enum in sv.all_enums().values())


def test_enum_member_names_are_unique_identifiers(sv):
    for enum in sv.all_enums().values():
        names = [mapping.enum_member_name(sv, enum, pv) for pv in enum.permissible_values.values()]
        assert all(name.isidentifier() for name in names)
        assert len(set(names)) == len(names)


def test_file_names_end_with_gd():
    assert mapping.file_name("Person").endswith(".gd")


def test_cli_generates_the_kitchen_sink(sv, tmp_path):
    result = CliRunner().invoke(cli, [str(KITCHEN_SINK), "-d", str(tmp_path)], catch_exceptions=False)
    assert result.exit_code == 0
    assert len(list(tmp_path.glob("*.gd"))) == len(sv.all_classes()) + len(sv.all_enums())


def schema_view(**elements: object) -> SchemaView:
    """Build a small real schema with the standard LinkML primitives."""
    return SchemaView(
        yaml.safe_dump(
            {
                "id": "https://example.org/test",
                "name": "test",
                "default_prefix": "test",
                "prefixes": {"linkml": "https://w3id.org/linkml/"},
                "imports": ["linkml:types"],
                "default_range": "string",
                **elements,
            }
        )
    )


def test_kitchen_sink_literal_contract(sv: SchemaView) -> None:
    """Scalar absence and collection elements have independent representations."""
    person = sv.get_class("Person")
    assert mapping.class_name(sv, person) == "LinkMLPerson"
    assert mapping.base_class(sv, person) == "LinkMLNamedThing"
    assert mapping.file_name("LinkMLNamedThing") == "link_ml_named_thing.gd"
    assert {s.name for s in mapping.class_slots(sv, person)} == {
        "aliases",
        "age",
        "height",
        "is_player",
        "birth_date",
        "last_seen",
        "balance",
        "luck",
        "status",
        "address",
        "best_friend",
        "friends",
        "pets",
        "history",
        "lucky_charm",
    }
    for name, expected in {
        "age": "Variant",
        "name": "Variant",
        "is_player": "Variant",
        "status": "Variant",
        "lucky_charm": "Variant",
        "address": "LinkMLAddress",
        "best_friend": "Variant",
        "friends": "Array[String]",
        "pets": "Dictionary[String, LinkMLPet]",
        "history": "Array[LinkMLEvent]",
    }.items():
        slot = sv.induced_slot(name, "Person")
        assert mapping.field_type(sv, person, slot) == expected
        assert mapping.field_default(sv, person, slot) == (
            "{}" if name == "pets" else "[]" if name in {"friends", "history"} else "null"
        )
    pet = sv.get_class("Pet")
    assert mapping.field_default(sv, pet, sv.induced_slot("species", "Pet")) == '"dog"'


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Node", "LinkMLNode"),
        ("3d item", "LinkML3dItem"),
        ("my_HTTP-type", "LinkMLMyHttpType"),
    ],
)
def test_prefixed_names(name: str, expected: str) -> None:
    """Prefixes make keywords, natives and digits safe."""
    sv = schema_view(classes={name: {"attributes": {"class": {"alias": "3d-value"}}}})
    cls = sv.get_class(name)
    assert mapping.class_name(sv, cls) == expected
    assert mapping.field_name(sv, cls, sv.induced_slot("class", name)) == "slot_3d_value"


@pytest.mark.parametrize(
    "elements, match",
    [
        ({"classes": {"foo-bar": {}, "foo bar": {}}}, "foo-bar.*foo bar|foo bar.*foo-bar"),
        ({"classes": {"Foo": {}}, "enums": {"foo": {}}}, "Foo.*foo|foo.*Foo"),
        ({"classes": {"!!!": {}}}, "!!!"),
        ({"classes": {"A": {"attributes": {"foo-bar": {}, "foo bar": {}}}}}, "foo.bar"),
        ({"enums": {"E": {"permissible_values": {"in progress": {}, "in-progress": {}}}}}, "in.progress"),
        ({"enums": {"E": {"permissible_values": {"!!!": {}}}}}, "!!!"),
    ],
)
def test_normalized_collisions_and_empty_names(elements: dict, match: str) -> None:
    """Do not overwrite or emit ambiguous symbols."""
    with pytest.raises(ValueError, match=match):
        GDScriptGenerator(schema_view(**elements).schema).render()


@pytest.mark.parametrize(
    "range_name, element",
    [
        ("string", "String"),
        ("integer", "int"),
        ("boolean", "bool"),
        ("float", "float"),
        ("double", "float"),
        ("decimal", "String"),
        ("date", "String"),
        ("datetime", "String"),
        ("time", "String"),
        ("date_or_datetime", "String"),
        ("uri", "String"),
        ("uriorcurie", "String"),
        ("curie", "String"),
        ("ncname", "String"),
        ("objectidentifier", "String"),
        ("nodeidentifier", "String"),
        ("jsonpointer", "String"),
        ("jsonpath", "String"),
        ("sparqlpath", "String"),
        ("Custom", "int"),
        ("E", "String"),
    ],
)
def test_value_representations(range_name: str, element: str) -> None:
    """Aliases resolve recursively; scalar values always remain nullable."""
    sv = schema_view(
        types={"Custom": {"typeof": "integer"}},
        enums={"E": {"permissible_values": {"a": {}}}},
        classes={
            "C": {
                "attributes": {
                    "one": {"range": range_name, "required": True},
                    "many": {"range": range_name, "multivalued": True},
                }
            }
        },
    )
    cls = sv.get_class("C")
    assert mapping.field_type(sv, cls, sv.induced_slot("one", "C")) == "Variant"
    assert mapping.field_default(sv, cls, sv.induced_slot("one", "C")) == "null"
    assert mapping.field_type(sv, cls, sv.induced_slot("many", "C")) == f"Array[{element}]"


@pytest.mark.parametrize(
    "key, flags, expected",
    [
        ({"identifier": True}, {}, "Array[int]"),
        ({"identifier": True}, {"inlined": True}, "Dictionary[int, LinkMLItem]"),
        ({"key": True}, {}, "Dictionary[int, LinkMLItem]"),
        ({"key": True}, {"inlined_as_list": True}, "Array[LinkMLItem]"),
        ({}, {}, "Array[LinkMLItem]"),
    ],
)
def test_collection_shapes(key: dict, flags: dict, expected: str) -> None:
    """A key alone forces inlining; only identifiers can be references."""
    sv = schema_view(
        classes={
            "Item": {"attributes": {"id": {"range": "integer", **key}}},
            "C": {"attributes": {"items": {"range": "Item", "multivalued": True, **flags}}},
        }
    )
    assert mapping.field_type(sv, sv.get_class("C"), sv.induced_slot("items", "C")) == expected


@pytest.mark.parametrize(
    "slot, expected",
    [
        ({"any_of": [{"range": "string"}, {"range": "integer"}]}, "Variant"),
        ({"any_of": [{"range": "string"}, {"range": "integer"}], "multivalued": True}, "Array[Variant]"),
        ({"exactly_one_of": [{"range": "integer"}, {"range": "string"}]}, "Variant"),
    ],
)
def test_unions(slot: dict, expected: str) -> None:
    """Unions preserve heterogeneous values without inventing static types."""
    sv = schema_view(classes={"C": {"attributes": {"value": slot}}})
    cls = sv.get_class("C")
    induced = sv.induced_slot("value", "C")
    assert mapping.field_type(sv, cls, induced) == expected
    assert mapping.field_default(sv, cls, induced) == ("[]" if slot.get("multivalued") else "null")


@pytest.mark.parametrize("operator", ["any_of", "exactly_one_of"])
@pytest.mark.parametrize("list_branch", [False, True])
def test_union_without_outer_range(operator: str, list_branch: bool) -> None:
    """The alternatives provide their own ranges and preserve branch shape."""
    sv = schema_view(
        default_range=None,
        classes={
            "Choice": {
                "attributes": {
                    "value": {
                        operator: [
                            {"range": "integer"},
                            {"range": "string", "multivalued": list_branch},
                        ]
                    }
                }
            }
        },
    )
    assert sv.schema.default_range is None
    slot = sv.induced_slot("value", "Choice")
    assert slot.range is None
    cls = sv.get_class("Choice")
    assert mapping.field_type(sv, cls, slot) == "Variant"
    assert mapping.field_default(sv, cls, slot) == "null"


def test_single_list_union_has_null_default_and_rejects_scalar_default() -> None:
    """List alternatives retain their shape and cannot authorize scalar defaults."""
    slot_shape = {"exactly_one_of": [{"range": "string", "multivalued": True}]}
    sv = schema_view(classes={"C": {"attributes": {"value": slot_shape}}})
    cls = sv.get_class("C")
    slot = sv.induced_slot("value", "C")
    assert mapping.field_type(sv, cls, slot) == "Variant"
    assert mapping.field_default(sv, cls, slot) == "null"
    defaulted = schema_view(classes={"C": {"attributes": {"value": {**slot_shape, "ifabsent": "string(x)"}}}})
    with pytest.raises(ValueError, match="C.*value.*incompatible default"):
        mapping.field_default(defaulted, defaulted.get_class("C"), defaulted.induced_slot("value", "C"))


@pytest.mark.parametrize(
    "range_name, default, expected",
    [
        ("string", "string(dog)", '"dog"'),
        ("integer", "integer(-42)", "-42"),
        ("integer", "integer(9223372036854775807)", "9223372036854775807"),
        ("boolean", "boolean(false)", "false"),
        ("boolean", "boolean(true)", "true"),
        ("float", "float(1.25e2)", "125.0"),
        ("double", "double(-0.5)", "-0.5"),
        ("decimal", "decimal(12345678901234567890.00100)", '"12345678901234567890.00100"'),
        ("date", "date(2026-11-12)", '"2026-11-12"'),
        ("Custom", "integer(7)", "7"),
        ("Custom", "Custom(7)", "7"),
        ("E", "string(in limbo)", '"in limbo"'),
        ("string", 'string(é "hi"\\\n\t)', '"é \\"hi\\"\\\\\\n\\t"'),
    ],
)
def test_literal_defaults(range_name: str, default: str, expected: str) -> None:
    """Defaults preserve scalar values and exact decimal lexical forms."""
    sv = schema_view(
        types={"Custom": {"typeof": "integer"}},
        enums={"E": {"permissible_values": {"in limbo": {}}}},
        classes={"C": {"attributes": {"value": {"range": range_name, "ifabsent": default}}}},
    )
    assert mapping.field_type(sv, sv.get_class("C"), sv.induced_slot("value", "C")) == "Variant"
    assert mapping.field_default(sv, sv.get_class("C"), sv.induced_slot("value", "C")) == expected


@pytest.mark.parametrize(
    "range_name, default",
    [
        ("integer", "integer(9223372036854775808)"),
        ("integer", "integer(-9223372036854775809)"),
        ("integer", "integer(1.2)"),
        ("float", "float(inf)"),
        ("float", "float(nan)"),
        ("float", "float(1e9999)"),
        ("boolean", "boolean(yes)"),
        ("integer", "string(12)"),
        ("string", "integer(12)"),
        ("decimal", "decimal(NaN)"),
        ("string", "python(print('oops'))"),
        ("string", "default"),
    ],
)
def test_invalid_defaults(range_name: str, default: str) -> None:
    """Reject expressions, overflow and incompatible primitive literals."""
    sv = schema_view(classes={"C": {"attributes": {"value": {"range": range_name, "ifabsent": default}}}})
    with pytest.raises(ValueError, match="C.*value"):
        mapping.field_default(sv, sv.get_class("C"), sv.induced_slot("value", "C"))


@pytest.mark.parametrize(
    "usage",
    [
        {"alias": "other"},
        {"range": "integer"},
        {"ifabsent": "string(changed)"},
        {"multivalued": True},
    ],
)
def test_inherited_storage_conflicts(usage: dict) -> None:
    """Variant syntax must not hide incompatible inherited value representations."""
    sv = schema_view(
        classes={"Parent": {"attributes": {"value": {}}}, "Child": {"is_a": "Parent", "slot_usage": {"value": usage}}}
    )
    with pytest.raises(ValueError, match="Child.*value"):
        mapping.class_slots(sv, sv.get_class("Child"))


def test_constraint_refinements_and_mixin_flattening() -> None:
    """Storage-compatible refinements are not redeclared; mixins add fields."""
    sv = schema_view(
        classes={
            "Parent": {"attributes": {"value": {}}},
            "Mixin": {"mixin": True, "attributes": {"extra": {}}},
            "Child": {
                "is_a": "Parent",
                "mixins": ["Mixin"],
                "slot_usage": {"value": {"required": True, "pattern": "^x"}},
            },
        }
    )
    assert [s.name for s in mapping.class_slots(sv, sv.get_class("Child"))] == ["extra"]


@pytest.mark.parametrize(
    "elements, match",
    [
        ({"classes": {"C": {"is_a": "Missing"}}}, "Missing"),
        ({"classes": {"C": {"mixins": ["Missing"]}}}, "Missing"),
        ({"classes": {"C": {"is_a": "D"}, "D": {"is_a": "C"}}}, "[Cc]ycl"),
        ({"classes": {"C": {"mixins": ["D"]}, "D": {"mixins": ["C"]}}}, "[Cc]ycl"),
        ({"classes": {"C": {"attributes": {"value": {"range": "Missing"}}}}}, "Missing"),
        (
            {"types": {"T": {"typeof": "Missing"}}, "classes": {"C": {"attributes": {"value": {"range": "T"}}}}},
            "Missing",
        ),
        (
            {
                "types": {"T": {"typeof": "U"}, "U": {"typeof": "T"}},
                "classes": {"C": {"attributes": {"value": {"range": "T"}}}},
            },
            "[Cc]ycl",
        ),
        ({"classes": {"C": {"attributes": {"value": {"any_of": [{"range": "Missing"}]}}}}}, "Missing"),
    ],
)
def test_unresolved_and_cyclic_references(elements: dict, match: str) -> None:
    """Invalid schema references fail at generation, not at Godot import."""
    with pytest.raises(ValueError, match=match):
        GDScriptGenerator(schema_view(**elements).schema).render()


@pytest.mark.parametrize(
    "dynamic",
    [
        {"reachable_from": {"source_ontology": "https://example.org/ontology"}},
        {"code_set": "https://example.org/codes"},
        {"pv_formula": "CODE"},
        {"include": [{"inherits": ["Other"]}]},
        {"minus": [{"inherits": ["Other"]}]},
        {"inherits": ["Other"]},
        {"matches": {"source_ontology": "https://example.org/ontology"}},
        {"concepts": ["example:Concept"]},
    ],
)
def test_dynamic_enums_are_rejected(dynamic: dict) -> None:
    """Even partial static values cannot masquerade as a complete dynamic enum."""
    sv = schema_view(enums={"E": {"permissible_values": {"a": {}}, **dynamic}})
    with pytest.raises(ValueError, match="E.*[Dd]ynamic|[Dd]ynamic.*E"):
        GDScriptGenerator(sv.schema).render()


def test_templates_escape_comments_and_emit_string_constants() -> None:
    """Descriptions escape BBCode and enum values remain quoted literals."""
    sv = schema_view(
        classes={"C": {"abstract": True, "description": "[b]hi[/b]\nsecond"}},
        enums={"E": {"permissible_values": {'quote"\\\n': {"description": "[code]"}}}},
    )
    files = GDScriptGenerator(sv.schema).render()
    source = files["link_mlc.gd"]
    assert "@abstract\nclass_name LinkMLC\nextends RefCounted" in source
    assert "## [lb]b[rb]hi[lb]/b[rb]\n## second" in source
    enum = files["link_mle.gd"]
    assert "extends RefCounted" in enum
    assert 'const VALUE_QUOTE: String = "quote\\"\\\\\\n"' in enum
    assert "## [lb]code[rb]" in enum


@pytest.mark.parametrize(
    "slot",
    [
        {"range": "Item", "ifabsent": "string(x)", "inlined": True},
        {"range": "integer", "multivalued": True, "ifabsent": "integer(1)"},
        {"any_of": [{"range": "Item"}, {"range": "string"}], "inlined": True, "multivalued": True},
        {"any_of": [{"range": "string", "multivalued": True}], "multivalued": True},
    ],
)
def test_unrepresentable_storage_and_defaults(slot: dict) -> None:
    """Reject object/collection literals and nested or ambiguously keyed unions."""
    sv = schema_view(
        classes={"Item": {"attributes": {"id": {"identifier": True}}}, "C": {"attributes": {"value": slot}}}
    )
    with pytest.raises(ValueError, match="C.*value"):
        GDScriptGenerator(sv.schema).render()


@pytest.mark.parametrize("inline", [False, True])
def test_collection_identifier_rejected(inline: bool) -> None:
    """Identifiers cannot introduce nested typed collection elements or keys."""
    sv = schema_view(
        classes={
            "Item": {"attributes": {"id": {"identifier": True, "multivalued": True}}},
            "C": {"attributes": {"items": {"range": "Item", "multivalued": True, "inlined": inline}}},
        }
    )
    with pytest.raises(ValueError, match="C.*items"):
        GDScriptGenerator(sv.schema).render()


def test_cyclic_identifier_reference_rejected() -> None:
    """Reference identifiers must eventually resolve to a value representation."""
    sv = schema_view(classes={"C": {"attributes": {"id": {"range": "C", "identifier": True}}}})
    with pytest.raises(ValueError, match="[Cc]yclic.*identifier"):
        GDScriptGenerator(sv.schema).render()


def test_inherited_alias_collision_rejected() -> None:
    """A new field cannot hide a different inherited field."""
    sv = schema_view(
        classes={
            "Parent": {"attributes": {"foo": {}}},
            "Child": {"is_a": "Parent", "attributes": {"bar": {"alias": "foo"}}},
        }
    )
    with pytest.raises(ValueError, match="Child.*foo.*bar|Child.*bar.*foo"):
        GDScriptGenerator(sv.schema).render()


def test_nested_union_and_list_union() -> None:
    """Explicit list unions avoid dictionary-key ambiguity."""
    sv = schema_view(
        classes={
            "Item": {"attributes": {"id": {"identifier": True}}},
            "C": {
                "attributes": {
                    "value": {
                        "any_of": [{"any_of": [{"range": "Item"}, {"range": "integer"}]}],
                        "multivalued": True,
                        "inlined_as_list": True,
                    }
                }
            },
        }
    )
    assert mapping.field_type(sv, sv.get_class("C"), sv.induced_slot("value", "C")) == "Array[Variant]"


@pytest.mark.parametrize(
    "elements",
    [
        {"slots": {"a": {"is_a": "b"}, "b": {"is_a": "a"}}, "classes": {"C": {"slots": ["a"]}}},
        {"classes": {"C": {"attributes": {"a": {"is_a": "a"}}}}},
    ],
)
def test_cyclic_slot_inheritance_rejected(elements: dict) -> None:
    """Slot ancestry cycles are errors, not silently truncated induced slots."""
    with pytest.raises(ValueError, match="[Cc]yclic.*slot"):
        GDScriptGenerator(schema_view(**elements).schema).render()


def test_inherited_union_representation_conflict() -> None:
    """Variant syntax must not hide a changed inherited collection shape."""
    sv = schema_view(
        classes={
            "Parent": {"attributes": {"value": {"any_of": [{"range": "integer"}, {"range": "string"}]}}},
            "Child": {"is_a": "Parent", "slot_usage": {"value": {"multivalued": True}}},
        }
    )
    with pytest.raises(ValueError, match="Child.*value"):
        GDScriptGenerator(sv.schema).render()


@pytest.mark.parametrize(
    "shape",
    [
        {"range_expression": {"is_a": "C"}},
        {"enum_range": {"permissible_values": {"x": {}}}},
        {"array": {"exact_number_dimensions": 2}},
    ],
)
def test_unsupported_structural_expressions(shape: dict) -> None:
    """Unsupported range and array syntax must fail explicitly."""
    sv = schema_view(classes={"C": {"attributes": {"value": shape}}})
    with pytest.raises(ValueError, match="C.*value.*unsupported"):
        GDScriptGenerator(sv.schema).render()


@pytest.mark.parametrize("operator", ["all_of", "none_of"])
def test_constraint_branches_validate_references(operator: str) -> None:
    """External constraints do not excuse unresolved referenced types."""
    sv = schema_view(classes={"C": {"attributes": {"value": {operator: [{"range": "Missing"}]}}}})
    with pytest.raises(ValueError, match="Missing"):
        GDScriptGenerator(sv.schema).render()


@pytest.mark.parametrize("operator", ["all_of", "none_of"])
@pytest.mark.parametrize(
    "branch",
    [
        {"range": "integer"},
        {"multivalued": True},
        {"range_expression": {"is_a": "C"}},
    ],
)
def test_constraint_branches_reject_storage_changes(operator: str, branch: dict) -> None:
    """Constraint-only syntax cannot silently introduce incompatible storage."""
    sv = schema_view(classes={"C": {"attributes": {"value": {operator: [branch]}}}})
    with pytest.raises(ValueError, match="C.*value"):
        GDScriptGenerator(sv.schema).render()


def test_constraint_branches_preserve_storage() -> None:
    """Compatible logical constraints remain external validation metadata."""
    sv = schema_view(
        classes={
            "C": {
                "attributes": {
                    "value": {
                        "all_of": [{"range": "string", "pattern": "^a"}],
                        "none_of": [{"range": "uri", "pattern": "^https:"}],
                        "multivalued": True,
                    }
                }
            }
        }
    )
    assert mapping.field_type(sv, sv.get_class("C"), sv.induced_slot("value", "C")) == "Array[String]"


def test_nested_keyed_union_rejected() -> None:
    """Nested any_of must not hide ambiguous dictionary storage."""
    sv = schema_view(
        classes={
            "Item": {"attributes": {"id": {"identifier": True}}},
            "C": {
                "attributes": {
                    "value": {
                        "any_of": [{"any_of": [{"range": "Item"}, {"range": "integer"}]}],
                        "multivalued": True,
                        "inlined": True,
                    }
                }
            },
        }
    )
    with pytest.raises(ValueError, match="C.*value.*keyed union"):
        GDScriptGenerator(sv.schema).render()


def test_acronym_filenames_remain_distinct() -> None:
    """Acronym boundaries are normalized consistently in type and file names."""
    sv = schema_view(classes={"AB": {}, "A B": {}})
    assert set(GDScriptGenerator(sv.schema).render()) == {"link_ml_ab.gd", "link_mlab.gd"}


@pytest.mark.parametrize(
    "dynamic",
    [
        {"is_a": "Other"},
        {"mixins": ["Other"]},
        {"values_from": ["https://example.org/values"]},
    ],
)
def test_compositional_enums_rejected(dynamic: dict) -> None:
    """Inherited and external enumerations cannot silently emit partial values."""
    with pytest.raises(ValueError, match="E.*dynamic"):
        GDScriptGenerator(schema_view(enums={"E": dynamic}).schema).render()


def test_union_base_range_reference_is_validated() -> None:
    """Union alternatives must not hide an unresolved explicit base range."""
    sv = schema_view(classes={"C": {"attributes": {"value": {"range": "Missing", "any_of": [{"range": "integer"}]}}}})
    with pytest.raises(ValueError, match="Missing"):
        GDScriptGenerator(sv.schema).render()


def test_union_alternatives_validate_unknown_and_unsupported_shapes() -> None:
    """Union alternatives cannot hide unresolved ranges or unsupported collection shapes."""
    cases = [
        (
            {"exactly_one_of": [{"range": "string", "multivalued": True}], "multivalued": True},
            "C.*value.*list alternatives inside collections",
        ),
        ({"any_of": [{"range": "Missing", "multivalued": True}]}, "Missing"),
    ]
    for slot, message in cases:
        sv = schema_view(classes={"C": {"attributes": {"value": slot}}})
        with pytest.raises(ValueError, match=message):
            GDScriptGenerator(sv.schema).render()


def test_nested_union_without_outer_range_is_supported() -> None:
    """Nested range alternatives resolve without an unrelated outer default range."""
    sv = schema_view(
        default_range=None,
        classes={"C": {"attributes": {"value": {"any_of": [{"any_of": [{"range": "integer"}, {"range": "string"}]}]}}}},
    )
    assert mapping.field_type(sv, sv.get_class("C"), sv.induced_slot("value", "C")) == "Variant"


def test_union_accepts_inlined_list_class_alternative_and_rejects_keyed_list() -> None:
    """Object-list alternatives need explicit array storage and reject implicit keys."""
    classes = {
        "Item": {"attributes": {"id": {"identifier": True, "range": "string"}}},
        "Choice": {
            "attributes": {
                "value": {
                    "exactly_one_of": [{"range": "Item", "multivalued": True, "inlined": True, "inlined_as_list": True}]
                }
            }
        },
    }
    sv = schema_view(classes=classes)
    assert mapping.field_type(sv, sv.get_class("Choice"), sv.induced_slot("value", "Choice")) == "Variant"
    keyed = schema_view(
        classes={
            **classes,
            "Choice": {
                "attributes": {"value": {"exactly_one_of": [{"range": "Item", "multivalued": True, "inlined": True}]}}
            },
        }
    )
    with pytest.raises(ValueError, match="Choice.*value.*keyed collection alternatives"):
        GDScriptGenerator(keyed.schema).render()


@pytest.mark.parametrize(
    "range_name, default",
    [
        ("string", 'string("dog")'),
        ("string", "string('dog')"),
        ("string", 'string( "dog" )'),
        ("integer", 'integer("7")'),
        ("string", "string(default_range)"),
        ("uri", "uri(class_uri)"),
        ("uri", "uri(slot_uri)"),
        ("curie", "curie(class_curie)"),
        ("uriorcurie", "uriorcurie(slot_curie)"),
        ("string", "string(default_ns)"),
        ("nodeidentifier", "nodeidentifier(bnode)"),
    ],
)
def test_quoted_and_symbolic_defaults_are_rejected(range_name: str, default: str) -> None:
    """Unsupported LinkML expression syntax must not become a different raw literal."""
    sv = schema_view(classes={"C": {"attributes": {"value": {"range": range_name, "ifabsent": default}}}})
    with pytest.raises(ValueError, match="C.*value.*(?:quoted|symbolic)"):
        mapping.field_default(sv, sv.get_class("C"), sv.induced_slot("value", "C"))


@pytest.mark.parametrize("names", [["left", "right"], ["string", "integer"]])
def test_slot_union_of_is_explicitly_rejected(names: list[str]) -> None:
    """LinkML union_of references slots, not the range names of a value union."""
    sv = schema_view(
        slots={
            names[0]: {"range": "string"},
            names[1]: {"range": "integer"},
            "combined": {"union_of": names, "multivalued": True},
        },
        classes={"C": {"slots": ["combined"]}},
    )
    with pytest.raises(ValueError, match="C.*combined.*unsupported.*union_of"):
        GDScriptGenerator(sv.schema).render()


@pytest.mark.parametrize("operator", ["all_of", "none_of"])
@pytest.mark.parametrize("union", ["any_of", "exactly_one_of"])
@pytest.mark.parametrize("multivalued", [False, True])
def test_constraints_preserve_enclosing_union(operator: str, union: str, multivalued: bool) -> None:
    """Compatible constraints, including nested logic, do not erase union storage."""
    sv = schema_view(
        classes={
            "C": {
                "attributes": {
                    "value": {
                        union: [{"range": "integer"}, {"range": "string"}],
                        "multivalued": multivalued,
                        operator: [{"required": True}, {"all_of": [{"pattern": "^x"}]}],
                    }
                }
            }
        }
    )
    source = GDScriptGenerator(sv.schema).render()["link_mlc.gd"]
    expected = "Array[Variant] = []" if multivalued else "Variant = null"
    assert f"var slot_value: {expected}\n" in source


@pytest.mark.parametrize("default, expected", [("integer(7)", "7"), ("string(dog)", '"dog"')])
def test_nested_union_defaults_use_leaf_representations(default: str, expected: str) -> None:
    """Both union operators recurse to actual primitive representations for defaults."""
    sv = schema_view(
        classes={
            "C": {
                "attributes": {
                    "value": {
                        "any_of": [{"exactly_one_of": [{"any_of": [{"range": "integer"}, {"range": "string"}]}]}],
                        "ifabsent": default,
                    }
                }
            }
        }
    )
    source = GDScriptGenerator(sv.schema).render()["link_mlc.gd"]
    assert f"var slot_value: Variant = {expected}\n" in source


def test_scalar_list_union_default_matches_only_scalar_leaf() -> None:
    """A scalar default is accepted when a scalar branch matches despite list branches."""
    sv = schema_view(
        classes={
            "C": {
                "attributes": {
                    "value": {
                        "exactly_one_of": [
                            {"range": "integer"},
                            {"range": "string", "multivalued": True},
                        ],
                        "ifabsent": "integer(7)",
                    }
                }
            }
        },
    )
    assert "var slot_value: Variant = 7" in GDScriptGenerator(sv.schema).render()["link_mlc.gd"]


def test_nested_union_default_rejects_incompatible_leaf_type() -> None:
    """Descending through Variant unions must not accept unrelated primitive defaults."""
    sv = schema_view(
        classes={
            "C": {
                "attributes": {
                    "value": {
                        "any_of": [{"any_of": [{"range": "integer"}, {"range": "string"}]}],
                        "ifabsent": "boolean(true)",
                    }
                }
            }
        }
    )
    with pytest.raises(ValueError, match="C.*value.*incompatible default"):
        GDScriptGenerator(sv.schema).render()


@pytest.mark.parametrize("key_flag", ["identifier", "key"])
def test_recursive_multivalued_dictionary_key_rejected(key_flag: str) -> None:
    """Reject recursive collection keys before attempting to resolve their storage."""
    sv = schema_view(
        classes={
            "C": {
                "attributes": {
                    "id": {
                        key_flag: True,
                        "range": "C",
                        "multivalued": True,
                        "inlined": True,
                    }
                }
            }
        }
    )
    with pytest.raises(ValueError, match="C.*id.*dictionary key"):
        GDScriptGenerator(sv.schema).render()


@pytest.mark.parametrize(
    "usage, match",
    [
        ({"value": {"is_a": "Missing"}}, "Missing"),
        ({"value": {"mixins": ["Missing"]}}, "Missing"),
        ({"value": {"is_a": "value"}}, "[Cc]yclic.*slot"),
        ({"value": {"mixins": ["value"]}}, "[Cc]yclic.*slot"),
        ({"value": {"is_a": "other"}, "other": {"is_a": "value"}}, "[Cc]yclic.*slot"),
    ],
)
def test_slot_usage_ancestry_is_validated(usage: dict, match: str) -> None:
    """Validate effective ancestry, including cycles formed by multiple overrides."""
    sv = schema_view(
        classes={
            "C": {
                "attributes": {"value": {"range": "string"}, "other": {"range": "string"}},
                "slot_usage": usage,
            }
        }
    )
    with pytest.raises(ValueError, match=match):
        GDScriptGenerator(sv.schema).render()


def test_slot_usage_valid_ancestry_refinement() -> None:
    """Valid ancestry and constraint-only refinements must continue to generate."""
    sv = schema_view(
        slots={"base": {"range": "string"}},
        classes={
            "C": {
                "attributes": {"value": {"range": "string"}},
                "slot_usage": {"value": {"is_a": "base", "required": True, "pattern": "^x"}},
            }
        },
    )
    assert "var slot_value: Variant = null\n" in GDScriptGenerator(sv.schema).render()["link_mlc.gd"]


def test_decimal_default_preserves_lexical_exponent_without_decimal_conversion() -> None:
    """Finite decimal lexemes need no Python Decimal exponent representability limit."""
    text = "1e999999999999999999999999999999"
    sv = schema_view(
        classes={
            "C": {
                "attributes": {
                    "value": {
                        "range": "decimal",
                        "ifabsent": f"decimal({text})",
                    }
                }
            }
        }
    )
    assert mapping.field_default(sv, sv.get_class("C"), sv.induced_slot("value", "C")) == f'"{text}"'
