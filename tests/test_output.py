"""Exercise real filesystem ownership, refusals and staged publication."""

import json
from hashlib import sha256
from pathlib import Path

import pytest

from linkml_gdscript.output import write_generated_files

MANIFEST = ".linkml-gdscript.json"


def snapshot(root: Path) -> dict[str, bytes | str | None]:
    """Capture bytes and entry kinds without following even broken symlinks."""
    return {
        str(path.relative_to(root)): (
            str(path.readlink()) if path.is_symlink() else path.read_bytes() if path.is_file() else None
        )
        for path in root.rglob("*")
    }


def test_removes_only_owned_obsolete_files(tmp_path: Path) -> None:
    """Two generations preserve a neighbor and retire only tracked scripts."""
    neighbor = tmp_path / "handwritten.gd"
    neighbor.write_text("extends RefCounted\n", encoding="utf-8")
    write_generated_files(tmp_path, {"old.gd": "old\n", "keep.gd": "one\n"}, "urn:test")
    write_generated_files(tmp_path, {"keep.gd": "two\n"}, "urn:test")
    assert not (tmp_path / "old.gd").exists()
    assert neighbor.read_text() == "extends RefCounted\n"
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    assert manifest == {"format": 1, "schema_id": "urn:test", "files": {"keep.gd": sha256(b"two\n").hexdigest()}}


def test_refuses_modified_owned_file_before_any_write(tmp_path: Path) -> None:
    """A handwritten edit is not expendable just because a manifest exists."""
    write_generated_files(tmp_path, {"a.gd": "a\n", "b.gd": "b\n"}, "urn:test")
    (tmp_path / "b.gd").write_text("manual edit\n")
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    with pytest.raises(ValueError, match="b.gd"):
        write_generated_files(tmp_path, {"a.gd": "new\n"}, "urn:test")
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


@pytest.mark.parametrize("location", ["new", "manifest"])
@pytest.mark.parametrize(
    "name", ["../outside.gd", "/outside.gd", "a/b.gd", "a\\b.gd", "C:outside.gd", "..", ".gd", "bad.txt", "a\0.gd"]
)
def test_refuses_unsafe_names(tmp_path: Path, location: str, name: str) -> None:
    """Neither current nor prior filenames may escape the owned basenames."""
    root = tmp_path / "generated"
    write_generated_files(root, {"a.gd": "old"}, "urn:test")
    (tmp_path / "outside.gd").write_text("sentinel")
    files = {"a.gd": "new"}
    if location == "new":
        files[name] = "unsafe"
    else:
        manifest = json.loads((root / MANIFEST).read_text())
        manifest["files"][name] = sha256(b"unsafe").hexdigest()
        (root / MANIFEST).write_text(json.dumps(manifest))
    before = snapshot(tmp_path)
    with pytest.raises(ValueError, match="filename"):
        write_generated_files(root, files, "urn:test")
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "change",
    [
        {"schema_id": "urn:other"},
        {"schema_id": 1},
        {"format": 2},
        {"format": True},
        {"format": "1"},
        {"files": []},
        {"files": {"a.gd": "bad"}},
        {"files": {"a.gd": "A" * 64}},
        {"files": {"a.gd": 1}},
        {"files": {"a.gd": "0" * 64, "A.gd": "0" * 64}},
        {"extra": True},
    ],
)
def test_refuses_invalid_manifest(tmp_path: Path, change: dict) -> None:
    """Manifest types, ownership, names and hashes are checked before publication."""
    write_generated_files(tmp_path, {"a.gd": "old"}, "urn:test")
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    manifest.update(change)
    (tmp_path / MANIFEST).write_text(json.dumps(manifest))
    before = snapshot(tmp_path)
    with pytest.raises(ValueError):
        write_generated_files(tmp_path, {"a.gd": "new"}, "urn:test")
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("text", ["{", "[]", "null", "{}"])
def test_refuses_malformed_manifest(tmp_path: Path, text: str) -> None:
    """JSON syntax and invalid top-level shapes must not change ownership."""
    write_generated_files(tmp_path, {"a.gd": "old"}, "urn:test")
    (tmp_path / MANIFEST).write_text(text)
    before = snapshot(tmp_path)
    with pytest.raises(ValueError):
        write_generated_files(tmp_path, {"a.gd": "new"}, "urn:test")
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("key", ["format", "schema_id", "a.gd"])
def test_refuses_duplicate_manifest_keys(tmp_path: Path, key: str) -> None:
    """Otherwise valid manifests cannot hide duplicate keys, even in the file map."""
    write_generated_files(tmp_path, {"a.gd": "old"}, "urn:test")
    path = tmp_path / MANIFEST
    manifest = json.loads(path.read_text())
    value = manifest["files"][key] if key == "a.gd" else manifest[key]
    pair = f"{json.dumps(key)}: {json.dumps(value)}"
    path.write_text(path.read_text().replace(pair, f"{pair}, {pair}"))
    before = snapshot(tmp_path)
    with pytest.raises(ValueError, match=f"Duplicate manifest key: {key}"):
        write_generated_files(tmp_path, {"a.gd": "new"}, "urn:test")
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("kind", ["missing", "edited", "symlink", "broken-symlink", "directory"])
@pytest.mark.parametrize("retained", [True, False])
def test_refuses_unsafe_owned_file(tmp_path: Path, kind: str, retained: bool) -> None:
    """Check every owned file, including retained files and broken links."""
    root = tmp_path / "generated"
    write_generated_files(root, {"a.gd": "old", "b.gd": "owned"}, "urn:test")
    outside = tmp_path / "outside.gd"
    outside.write_text("sentinel")
    path = root / "b.gd"
    path.unlink()
    if kind == "edited":
        path.write_text("edit")
    elif kind == "symlink":
        path.symlink_to(outside)
    elif kind == "broken-symlink":
        path.symlink_to(tmp_path / "missing")
    elif kind == "directory":
        path.mkdir()
    before = snapshot(tmp_path)
    files = {"a.gd": "new", "b.gd": "new"} if retained else {"a.gd": "new"}
    with pytest.raises(ValueError, match="b.gd"):
        write_generated_files(root, files, "urn:test")
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("kind", ["file", "same-bytes", "case-fold", "symlink", "broken-symlink", "directory"])
@pytest.mark.parametrize("manifest_present", [True, False])
def test_refuses_unmanaged_target(tmp_path: Path, kind: str, manifest_present: bool) -> None:
    """No unmanaged entry can be adopted, including legacy output with no manifest."""
    root = tmp_path / "generated"
    if manifest_present:
        write_generated_files(root, {"a.gd": "old"}, "urn:test")
    else:
        root.mkdir()
    outside = tmp_path / "outside.gd"
    outside.write_text("sentinel")
    path = root / ("B.gd" if kind == "case-fold" else "b.gd")
    if kind == "directory":
        path.mkdir()
    elif kind in {"symlink", "broken-symlink"}:
        path.symlink_to(outside if kind == "symlink" else tmp_path / "missing")
    else:
        path.write_text("new" if kind == "same-bytes" else "unmanaged")
    before = snapshot(tmp_path)
    with pytest.raises(ValueError, match="b.gd"):
        write_generated_files(root, {"a.gd": "new", "b.gd": "new"}, "urn:test")
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("target", ["root", "manifest"])
@pytest.mark.parametrize("kind", ["symlink", "broken-symlink", "wrong-kind"])
def test_refuses_unsafe_root_or_manifest(tmp_path: Path, target: str, kind: str) -> None:
    """Reject root/manifest symlinks independently of whether they exist."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel").write_text("unchanged")
    root = tmp_path / "generated"
    if target == "manifest":
        root.mkdir()
    path = root if target == "root" else root / MANIFEST
    if kind == "wrong-kind":
        path.write_text("not a directory") if target == "root" else path.mkdir()
    else:
        path.symlink_to(outside if kind == "symlink" else tmp_path / "missing")
    before = snapshot(tmp_path)
    with pytest.raises(ValueError):
        write_generated_files(root, {"a.gd": "new"}, "urn:test")
    assert snapshot(tmp_path) == before


def test_refuses_new_case_fold_collision_before_creating_directory(tmp_path: Path) -> None:
    """New names must also be portable to case-insensitive filesystems."""
    root = tmp_path / "generated"
    with pytest.raises(ValueError, match="collision"):
        write_generated_files(root, {"a.gd": "a", "A.gd": "b"}, "urn:test")
    assert not root.exists()


def test_repeat_empty_unicode_and_unrelated_entries(tmp_path: Path) -> None:
    """Deterministic bytes and zero-file generations preserve sidecars and neighbors."""
    (tmp_path / "handwritten.gd").write_text("manual")
    (tmp_path / "z.gd.uid").write_text("uid://keep")
    (tmp_path / ".godot").mkdir()
    (tmp_path / ".godot" / "cache").write_text("keep")
    unrelated = snapshot(tmp_path)
    files = {"z.gd": "Ω café 😀\n", "a.gd": "a\n"}
    write_generated_files(tmp_path, files, "urn:test")
    before = snapshot(tmp_path)
    write_generated_files(tmp_path, dict(reversed(files.items())), "urn:test")
    assert snapshot(tmp_path) == before
    assert (tmp_path / "z.gd").read_bytes() == files["z.gd"].encode("utf-8")
    manifest = json.loads((tmp_path / MANIFEST).read_text())
    assert manifest["files"]["z.gd"] == sha256(files["z.gd"].encode("utf-8")).hexdigest()
    assert (tmp_path / MANIFEST).read_bytes() == (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    write_generated_files(tmp_path, {}, "urn:test")
    assert snapshot(tmp_path) == unrelated | {
        MANIFEST: b'{\n  "files": {},\n  "format": 1,\n  "schema_id": "urn:test"\n}\n'
    }
    write_generated_files(tmp_path / "empty", {}, "urn:test")
    assert json.loads((tmp_path / "empty" / MANIFEST).read_text())["files"] == {}


def test_staging_failure_preserves_owned_bytes(tmp_path: Path) -> None:
    """A real staging-directory permission failure leaves all old output intact."""
    write_generated_files(tmp_path, {"a.gd": "old", "obsolete.gd": "keep"}, "urn:test")
    before = snapshot(tmp_path)
    mode = tmp_path.stat().st_mode
    tmp_path.chmod(0o500)
    try:
        with pytest.raises(PermissionError) as failure:
            write_generated_files(tmp_path, {"a.gd": "new"}, "urn:test")
        assert Path(failure.value.filename).name.startswith(".linkml-gdscript-")
        assert snapshot(tmp_path) == before
    finally:
        tmp_path.chmod(mode)


def test_refuses_case_fold_neighbor_of_retained_target(tmp_path: Path) -> None:
    """An unmanaged case variant added later still conflicts with a current target."""
    write_generated_files(tmp_path, {"a.gd": "old"}, "urn:test")
    (tmp_path / "A.gd").write_text("manual")
    before = snapshot(tmp_path)
    with pytest.raises(ValueError, match="a.gd"):
        write_generated_files(tmp_path, {"a.gd": "new"}, "urn:test")
    assert snapshot(tmp_path) == before
