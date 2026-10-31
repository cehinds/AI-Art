#!/usr/bin/env python3
"""Rebuild every generated core view set from retained raw atlases, offline."""
from pathlib import Path
import subprocess
import sys
import json

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[1]
NORMALIZER = HERE / "normalize_atlas.py"
CHARACTERS = HERE / "import_character_atlas.py"
BATCHES = [
    ("raw/world-stone-wall-water-atlas.png", "stone-floor", "wall-back", "water-floor"),
    ("raw/world-doors-bridge-atlas.png", "door-open", "door-closed", "bridge"),
    ("raw/world-crate-barrel-chest-atlas.png", "crate", "barrel", "chest"),
    ("raw/world-pipe-valve-torch-atlas.png", "pipe", "valve", "torch"),
    ("raw/world-gate-grate-stairs-atlas.png", "gate", "grate", "stairs"),
    ("raw/world-exit-rubble-rat-atlas.png", "exit-marker", "rubble", "rat"),
    ("raw/world-expansion-wall-woodfloor-atlas.png", "wall-side", "wood-floor", "wall-corner"),
    ("raw/expansion-pillar-barricade-spikes-atlas.png", "stone-pillar", "broken-barricade", "spike-trap"),
    ("raw/expansion-plate-bed-bench-atlas.png", "pressure-plate", "safe-bed", "crafting-bench"),
    ("raw/expansion-alchemy-dummy-screen-atlas.png", "alchemy-table", "training-dummy", "social-screen"),
    ("raw/expansion-armchair-rat-pair-atlas.png", "armchair", "rat-scout", "rat-guard"),
    ("raw/expansion-slime-bat-drone-atlas.png", "slime", "cave-bat", "spider-drone"),
    ("raw/expansion-mimic-sword-shield-atlas.png", "mimic", "iron-sword", "round-shield"),
    ("raw/supplies-gate-pair-helmet-atlas.png", "iron-gate-open", "iron-gate-closed", "iron-helmet"),
    ("raw/supplies-hatch-pair-leather-armor-atlas.png", "floor-hatch-open", "floor-hatch-closed", "leather-armor"),
    ("raw/supplies-lever-pair-gem-ring-atlas.png", "lever-off", "lever-on", "gem-ring"),
    ("raw/supplies-switch-pair-wand-atlas.png", "wall-switch-off", "wall-switch-on", "arcane-wand"),
    ("raw/supplies-potion-trio-atlas.png", "health-potion", "mana-potion", "antidote"),
    ("raw/supplies-gold-pouch-key-reward-box-atlas.png", "gold-pouch", "dungeon-key", "reward-box"),
    ("raw/supplies-ladder-ropebridge-campfire-atlas.png", "wood-ladder", "rope-bridge", "campfire"),
    # Keep the final batch three rows wide; this is the authoritative output for
    # ladder and rope bridge, followed by the last supplies object.
    ("raw/supplies-anvil-ladder-bridge-atlas.png", "blacksmith-anvil", "wood-ladder", "rope-bridge"),
]
EXPECTED = 65

for raw, *objects in BATCHES:
    raw_path = HERE / raw
    if not raw_path.is_file():
        raise FileNotFoundError(raw_path)
    cmd = [sys.executable, str(NORMALIZER), (Path("reusable/views-core") / raw).as_posix(), *objects]
    subprocess.run(cmd, cwd=PACK, check=True)
subprocess.run([sys.executable, str(CHARACTERS)], cwd=PACK, check=True)

index_path = HERE / "set-index.json"
index = json.loads(index_path.read_text())
sets = index.get("view_sets", [])
if len(sets) != EXPECTED:
    raise RuntimeError(f"Expected {EXPECTED} view sets, found {len(sets)}")
for view_set in sets:
    if not view_set.get("complete") or set(view_set.get("views", {})) != {"front", "top", "right", "left", "bottom", "rear"}:
        raise RuntimeError(f"Incomplete view set: {view_set.get('object_id')}")
print(f"Rebuilt {len(sets)} complete core view sets ({len(index['assets'])} view assets).")
