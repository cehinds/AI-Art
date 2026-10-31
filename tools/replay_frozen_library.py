#!/usr/bin/env python3
"""Portable frozen-metadata replay runner for four production libraries.

This is deliberately inert until called with an explicit phase and
--pack-freeze-confirmed. It never writes to a canonical pack. `freeze` records
the exact post-tag index, sidecars, active PNG byte/RGBA hashes, and all other
pack file hashes. `replay` requires that receipt, makes a plain isolated copy,
deletes active PNGs and metadata there, restores only immutable metadata inputs,
then invokes the pack's declared builder. Any active PNG needed as a declared
source dependency is restored from the frozen hash-verified snapshot and listed
as such; there is no live-output fallback. Finally the runner restores exact
frozen index/sidecar bytes and compares every generated PNG by both hashes.

No command has been executed by authoring this file. See --help for the future
freeze/replay invocation syntax.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import ZipFile, ZIP_DEFLATED
from contextlib import ExitStack

try:
    from PIL import Image
except ImportError as exc:  # fail clearly before touching any paths
    raise SystemExit("Pillow is required for canonical RGBA hashing") from exc


ASSETS = Path(__file__).resolve().parents[1] / "dungeon-crawler-tactics/Web/wwwroot/assets"
RUNBOOK = ASSETS / "replay-inputs/runbook.json"
ROOT = ASSETS / "replay-inputs/receipts"
SUPPORTED = {"style-ink", "style-dark", "book-dark", "reusable-gameplay"}
FREEZE_PHRASE = "PACK_FREEZE_CONFIRMED"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def rgba_sha(path: Path) -> str:
    with Image.open(path) as im:
        im = im.convert("RGBA")
        return sha(struct.pack(">II", im.width, im.height) + im.tobytes())


def safe_rel(value: str) -> str:
    if not isinstance(value, str) or value in ("", "."):
        raise ValueError(f"empty/dot pack-relative path is not allowed: {value!r}")
    p = PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        raise ValueError(f"unsafe pack-relative path: {value!r}")
    return p.as_posix()


def load_config() -> dict[str, dict[str, Any]]:
    doc = json.loads(RUNBOOK.read_text())
    cfg = {}
    for row in doc["libraries"]:
        if row["id"] not in SUPPORTED:
            continue
        cfg[row["id"]] = {
            "canonical_root": ASSETS / safe_rel(row["pack_root"]),
            "pack_relative": safe_rel(row["pack_root"]),
            "index_paths": [safe_rel(x["path"]) for x in row["index_paths"]],
            "builder": safe_rel(row["replay"]["entrypoint"]),
            "builder_argv": row["replay"]["command_from_isolated_pack_root"].split()[2:],
            "expected_counts": row["counts"],
            "builder_report_paths": [],
        }
    if set(cfg) != SUPPORTED:
        raise RuntimeError(f"runbook pack list mismatch: {sorted(cfg)}")
    # Ink's runbook command is a non-writing verification command. Final replay
    # must actually recreate absent outputs, so remove verify-only and preserve
    # its resolution report argument with a per-run external path.
    cfg["style-ink"]["builder_argv"] = []
    cfg["style-ink"]["resolution_report"] = True
    cfg["style-ink"]["builder_report_paths"] = ["reusable/views-additional/build_all_coordinate_resolution.json"]
    cfg["reusable-gameplay"]["builder_argv"] = []
    cfg["reusable-gameplay"]["resolution_report"] = True
    return cfg


def metadata_for(pack: Path, index_relpaths: list[str]) -> tuple[dict[str, bytes], dict[str, dict[str, Any]]]:
    metadata: dict[str, bytes] = {}
    outputs: dict[str, dict[str, Any]] = {}
    for rel in index_relpaths:
        p = pack / rel
        if not p.is_file() or p.is_symlink():
            raise FileNotFoundError(f"missing/nonregular index: {p}")
        metadata[rel] = p.read_bytes()
        idx = json.loads(metadata[rel])
        assets = idx.get("assets")
        if not isinstance(assets, list):
            raise ValueError(f"unsupported index schema (assets list missing): {rel}")
        for asset in assets:
            image = asset.get("image", {})
            png_rel = safe_rel(image.get("path", ""))
            side_rel = safe_rel(asset.get("metadata_path", ""))
            if png_rel in outputs:
                raise ValueError(f"duplicate active PNG path in index: {png_rel}")
            png = pack / png_rel
            side = pack / side_rel
            if not png.is_file() or png.is_symlink() or not side.is_file() or side.is_symlink():
                raise FileNotFoundError(f"missing/nonregular active output or sidecar: {png_rel}, {side_rel}")
            side_bytes = side.read_bytes()
            if side_rel in metadata and metadata[side_rel] != side_bytes:
                raise ValueError(f"two indexed assets disagree on shared sidecar path: {side_rel}")
            side_doc = json.loads(side_bytes)
            if not isinstance(side_doc, dict) or side_doc.get("id") != asset.get("id"):
                raise ValueError(f"sidecar identity mismatch for {asset.get('id')}: {side_rel}")
            side_image = side_doc.get("image", {})
            for key in ("path", "sha256", "rgba_sha256"):
                if side_image.get(key) != image.get(key):
                    raise ValueError(f"index/sidecar image.{key} mismatch for {asset.get('id')}")
            metadata[side_rel] = side_bytes
            # The index is the frozen emitted-byte contract; sidecar output
            # hashes must agree before creating a receipt.
            actual = {"sha256": file_sha(png), "rgba_sha256": rgba_sha(png)}
            expected = {"sha256": image.get("sha256"), "rgba_sha256": image.get("rgba_sha256")}
            if actual != expected:
                raise ValueError(f"canonical PNG differs from frozen index for {asset.get('id')}: {actual} != {expected}")
            outputs[png_rel] = {"asset_id": asset.get("id"), "sha256": actual["sha256"],
                                "rgba_sha256": actual["rgba_sha256"], "metadata_path": side_rel}
    return metadata, outputs


def discover_png_dependencies(pack: Path, metadata: dict[str, bytes], active_pngs: set[str],
                              index_paths: list[str], pack_id: str) -> dict[str, list[str]]:
    """Accept only actual builder input fields, never archival QA output hashes.

    Active output PNGs must not be used as frozen inputs. Retain any legitimate
    historical/derived input under raw/ with its exact SHA before freezing.
    Dark batch builders rebuild base outputs first and apply repairs afterwards;
    their generated intermediate reads are not pre-existing source dependencies.
    """
    hits = []
    if pack_id in {"style-ink", "reusable-gameplay"}:
        for rel, raw in metadata.items():
            if rel in index_paths or not rel.endswith('.json'):
                continue
            doc = json.loads(raw)
            if not isinstance(doc, dict):
                continue
            provenance = doc.get('provenance', {})
            fields = ['source_atlas']
            fields += ['replay_source'] if pack_id == 'style-ink' else ['source_crop_path']
            inputs = [(field, provenance.get(field)) for field in fields]
            for field in ('axis_remap', 'symmetric_projection_derivation'):
                value = provenance.get(field)
                if isinstance(value, dict):
                    inputs.append((field + '.source_path', value.get('source_path')))
            for field, value in inputs:
                if value in active_pngs:
                    hits.append({'sidecar': rel, 'field': field, 'active_png': value})
    elif pack_id not in {'style-dark', 'book-dark'}:
        raise ValueError('Unknown builder dependency contract: ' + pack_id)
    if hits:
        raise ValueError('Builder depends on active outputs; retain immutable hash-bound inputs first: ' + json.dumps(hits))
    return {}


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp-final-replay")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def tree_hashes(root: Path, excluded: set[str]) -> dict[str, str]:
    result = {}
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            raise ValueError(f"symlink is not allowed in replay pack: {p}")
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            if rel not in excluded and not rel.startswith("reusable/downloads/"):
                result[rel] = file_sha(p)
    return result


def receipt_path(pack_id: str) -> Path:
    return ROOT / pack_id / "frozen-receipt.json"


def freeze(pack_id: str, cfg: dict[str, Any]) -> None:
    pack = cfg["canonical_root"]
    metadata, outputs = metadata_for(pack, cfg["index_paths"])
    metadata_paths = sorted(metadata)
    active_paths = sorted(outputs)
    if len(outputs) != cfg["expected_counts"]["unique_indexed_pngs"]:
        raise ValueError("active PNG count differs from runbook; refresh configuration after freeze")
    report_paths = [safe_rel(p) for p in cfg["builder_report_paths"]]
    excluded = set(metadata_paths) | set(active_paths) | set(report_paths)
    immutable = tree_hashes(pack, excluded)
    active_png_paths = set(outputs)
    dependencies = discover_png_dependencies(pack, metadata, active_png_paths, cfg["index_paths"], pack_id)
    dependency_paths = sorted({p for refs in dependencies.values() for p in refs})
    out = ROOT / pack_id / "frozen-inputs"
    if out.exists() or receipt_path(pack_id).exists():
        raise FileExistsError(f"refusing to overwrite existing frozen receipt inputs: {out}")
    out.mkdir(parents=True)
    archive_path = out / "metadata.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for rel, data in sorted(metadata.items()):
            archive.writestr(rel, data)
    with ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("Frozen metadata archive integrity failure")
    dependency_snapshots = {}
    for rel in dependency_paths:
        source = pack / rel
        data = source.read_bytes()
        spec = outputs[rel]
        if sha(data) != spec["sha256"] or rgba_sha(source) != spec["rgba_sha256"]:
            raise ValueError(f"active source dependency is not hash-closed: {rel}")
        snapshot_rel = f"frozen-inputs/png-dependencies/{rel}"
        atomic_write(ROOT / pack_id / snapshot_rel, data)
        dependency_snapshots[rel] = {"snapshot_path": snapshot_rel, "sha256": spec["sha256"],
                                     "rgba_sha256": spec["rgba_sha256"]}
    receipt = {
        "schema": "frozen-pack-replay-inputs-v1", "pack_id": pack_id,
        "pack_root": cfg["pack_relative"], "frozen_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "excluded_non_builder_outputs": ["reusable/downloads/ (independently validated export bundles)"],
        "metadata_provenance": "exact byte snapshots retained from explicitly frozen post-tag canonical metadata; restored as builder input and final truth, not claimed as derived from image atlases",
        "indices": {rel: sha(metadata[rel]) for rel in cfg["index_paths"]},
        "metadata_archive": {"path": "frozen-inputs/metadata.zip", "sha256": file_sha(archive_path), "bytes": archive_path.stat().st_size},
        "metadata": {rel: {"sha256": sha(data), "snapshot_path": "frozen-inputs/metadata.zip", "snapshot_member": rel}
                     for rel, data in metadata.items()},
        "active_pngs": outputs,
        "active_png_count": len(outputs), "active_sidecar_count": len(metadata) - len(cfg["index_paths"]),
        "immutable_pack_inputs": immutable,
        "active_png_dependencies": dependencies,
        "active_png_dependency_snapshots": dependency_snapshots,
        "expected_counts_from_runbook": cfg["expected_counts"],
        "builder": cfg["builder"], "builder_argv_from_runbook": cfg["builder_argv"],
        "builder_report_paths": report_paths,
    }
    atomic_write(receipt_path(pack_id), (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"pack": pack_id, "phase": "freeze", "active_pngs": len(outputs),
                      "sidecars": receipt["active_sidecar_count"], "metadata": len(metadata),
                      "receipt": str(receipt_path(pack_id))}, indent=2))


def verify_snapshot(pack_id: str, cfg: dict[str, Any]) -> tuple[dict[str, Any], dict[str, bytes]]:
    rp = receipt_path(pack_id)
    receipt = json.loads(rp.read_text())
    if receipt.get("pack_id") != pack_id or receipt.get("pack_root") != cfg["pack_relative"]:
        raise ValueError("frozen receipt is bound to another pack")
    snaproot = ROOT / pack_id
    metadata: dict[str, bytes] = {}
    archive_spec = receipt.get("metadata_archive")
    if archive_spec and file_sha(snaproot / safe_rel(archive_spec["path"])) != archive_spec["sha256"]:
        raise ValueError("Retained metadata archive hash mismatch")
    with ExitStack() as stack:
        archives = {}
        for rel, spec in receipt["metadata"].items():
            p = snaproot / safe_rel(spec["snapshot_path"])
            if spec.get("snapshot_member"):
                if p not in archives:
                    archives[p] = stack.enter_context(ZipFile(p))
                data = archives[p].read(safe_rel(spec["snapshot_member"]))
            else:
                data = p.read_bytes()
            if sha(data) != spec["sha256"]:
                raise ValueError(f"retained metadata snapshot hash mismatch: {rel}")
            metadata[rel] = data
    for rel in cfg["index_paths"]:
        if sha(metadata[rel]) != receipt["indices"][rel]:
            raise ValueError(f"index snapshot hash mismatch: {rel}")
    return receipt, metadata


def replay(pack_id: str, cfg: dict[str, Any], output_root: Path) -> None:
    receipt, metadata = verify_snapshot(pack_id, cfg)
    canonical = cfg["canonical_root"]
    if output_root == canonical or output_root in canonical.parents or canonical in output_root.parents:
        raise ValueError("isolated destination must not overlap the canonical pack")
    if output_root.exists():
        raise FileExistsError(f"isolated destination must be new: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    isolated_pack = output_root / canonical.name
    shutil.copytree(canonical, isolated_pack, copy_function=shutil.copy2,
                    ignore=lambda folder, names: {"downloads"} if Path(folder) == canonical / "reusable" else set())
    active_pngs = receipt["active_pngs"]
    metadata_paths = set(receipt["metadata"])
    # Verify the just-copied non-output source tree against the frozen receipt.
    report_paths = set(receipt.get("builder_report_paths", []))
    excluded = set(active_pngs) | metadata_paths | report_paths
    actual_immutable = tree_hashes(isolated_pack, excluded)
    if actual_immutable != receipt["immutable_pack_inputs"]:
        raise ValueError("isolated copy has missing/extra/changed immutable source inputs")
    # Explicitly delete every active PNG and metadata file in the copy.
    for rel in active_pngs:
        p = isolated_pack / safe_rel(rel)
        if p.exists(): p.unlink()
    for rel in metadata_paths:
        p = isolated_pack / safe_rel(rel)
        if p.exists(): p.unlink()
    for rel in report_paths:
        p = isolated_pack / safe_rel(rel)
        if p.exists(): p.unlink()
    # Rehydrate frozen metadata as builder inputs, never from live files.
    for rel, data in metadata.items(): atomic_write(isolated_pack / rel, data)
    # Active output files used as sources are an explicit retained-input class.
    # Restore only declared references from immutable snapshots after deletion.
    dependencies = receipt["active_png_dependencies"]
    dep_paths = sorted({p for refs in dependencies.values() for p in refs})
    for rel in dep_paths:
        dep = receipt["active_png_dependency_snapshots"][rel]
        source = ROOT / pack_id / dep["snapshot_path"]
        expected = dep["sha256"]
        if file_sha(source) != expected or rgba_sha(source) != dep["rgba_sha256"]:
            raise ValueError(f"immutable retained dependency snapshot mismatch: {rel}")
        target = isolated_pack / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if file_sha(target) != expected:
            raise ValueError(f"retained dependency copy mismatch: {rel}")
    # Hash-guard all metadata after rehydration immediately before execution.
    for rel, data in metadata.items():
        if (isolated_pack / rel).read_bytes() != data:
            raise ValueError(f"rehydrated metadata mismatch: {rel}")
    report_dir = output_root / "reports"
    report_dir.mkdir()
    argv = [sys.executable, str(isolated_pack / cfg["builder"])] + list(cfg["builder_argv"])
    if cfg.get("resolution_report"):
        argv += ["--resolution-report", str(report_dir / "resolution.json")]
    log_path = report_dir / "builder.log"
    run_env = os.environ.copy()
    run_env["PYTHONDONTWRITEBYTECODE"] = "1"
    with log_path.open("wb") as log:
        proc = subprocess.run(argv, cwd=isolated_pack, env=run_env, stdout=log, stderr=subprocess.STDOUT, check=False)
    if proc.returncode:
        raise RuntimeError(f"builder failed ({proc.returncode}); see {log_path}")
    # Compare active outputs to frozen index expectations before restoring any
    # metadata the builder may have rewritten.
    rows, errors = [], []
    for rel, expected in active_pngs.items():
        p = isolated_pack / rel
        if not p.is_file():
            errors.append({"path": rel, "error": "missing output"}); continue
        got = {"sha256": file_sha(p), "rgba_sha256": rgba_sha(p)}
        row = {"path": rel, "expected": expected, "actual": got}
        rows.append(row)
        if got["sha256"] != expected["sha256"] or got["rgba_sha256"] != expected["rgba_sha256"]:
            errors.append({"path": rel, "error": "PNG byte/RGBA hash mismatch", **row})
    atomic_write(report_dir / "png-comparison.json", (json.dumps({"count": len(rows), "errors": errors, "rows": rows}, indent=2) + "\n").encode())
    if errors:
        raise RuntimeError(f"{len(errors)} PNG output mismatches; see {report_dir / 'png-comparison.json'}")
    # Builder metadata is not accepted as authoritative. Re-emit exact frozen
    # bytes; this is an explicit retained-metadata operation, not atlas replay.
    builder_metadata = {}
    for rel in metadata:
        p = isolated_pack / rel
        builder_metadata[rel] = p.read_bytes() if p.is_file() else None
    for rel, data in metadata.items(): atomic_write(isolated_pack / rel, data)
    metadata_rows, metadata_errors = [], []
    for rel, expected in metadata.items():
        got = (isolated_pack / rel).read_bytes()
        row = {"path": rel, "expected_sha256": sha(expected), "actual_sha256": sha(got)}
        metadata_rows.append(row)
        if got != expected: metadata_errors.append(row)
    atomic_write(report_dir / "metadata-comparison.json", (json.dumps({"count": len(metadata_rows), "errors": metadata_errors, "rows": metadata_rows,
              "provenance": "exact frozen metadata bytes re-emitted; not generated by the PNG builder"}, indent=2) + "\n").encode())
    if metadata_errors:
        raise RuntimeError("metadata/index byte mismatch after retained snapshot re-emission")
    # Only indexed active outputs may differ from the immutable copied tree.
    actual_immutable = tree_hashes(isolated_pack, set(active_pngs) | metadata_paths)
    # The allowlist is the exact builder output report list declared at freeze;
    # do not broaden this to arbitrary JSON or newly-created files.
    actual_immutable = {k: v for k, v in actual_immutable.items() if k not in report_paths}
    generated_reports = {}
    for rel in sorted(report_paths):
        p = isolated_pack / rel
        if p.exists(): generated_reports[rel] = file_sha(p)
    if actual_immutable != receipt["immutable_pack_inputs"]:
        raise RuntimeError("builder changed or created non-output pack inputs")
    summary = {"schema": "final-pack-replay-result-v1", "pack_id": pack_id,
               "canonical_root": str(canonical), "isolated_pack": str(isolated_pack),
               "builder_argv": argv, "active_pngs_compared": len(rows),
               "excluded_non_builder_outputs": receipt.get("excluded_non_builder_outputs", []),
               "active_pngs_exact": True, "metadata_files_compared": len(metadata_rows),
               "metadata_exact": True, "restored_active_png_inputs": dep_paths,
               "builder_reports": generated_reports,
               "metadata_provenance": "frozen snapshot bytes rehydrated before builder and re-emitted after exact PNG comparison",
               "builder_metadata_byte_changes": [rel for rel, before in builder_metadata.items()
                                                  if before != metadata[rel]],
               "builder_log": str(log_path), "report_dir": str(report_dir)}
    atomic_write(report_dir / "result.json", (json.dumps(summary, indent=2) + "\n").encode())
    print(json.dumps(summary, indent=2))


def main() -> None:
    global ASSETS, RUNBOOK, ROOT
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("phase", choices=("freeze", "replay"), help="freeze expected snapshots or replay one frozen pack")
    ap.add_argument("pack", choices=sorted(SUPPORTED))
    ap.add_argument("--pack-freeze-confirmed", choices=(FREEZE_PHRASE,), required=True,
                    help="explicit root gate; value must be PACK_FREEZE_CONFIRMED")
    ap.add_argument("--isolated-output", type=Path,
                    help="required for replay; must not exist; contains one plain isolated pack copy")
    ap.add_argument("--assets-root", type=Path, default=ASSETS, help="Canonical assets root; relocation is supported by pack-relative receipts")
    ap.add_argument("--runbook", type=Path, help="Portable four-pack runbook; defaults to <assets-root>/replay-inputs/runbook.json")
    ap.add_argument("--receipt-root", type=Path, help="Frozen inputs/receipts outside all packs; defaults to <assets-root>/replay-inputs/receipts")
    args = ap.parse_args()
    ASSETS = args.assets_root.resolve()
    RUNBOOK = (args.runbook or ASSETS / "replay-inputs/runbook.json").resolve()
    ROOT = (args.receipt_root or ASSETS / "replay-inputs/receipts").resolve()
    configs = load_config()
    for value in configs.values():
        pack = value["canonical_root"].resolve()
        if not pack.is_relative_to(ASSETS) or pack == ASSETS:
            raise ValueError("Runbook pack must be inside the selected assets root")
        if ROOT == pack or pack in ROOT.parents or RUNBOOK.is_relative_to(pack):
            raise ValueError("Replay receipts and runbook must be outside all pack roots")
    cfg = configs[args.pack]
    if args.phase == "freeze": freeze(args.pack, cfg)
    else:
        if args.isolated_output is None:
            ap.error("replay requires --isolated-output")
        ROOT.mkdir(parents=True, exist_ok=True)
        lock = ROOT / ".active-replay.lock"
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise SystemExit(f"another pack replay appears active; lock exists: {lock}") from exc
        try:
            with os.fdopen(fd, "w") as f:
                f.write(json.dumps({"pack": args.pack, "pid": os.getpid()}))
            replay(args.pack, cfg, args.isolated_output.resolve())
        finally:
            lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
