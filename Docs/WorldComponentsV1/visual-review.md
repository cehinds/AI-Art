# World Components V1 — native assembly review

Asset-only candidates, inspected at native/nearest-neighbor scale on 2026-10-30. No game integration, runtime collision, Unity import or WFC acceptance is claimed.

## Coast and river first pass

- The [coast master](../../ArtSource/WorldComponentsV1/coast-island-master.png) is a single continuous island: grass center, water outside, thin pale bank/foam boundary. The nine source positions are NW/N/NE, W/grass/E, SW/S/SE. A shared group resize produces the 96×96 native atlas, then nine 32×32 cells.
- The [river master](../../ArtSource/WorldComponentsV1/river-mask-master.png) contains sixteen row-major masks 0–15, with N=1/E=2/S=4/W=8. The shared group resize produces a 128×128 native atlas before slicing. All sixteen declared topologies are recognizable: isolated pool, four ends, two straights, four bends, four tees and a cross.
- The narrow coast, cobalt water and restrained pale bank match the inspected PR reference's component roles more closely than the earlier broad-beach coast family. This is a visual direction judgment, not a pixel-exact reproduction claim.

## Visible limitations

- [Extended island](../../Review/world-components-v1/assemblies/coast-extended-island.png): repeated edge cells repeat coastline bulges. Grass and water texture phase changes remain visible at some cell boundaries. The nine-part atlas does not supply concave land corners or one-cell islands. A separate open-ocean candidate is cropped from the master's unobstructed outer-water corner; [its repeat proof](../../Review/world-components-v1/assemblies/ocean-repeat.png) shows the actual wave phase.
- [River loop](../../Review/world-components-v1/assemblies/river-loop.png): channel/foam width changes at joins, particularly lower-right bend/straight connections. The coast atlas grass used inside the loop has a visibly different color/texture block from the river atlas grass. Cross-family ground compatibility is unapproved.
- [River cross and ends](../../Review/world-components-v1/assemblies/river-cross-branches.png): flow is readable, but the end-to-cross openings narrow or widen at their join; bank positions are not consistently registered to a common exact pixel profile.
- [Repeated vertical channel](../../Review/world-components-v1/assemblies/river-northsouth-repeat.png) and [horizontal channel](../../Review/world-components-v1/assemblies/river-eastwest-repeat.png) expose the actual bank and texture registration rather than hiding joins behind independent cell fitting.

The [boundary audit](../../Review/world-components-v1/adjacency-audit.json) records opaque edge sample counts and RGB deltas. It has no arbitrary pass threshold: numerical edge similarity cannot establish matching river widths, bank shapes or visual continuity. Port strings in the manifest describe intended terrain profiles and flow, not proven seamless adjacency.

## Bridge, mountain and cliff review

- [Stone bridge candidates](../../Review/world-components-v1/assemblies/stone-bridge-candidates.png): pale gray stone construction is clear in both orientations. The two named abutment candidates still resemble complete short spans. Their repeatable attachment to another span/bank is unapproved; the manifest explicitly records them as variants rather than certified join pieces.
- [Cutout alpha checker](../../Review/world-components-v1/cutout-alpha-checker.png): the eight 64×64 bridge/mountain objects have transparent exterior pixels and registered bottom-center footprints. Colored raw RGB outside alpha=0 does not paint the checker. Foreground alpha is preserved, including partly transparent edge pixels; these are not falsely described as binary-alpha cutouts.
- [Mountain variants](../../Review/world-components-v1/assemblies/mountain-cluster-variants.png): four readable ochre/gold pointed rock clusters with dark outlines and distinct silhouettes. They are isolated overlay objects, not a tested connected ridge autotile set. Width is normalized to at most 60px; differing heights remain visible rather than being stretched to equal shapes.
- [Cliff cardinal inventory](../../Review/world-components-v1/assemblies/cliff-cardinal-inventory.png): S/N/E/W have natural warm earth scarp faces and tan rock rims, not masonry walls. High side is north/south/west/east respectively. [South](../../Review/world-components-v1/assemblies/cliff-south-repeat.png), [north](../../Review/world-components-v1/assemblies/cliff-north-repeat.png), [east](../../Review/world-components-v1/assemblies/cliff-east-repeat.png), and [west](../../Review/world-components-v1/assemblies/cliff-west-repeat.png) repeats preserve their cardinal role, with repeated texture/edge phase still visible. Corners, stair cuts and cross-family grass-color matching are not supplied or certified.

## Remaining acceptance boundaries

Decide whether further generations are needed for exact river port profiles, consistent ground palettes, concave coast/cliff corners and modular bridge joins before claiming compatibility. No further generation, game integration or publication is implied by this candidate delivery. Source/metadata verification passes for **38 assets / five preserved masters / six definitions / 14 assembly proofs**; that is reproducibility evidence, not a seamlessness verdict.

Full inventory and preserved-source hashes are in the [manifest](../../Assets/Art/Production/WorldComponentsV1/manifest.json). Start the [review gallery](../../Review/world-components-v1/index.html) for native contacts and every assembly.
