"""Verify the fifteen elite identity, animation and image-tier contracts."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
from PIL import Image

base = Path(__file__).resolve().parent
repo = base.parents[2]
manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
enemies = manifest["enemies"]
assert len(enemies) == 15
assert Counter(row["seat"] for row in enemies.values()) == {"weald": 5, "marches": 5, "reach": 5}
for key, row in enemies.items():
    assert row["role"] == "elite" and row["artRoot"].endswith("/" + key)
    assert set(row["stance"]) == {"smash", "attack", "counter", "sweep", "defend", "preparing"}
    assert set(row["clips"]) == {"attack", "react", "defend"}
    assert all(len(sequence) == 2 for sequence in row["clips"].values())
    frames = [row["idle"], *row["stance"].values(),
              *(frame for sequence in row["clips"].values() for frame in sequence), row["downed"]]
    assert len(set(frames)) == 14
    for src in ("design.png", "pose-master.png", "prompts.txt", "contact-sheet.jpg"):
        assert (base / key / src).is_file(), (key, src)
    for tier, size in (("hd", 512), ("light", 256)):
        images = repo / tier / row["artRoot"]
        assert {p.stem for p in images.glob("*.webp")} == set(frames), (key, tier)
        digests = set()
        for frame in frames:
            with Image.open(images / (frame + ".webp")) as im:
                assert im.size == (size, size) and im.mode == "RGBA", (key, tier, frame)
                a = im.getchannel("A")
                assert a.getextrema()[0] == 0 and a.getextrema()[1] >= 190
                bounds = a.point(lambda value: 255 if value > 50 else 0).getbbox()
                assert bounds and bounds[0] > 1 and bounds[1] > 1
                assert bounds[2] < size-1 and bounds[3] < size-1
                assert abs(bounds[3] - size*480/512) <= 3, (key, frame, bounds)
                digests.add(sha256(im.tobytes()).digest())
        assert len(digests) == len(frames), key
print("PASS: 15 elite identities, five per seat, 210 distinct per-enemy frames in both tiers, approved 512/256 canvas sizes and foot baseline.")

