"""Plumbing of the GDScript generator: load a schema, render templates, write files.

Nothing in this module decides what the GDScript looks like. Those decisions
live in :mod:`linkml_gdscript.mapping` and in ``templates/``.
"""

from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from types import ModuleType
from typing import ClassVar

import click
from jinja2 import Environment, PackageLoader, StrictUndefined
from linkml.utils.generator import Generator, shared_arguments
from linkml_runtime.linkml_model.meta import PermissibleValue, SlotDefinition

from linkml_gdscript import mapping as default_mapping


def doc_comment(text: str | None, indent: str = "") -> str:
    """Format text as a GDScript documentation comment, one ``##`` per line.

    >>> print(doc_comment("A person.\\nAlive or dead."))
    ## A person.
    ## Alive or dead.
    >>> doc_comment(None)
    ''
    """
    return "\n".join(f"{indent}## {line}".rstrip() for line in (text or "").splitlines())


@dataclass(frozen=True)
class Field:
    """A slot as seen by ``class.gd.jinja``."""

    name: str
    """GDScript variable name."""
    type: str
    """GDScript type hint."""
    default: str | None
    """GDScript initialiser expression, or ``None``."""
    slot: SlotDefinition
    """The induced LinkML slot, for anything else a template needs."""


@dataclass(frozen=True)
class EnumMember:
    """A permissible value as seen by ``enum.gd.jinja``."""

    name: str
    """GDScript enum member name."""
    value: PermissibleValue
    """The LinkML permissible value (``value.text`` is the original string)."""


@dataclass
class GDScriptGenerator(Generator):
    """Generate one GDScript file per LinkML class and enum.

    :param mapping: module providing the functions documented in
        :mod:`linkml_gdscript.mapping`. Only tests need to override it.
    """

    generatorname: ClassVar[str] = Path(__file__).name
    generatorversion: ClassVar[str] = version("linkml-gdscript")
    valid_formats: ClassVar[list[str]] = ["gd"]
    file_extension: ClassVar[str] = "gd"
    uses_schemaloader: ClassVar[bool] = False
    requires_metamodel: ClassVar[bool] = False

    mapping: ModuleType = default_mapping

    def render(self) -> dict[str, str]:
        """Render the schema in memory.

        :return: GDScript source keyed by file name.
        """
        sv, m = self.schemaview, self.mapping
        env = Environment(
            loader=PackageLoader("linkml_gdscript"),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        env.filters["doc_comment"] = doc_comment
        env.globals.update(sv=sv, schema=sv.schema, mapping=m)
        files: dict[str, str] = {}

        def add(name: str, template: str, **context: object) -> None:
            file_name = m.file_name(name)
            if file_name in files:
                raise ValueError(f"Two schema elements map to the same file: {file_name}")
            files[file_name] = env.get_template(template).render(name=name, **context)

        for enum in sv.all_enums().values():
            members = [EnumMember(m.enum_member_name(sv, enum, pv), pv) for pv in enum.permissible_values.values()]
            add(m.enum_name(sv, enum), "enum.gd.jinja", enum=enum, members=members)
        for cls in sv.all_classes().values():
            fields = [
                Field(m.field_name(sv, cls, slot), m.field_type(sv, cls, slot), m.field_default(sv, cls, slot), slot)
                for slot in m.class_slots(sv, cls)
            ]
            add(m.class_name(sv, cls), "class.gd.jinja", cls=cls, base=m.base_class(sv, cls), fields=fields)
        return files

    def serialize(self, directory: str | Path | None = None, **kwargs) -> str:
        """Generate the GDScript code.

        :param directory: if given, write one file per class and enum there.
        :return: all generated sources concatenated, for inspection.
        """
        files = self.render()
        if directory is not None:
            out = Path(directory)
            out.mkdir(parents=True, exist_ok=True)
            for file_name, source in files.items():
                (out / file_name).write_text(source, encoding="utf-8")
        return "\n".join(files.values())


@shared_arguments(GDScriptGenerator)
@click.option(
    "--output-directory",
    "-d",
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory to write the .gd files to. Without it, the code is printed.",
)
@click.command(name="gen-gdscript")
def cli(yamlfile: Path, output_directory: Path | None = None, **args) -> None:
    """Generate GDScript (Godot 4) classes from a LinkML schema."""
    source = GDScriptGenerator(yamlfile, **args).serialize(directory=output_directory)
    if output_directory is None:
        click.echo(source)
