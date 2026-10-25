# AI Art

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

The game pins this repository to an exact commit in `art-assets.lock.json`; its Pages workflow restores and verifies the indexed files before validation and publication. Art still appears at the game's existing URLs. New art belongs here. After exporting revised assets, update `asset-index.json`, commit and push this repository, then update the game lock to that commit and the new index hash.

The canonical tile grid is orthogonal, 128 × 128 logical pixels on transparent 256 × 256 component canvases. Doors face forward with straight horizontal thresholds. Keep the three styles visually distinct but geometrically compatible.

This is an unofficial fan project. Location-specific artwork and layouts are adaptations; an asset does not establish an exact canonical map. This repository does not grant rights to underlying third-party characters, settings or trademarks.
