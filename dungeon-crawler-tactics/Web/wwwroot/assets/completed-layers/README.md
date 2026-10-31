# Completed layers

144 complete authored map modules and clean HUD backgrounds, plus optional generated repairs. No prior fragments or contextual restorations are included. Original hidden pixels cannot be recovered: surfaces are inferred.

The main demo follows the reference architecture footprint and source object anchors. Completed architecture is generated inference, split into native construction regions plus the whole gold exit, and assembled only from independent components. Regions are construction surfaces and are not counted as new authored objects. A secondary modular-room-demo demonstrates free reuse. Architecture has designed floor/canal openings. Ground remains fully covered behind all objects. Opaque stone alpha is normalized from generated high-alpha material; designed openings stay transparent. The original generated source is archived and never drawn directly by the recipe.

`manifest.json` records pivots, collision footprints, four-side sockets, alpha intent and provenance. `recipe.json` lists every placement. `layers/` contains nine category plates. The ORA contains 255 editable component instances grouped into nine categories with automatic/pass-through isolation; exact recipe replay is independently checked. `comparisons/` compare old visible-fragment layers against new modular category plates; they are not pixel-match claims.

Rebuild from repository: `python3 Tools/build_completed_layers.py`. Replay this portable package: `python3 reassemble.py --recipe recipe.json --output replay.png` (requires Pillow).
