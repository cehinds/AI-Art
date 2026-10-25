# Remaster Environment Atlas Sources

## Status and scope

Six ImageGen-created opaque source atlases are recorded in `ArtSource/RemasterExpansion/environment/sheets.json`. Each selected PNG is 1254 × 1254 pixels, laid out as a nominal 4 × 4 square-cell atlas. The exporter uses fixed-grid cells and produces 32 × 32 tiles at 32 PPU. Names are row-major and listed in the descriptor. All sources remain **candidate art**, not canonically verified or approved for release.

These atlases are original generated reinterpretations. The reference screenshots informed palette, materials, and terrain layering only; no online game tile or sprite pixels were extracted or reused. The generated sheets have been inspected at atlas scale, but source seams are not guaranteed. Review the exporter’s assembled adjacency proofs before claiming seamless coverage or tileability.

## Reference sources

| Local reference | Online source | Use |
|---|---|---|
| `References/PixelRemaster/town-screenshot-reference.jpg` | [“O tempora: Final Fantasy II (Pixel Remaster)”](https://klardendum.com/review/o-tempora-final-fantasy-ii-pixel-remaster/) | Blue roof, cream masonry, town cobble and water palette/material cues. The page is dated 2021-11-29. |
| `References/PixelRemaster/semitt-reference.jpg` | [Semitt Falls map, FF2 Pixel Remaster guide](https://gcgx.games/ff2/re/semitt_falls.html) | Brown cave-rock strata, ledges and stair context. The page identifies the Semitt Falls map and is updated 2024-03-09. |
| `Review/art/03-environment-kit.png` | Project-approved style study | Pixel-cluster, palette and contrast reference for all six atlases. |

The web pages and local screenshots are reference material only. Their layouts, maps, and pixel art were not traced or copied into the new sheets.

## Selected sources and tile order

| Family | Selected source | Exact 4 × 4 row-major names |
|---|---|---|
| Overworld | `ArtSource/RemasterExpansion/environment/overworld-tiles-4x4.png` | grass-plain-01, grass-plain-02, earth-plain-01, earth-plain-02; sand-plain-01, sand-plain-02, snow-plain-01, snow-plain-02; forest-01 through forest-04; mountain-01 through mountain-04 |
| Town | `ArtSource/RemasterExpansion/environment/town-blue-roof-4x4-v4.png` | roof-nw, roof-n, roof-ne, wall-cream-a; roof-w, roof-center, roof-e, wall-cream-b; roof-sw, roof-s, roof-se, window; door-closed, door-open, chimney, cobble |
| Interior | `ArtSource/RemasterExpansion/environment/interior-tiles-4x4-v2.png` | stone-floor-01, stone-floor-02, wood-floor-01, wood-floor-02; carpet-nw, carpet-n, carpet-ne, table; carpet-w, carpet-center, carpet-e, chair; carpet-sw, carpet-s, carpet-se, shelf |
| Cave | `ArtSource/RemasterExpansion/environment/cave-tiles-4x4-v3.png` | wall-nw, wall-n, wall-ne, cracked-wall; wall-w, wall-center, wall-e, floor-01; wall-sw, wall-s, wall-se, floor-02; stairs-up, stairs-down, loose-rock, treasure-chest |
| Coast | `ArtSource/RemasterExpansion/environment/coast-tiles-4x4-v2.png` | shore-nw, shore-n, shore-ne, deepwater-01; shore-w, shore-center, shore-e, deepwater-02; shore-sw, shore-s, shore-se, deepwater-03; sand-01, sand-02, bridge-horizontal, bridge-vertical |
| Castle | `ArtSource/RemasterExpansion/environment/castle-tiles-4x4-v2.png` | masonry-nw, masonry-n, masonry-ne, floor-01; masonry-w, masonry-center, masonry-e, floor-02; masonry-sw, masonry-s, masonry-se, red-carpet; stairs, pillar, banner, grate |

Every selected file is opaque and square at 1254 × 1254. The descriptor records `target:[32,32]`, `ppu:32`, center pivot, family owner, 16 names, and the source dimensions. Generated revisions that were superseded remain in the environment folder and are listed with reasons in `ArtSource/RemasterExpansion/environment/excluded-sources.json`; the selected filenames above are the only sources referenced by `sheets.json`.

## Full prompts and edit provenance

All generations used the built-in ImageGen tool. The style directions below repeat the project intent in each original prompt. For edited sheets, the selected source comes from the recorded generation prompt followed by the exact cleanup edit prompt. Cleanup edits removed atlas-wide grid lines; they were still ImageGen edits, not programmatic painting.

### Overworld — selected `overworld-tiles-4x4.png`

```text
Use case: stylized-concept. Asset type: source tile atlas for a Final Fantasy II-inspired top-down JRPG remake. Primary request: create one opaque, square, perfectly uniform 4-column × 4-row atlas of exactly sixteen independent full-bleed 32px-target environment tiles, in this exact row-major order: grass-plain-01, grass-plain-02, earth-plain-01, earth-plain-02; sand-plain-01, sand-plain-02, snow-plain-01, snow-plain-02; forest-01, forest-02, forest-03, forest-04; mountain-01, mountain-02, mountain-03, mountain-04. Every cell has equal dimensions, meets its neighbors with no separator, frame, gutter, border, or grid line, and fills its entire cell. Grass: two subtly distinct green meadow textures. Earth: two brown traversable dirt textures. Sand: pale warm desert variations. Snow: clean cool-white snow variations. Forest: top-down dense evergreen canopy terrain tiles with consistent trunk/canopy scale and green palette. Mountain: rugged gray-brown mountain terrain with directional edge/peak variants suitable for overworld map placement. Style: high-quality crisp 16-bit pixel clusters, simplified readable shapes at small tile scale, restrained palette and clear value grouping, rich but not noisy. Strict overhead orthographic game-map camera, no perspective convergence. No characters, roads, buildings, text, labels, icons, tile separators, shadows, UI, watermark, or sample-board presentation. Make it a practical game tileset source sheet, not an illustration collage.
```

### Town blue roof — selected `town-blue-roof-4x4-v4.png`

The first town generation and the second grid-line cleanup remain superseded siblings in the source folder. The selected source uses the second town generation followed by both cleanup prompts below.

Generation prompt:

```text
Use case: stylized-concept. Asset type: source tile atlas for a Final Fantasy II-inspired top-down JRPG town. Generate an opaque square atlas containing exactly 16 separate game tiles in a mathematically uniform 4-column × 4-row grid. Invisible cell boundaries: absolutely no drawn grid lines, outlines, separators, borders, gutters, margins, paper, panel layout, or contact-sheet decorations. Each tile is its own 32×32-target surface filling exactly one cell edge-to-edge. Nothing may cross a cell boundary. Do not draw a single large roof or building spanning multiple cells. Exact row-major coordinates: row1 [roofNW, roofN, roofNE, wallA]; row2 [roofW, roofCenter, roofE, wallB]; row3 [roofSW, roofS, roofSE, window]; row4 [doorClosed, doorOpen, chimney, cobble]. The first nine tiles individually depict compatible sections of the same cobalt-blue curved-tile roof in strict top-down orthographic view: NW/N/NE are distinct upper edge/corner variants; W/center/E are side/interior repeats; SW/S/SE are lower edge/corner variants. Each roof section occupies one tile alone, with blue shingles and only the appropriate edge/eave on that tile. Fourth column, first two rows are cream limestone brick walls. Third-row fourth tile is a dark inset wooden window in cream masonry. Bottom-left is a closed brown door set in cream brick, next is an open matching door with dark empty doorway; row4 column3 is a standalone red-brick chimney top; row4 column4 is beige-gray cobbled ground texture. Style: crisp richly clustered 16-bit pixel art, warm masonry and classic deep blue roof colors. Strict overhead orthographic tile plane, no perspective convergence. No people, furniture, water, labels, text, iconography, shadows beyond pixel-art material shading, or watermark. Strictly respect the cell-to-content list; cell artwork must not bleed outside its exact square.
```

First line-removal edit:

```text
Edit the supplied town atlas while preserving the exact square 4×4 content layout and all material artwork, colors, roof/wall/window/door/chimney/cobble positions. Remove the thin straight black separator lines that mark the cell boundaries across the whole atlas, including the horizontal lines through roof and wall cells and the vertical line at their edges. Fill those line pixels with continuation of the adjacent material pattern. Keep the roof's natural shingle seams and the masonry/cobble texture; remove only atlas-wide straight cell divider lines. No drawn grid, framing, border, gutters, or labels. Keep each cell region in the exact current 4×4 coordinate position; do not add extra content.
```

Final targeted cleanup edit:

```text
Make one precise cleanup edit. Preserve the exact atlas contents and positions. Remove the single remaining perfectly straight black horizontal line crossing the blue roof at the 50%-height boundary (the row divider), filling it with a natural continuation of the roof shingles. Also remove any other straight atlas divider at the 4×4 tile boundaries. Keep natural curved shingle/eave outlines and the art itself. Do not add any separators, boxes, text or new objects. Opaque square full-bleed sheet.
```

### Interior — selected `interior-tiles-4x4-v2.png`

Generation prompt:

```text
Use case: stylized-concept. Asset type: interior environment tileset source atlas for an FFII-inspired top-down JRPG. Produce a square opaque image with exactly sixteen independent full-bleed tiles in a regular 4×4 grid; equal square cells, no divider lines, gutters, labels, borders, UI, or panel. No art may cross a cell edge; every cell must be its own tile surface. Exact row-major order: row1 [stone-floor-01, stone-floor-02, wood-floor-01, wood-floor-02]; rows2-4 columns1-3 are one coherent 3×3 red carpet autotile in exact positions [carpet-NW, carpet-N, carpet-NE; carpet-W, carpet-center, carpet-E; carpet-SW, carpet-S, carpet-SE]; row2-column4 is a standalone wooden table; row3-column4 is a standalone wooden chair; row4-column4 is a standalone wooden bookshelf. Stone floors are two cool gray dungeon/interior flagstone variants; wood floors are two warm oak plank variants. Carpet is a rich crimson woven rug with muted gold border and medallion center, each edge/corner fitting its exact cell. Furniture viewed strictly from overhead with clear tile footprint, polished brown wood, no room scene around it; table has simple top-down board, chair readable from overhead, shelf with books/objects viewed from above. Style: crisp clustered 16-bit pixel art with deliberate large pixel shapes, approved rich restrained JRPG palette. Opaque color/material fills to each edge, no transparency. No characters, room perspective, cast shadows, text, labels, numbers, watermark, separate inset images, or illustrative board layout. This is a practical 32px-tile atlas.
```

Selected cleanup edit:

```text
Edit the supplied atlas while preserving the square 4×4 tile layout, every tile's content and exact content order, palette, floor styles, rug, table, chair and bookshelf. Remove all dark straight grid/separator lines that coincide with the 4×4 cell boundaries, especially the horizontal lines across the atlas. Replace those line pixels with continuation of the adjacent tile material so the atlas has no visible cell framing or drawn grid. Keep each cell's content entirely within its existing square; do not make one room scene. Opaque full-bleed tile sheet, no gaps or borders between cells, no text or additional objects.
```

### Cave — selected `cave-tiles-4x4-v3.png`

Generation prompt:

```text
Use case: stylized-concept. Asset type: 4×4 atlas of individual 32px cave game tiles. This must be a TILE TEXTURE SHEET, never a cave-room illustration, floor plan, map screenshot, poster or assembled environment. Square opaque canvas. Exactly 4 equal columns × 4 equal rows; invisible uniform cell grid; each cell is independent full-bleed art filling one square and stopping at its invisible edge. No lines, cell borders, separators, gutters, labels or text. 16 tiles in exact row-major order: wall-NW, wall-N, wall-NE, cracked-wall; wall-W, wall-center, wall-E, floor-01; wall-SW, wall-S, wall-SE, floor-02; stairs-up, stairs-down, loose-rock, treasure-chest. The first nine are individual brown layered-rock cave wall pieces, each a close top-down tile-scale rock face with its named edge treatment, not part of a continuous room image. Center tile is solid rock surface; corners and edge pieces have clean readable cliff profiles. Cracked-wall is a separate fractured rock surface. Floor tiles are dark earthen cave floor with sparse small stones, completely top-down. Stairs are distinct small overhead stone steps on cave ground, one up and one down. Loose rock is one small boulder centered on brown cave ground. Chest is one small closed wooden chest centered on brown cave ground. Rich muted ochre, umber and charcoal, crisp clustered 16-bit pixel shading. Camera is orthographic straight overhead. Absolutely no giant ledges crossing slots, no multi-tile room compositions, no continuous broad scene, no characters/monsters. Opaque ground/material all the way to each cell edge. Do not draw atlas boundaries.
```

Selected cleanup edit:

```text
Preserve the square 4×4 cave atlas, exact cell contents, order, rock edges, floor, stairs, boulder and chest. Remove every thin straight atlas-wide grid/separator line exactly at the invisible 4×4 cell boundaries, both horizontal and vertical; fill each line with continuation of the appropriate adjacent pixel-art material. Retain natural irregular cave-rock contours and shading, do not alter the 16 tile concepts or move content between cells. No visible dividers, framing, gutters, labels or text. Opaque full-bleed atlas.
```

### Coast — selected `coast-tiles-4x4-v2.png`

Generation prompt:

```text
Use case: stylized-concept. Asset type: source tile atlas for a Final Fantasy II-inspired top-down JRPG coast. Square opaque image, exact 4 columns × 4 rows with sixteen equal full-bleed tile surfaces and no drawn borders, grid lines, dividers, gaps, gutters, labels, or watermarks. Each art tile occupies only its own square cell; this is not a coastline scene or map. Exact row-major positions: first three columns of first three rows are a 3×3 shoreline autotile [shore-NW, shore-N, shore-NE; shore-W, shore-center, shore-E; shore-SW, shore-S, shore-SE]. The fourth column of rows1-3 is deepwater-01, deepwater-02, deepwater-03. Row4 is sand-01, sand-02, bridge-horizontal, bridge-vertical. Shoreline tiles each show warm tan sand meeting richly blue water at the appropriately oriented edge/corner; shore-center is a mixed coastal transition surface usable where edges connect. Distinct shoreline forms should continue across compatible neighboring tile edges without border marks. Deepwater tiles are full-bleed blue water with subtle pixel wave variations and no land. Sand tiles are full-bleed pale golden sand. Bridges are top-down wooden planks over blue water, one horizontal, one vertical, both bounded inside their own cell and continuing water around them. Style: polished restrained 16-bit clustered pixel art, orthographic overhead view, crisp edge-to-edge texture, matches a rich JRPG coast rather than photorealism. No characters, boats, buildings, scenery compositions, text, symbols, captions, or UI.
```

Selected cleanup edit:

```text
Preserve the exact square 4×4 coast atlas, all 16 cell positions, shoreline orientations, water, sand, and bridge art. Remove all atlas-wide thin straight horizontal and vertical grid/separator lines at the invisible uniform cell boundaries, filling with continuation of each tile's material. Keep natural irregular foam/wave boundaries between sand and sea, but erase straight mechanical cell dividers only. No drawn grid, borders, gutters, labels, or text. Each full-bleed cell remains opaque and in its current location.
```

### Castle — selected `castle-tiles-4x4-v2.png`

Generation prompt:

```text
Use case: stylized-concept. Asset type: castle environment tile atlas for Final Fantasy II-inspired top-down JRPG. Square opaque atlas exactly 4×4 equal full-bleed tile cells, each an independent orthographic 32px-target tile. No visible grid, cell dividers, lines, separators, borders, gutters, labels, captions, or watermark. First three columns across rows1-3 are the 9-piece castle masonry autotile in exact order: [masonry-NW, masonry-N, masonry-NE; masonry-W, masonry-center, masonry-E; masonry-SW, masonry-S, masonry-SE]. Each cell is one piece of pale gray-beige castle blockwork, with proper wall top/side/corner edge only on that named tile, center a continuous masonry surface; slight dark mortar and restrained weathering. Other row-major cells: row1-column4 castle-floor-01, row2-column4 castle-floor-02, row3-column4 red-carpet, row4 [stairs, pillar, banner, grate]. Floors are two dark slate flagstone variants. Red carpet is a rich crimson strip segment with gold trim, top-down, within its tile. Stairs are a top-down short gray stone staircase. Pillar is a round pale stone column seen from above. Banner is a red-and-gold cloth hanging from a small wall fitting shown top-down, fully within tile. Grate is a dark iron floor grate. Style: rich restrained 16-bit clustered pixel art, high contrast clear masonry, direct overhead orthographic view matching the approved environment-kit material palette. No characters, weapons, room scenes, perspective, UI, text, symbols, or decorative sheet layout. Opaque material fills each cell edge-to-edge, no drawn separators.
```

Selected cleanup edit:

```text
Preserve this opaque 4×4 castle tile atlas, exact cell positions/order, stonework, floors, red carpet, stairs, pillar, banner and grate. Remove only the straight atlas-wide black grid/separator lines at the invisible equal cell boundaries, horizontal and vertical. Fill boundary pixels by continuing the neighboring material texture. Keep natural masonry mortar lines, stone edges and carpet trim. No visible grid, separators, panel borders, gutters, labels or text. Do not shift, resize, or add tile content.
```

## Verification boundary

The selected files were inspected at source scale and confirmed opaque and square. The files and descriptor establish source existence, layout contract, names, target size and PPU. They do not prove that every adjacent edge is seamless, that an assembled map is visually clean, or that the tiles have been imported into Unity or playtested.

The exporter assembled actual 32 × 32 cells into `Review/remaster-expansion/environment-assemblies.png` and family proofs. The town 3 × 3 roof and interior 3 × 3 carpet read as coherent bounded patches; cave rock detail is busy at native size. An initial coast proof incorrectly repeated the northwest corner as its exterior. The corrected `Review/remaster-expansion/environment-overview.png` uses sand outside and named shoreline edge pieces for a pond study, with an explicitly selected center variant. This fixes the assembly mistake but does not certify seamlessness: material and foam transitions still need review, and the generated corner pieces do not establish a complete shoreline autotile system. The cave room proof now uses a floor center, while the original wall-center asset remains available. Ground repetition plus Firion demonstrates the shared 32 PPU scale. The overworld and single-tile repeat proofs demonstrate export and repetition, not complete terrain transitions. No runtime import or playtest is claimed here.
