# AI Art

Dungeon Crawler artwork lives on the `dungeon-crawler` branch; `main` is the shared repository index and the other games have their own branches.

Art library for [Dungeon Crawler Tactics](https://github.com/cehinds/dungeon-crawler-tactics).

The `dungeon-crawler-tactics/` directory preserves project-relative paths, so the game can restore assets without changing browser URLs or Unity resource paths.

- `Web/wwwroot/assets/`: transparent components, directional sprites, animation strips, concept art, manifests, contact sheets and downloadable ZIP kits.
- `Docs/BookLocationTiles/sources/`: full native square tile atlases in Pocket Dungeon, Ink & Lanterns and Dungeon After Dark styles.
- `Docs/ConceptArt/`: exploration, combat and style references.
- `Docs/Screenshots/`: retained visual review captures.
- `UnityPackage/` and `UnityProject/`: runtime resource images.
- `originals/`: available unedited image-generation outputs, with their original tool job filenames and a hash index.
- `asset-index.json`: exact project paths, byte sizes and SHA-256 hashes used by the game's asset synchronizer.

## Use and update

The [Pocket Dungeon reusable library](Web/wwwroot/assets/style-packs/pocket-dungeon/reusable/README.md)
adds tagged PNG sidecars, exact reconstruction maps, transparent UI layers,
inferred six-view object sets and a seeded tile example. Its source PNGs remain
unchanged. Run `python3 tools/render_pocket_map.py --list` from the repository
root to list reconstructable originals; validation and rebuild commands are in
the library guide.

The game pins this repository to an exact commit in `art-assets.lock.json`; its Pages workflow restores and verifies the indexed files before validation and publication. Art still appears at the game's existing URLs. New art belongs here. After exporting revised assets, run `python3 tools/index_assets.py dungeon-crawler-tactics` from the repository root, commit and push the `dungeon-crawler` branch, then update the game lock to that commit and the new index hash.

The canonical tile grid is orthogonal, 128 × 128 logical pixels on transparent 256 × 256 component canvases. Doors face forward with straight horizontal thresholds. Keep the three styles visually distinct but geometrically compatible.

This is an unofficial fan project. Location-specific artwork and layouts are adaptations; an asset does not establish an exact canonical map. This repository does not grant rights to underlying third-party characters, settings or trademarks.

## Joining terrain tiles

Full floor components contain a completely opaque 128 × 128 material plane inside the shared transparent 256 × 256 sprite canvas. Their painted icon borders and faint alpha halos are excluded from the derived export. Repeating wall segments trim only the joining axis. Doors, props and partial terrain transitions retain their silhouettes.

Each affected component records its reviewed `derived.sourceWindow`; full floors also record their source-sampled grout matte. Original source atlases remain unchanged. The game's `Tools/book_tile_geometry.py` implements this deterministic normalization, and `materialInset` on an authored asset can override the default 6.5% inset.

## Tile edge tags

All 2,232 Book Location component records have explicit `edges.north`, `edges.east`, `edges.south`, and `edges.west` tag arrays in their kit manifests and ZIPs. Each side has one `join.*` connector; matching opposite connectors join after rotation. Manual-review pieces and nonjoining overlays are marked explicitly. These tags describe visual connections, independently of collision and hazards. See the [authoring guide](https://github.com/cehinds/dungeon-crawler-tactics/blob/main/Docs/Tile-Edges.md) for custom connectors, rotation, validation, and the source inventory.
