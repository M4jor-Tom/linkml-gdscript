"""The LinkML -> GDScript mapping. NOT IMPLEMENTED YET: this file is the worklist.

Everything language- and domain-specific lives here and in ``templates/``.
The plumbing (schema loading, CLI, rendering, file writing) is done and calls
these functions; it never decides what GDScript should look like.

How to work on this file:

1. Read ``docs/MAPPING.md`` and fill in the decision table first.
2. Implement one function below, replacing its ``raise NotImplementedError``.
3. Remove the ``@todo_mapping`` marker from its test in ``tests/test_mapping.py``
   (the test suite fails until you do, so nothing is forgotten).
4. ``rg 'TODO\\(mapping\\)'`` lists everything still open.

Every function receives the :class:`SchemaView`, which answers any question
about the schema (``sv.class_induced_slots``, ``sv.class_ancestors``,
``sv.get_identifier_slot``, ``sv.all_types`` ...). Slots passed in are
*induced* slots: inheritance, mixins and ``slot_usage`` are already resolved.

Return values are raw GDScript source fragments, inserted verbatim by the templates.
"""

from linkml_runtime.linkml_model.meta import ClassDefinition, EnumDefinition, PermissibleValue, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView


def class_name(sv: SchemaView, cls: ClassDefinition) -> str:
    """Return the GDScript ``class_name`` for a LinkML class.

    To decide: casing, collisions with Godot built-in classes (``Node``,
    ``Resource``, ``Object`` ...) and reserved words, optional project prefix.
    """
    raise NotImplementedError("TODO(mapping): class_name")


def base_class(sv: SchemaView, cls: ClassDefinition) -> str:
    """Return what the generated class ``extends``.

    To decide: the root type for classes without ``is_a`` (``Resource``,
    ``RefCounted``, ``Node`` ...), and whether ``is_a`` always becomes ``extends``.
    """
    raise NotImplementedError("TODO(mapping): base_class")


def class_slots(sv: SchemaView, cls: ClassDefinition) -> list[SlotDefinition]:
    """Return the induced slots declared as fields in this class's own file.

    To decide: GDScript has single inheritance only, so mixin slots must be
    flattened in somewhere; slots already inherited through ``extends`` should
    probably not be redeclared. Field order is the order returned here.
    """
    raise NotImplementedError("TODO(mapping): class_slots")


def field_name(sv: SchemaView, slot: SlotDefinition) -> str:
    """Return the GDScript variable name for a slot.

    To decide: casing, use of ``slot.alias``, collisions with reserved words
    and with members of the base class (``name``, ``script`` ...).
    """
    raise NotImplementedError("TODO(mapping): field_name")


def field_type(sv: SchemaView, slot: SlotDefinition) -> str:
    """Return the GDScript type hint for a slot, e.g. ``int`` or ``Array[Person]``.

    This is the heart of the mapping. To decide, at least:

    - each LinkML type (string, integer, float, double, decimal, boolean, date,
      datetime, time, uri, uriorcurie, curie, ncname ...) and custom ``types``
    - optional (not ``required``) scalars: ``int``/``float``/``bool`` cannot be null
    - ``multivalued``: ``Array[T]``
    - class ranges: inlined object vs. reference by identifier
    - ``inlined`` dicts: ``Dictionary[K, V]`` needs Godot >= 4.4
    - enum ranges
    - ``any_of`` / union ranges: no union types in GDScript
    """
    raise NotImplementedError("TODO(mapping): field_type")


def field_default(sv: SchemaView, slot: SlotDefinition) -> str | None:
    """Return the GDScript initialiser expression for a slot, or ``None`` for no initialiser.

    To decide: honouring ``ifabsent``, defaults for collections and for object-valued fields.
    """
    raise NotImplementedError("TODO(mapping): field_default")


def enum_name(sv: SchemaView, enum: EnumDefinition) -> str:
    """Return the GDScript ``class_name`` of the script hosting a LinkML enum.

    To decide: same questions as :func:`class_name`.
    """
    raise NotImplementedError("TODO(mapping): enum_name")


def enum_member_name(sv: SchemaView, enum: EnumDefinition, value: PermissibleValue) -> str:
    """Return the GDScript enum member for a permissible value.

    To decide: casing, permissible values that are not identifiers
    (``"in progress"``, ``"3d"``), collisions after normalisation.
    """
    raise NotImplementedError("TODO(mapping): enum_member_name")


def file_name(gdscript_class_name: str) -> str:
    """Return the file name (with ``.gd``) for a generated class or enum script.

    To decide: Godot's style guide uses snake_case file names.
    """
    raise NotImplementedError("TODO(mapping): file_name")
