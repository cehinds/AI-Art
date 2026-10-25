# Procedural tile side tags

Every `kind: tile` entry in the Batch01, Campaign and RemasterExpansion manifests appears exactly once in [the sidecar](../Assets/Art/Production/procedural-tiles.json). Animated tile frames are individual entries with a shared clip identity and explicit phase. Campaign currently contributes no tile entries; its world icons remain sprites.

Run from the repository root:

```powershell
node Tools/procedural-tiles/build.cjs
node --test Tools/procedural-tiles/test.cjs Tools/procedural-tiles/terrain.test.cjs
node Tools/procedural-tiles/check.cjs remaster:world-tiles.river-expansion02.river-ns south remaster:world-tiles.river-expansion02.river-ns
```

Open [the local review](../Review/procedural-tiles/index.html) to inspect coverage, side tags and checked assembly evidence. Compiler inputs include manifest hashes; tests reject stale coverage after a manifest changes. The compiler writes an additive JSON sidecar and review files. It never edits existing PNGs, metadata or source manifests.

## Semantic terrain intent: schema 2

All 393 tiles also carry `terrain.primary`, searchable aliases and material tags, biome tags, usage, shape, topology, transition endpoints, and deterministic variant groups. These are additive classifications: they never broaden the existing family/layer/world-scale/socket guards or enable a blocked tile.

`path`, `dirt-road` and `soil-path` identify the authored earth-path area kit. `grass` includes meadow turf, and `snow` includes compacted tundra snow. Domain material labels retain distinctions such as meadow turf versus compacted soil, forest-floor moss versus meadow, or snow versus frozen tundra earth. Blue frozen earth is **not** tagged as water. Doors, windows and other features retain separate variant groups and state tags.

Topology and image selection are separate:

- `area-corner16` uses four terrain vertices, with bits NW=1, NE=2, SE=4, SW=8. This is a 16-case corner model, **not** a complete 47-blob neighborhood set. Vertex mask 5 and mask 10 are different diagonal cases. Missing cases fail explicitly.
- `route4` uses declared graph connections, with bits N=1, E=2, S=4, W=8. Adjacent parallel routes do not connect unless the graph declares an edge. A one-port end records both `opening` and the opposite sealed `cap` direction.
- `fill` selects a homogeneous material role. `feature` does not imply connectivity or navigation.

Batch01 `path-nw` is an **area outer corner**, not a one-cell road bend. The library does not supply a complete one-cell road-network kit: road endpoints, T-junctions and cross-junctions cannot be invented from its ninepatch names. The river kit has actual network ports, but only a north-opening source/end; other end directions and an isolated network pool remain gaps.

`Tools/procedural-tiles/terrain.cjs` exports browser-safe `select`, `fieldIntent`, `routeGraph`, `generate`, `validate`, `coverage` and `transitionSupport`. It imports the existing matcher. Example:

```javascript
const terrain = require('./Tools/procedural-tiles/terrain.cjs');
const result = terrain.generate(catalog, {
  kind: 'demo', preset: 'path', seed: 20261025
});
// result: supported 9x7 wide path area with explicit grass exterior,
// 63 actual tile IDs and 110 checked adjacent pairs.
```

The `grass` and `snow` presets produce separate homogeneous fields using actual existing variants. Explicit area intents accept a Boolean vertex grid; each cell's four vertices determine its mask. Explicit route intents accept path segments and optional exterior fill. Unsupported masks return `unsupported-topology` with `missingRequests` and **no fallback placements**. Images are selected only after the requested topology is known; a seeded weighted choice never substitutes a corner for a fill.

[Terrain coverage](../Review/procedural-tiles/terrain-coverage.json) lists supported and missing masks/roles by terrain and family, plus authored transition pairs. Grass/soil and snow/frozen-earth pairs exist in specific kits. Their existence does not imply grass/snow transitions or arbitrary biome mixing. `transitionSupport(catalog, {from:'grass', to:'snow'})` reports the missing pair; generation cannot silently use unrelated art.

The complete build reproduces three actual PNG proofs: [wide path](../Review/procedural-tiles/terrain-path.png), [grass field](../Review/procedural-tiles/terrain-grass.png) and [snow field](../Review/procedural-tiles/terrain-snow.png). Each has 63 cells and 110 logically compatible neighboring pairs. Native visual review found visible periodic texture and row seams in the original grass/snow artwork. Variant groups mean **the same topology only**, with `visualCompatibility: unreviewed`; they do not certify visually smooth or seamless mixing. No pixels were edited for this semantic pass.

See [the reference research](ProceduralTerrainReferences.md) for the distinction between corner, edge and blob autotiles, terrain-connect versus explicit path networks, and source-backed design precedents. Those references informed the model; no external artwork was copied.

## What a match means

A successful check means **logical edge compatibility**, with no guarantee of seamless pixels, compatible lighting, source-game accuracy, collision, traversal or runtime behavior. Every tile retains `visualSeamApproved: false`. A family may have useful logical topology while still showing texture phase offsets between real exported pixels.

The matcher requires all of the following:

- Both tile entries and both selected sides are `modeled`.
- The same layer and world size (`width / PPU`, `height / PPU`). A 32px tile at 32 PPU and a 64px tile at 64 PPU both occupy one world unit; native resolution alone does not block them.
- Exactly equal ordered material profiles on opposite sides.
- The same family, unless an explicit cross-family policy allows the exact layer and every profile material. The shipped exception permits only uniform grass edges between Batch01 path and plain-ground tiles from their shared terrain atlas. Roofs and building ground remain separate families and layers.
- When both tiles animate, equal phase index, frame count, frame duration and total cycle duration. Use a shared animation clock; matching labels cannot prevent two independent clocks drifting apart.

Blocked tiles still carry all four observed material profiles, corner observations, a feature description where relevant and a reason for review. Their observed tags never grant connectability. Doors, stairs, furniture and other feature tiles retain `traversal: unknown`; a visible open doorway is not navigation approval.

## Profile ordering and corners

North and south profiles run west to east. East and west profiles run north to south. Opposite sides use the same world-coordinate order, so the checker compares them directly without reversing either profile. Five canonical stations are `[0, .25, .5, .75, 1]`. These encode semantic material regions, not sampled pixel colors or measured seam coordinates.

A uniform edge repeats one material five times. A transition edge records `[start, start, boundary, end, end]`. A river opening records `[grass, river-bank, river-water, river-bank, grass]`; its corners remain grass. River topology can therefore distinguish a closed bank from an open channel while retaining matching land endpoints.

Explicit corner materials supplement the edge endpoints:

| Role | NW | NE | SE | SW |
| --- | --- | --- | --- | --- |
| Outer NW | outside | outside | inside | outside |
| Inner NW bite | outside | inside | inside | inside |

The other orientations follow the authored roles in `core.cjs`. Convex and concave corners have different endpoint profiles; the names are never treated as interchangeable. Tiles are used in their authored orientation. No implicit rotation or mirroring is allowed, because lighting, features and preauthored corner roles may change.

## Evidence and conservative classifications

The rules are explicit per kit. Legacy classifications use selected source descriptors, native contacts and existing adjacency assemblies. They distinguish roof eaves from ground, carpet binding from unspecified room floor, rock ledge tops from cave floors, surf from sand, and dock beams from water. Exceptional pieces retain their actual meaning: coast `shore-center` is a small island with water at its outer edges; the dungeon's `wall-door-open` is a doorway, not an ordinary center wall fill.

Some mountain, feature, waterfall and mixed rubble boundaries remain blocked despite observed material tags. Their unresolved elevation, footprint, direction or transitions require authored review. Coverage reports enumerate every modeled and blocked ID rather than treating missing data as a match.

The original `inner-sw` and `inner-se` candidates in both Expansion04 building kits are retained but blocked with `reviewReason: superseded-corner-orientation`: native courtyard inspection found their outside bites reaching incorrect edges. Stone-building `inner-se-v2` is also blocked: its native 64px PNG still places grass at the top/right edges. Its latest replacement target is `inner-se-v3`; both rejected stone-SE versions link there. Other corrected v2 corners retain their reviewed orientations. Observed mixed profiles never claim the rejected candidates have their intended geometry. A replacement requires inspection of its actual native PNG before acceptance.

The seeded river demo uses actual exported PNGs and checks every adjacent pair with the same matcher. A successful demonstration validates its declared logical arrangement; it does not establish universal seamlessness. Review the actual native assembly before shipping.

## Extending the library

Add explicit kit materials and orientation rules to `build.cjs` or `legacy.cjs`, then rebuild and run tests. New building kits use their declared outer/edge/center/inner roles, with grass outside, cream-wall/flagstone building ground or timber-edge/blue-slate roof. Source pixel geometry and lighting still require visual review. Do not add a permissive fallback based only on a name, and do not remove blocked entries to make coverage appear complete.

For code consumers, `require('./Tools/procedural-tiles/core.cjs').check(tileA, direction, tileB, catalog.policy)` returns `{ match, reason }`. Successful results additionally contain `visualSeamGuaranteed: false`. The browser review embeds this same pure matcher instead of maintaining a second compatibility implementation.
