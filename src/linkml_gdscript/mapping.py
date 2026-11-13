"""Structural LinkML → GDScript projection; semantic validation stays external."""

import json
import math
import re
from dataclasses import replace

from linkml_runtime.linkml_model.meta import (
    AnonymousSlotExpression,
    ClassDefinition,
    EnumDefinition,
    PermissibleValue,
    SlotDefinition,
)
from linkml_runtime.utils.schemaview import SchemaView

_PRIMITIVES = {
    "string": "String",
    "integer": "int",
    "boolean": "bool",
    "float": "float",
    "double": "float",
    "decimal": "String",
    "time": "String",
    "date": "String",
    "datetime": "String",
    "date_or_datetime": "String",
    "uriorcurie": "String",
    "curie": "String",
    "uri": "String",
    "ncname": "String",
    "objectidentifier": "String",
    "nodeidentifier": "String",
    "jsonpointer": "String",
    "jsonpath": "String",
    "sparqlpath": "String",
}


def _words(name: str) -> list[str]:
    """Split punctuation, acronym and camel-case boundaries into ASCII words."""
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", str(name))
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    words = re.findall(r"[A-Za-z0-9]+", text)
    if not words:
        raise ValueError(f"Name has no usable ASCII characters: {name!r}")
    return words


def _type_name(name: str) -> str:
    """Prefix a normalized PascalCase global type."""
    return "LinkML" + "".join(word.capitalize() for word in _words(name))


def _global_name(sv: SchemaView, name: str) -> str:
    """Check the shared class/enum and case-insensitive filename namespaces."""
    # ponytail: per-symbol scans are O(n²); cache per render if large schemas need it.
    names: dict[str, str] = {}
    files: dict[str, str] = {}
    for kind, elements in (("class", sv.all_classes()), ("enum", sv.all_enums())):
        for source in elements:
            label = f"{kind} {source!r}"
            target = _type_name(source)
            filename = file_name(target).casefold()
            for namespace, key in ((names, target), (files, filename)):
                if key in namespace:
                    raise ValueError(f"Name collision: {namespace[key]} and {label} map to {key}")
                namespace[key] = label
    return _type_name(name)


def _check_slot_ancestry(
    sv: SchemaView,
    slot: SlotDefinition,
    path: tuple[str, ...] = (),
    effective: dict[str, SlotDefinition] | None = None,
) -> None:
    """Reject missing/cyclic slot ancestry, including class-local usage overrides."""
    if slot.name in path:
        raise ValueError(f"Cyclic slot inheritance: {' -> '.join((*path, slot.name))}")
    for parent in ([slot.is_a] if slot.is_a else []) + slot.mixins:
        parent_slot = (effective or {}).get(parent) or sv.get_slot(parent, strict=True)
        _check_slot_ancestry(sv, parent_slot, (*path, slot.name), effective)


def _check_ancestry(sv: SchemaView, name: str, path: tuple[str, ...] = ()) -> None:
    """Reject missing class parents/mixins and cycles before inducing slots."""
    if name in path:
        raise ValueError(f"Cyclic class inheritance: {' -> '.join((*path, name))}")
    cls = sv.get_class(name, strict=True)
    for slot in [*cls.attributes.values(), *(sv.get_slot(name, strict=True) for name in cls.slots)]:
        _check_slot_ancestry(sv, slot)
    for parent in ([cls.is_a] if cls.is_a else []) + cls.mixins:
        _check_ancestry(sv, parent, (*path, name))
    effective = {slot.name: slot for slot in sv.class_induced_slots(name)}
    for slot in effective.values():
        _check_slot_ancestry(sv, slot, effective=effective)


def class_name(sv: SchemaView, cls: ClassDefinition) -> str:
    """Return the namespaced global class identifier, rejecting collisions."""
    return _global_name(sv, cls.name)


def base_class(sv: SchemaView, cls: ClassDefinition) -> str:
    """Use single inheritance, or RefCounted for a root class."""
    _check_ancestry(sv, cls.name)
    return class_name(sv, sv.get_class(cls.is_a, strict=True)) if cls.is_a else "RefCounted"


def _field_name(slot: SlotDefinition) -> str:
    """Use an alias in preference to the original slot name."""
    return "slot_" + "_".join(_words(slot.alias or slot.name)).lower()


def field_name(sv: SchemaView, cls: ClassDefinition, slot: SlotDefinition) -> str:
    """Return a safe field name, checking all effective fields for collisions."""
    _check_ancestry(sv, cls.name)
    names: dict[str, str] = {}
    for effective in sv.class_induced_slots(cls.name):
        name = _field_name(effective)
        if name in names and names[name] != effective.name:
            raise ValueError(f"{cls.name}: fields {names[name]!r} and {effective.name!r} map to {name}")
        names[name] = effective.name
    return _field_name(slot)


def class_slots(sv: SchemaView, cls: ClassDefinition) -> list[SlotDefinition]:
    """Flatten mixins, suppressing only storage-compatible inherited fields."""
    _check_ancestry(sv, cls.name)
    inherited = {s.name: s for s in sv.class_induced_slots(cls.is_a)} if cls.is_a else {}
    slots = sv.class_induced_slots(cls.name)
    for slot in slots:
        field_name(sv, cls, slot)
        if slot.name in inherited:
            parent_slot = inherited[slot.name]
            parent = sv.get_class(cls.is_a, strict=True)
            current = (_field_name(slot), _storage_type(sv, cls, slot), field_default(sv, cls, slot))
            previous = (
                _field_name(parent_slot),
                _storage_type(sv, parent, parent_slot),
                field_default(sv, parent, parent_slot),
            )
            if current != previous:
                raise ValueError(f"{cls.name}.{slot.name}: incompatible inherited storage {previous} -> {current}")
    return [slot for slot in slots if slot.name not in inherited]


def _primitive(sv: SchemaView, name: str, path: tuple[str, ...] = ()) -> str:
    """Resolve custom typeof chains without silently accepting unknown types."""
    if name in path:
        raise ValueError(f"Cyclic type: {' -> '.join((*path, name))}")
    typedef = sv.get_type(name, strict=True)
    if typedef.typeof:
        return _primitive(sv, typedef.typeof, (*path, name))
    if name not in _PRIMITIVES:
        raise ValueError(f"Unsupported primitive type: {name}")
    return name


def _expression_slot(slot: SlotDefinition, expression: AnonymousSlotExpression) -> SlotDefinition:
    """Apply an expression without retaining the enclosing constraints being checked."""
    overrides = {"all_of": [], "none_of": []}
    overrides.update({key: value for key, value in vars(expression).items() if value is not None and value != []})
    return replace(slot, **overrides)


def _alternatives(slot: SlotDefinition) -> list[SlotDefinition]:
    """Expand unions while preserving effective outer inlining settings."""
    return [
        _expression_slot(replace(slot, any_of=[], exactly_one_of=[], multivalued=False), expression)
        for expression in [*slot.any_of, *slot.exactly_one_of]
    ]


def _value_type(sv: SchemaView, cls: ClassDefinition, slot: SlotDefinition, path: tuple[str, ...] = ()) -> str:
    """Resolve actual value representation independently of scalar nullability."""
    context = f"{cls.name}.{slot.name}"
    if slot.union_of:
        raise ValueError(f"{context}: unsupported slot union_of composition")
    if slot.range_expression or slot.enum_range or slot.array:
        raise ValueError(f"{context}: unsupported range expression or array shape")
    alternatives = _alternatives(slot)
    if alternatives:
        if slot.range is not None or sv.schema.default_range is not None:
            _value_type(sv, cls, replace(slot, any_of=[], exactly_one_of=[]), path)
        for alternative in alternatives:
            alternative_storage = _storage_type(sv, cls, alternative, path)
            if alternative.multivalued and slot.multivalued:
                raise ValueError(f"{context}: list alternatives inside collections are unsupported")
            if alternative.multivalued and alternative_storage.startswith("Dictionary["):
                raise ValueError(f"{context}: keyed collection alternatives are unsupported")
            if slot.multivalued and _alternatives(alternative):
                _storage_type(sv, cls, replace(alternative, multivalued=True), path)
            if slot.multivalued and alternative.range in sv.all_classes() and sv.is_inlined(alternative):
                key = sv.get_identifier_slot(alternative.range, use_key=True)
                if key and not slot.inlined_as_list:
                    raise ValueError(f"{context}: ambiguous keyed union")
        return "Variant"
    name = slot.range or sv.schema.default_range
    if name in sv.all_classes():
        _check_ancestry(sv, name)
        if sv.is_inlined(slot):
            return class_name(sv, sv.get_class(name, strict=True))
        if name in path:
            raise ValueError(f"{context}: cyclic identifier reference: {' -> '.join((*path, name))}")
        identifier = sv.get_identifier_slot(name)
        if identifier is None:
            raise ValueError(f"{context}: no identifier for reference to {name}")
        if identifier.multivalued:
            raise ValueError(f"{context}: nested collection identifier in {name}")
        return _storage_type(sv, sv.get_class(name), identifier, (*path, name))
    if name in sv.all_enums():
        enum_name(sv, sv.get_enum(name, strict=True))
        return "String"
    return _PRIMITIVES[_primitive(sv, name)]


def _storage_type(sv: SchemaView, cls: ClassDefinition, slot: SlotDefinition, path: tuple[str, ...] = ()) -> str:
    """Map collections and their keys without erasing scalar representation."""
    value = _value_type(sv, cls, slot, path)
    storage = f"Array[{value}]" if slot.multivalued else value
    if (
        slot.multivalued
        and value != "Variant"
        and slot.range in sv.all_classes()
        and sv.is_inlined(slot)
        and not slot.inlined_as_list
    ):
        key = sv.get_identifier_slot(slot.range, use_key=True)
        if key:
            if key.multivalued:
                raise ValueError(f"{cls.name}.{slot.name}: unsupported multivalued dictionary key {key.name}")
            key_type = _storage_type(sv, sv.get_class(slot.range), key, path)
            if key_type not in _PRIMITIVES.values():
                raise ValueError(f"{cls.name}.{slot.name}: unsupported dictionary key {key.name}")
            storage = f"Dictionary[{key_type}, {value}]"
    for expression in [*slot.all_of, *slot.none_of]:
        branch = _expression_slot(slot, expression)
        if _storage_type(sv, cls, branch, path) != storage:
            raise ValueError(f"{cls.name}.{slot.name}: constraint branch changes storage representation")
    return storage


def field_type(sv: SchemaView, cls: ClassDefinition, slot: SlotDefinition) -> str:
    """Keep object/container hints; all scalar value declarations use Variant."""
    storage = _storage_type(sv, cls, slot)
    return "Variant" if storage in _PRIMITIVES.values() else storage


def string_literal(text: str) -> str:
    """Quote a Unicode string using escapes shared by JSON and GDScript."""
    return json.dumps(str(text), ensure_ascii=False)


def escape_description(text: str) -> str:
    """Escape literal Godot BBCode without re-escaping the inserted markers."""
    return str(text).translate(str.maketrans({"[": "[lb]", "]": "[rb]"}))


def _leaf_value_types(sv: SchemaView, cls: ClassDefinition, slot: SlotDefinition) -> set[str]:
    """Resolve default compatibility through nested unions to actual value representations."""
    if slot.multivalued:
        return set()
    alternatives = _alternatives(slot)
    if not alternatives:
        return {_value_type(sv, cls, slot)}
    return {value for alternative in alternatives for value in _leaf_value_types(sv, cls, alternative)}


def field_default(sv: SchemaView, cls: ClassDefinition, slot: SlotDefinition) -> str | None:
    """Emit checked literal defaults, null scalars, or empty collections."""
    storage = _storage_type(sv, cls, slot)
    if slot.ifabsent is None:
        return "{}" if storage.startswith("Dictionary[") else "[]" if slot.multivalued else "null"
    context = f"{cls.name}.{slot.name}"
    match = re.fullmatch(r"([A-Za-z_][A-Za-z_0-9]*)\((.*)\)", str(slot.ifabsent), re.DOTALL)
    if not match or slot.multivalued or storage.startswith("LinkML"):
        raise ValueError(f"{context}: unsupported literal default {slot.ifabsent!r}")
    kind, text = match.groups()
    if text.lstrip().startswith(('"', "'")) or text.strip() in {
        "default_range",
        "class_uri",
        "slot_uri",
        "class_curie",
        "slot_curie",
        "bnode",
        "default_ns",
    }:
        raise ValueError(f"{context}: unsupported quoted or symbolic default {slot.ifabsent!r}")
    if kind not in sv.all_types():
        raise ValueError(f"{context}: unknown default type {kind!r}")
    primitive = _primitive(sv, kind)
    value_type = _PRIMITIVES[primitive]
    if value_type not in _leaf_value_types(sv, cls, slot):
        raise ValueError(f"{context}: incompatible default {slot.ifabsent!r} for {storage}")
    if primitive == "integer":
        if not re.fullmatch(r"[+-]?[0-9]+", text) or not -(2**63) <= int(text) < 2**63:
            raise ValueError(f"{context}: invalid signed 64-bit integer default {text!r}")
        return str(int(text))
    if primitive in {"float", "double", "decimal"}:
        if not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", text):
            raise ValueError(f"{context}: invalid numeric default {text!r}")
        if primitive == "decimal":
            return string_literal(text)
        number = float(text)
        if not math.isfinite(number):
            raise ValueError(f"{context}: nonfinite float default {text!r}")
        return repr(number)
    if primitive == "boolean":
        if text not in {"true", "false"}:
            raise ValueError(f"{context}: invalid boolean default {text!r}")
        return text
    return string_literal(text)


def enum_name(sv: SchemaView, enum: EnumDefinition) -> str:
    """Static enums are namespaced RefCounted hosts; unresolved enums fail."""
    if any(
        getattr(enum, field)
        for field in (
            "reachable_from",
            "code_set",
            "code_set_tag",
            "code_set_version",
            "pv_formula",
            "include",
            "minus",
            "inherits",
            "matches",
            "concepts",
            "is_a",
            "mixins",
            "values_from",
        )
    ):
        raise ValueError(f"{enum.name}: dynamic enum definitions are not supported")
    return _global_name(sv, enum.name)


def enum_member_name(sv: SchemaView, enum: EnumDefinition, value: PermissibleValue) -> str:
    """Name string constants and reject collisions within their enum host."""
    names: dict[str, str] = {}
    for member in enum.permissible_values.values():
        name = "VALUE_" + "_".join(_words(member.text)).upper()
        if name in names:
            raise ValueError(f"{enum.name}: enum values {names[name]!r} and {member.text!r} map to {name}")
        names[name] = member.text
    return "VALUE_" + "_".join(_words(value.text)).upper()


def file_name(gdscript_class_name: str) -> str:
    """Use snake_case script filenames."""
    return "_".join(_words(gdscript_class_name)).lower() + ".gd"
