"""Single-schema ownership and safe preflight for generated scripts.

Publication uses atomic file replacements, not a directory transaction. I/O failures
propagate; recover into a fresh directory rather than trusting a partial publication.
This is a single-writer protocol, not protection against concurrent filesystem changes.
"""

import hashlib
import json
import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory

MANIFEST_NAME = ".linkml-gdscript.json"


def _validate_names(names: object) -> None:
    """Require a file map with plain, case-fold-unique GDScript basenames."""
    if not isinstance(names, dict):
        raise ValueError("Generated files must be a filename map")
    seen: set[str] = set()
    for name in names:
        if (
            not isinstance(name, str)
            or not name.endswith(".gd")
            or name == ".gd"
            or any(char in name for char in ("/", "\\", "\0", ":"))
            or Path(name).is_absolute()
        ):
            raise ValueError(f"Invalid generated filename: {name!r}")
        if name.casefold() in seen:
            raise ValueError(f"Case-fold collision in generated filename: {name}")
        seen.add(name.casefold())


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate JSON keys rather than silently changing ownership."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate manifest key: {key}")
        result[key] = value
    return result


def _load_owned(path: Path, schema_id: str) -> dict[str, str]:
    """Read and validate format 1 ownership without adopting existing scripts."""
    if path.is_symlink():
        raise ValueError(f"Refusing symlink manifest: {path}")
    if not path.exists():
        return {}
    if not path.is_file():
        raise ValueError(f"Manifest is not a regular file: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"format", "schema_id", "files"}
        or type(manifest["format"]) is not int
        or manifest["format"] != 1
        or not isinstance(manifest["schema_id"], str)
        or manifest["schema_id"] != schema_id
    ):
        raise ValueError(f"Invalid manifest format or schema ID: {path}; use a fresh output directory")
    owned = manifest["files"]
    _validate_names(owned)
    for name, digest in owned.items():
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError(f"Invalid manifest digest for {name}")
    return owned


def write_generated_files(directory: str | Path, files: dict[str, str], schema_id: str) -> None:
    """Preflight, stage, then publish current files and retire verified owned scripts.

    No writes occur on validation failures. Unmanaged targets and changed or missing
    owned files require a fresh output directory; no ownership takeover is supported.
    """
    _validate_names(files)
    payloads = {name: source.encode("utf-8") for name, source in files.items()}
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}
    if not isinstance(schema_id, str):
        raise ValueError("Schema ID must be a string")
    root = Path(directory)
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError(f"Output root must be a non-symlink directory: {root}")
    owned = _load_owned(root / MANIFEST_NAME, schema_id)
    for name, digest in owned.items():
        path = root / name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Owned file missing, modified or not regular: {name}; use a fresh output directory")
    unmanaged = {path.name.casefold() for path in root.iterdir() if path.name not in owned} if root.exists() else set()
    for name in files:
        path = root / name
        if name.casefold() in unmanaged or (name not in owned and (path.is_symlink() or path.exists())):
            raise ValueError(f"Unmanaged target collision: {name}; use a fresh output directory")
    manifest = {"format": 1, "schema_id": schema_id, "files": hashes}
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    root.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".linkml-gdscript-", dir=root) as temporary:
        staged = Path(temporary)
        for name, data in payloads.items():
            (staged / name).write_bytes(data)
        (staged / MANIFEST_NAME).write_bytes(manifest_bytes)
        for name in sorted(files):
            os.replace(staged / name, root / name)
        for name in sorted(owned.keys() - files.keys()):
            (root / name).unlink()
        os.replace(staged / MANIFEST_NAME, root / MANIFEST_NAME)
