# Art review and remaining work

The higher-resolution library is growing alongside the preserved first-pass Campaign library. A source sheet, a normalized PNG, a timed preview and a working Unity animation are separate completion states. The [generated coverage report](RemasterExpansionCoverage.md) is the measured export inventory.

## Next production passes

| Priority | Deliverable | Review evidence needed |
| --- | --- | --- |
| 1 | Complete each higher-resolution battle set with idle, hit, critical, victory and KO states | Same costume, body scale and baseline as its attack/cast; readable transitions at native size |
| 2 | Extend 64 px four-direction field walks beyond Firion | Distinct stride/passing poses, consistent direction, feet registration, map-scale preview |
| 3 | Repair environment joins and supply missing edge/corner combinations | Actual exported tiles assembled into rooms, shore bends, paths and floor/wall transitions; no painted-over proof images |
| 4 | Build location-specific palettes and map assemblies | Original-game layout reference, collision and elevation review, door/stair connectivity, props and events |
| 5 | Integrate and review in Unity | Licensed Editor import validation, generated clips, SpriteRenderer/Animator wiring, correct PPU, pixel-camera review and playback |

The small Campaign battle sheets already include individual idle, wind-up, attack, cast, hit, critical, victory and KO poses. Their existence does not provide complete 128 px animation coverage. Likewise, a 128 px canvas includes movement and weapon space; the character body occupies only part of that canvas.

Attack and cast timings are authored interpretations of readable JRPG action phases. They have not been measured from Pixel Remaster footage. Existing state IDs and source revisions remain preserved so future animation work can be added without renaming current assets.

No task in this list implies that the full campaign, all equipment variants, all map tiles or every event animation is complete. Runtime review remains pending while Unity licensing is unavailable.
