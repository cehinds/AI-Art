# Procedural terrain references and implementation decisions

Researched 2026-10-25 using developer documentation and original technical sources. These are system-design references; no external game textures or code were imported.

## References

| Reference | Relevant behavior | Application to this library |
| --- | --- | --- |
| [Factorio: tile transition collisions, FFF-344](https://www.factorio.com/blog/post/fff-344) | Extra transition sprites soften material boundaries; visual shape and collision need separate treatment. | Record the two terrain materials and transition type. Keep appearance tags separate from walkability. Existing opaque tiles are not falsely labeled as overlays. |
| [Factorio: concrete rendering, FFF-214](https://www.factorio.com/blog/post/fff-214) | Material and detail layers, plus differently sized detail sprites, help reduce obvious repetition. | Group compatible art variants and select them deterministically. Larger detail layers are a future art requirement, not implemented by relabeling current PNGs. |
| [Factorio: terrain correction history, FFF-346](https://www.factorio.com/blog/post/fff-346) | Terrain generation had to respect shapes the available artwork could represent; later transitions reduced those restrictions. | Report unsupported masks instead of silently substituting a tile with the wrong boundary. Changing terrain layout to accommodate art must be explicit. |
| [RPG Maker MZ: official asset standards](https://rpgmakerofficial.com/product/MZ_help-en/01_11_01.html#p02) | Autotiles use dedicated corner and neighboring-cell patterns, with separate ground, building, wall and animated-water layouts. | Distinguish area fills, convex/concave corners, buildings and water animation. Existing nine-patch sets do not become complete autotile libraries just by adding tags. |
| [Tiled: terrain sets](https://doc.mapeditor.org/en/stable/manual/terrain/) | Two-material corner and edge sets each have 16 patterns. Mixed sets combine both; reduced 47-pattern blob sets are also supported. Its pattern view exposes missing combinations. | Keep corner masks separate from route opening masks; publish available and missing patterns. Material names alone do not establish matching geometry. |
| [Godot: terrain connect versus path mode](https://docs.godotengine.org/en/4.5/tutorials/2d/using_tilemaps.html#handling-tile-connections-automatically-using-terrains) | Connect follows neighboring terrain; Path follows the painted stroke and can keep adjacent roads separate. | A route graph declares actual links. Two nearby paths should not automatically form a junction. Filled regions instead follow area topology. |
| [Unity: Rule Tile](https://docs.unity3d.com/Packages/com.unity.2d.tilemap.extras@3.0/manual/RuleTile.html) | Rules examine neighboring cells and may select fixed, random or animated outputs. Rotation and mirroring are explicit options. | Separate shape selection from variant selection. Preserve authored orientations because pixel-art lighting may make arbitrary rotation inappropriate. Unity RuleTile integration is not part of this art-repository change. |
| [BorisTheBrave: tileset roundup](https://www.boristhebrave.com/2013/07/14/tileset-roundup/) | Explains corner-based marching squares, the 47 solid blob patterns, and quadrant-based subtile construction used by RPG Maker VX artists. | Use an explicit topology model and count missing patterns against that model. Do not describe a corner-based nine-patch kit as a complete 47-pattern blob set. |
| [Original WaveFunctionCollapse project](https://github.com/mxgmn/WaveFunctionCollapse) | Propagates local pattern constraints and can encounter contradictions. The project links games including Bad North and Caves of Qud. | Local compatibility constraints can support a future solver, but do not prove a connected route or a playable map. This implementation does not claim to reproduce those games' generators or implement full WFC. |

## Selected approach

1. Describe the intended surface and use: grass, snow, soil path, water, roof, wall and other observed materials.
2. Describe geometry independently: fill, edge, outer/inner corner, route end, straight, bend, junction, crossing or feature.
3. Select the required corner or route mask before selecting a visual variant. A nine-patch outer corner is not a one-cell road bend; a three-cell-wide area cap is not a single-tile road end.
4. Enforce existing side-profile, family, layer, world-scale and animation guards. Semantic tags do not override a blocked tile.
5. Use deterministic choices only among tiles with the same required topology. Equal weights are the initial authoring policy, not a claim about reference-game probabilities.
6. Report missing patterns with their terrain, family and mask. Do not fill a missing end or junction using unrelated art.
7. Inspect the actual exported pixels in generated layouts. Metadata establishes logical continuity; repeated textures and mismatched boundary pixels remain art work.

## What remains art work

The present library includes partial nine-patch terrain sets and a river network set, rather than a complete route and blob set for every biome. Smooth arbitrary paths require appropriately drawn ends, bends, T-junctions, crossings and isolated pieces. Irregular fields also need their missing concave and diagonal combinations. A coverage report should identify these gaps before generation; tags cannot supply absent artwork.

For the implemented schema, selector APIs, supported examples and current measured coverage, see [ProceduralTiles.md](ProceduralTiles.md). The browser review exposes the same catalog and selection rules.
