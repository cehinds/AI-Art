# Extra Environment Tile Sources

## Status

These are four ImageGen-generated, opaque square 4×4 source atlases for environment coverage expansion. Each selected descriptor in `ArtSource/RemasterExpansion/environment-extra/sheets.json` names sixteen row-major cells for export to 32×32 at 32 PPU. All four masters are review candidates. Their surfaces, drawn transitions, and seams must be judged from the exporter’s actual fixed-grid crops and native assembled proofs. No seamlessness or runtime approval is claimed. Superseded generation bases are retained and registered in `excluded-sources.json`.

## Style references

Inspected references: `Review/art/03-environment-kit.png`, plus the selected overworld, cave, castle, town, and coast masters under `ArtSource/RemasterExpansion/environment/`. The new prompts specify compact GBA-era pixel clusters, muted palette, upper-left light, orthographic ground plane, and short oblique wall or platform faces. References informed style and palette only. No source pixels were copied.

## Selected atlases and row-major names

| Family | Selected source | Exact 4×4 names, row-major |
|---|---|---|
| Snow and ice | `snow-ice-tiles-4x4-v2.png` | snow-ice-nw, snow-ice-n, snow-ice-ne, snow-field-01; snow-ice-w, snow-ice-center, snow-ice-e, snow-field-02; snow-ice-sw, snow-ice-s, snow-ice-se, frozen-ice-01; frost-plain-01, frost-plain-02, cracked-ice-01, cracked-ice-02 |
| Desert ruins | `desert-ruins-tiles-4x4-v2.png` | ruin-nw, ruin-n, ruin-ne, sandstone-floor-01; ruin-w, ruin-center, ruin-e, sandstone-floor-02; ruin-sw, ruin-s, ruin-se, sand-floor-01; sand-floor-02, cracked-sandstone, ruin-rubble-01, ruin-rubble-02 |
| Ship and dock | `ship-dock-tiles-4x4-v2.png` | dock-nw, dock-n, dock-ne, water-01; dock-w, dock-center, dock-e, water-02; dock-sw, dock-s, dock-se, water-03; deck-planks-01, deck-planks-02, rope-lashed-deck, gangplank |
| Dungeon transitions | `dungeon-transitions-tiles-4x4-v2.png` | wall-nw, wall-n, wall-ne, floor-flagstone-01; wall-w, wall-door-open, wall-e, floor-flagstone-02; wall-sw, wall-s, wall-se, stairs-down; door-closed, door-open, stairs-up, stone-pillar |

The intended transition blocks occupy the upper-left 3×3 of each atlas. The dungeon center cell is an open doorway variant; for a navigable wall-ring assembly, use a floor center instead and place `wall-door-open` only where a doorway belongs. The rest of each family supplies repeat surfaces and/or practical variants.

## Generation and edit prompts

Built-in ImageGen was used for each original atlas and for the cleanup edits. The second snow/ice generation was selected as v1 and then edited to create the selected v2. The original v1 atlas for each family remains unmodified in this folder. Cleanup edits did not eliminate all straight fine seams in the desert, dock, and dungeon art; these remain candidate sources and must pass crop and native-assembly review.

### Snow and ice — selected `snow-ice-tiles-4x4-v2.png`

Generation prompt used for the preserved v1:

```text
Use case: stylized-concept. Make a square opaque 4-by-4 image atlas of sixteen separate small top-down JRPG terrain tiles, each equal square, each tile complete within its own square. No cell borders, no grid lines, no gutters, no labels or text, no outside margins; no artwork spans between cells. This is crisp GBA-era pixel art with compact pixel clusters, restrained cool palette, orthographic ground textures and a subtle upper-left light. Keep each tile distinct enough to identify its named role at 32×32 pixels. Exact row-major cells:
1 snow-ice-nw: corner where pale snowfield curves into dark blue frozen lake at upper-left;
2 snow-ice-n: straight horizontal northern ice shoreline under snow;
3 snow-ice-ne: matching upper-right ice shoreline corner;
4 snow-field-01: seamless pale snow texture.
5 snow-ice-w: western shoreline edge;
6 snow-ice-center: straight transition edge where snow meets ice;
7 snow-ice-e: eastern shoreline edge;
8 snow-field-02: alternate seamless pale snow texture.
9 snow-ice-sw: lower-left ice-shore corner;
10 snow-ice-s: southern shoreline edge;
11 snow-ice-se: lower-right ice-shore corner;
12 frozen-ice-01: repeatable deep blue frozen surface.
13 frost-plain-01: repeatable fine snow texture;
14 frost-plain-02: repeatable snow with sparse icy flecks;
15 cracked-ice-01: repeatable blue ice with a few thin white cracks;
16 cracked-ice-02: alternate cracked blue ice.
The nine shoreline tiles should have a coherent shared geometry: snow is white-blue land, ice is dark cyan-blue ground; the snowy boundary is irregular but the named corner and side orientations are easy to read. Ground plane only; no cliffs, rocks, mountains, trees, footprints, props, characters, buildings, scenic views, shadows, or 3D lighting. No pixel-perfect mechanics or photographed textures; clean large pixel blocks that remain legible when reduced.
```

Selected ImageGen cleanup edit:

```text
Edit this source atlas only to remove the thin straight dark grid lines that mark the 4-by-4 equal-cell boundaries. Preserve every snow, frozen lake, and ice texture and preserve the exact square 4x4 layout, tile positions, and artwork. Fill divider pixels by continuing the adjoining snow/ice material; retain natural irregular snow banks and organic ice cracks. There must be no visible atlas-wide straight lines, drawn frames, borders, labels, or gutters. Do not redesign or move any tile content. Keep the atlas fully opaque and square, edge-to-edge.
```

### Desert ruins — selected `desert-ruins-tiles-4x4-v2.png`

Generation prompt:

```text
Use case: stylized-concept. Make one square opaque 4-column by 4-row atlas of exactly sixteen individual full-bleed 32px-target environment tiles for a top-down JRPG. Equal square cells; no gutters, cell borders, grid lines, labels, text, watermark, or art crossing cell boundaries. Not a map scene or sheet illustration. Art style: crisp rich GBA-era pixel clusters, compact silhouettes readable at 32x32, restrained warm sandstone/tan/ochre and slate, consistent upper-left lighting. Ground plane orthographic overhead; ruin wall edges may have short top-down oblique height faces. Exact row-major contents: row1 [ruin-nw, ruin-n, ruin-ne, sandstone-floor-01]; row2 [ruin-w, ruin-center, ruin-e, sandstone-floor-02]; row3 [ruin-sw, ruin-s, ruin-se, sand-floor-01]; row4 [sand-floor-02, cracked-sandstone, ruin-rubble-01, ruin-rubble-02]. The first nine tiles are a buildable 3×3 raised sandstone ruin platform against sand: distinct matching outer corners, straight sides, repeat center, and lower facing edges; their top surfaces and wall heights align when placed in the named 3×3 order. Row4 cells are full-bleed repeat surfaces or small surface details, each belonging to the same ruin/sand material set. No isolated props, people, symbols, plants, scenery, or modern features. Preserve clean square tile silhouettes; no bevel frames or printed grid.
```

Selected ImageGen cleanup edit:

```text
Edit this generated 4×4 desert ruins tile atlas. Preserve the exact sixteen tile positions, sand and sandstone materials, colors, textures, and 3×3 ruin-platform layout. Remove ONLY the thin straight dark atlas-wide grid/divider lines at the exact equal 4-column and 4-row cell boundaries; fill those pixels by extending the adjacent sand, stone, or shadow texture. Keep natural mortar, block outlines, rock cracks and ruin edges. No grid, cell frames, borders, gutters, labels, text, extra objects, or content crossing cells. Fully opaque square image. This is a source-art cleanup, not a redesign.
```

### Ship and dock — selected `ship-dock-tiles-4x4-v2.png`

Generation prompt:

```text
Use case: stylized-concept. Generate an opaque square production-candidate tile atlas, exact 4×4 equal square cells, sixteen independent full-bleed top-down JRPG ship and dock tiles. No gutters, visible grid, separator lines, frames, labels, text, watermark, or content crossing cell boundaries. Crisp GBA-era pixel art, rich but restrained brown timber, muted blue water, consistent top-left light, tile-scale shapes readable at 32×32. Orthographic overhead ground plane; minimal top-down oblique thickness only at dock edges. Exact row-major: row1 [dock-nw, dock-n, dock-ne, water-01]; row2 [dock-w, dock-center, dock-e, water-02]; row3 [dock-sw, dock-s, dock-se, water-03]; row4 [deck-planks-01, deck-planks-02, rope-lashed-deck, gangplank]. First nine make one coherent 3×3 rectangular wooden dock platform surrounded by blue water: upper corners/edge, side edges, plank-filled center, lower edges/corners; timber edge beams align continuously in the named 3×3 arrangement and the platform interior repeats as planks. Water cells are seamless blue water with slight pixel-wave variation. Last-row surfaces are repeatable practical timber textures; gangplank is a short plank bridge segment over blue water, fully contained in its cell. No people, ships, rigging, scenic illustration, shoreline, objects unrelated to pier construction, perspective horizon, or 3D rendering.
```

Selected ImageGen cleanup edit:

```text
Edit this generated 4×4 ship/dock tile atlas. Preserve the exact sixteen tile positions, coherent wooden dock in the first 3×3, blue water surroundings, timber textures, rope and gangplank. Remove ONLY the thin straight dark atlas-wide grid/divider lines at the exact equal 4-column and 4-row cell boundaries; fill those pixels with continuation of the adjoining wood plank or water pattern. Keep natural plank seams, timber edges, rope, water wave marks and shadows. No grid, cell frames, borders, gutters, labels, text, extra objects, or content crossing cells. Fully opaque square image. This is a source-art cleanup, not a redesign.
```

### Dungeon transitions — selected `dungeon-transitions-tiles-4x4-v2.png`

Generation prompt:

```text
Use case: stylized-concept. Create an opaque square 4×4 atlas of sixteen distinct complete top-down JRPG dungeon environment tiles, each equal square and filling its cell. No gutters, cell outlines, separator/grid lines, borders, text, labels, watermark or art crossing boundaries. Style: crisp clustered GBA pixel art, muted cool gray/blue stone, restrained warm top-left highlights; stone walls may use short orthographic top-down oblique height faces, floor remains top-down. Exact row-major cells: row1 [wall-nw, wall-n, wall-ne, floor-flagstone-01]; row2 [wall-w, wall-door-open, wall-e, floor-flagstone-02]; row3 [wall-sw, wall-s, wall-se, stairs-down]; row4 [door-closed, door-open, stairs-up, stone-pillar]. First nine form a buildable 3×3 raised stone wall/doorway patch around an open central doorway; named corners and side faces match in the 3×3 arrangement, leaving a clear floor opening in the center. Outer edge stones transition cleanly into surrounding flagstone floor; no detached arch. Row4 has a closed door and matching open door shown as top-down/oblique doorway fittings, ascending/descending short stone stairs, and a single square-footprint stone pillar, all isolated within their tiles on compatible dungeon stone. Practical reusable terrain, not a scene or prop board.
```

Selected ImageGen cleanup edit:

```text
Edit this generated 4×4 dungeon tile atlas. Preserve the exact tile positions and all stone wall, doorway, flagstone floor, stair and pillar artwork. Remove ONLY the thin straight dark atlas-wide grid/divider lines at the exact equal 4-column and 4-row cell boundaries; fill them with continuation of the adjacent stone or floor texture. Keep natural masonry joints, wall outlines, doorway silhouettes, stair edges and pillar shading. No grid, cell frames, borders, gutters, labels, text, new objects, or movement of tile content. Fully opaque square image. This is a source-art cleanup, not a redesign.
```

## Proof and acceptance boundary

Pipeline proofs use actual exported 32×32 cells with no edge painting. Reviewed `Review/remaster-expansion/environment-extras-overview.png` and native/4× adjacency proofs on 2026-10-24:

| Family | Native proof finding |
|---|---|
| Snow and ice | The outer lake edge against `snow-field-01` reads as a coherent frozen lake. The `snow-ice-center` cell creates a small white snow island in the ice center. An alternate assembly with actual `frozen-ice-01` removes the island but introduces a rectangular highlight boundary around the center tile (`Review/remaster-expansion/snow-center-comparison.png`, `snow-ice-frozen-center-test-4x.png`). Neither center choice is seam-free; keep the master and assembly as review candidates. |
| Desert ruins | The 3×3 raised sandstone patch reads as a bounded platform against sand. Some dark block joints and edge shading look strong at 32px, but joins remain legible as masonry and shadow. |
| Ship and dock | The dock joins into a clear pier on water. Repeated plank joints are heavy and make the deck look grid-like at native size; exterior water reads continuously. |
| Dungeon transitions | The 3×3 wall ring joins against flagstone and has a navigable `floor-flagstone-01` center. The open doorway is exported as a separate variant and is not used as a floating room-center tile. Wall shadows and block seams are prominent but the structure is readable. |

These are visual candidate findings, not an approval or a seamlessness guarantee. No runtime integration or playtest is claimed.
