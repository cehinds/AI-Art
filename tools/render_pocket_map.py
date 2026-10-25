#!/usr/bin/env python3
"""Recreate a Pocket Dungeon source image from its indexed PNG layers.

Examples:
  python tools/render_pocket_map.py --list
  python tools/render_pocket_map.py --map atlas-world --output /tmp/world.png
  python render_pocket_map.py --pack pocket-dungeon --map concept-original --output recreated.png
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from validate_pocket_reusable import DEFAULT_PACK, contained, digest, image_info, read_json, render


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--map", dest="map_name", help="Map id or pack-relative map JSON path")
    parser.add_argument("--output", type=Path, help="Destination PNG (source files are protected)")
    parser.add_argument("--list", action="store_true", help="List available reconstruction maps")
    args = parser.parse_args()
    try:
        pack = args.pack.resolve()
        index = read_json(pack / "reusable/index.json")
        if args.list:
            for item in index["maps"]:
                print(f"{item['id']}\t{item['label']}\t{item['source']}")
            return 0
        if not args.map_name or not args.output:
            parser.error("--map and --output are required unless --list is used")
        entries = {item["id"]: item for item in index["maps"]}
        relative = entries[args.map_name]["file"] if args.map_name in entries else args.map_name
        document = read_json(contained(pack, relative))
        assets = {asset["id"]: asset for asset in index["assets"]}
        source = image_info(pack, document["source"])
        protected = {contained(pack, asset["image"]["path"]).resolve() for asset in assets.values()}
        protected.update(contained(pack, item["source"]).resolve() for item in index["maps"])
        if args.output.resolve() in protected:
            raise ValueError("Output would overwrite original or reusable artwork; choose a new PNG path")
        if args.output.suffix.lower() != ".png":
            raise ValueError("Output must use .png for lossless RGBA preservation")
        for asset_id in {layer["asset_id"] for layer in document["layers"]}:
            image_info(pack, assets[asset_id]["image"])
        result = render(pack, document, assets)
        if source.size != result.size or source.tobytes() != result.tobytes():
            raise ValueError("Reconstruction differs from its source; refusing to label it exact")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result.save(args.output, format="PNG")
        print(json.dumps({"map": document["id"], "output": str(args.output), "width": result.width,
                          "height": result.height, "rgba_sha256": digest(result), "differing_pixels": 0}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"render_pocket_map: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
