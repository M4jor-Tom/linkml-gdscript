"""A deliberately naive mapping, used ONLY to test the plumbing end to end.

This is not a reference and not a starting point for the real mapping: every
field is an untyped ``Variant`` and no hard case from docs/MAPPING.md is handled.
"""

from linkml_runtime.linkml_model.meta import ClassDefinition, EnumDefinition, PermissibleValue, SlotDefinition
from linkml_runtime.utils.formatutils import camelcase, underscore
from linkml_runtime.utils.schemaview import SchemaView


def class_name(sv: SchemaView, cls: ClassDefinition) -> str:
    return camelcase(cls.name)


def base_class(sv: SchemaView, cls: ClassDefinition) -> str:
    return "RefCounted"


def class_slots(sv: SchemaView, cls: ClassDefinition) -> list[SlotDefinition]:
    return sv.class_induced_slots(cls.name)


def field_name(sv: SchemaView, cls: ClassDefinition, slot: SlotDefinition) -> str:
    return underscore(slot.name)


def field_type(sv: SchemaView, cls: ClassDefinition, slot: SlotDefinition) -> str:
    return "Variant"


def field_default(sv: SchemaView, cls: ClassDefinition, slot: SlotDefinition) -> str | None:
    return "[]" if slot.multivalued else None


def enum_name(sv: SchemaView, enum: EnumDefinition) -> str:
    return camelcase(enum.name)


def enum_member_name(sv: SchemaView, enum: EnumDefinition, value: PermissibleValue) -> str:
    return underscore(value.text).upper()


def file_name(gdscript_class_name: str) -> str:
    return f"{gdscript_class_name}.gd"
