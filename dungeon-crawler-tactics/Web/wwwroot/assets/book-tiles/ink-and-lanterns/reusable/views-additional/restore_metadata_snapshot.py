#!/usr/bin/env python3
"""Restore an exact, hash-bound retained metadata snapshot into an output tree."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
import zipfile


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_member(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError(f"unsafe metadata member path: {value!r}")
    rel = PurePosixPath(value)
    if rel.is_absolute() or any(part in ("", ".", "..") for part in rel.parts):
        raise ValueError(f"unsafe metadata member path: {value!r}")
    return rel


def restore(manifest_path: Path, archive_path: Path, output_root: Path) -> dict:
    manifest_path = manifest_path.resolve()
    archive_path = archive_path.resolve()
    output_root = output_root.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("kind") != "retained-metadata-snapshot":
        raise ValueError("unsupported retained metadata snapshot manifest")
    if manifest.get("provenance") != "exact-byte-retained-metadata; not regenerated from source art":
        raise ValueError("metadata snapshot provenance is missing or unsupported")

    expected_tool = manifest.get("restore_tool_sha256")
    if not expected_tool or sha_file(Path(__file__).resolve()) != expected_tool:
        raise ValueError("restore helper SHA-256 does not match snapshot manifest")
    archive_info = manifest.get("archive", {})
    if not archive_path.is_file() or archive_path.stat().st_size != archive_info.get("bytes"):
        raise ValueError("metadata snapshot archive is missing or has the wrong size")
    if sha_file(archive_path) != archive_info.get("sha256"):
        raise ValueError("metadata snapshot archive SHA-256 mismatch")

    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise ValueError("snapshot manifest has no file records")
    expected = {}
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("invalid snapshot file record")
        rel = safe_member(row.get("path"))
        if rel.as_posix() in expected:
            raise ValueError(f"duplicate snapshot member: {rel}")
        if not isinstance(row.get("bytes"), int) or row["bytes"] < 0:
            raise ValueError(f"invalid size for snapshot member: {rel}")
        if not isinstance(row.get("sha256"), str) or len(row["sha256"]) != 64:
            raise ValueError(f"invalid SHA-256 for snapshot member: {rel}")
        expected[rel.as_posix()] = row

    with zipfile.ZipFile(archive_path, "r") as archive:
        if archive.testzip() is not None:
            raise ValueError("metadata snapshot ZIP CRC verification failed")
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("ZIP members do not exactly match manifest file list")
        for info in infos:
            rel = safe_member(info.filename)
            mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode) or info.is_dir():
                raise ValueError(f"non-regular ZIP member rejected: {info.filename}")
            row = expected[rel.as_posix()]
            if info.file_size != row["bytes"]:
                raise ValueError(f"ZIP member size mismatch: {info.filename}")
            digest = hashlib.sha256()
            with archive.open(info, "r") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            if digest.hexdigest() != row["sha256"]:
                raise ValueError(f"ZIP member SHA-256 mismatch: {info.filename}")

        # Preflight all destinations before writing any file. Existing exact
        # bytes are allowed for safe repeated restore; conflicting bytes fail.
        output_root.mkdir(parents=True, exist_ok=True)
        destinations = {}
        for name, row in expected.items():
            target = (output_root / Path(*PurePosixPath(name).parts)).resolve()
            if target != output_root and output_root not in target.parents:
                raise ValueError(f"destination escapes output root: {name}")
            if target.exists():
                if not target.is_file() or target.stat().st_size != row["bytes"] or sha_file(target) != row["sha256"]:
                    raise ValueError(f"refusing to overwrite different metadata: {name}")
            destinations[name] = target

        written = 0
        for name, target in destinations.items():
            row = expected[name]
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=target.parent)
            try:
                digest = hashlib.sha256()
                count = 0
                with os.fdopen(fd, "wb") as out, archive.open(name, "r") as src:
                    for block in iter(lambda: src.read(1024 * 1024), b""):
                        out.write(block)
                        digest.update(block)
                        count += len(block)
                    out.flush()
                    os.fsync(out.fileno())
                if count != row["bytes"] or digest.hexdigest() != row["sha256"]:
                    raise ValueError(f"member changed while restoring: {name}")
                os.replace(temporary, target)
                written += 1
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)

    restored = 0
    for name, row in expected.items():
        target = output_root / Path(*PurePosixPath(name).parts)
        if target.stat().st_size != row["bytes"] or sha_file(target) != row["sha256"]:
            raise ValueError(f"restored metadata verification failed: {name}")
        restored += 1

    return {"status": "restored-exact-retained-metadata", "output_root": str(output_root),
            "manifest_sha256": sha_file(manifest_path), "archive_sha256": archive_info["sha256"],
            "files_verified": restored, "files_written": written,
            "metadata_only": True, "source_art_not_regenerated": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="hash-bound metadata snapshot manifest JSON")
    parser.add_argument("archive", type=Path, help="metadata snapshot ZIP")
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="isolated output root where exact metadata paths will be restored")
    args = parser.parse_args()
    print(json.dumps(restore(args.manifest, args.archive, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
