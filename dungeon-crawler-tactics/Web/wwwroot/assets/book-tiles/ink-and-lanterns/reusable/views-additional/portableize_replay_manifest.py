#!/usr/bin/env python3
"""Convert an external replay manifest to pack-relative retained-input refs.

Use --plan-only to write a portable-shaped manifest without changing the pack.
Use --stage-retained only after the pack is frozen; it verifies and copies all
external immutable inputs into raw/replay-retained before emitting a ready
portable manifest. It never reads or stages mutable output PNGs as dependencies.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, shutil, struct, tempfile
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_PACK = HERE.parents[1]

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def rgba_sha(path: pathlib.Path) -> str:
    image = Image.open(path).convert("RGBA")
    return sha(struct.pack(">II", *image.size) + image.tobytes())

def safe_rel(value: str) -> pathlib.PurePosixPath:
    rel = pathlib.PurePosixPath(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"portable ref must be traversal-free and pack-relative: {value}")
    return rel

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=pathlib.Path)
    parser.add_argument("--pack-root", type=pathlib.Path, default=DEFAULT_PACK)
    parser.add_argument("--output", required=True, type=pathlib.Path, help="portable manifest output; keep outside pack during preflight")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan-only", action="store_true", help="do not write retained files into pack")
    mode.add_argument("--stage-retained", action="store_true", help="stage exact immutable inputs under the frozen pack")
    args = parser.parse_args()

    pack = args.pack_root.resolve()
    manifest = json.loads(args.manifest.read_text())
    index_path = pack / "reusable/views-additional/set-index.json"
    index_hash = sha(index_path.read_bytes())
    if manifest.get("index_sha256") != index_hash:
        raise SystemExit(f"manifest/index hash mismatch: {manifest.get('index_sha256')} != {index_hash}")

    staged = {}
    def retain(task: dict, external_field: str, portable_field: str, expected_field: str, rgba_field: str | None,
               purpose: str) -> None:
        external = task.get(external_field)
        if not external:
            return
        source = pathlib.Path(external).resolve()
        if source == pack or pack in source.parents:
            raise ValueError(f"retained source unexpectedly points inside pack: {external}")
        expected = task.get(expected_field)
        if not expected or sha(source.read_bytes()) != expected:
            raise ValueError(f"immutable retained source hash mismatch: {external}")
        if rgba_field and task.get(rgba_field) and rgba_sha(source) != task[rgba_field]:
            raise ValueError(f"immutable retained RGBA hash mismatch: {external}")
        ref = safe_rel(task.get(portable_field) or
                       (pathlib.PurePosixPath("reusable/views-additional/raw/replay-retained") / purpose / source.name).as_posix())
        if not ref.as_posix().startswith("reusable/views-additional/raw/replay-retained/"):
            raise ValueError(f"portable retained ref outside owned replay namespace: {ref}")
        dest = pack.joinpath(*ref.parts)
        if args.stage_retained:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                if sha(dest.read_bytes()) != expected:
                    raise ValueError(f"refusing to replace different retained input: {ref.as_posix()}")
            else:
                shutil.copy2(source, dest)
            if sha(dest.read_bytes()) != expected:
                raise ValueError(f"staged retained input failed hash check: {ref.as_posix()}")
        task[portable_field] = ref.as_posix()
        task.pop(external_field, None)
        staged[ref.as_posix()] = {"sha256": expected, "rgba_sha256": task.get(rgba_field) if rgba_field else None,
                                  "source_kind": "immutable retained reviewed-current input", "purpose": purpose}

    for task in manifest.get("tasks", []):
        retain(task, "external_source_path", "source_portable_ref", "source_sha256", "source_rgba_sha256", "inputs")
        retain(task, "fallback_external_source_path", "fallback_portable_ref", "fallback_sha256", "fallback_rgba_sha256", "fallback")

    for row in manifest.get("catalog_only_outputs", []):
        external = row.pop("retained_input_path", None)
        if not external:
            continue
        source = pathlib.Path(external).resolve()
        expected = row.get("retained_input_sha256")
        if not expected or sha(source.read_bytes()) != expected:
            raise ValueError(f"catalog retained input hash mismatch: {external}")
        ref = safe_rel(row.get("retained_input_ref") or
                       (pathlib.PurePosixPath("reusable/views-additional/raw/replay-retained/catalog") / source.name).as_posix())
        if not ref.as_posix().startswith("reusable/views-additional/raw/replay-retained/"):
            raise ValueError(f"portable catalog ref outside owned replay namespace: {ref}")
        dest = pack.joinpath(*ref.parts)
        if args.stage_retained:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() and sha(dest.read_bytes()) != expected:
                raise ValueError(f"refusing to replace different catalog retained input: {ref.as_posix()}")
            if not dest.exists():
                shutil.copy2(source, dest)
            if sha(dest.read_bytes()) != expected:
                raise ValueError(f"staged catalog input failed hash check: {ref.as_posix()}")
        row["retained_input_ref"] = ref.as_posix()
        row["retained_input_rgba_sha256"] = rgba_sha(source)
        staged[ref.as_posix()] = {"sha256": expected, "source_kind": "immutable retained reviewed-current input",
                                  "purpose": "catalog-only output; not regenerated from historical source"}

    manifest["portable_retained_inputs"] = staged
    manifest["portable_inputs_staged"] = bool(args.stage_retained)
    manifest["portable_manifest_ready"] = bool(args.stage_retained)
    manifest["portable_provenance"] = "All retained inputs are hash-bound immutable reviewed-current PNGs. Source-atlas recipes remain separate and are not replaced with current outputs."
    serialized = json.dumps(manifest, indent=2) + "\n"
    if any(token in serialized for token in ("/scratch/", "\\scratch\\", "/tmp/", "\\tmp\\", "/workspace/", "\\workspace\\")):
        raise ValueError("portable manifest still contains an absolute workspace or scratch dependency")
    output = args.output.resolve()
    if output == pack or pack in output.parents:
        raise ValueError("write the portable manifest outside the pack during this operation")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=output.parent, prefix=output.name + ".", suffix=".tmp")
    with os.fdopen(fd, "w") as stream:
        stream.write(serialized); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, output)
    print(json.dumps({"output": str(output), "index_sha256": index_hash,
                      "portable_refs": len(staged), "portable_inputs_staged": args.stage_retained,
                      "portable_manifest_ready": args.stage_retained}))

if __name__ == "__main__":
    main()
