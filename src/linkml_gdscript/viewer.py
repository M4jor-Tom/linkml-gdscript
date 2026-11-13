"""Open a LinkML schema diagram in the Nix-provided Surf browser."""

import argparse
import subprocess
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory


def html_page(mermaid: str) -> str:
    """Keep diagram source inert until the pinned Mermaid renderer reads it."""
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Rendering LinkML schema</title>
<body>
<pre class="mermaid">{escape(mermaid)}</pre>
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@12.3.0/dist/mermaid.esm.min.mjs';
mermaid.initialize({{startOnLoad: false, securityLevel: 'strict'}});
await mermaid.run();
document.title = 'LinkML schema';
</script>
</body>
</html>
"""


def main() -> None:
    """Generate a temporary diagram and keep it available until Surf closes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schema", type=Path)
    schema = parser.parse_args().schema
    result = subprocess.run(
        ["gen-erdiagram", "--format", "mermaid", str(schema)], check=True, stdout=subprocess.PIPE, text=True
    )
    with TemporaryDirectory(prefix="linkml-view-schema-") as directory:
        page = Path(directory) / "schema.html"
        page.write_text(html_page(result.stdout), encoding="utf-8")
        url = page.as_uri()
        print(url, flush=True)
        subprocess.run(["surf", "-S", "-T", url], check=True)


if __name__ == "__main__":
    main()
