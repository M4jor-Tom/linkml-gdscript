"""Shared fixtures."""

from pathlib import Path

import pytest
from linkml_runtime.utils.schemaview import SchemaView

KITCHEN_SINK = Path(__file__).parent / "input" / "kitchen_sink.yaml"


@pytest.fixture(scope="session")
def sv() -> SchemaView:
    """The kitchen sink schema, covering every construct of docs/MAPPING.md."""
    return SchemaView(str(KITCHEN_SINK))
