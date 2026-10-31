#!/usr/bin/env python3
"""Replay any supplied sample JSON using only Pillow and files in this pack."""
import json, sys
from pathlib import Path
from PIL import Image
base = Path(__file__).resolve().parent
recipe = json.loads(Path(sys.argv[1]).read_text())
im = Image.new("RGBA", tuple(recipe["canvas"]))
for item in recipe["instances"]:
    im.alpha_composite(Image.open(base / item["file"]).convert("RGBA"), tuple(item["offset"]))
im.save(sys.argv[2])
