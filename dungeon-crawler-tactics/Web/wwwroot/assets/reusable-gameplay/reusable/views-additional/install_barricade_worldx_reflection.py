#!/usr/bin/env python3
"""Apply the root-approved rigid world-X reflection to the Swine barricade."""
from __future__ import annotations
import hashlib, json, os
from pathlib import Path
from PIL import Image, ImageOps

PACK = Path(__file__).resolve().parents[2]
VIEWS = PACK / "reusable/views-additional"
RAW = VIEWS / "raw"
OID = "concepts-boss-swine-concept-barricade-front"
SRC = PACK / "reusable/native" / f"{OID}.png"
SOURCE_SHA = "d5127cd64c67da7739d5f847f072d6b257046ec79f98cecf7f4024ba6fef6fc0"
EXPECTED_INPUT = {
    "front": "cf4b47414e7ab6e6f22601147690bc9fd3c64021420e86796718c4a683d5653f",
    "top": "57d21c8eaab5e4997975fda085be7ec2cb0945d776a9d6ccfc95f38c008acf2b",
    "right": "c10df26f096bb4360f616051e17801ec6e51fb08d5d371354ebb1680809450ef",
    "left": "f9f79bfe1baa46c103cef95dcff64b1e3c2351f6b0b828db57023d07f69a99a1",
    "bottom": "0a069290a577684d377bd2172725f111a26736102d204f649d3b624b112eb41f",
    "rear": "4bb011c6be0489e256cc0f57efb37b150298bfd2619bfc0d1c9477e54ca2c574",
}

def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

if sha_bytes(SRC.read_bytes()) != SOURCE_SHA:
    raise SystemExit("canonical source changed; refusing install")
idx_path = VIEWS / "set-index.json"
index = json.loads(idx_path.read_text())
records = {a["id"]: a for a in index["assets"]}
staged = {}
inputs = {v: (VIEWS / f"{OID}.{v}.png").read_bytes() for v in EXPECTED_INPUT}
if any(sha_bytes(inputs[v]) != expected for v, expected in EXPECTED_INPUT.items()):
    raise SystemExit("one or more live view inputs changed; refusing install")
for view in EXPECTED_INPUT:
    im = Image.open(VIEWS / f"{OID}.{view}.png").convert("RGBA")
    if view in ("front", "rear", "top", "bottom"):
        candidate = ImageOps.mirror(im)
        input_view = view
        transform = "horizontal mirror (rigid world-X reflection)"
    else:
        input_view = "left" if view == "right" else "right"
        candidate = Image.open(VIEWS / f"{OID}.{input_view}.png").convert("RGBA")
        transform = "swap opposite camera projection under world-X reflection; no image flip"
    staged[view] = (candidate, input_view, transform, sha_bytes(candidate.tobytes()))

for view, (candidate, input_view, transform, rgba_hash) in staged.items():
    aid = f"{OID}.{view}"
    ip = VIEWS / f"{aid}.png"
    jp = VIEWS / f"{aid}.json"
    old = inputs[view]
    meta = json.loads(jp.read_text())
    tmp = ip.with_suffix(".png.tmp")
    candidate.save(tmp, format="PNG", optimize=False)
    os.replace(tmp, ip)
    written = ip.read_bytes()
    meta["image"]["sha256"] = sha_bytes(written)
    meta["image"]["rgba_sha256"] = hashlib.sha256(candidate.width.to_bytes(4,"big") + candidate.height.to_bytes(4,"big") + candidate.tobytes()).hexdigest()
    meta["provenance"].update({
        "source_image": f"reusable/native/{OID}.png",
        "source_image_sha256": SOURCE_SHA,
        "reference_source_image": f"reusable/native/{OID}.png",
        "notes": "Inferred principal view; source wheel chirality preserved by root-approved rigid world-X reflection. Not recovered pixels.",
        "generation_recipe": "reusable/views-additional/install_barricade_worldx_reflection.py",
        "source_view_asset": f"{OID}.{input_view}",
        "source_view_sha256": EXPECTED_INPUT[input_view],
        "view_transform": transform,
    })
    jp.write_text(json.dumps(meta, indent=2) + "\n")
    records[aid].clear(); records[aid].update(meta)
    (RAW / f"{aid}.worldx-reflection-20261026.json").write_text(json.dumps({
        "asset_id": aid,
        "source_image": f"reusable/native/{OID}.png",
        "source_image_sha256": SOURCE_SHA,
        "input_view": input_view,
        "input_view_sha256": EXPECTED_INPUT[input_view],
        "old_png_sha256": sha_bytes(old),
        "new_png_sha256": sha_bytes(written),
        "rgba_sha256": meta["image"]["rgba_sha256"],
        "transform": transform,
        "candidate_rgba_sha256": rgba_hash,
    }, indent=2) + "\n")
index["assets"] = [records[a["id"]] for a in index["assets"]]
idx_path.write_text(json.dumps(index, indent=2) + "\n")
print(json.dumps({v: {"sha256": records[f"{OID}.{v}"]["image"]["sha256"], "transform": staged[v][2]} for v in EXPECTED_INPUT}, indent=2))
