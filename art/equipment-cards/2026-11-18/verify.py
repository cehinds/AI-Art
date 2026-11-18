"""Verify the equipment proposal's complete high/light artwork coverage.
Run from any directory with Python 3 and Pillow.
"""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
from PIL import Image

pack = Path(__file__).resolve().parent
repo = pack.parents[2]
catalog = json.loads((pack / "coverage.json").read_text(encoding="utf-8"))
items = catalog["items"]
assert len(items) == len({item["name"] for item in items}) == 90
assert Counter(item["status"] for item in items) == catalog["counts"]
art_ids = {item["asset"] for item in items}
assert len(art_ids) == 90, "Two items share the same illustration"
new = [item for item in items if item["status"] != "existing"]
assert len(new) == 49
assert len(list((pack / "masters").glob("*.png"))) == len(new)
digests = set()
for item in items:
    for tier in ("hd", "light"):
        with Image.open(repo / tier / item["asset"]) as art:
            art.load()
            if item in new:
                assert art.format == "WEBP" and "A" in art.getbands(), item["id"]
                assert art.width == art.height and 0 < art.width <= 512, item["id"]
                alpha = art.getchannel("A")
                assert alpha.getextrema()[0] == 0 and alpha.getextrema()[1] >= 190
                bounds = alpha.point(lambda value: 255 if value > 48 else 0).getbbox()
                assert bounds and bounds[0] > 0 and bounds[1] > 0
                assert bounds[2] < art.width and bounds[3] < art.height
    if item in new:
        with Image.open(pack / "masters" / (item["id"] + ".png")) as master:
            assert master.format == "PNG" and min(master.size) >= 512
            assert "A" in master.getbands()
        digest = sha256((repo / "hd" / item["asset"]).read_bytes()).digest()
        assert digest not in digests, item["id"]
        digests.add(digest)
print(f"Verified {len(items)} distinct card artworks in both tiers, including {len(new)} new illustrations and their masters.")
