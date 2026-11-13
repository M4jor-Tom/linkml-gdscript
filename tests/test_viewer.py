"""The local schema viewer preserves Mermaid text and refuses generation errors."""

import subprocess
import sys
from pathlib import Path


def test_mermaid_is_embedded_as_text_not_html() -> None:
    """Schema labels cannot close the diagram element or inject HTML scripts."""
    from linkml_gdscript.viewer import html_page

    page = html_page('erDiagram\n</pre><script>alert(1)</script>& "Ω"')
    assert "erDiagram\n&lt;/pre&gt;&lt;script&gt;alert(1)&lt;/script&gt;&amp; &quot;Ω&quot;" in page
    assert '<pre class="mermaid">' in page


def test_missing_schema_fails_before_opening_surf(tmp_path: Path) -> None:
    """An invalid input must report the generation failure rather than open a blank viewer."""
    missing = tmp_path / "missing.yaml"
    result = subprocess.run(
        [sys.executable, "-m", "linkml_gdscript.viewer", str(missing)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode != 0
    assert str(missing) in result.stderr
    assert "does not exist" in result.stderr
