"""Exercise the native dependencies needed by the supported LinkML tooling."""

import subprocess

from conftest import KITCHEN_SINK


def test_erdiagram_cli_loads_native_dependencies() -> None:
    """A missing C++ runtime must fail the same diagram command developers use."""
    result = subprocess.run(
        ["gen-erdiagram", str(KITCHEN_SINK)], capture_output=True, text=True, timeout=60, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "erDiagram\n" in result.stdout, result.stdout
    for entity in ("Person", "Pet", "Address"):
        assert f"{entity} {{" in result.stdout, result.stdout
