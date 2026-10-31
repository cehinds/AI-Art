# World Components V1 — candidate tile pipeline

This pass creates assets only. It does not modify the game, Unity scenes, bindings, map geometry, collision or save files. Reference captures inform the generated component geometry and palette; reference screenshot pixels are not production assets.

Generated masters live under `ArtSource/WorldComponentsV1/`. Register inspected atlas definitions in `Tools/world-components-v1/kit.json`. Each definition supplies a unique ID, source path, columns, rows, native `tileSize` (32 or 64), and one row-major declaration per cell. Optional `sourceCrop` is an inspected source-pixel rectangle. For continuous terrain, the exporter trims transparent margins around the **whole atlas as one group**. Opaque sheet margins require an explicit inspected crop; they are never guessed from color.

Continuous terrain atlases are resized once with nearest-neighbor sampling, then native cells are sliced. Their cells are never independently fitted, preserving shared grid registration. The explicit `cutout-atlas` exception is for isolated bridge/mountain objects: split the original regular source slots first, trim each silhouette at alpha ≥128, fit inside 60×60 while preserving aspect, and place it bottom-center on a transparent 64×64 canvas. This removes oversized source gutters without treating isolated objects as terrain-edge tiles. Source slot, silhouette crop, native placement and alpha/bbox statistics are recorded. No production pixels are painted or recolored. Original masters stay unchanged with SHA-256 provenance.

Every tile declares `terrain`, `layer`, `cornerRole`, `anchor`, and `ports` for north/east/south/west. Port strings describe material profiles; north/south profiles read west-to-east, and east/west profiles read north-to-south. River masks use N=1, E=2, S=4, W=8; bridge walk ports and water-flow ports must be declared separately. These are asset semantics, not runtime collision or a claim of WFC compatibility.

Assemblies describe grids of `sheet/id` references. Layer stacks are supported only when every layer shares the same native tile size. This kit's 64px bridge objects are shown separately from its 32px water cells; no implicit resampling hides that difference. Assemblies and the cutout checkerboard are displayed at 3× nearest-neighbor scale. Boundary RGB differences are diagnostic measurements, not pass/fail thresholds or proof of seamless artwork. Inspect coast width, water color, turns/junctions, bridge endpoints and mountain silhouettes directly.

```powershell
node Tools/world-components-v1/export.cjs --check-only
node Tools/world-components-v1/export.cjs
node Tools/world-components-v1/verify.cjs
```

Preflight writes nothing. Ordinary export refuses to overwrite a differing existing production PNG and preserves metadata; use a new versioned candidate ID for a changed master/crop. Derived review files and the kit manifest are refreshed by export. Read-only verification reconstructs every native PNG from the preserved master and its declared terrain/cutout transform, checks source/prompt hashes, alpha/bbox records, ports, unique GUIDs and registered-output inventory.

Review starts at `Review/world-components-v1/index.html`; the manifest lives at `Assets/Art/Production/WorldComponentsV1/manifest.json`. The [native assembly review](visual-review.md) records visible limits. Current delivery: **38 candidate assets from five preserved masters, six atlas/crop definitions, 14 adjacency assemblies and one cutout alpha checker**. No game integration or Unity validation was performed in this asset pass.

| Family | Count | Native canvas |
|---|---:|---|
| Convex island coast / grass center | 9 | 32×32 |
| River masks 0–15 | 16 | 32×32 |
| Open water crop | 1 | 32×32 |
| Natural cliff edges S/N/E/W | 4 | 32×32 |
| Stone bridge spans / candidate abutments | 4 | 64×64 transparent |
| Gold-rock mountain cluster variants | 4 | 64×64 transparent |
