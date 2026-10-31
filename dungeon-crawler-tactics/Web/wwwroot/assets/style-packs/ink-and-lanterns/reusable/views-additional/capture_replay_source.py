"""Retain a current approved PNG as an explicit lossless replay source.

Use only when the normalized file is correct and trusted, while an older multi-stage
resampling recipe cannot reproduce its exact bytes. The retained source is copied
into raw/; build_all.py reads that independent artifact, never the output path.
"""
from pathlib import Path
import hashlib, json, re, sys

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
INDEX = OUT / "set-index.json"
if len(sys.argv) != 2:
    raise SystemExit("usage: python reusable/views-additional/capture_replay_source.py <asset-id>")
asset_id = sys.argv[1]
index = json.loads(INDEX.read_text())
assets = {a["id"]: a for a in index["assets"]}
if asset_id not in assets:
    raise SystemExit(f"unknown asset ID: {asset_id}")
meta = json.loads((PACK / assets[asset_id]["metadata_path"]).read_text())
source = PACK / meta["image"]["path"]
safe = re.sub(r"[^A-Za-z0-9._-]+", "_", asset_id)
replay = OUT / "raw" / f"{safe}.approved-replay.png"
replay.parent.mkdir(parents=True, exist_ok=True)
replay.write_bytes(source.read_bytes())
sha = hashlib.sha256(replay.read_bytes()).hexdigest()
meta.setdefault("provenance", {})["replay_source"] = replay.relative_to(PACK).as_posix()
meta["provenance"]["replay_source_sha256"] = sha
meta["provenance"]["replay_derivation"] = (
    "Approved rendered view was copied losslessly to a distinct retained raw replay artifact. "
    "Its legacy multi-stage scale calibration cannot be reconstructed byte-for-byte from the "
    "older crop parameters; exact PNG and canonical RGBA hashes are validated before replay. "
    "The replay source is separate from the output path."
)
sidecar = PACK / meta["metadata_path"]
sidecar.write_text(json.dumps(meta, indent=2) + "\n")
assets[asset_id] = meta
index["assets"] = list(assets.values())
INDEX.write_text(json.dumps(index, indent=2) + "\n")
print(f"Retained {replay.relative_to(PACK)} ({sha})")
