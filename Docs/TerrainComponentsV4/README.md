# Terrain Components V4 — palette and density review

Assets only: 22 production PNGs. One bright field-grass material at 64x64, four registered 32x32 grass phases, one 32x32 woodland ground material, and sixteen transparent 32x32 cardinal river overlays. All use 32 PPU. No roads, trees, game code, scenes, builds, integration or release changes.

Grass uses the selected upper-left 627x627 crop of the generated master, normalized to 64px so the coarser 2px grain survives. Four phase crops retain the 64px material arrangement on a 32px logical grid. Reflected four-pixel source strips register phase and wrap boundaries. Earlier fine-grain material and previews remain in review iterations. The selected field material mean RGB is (105.07,178.80,54.61), compared with measured reference (103,169,59); no color recoloring was performed.

The canonical river viewport uses a different woodland biome ground. It comes from our generated refined scene, normalized to 130x270, then a clean nonriver/nontree crop at (0,95,32,32), with reflected four-pixel source edges. This is a production material derivative; the complete generated scene remains a separate review-only reconstruction. Original retail screenshot pixels never enter production art.

River width is now 19–21px of dark-blue core across the tested connector rows, within the 18–22px reference target. The first narrow atlas is preserved but rejected. In the wide master, square source crops of the pool (420px), straight (350px) and bend (350px) preserve the authored geometry at the desired scale. N ends combine the straight top half with the pool bottom half; T junctions combine the straight left half and authored bend quarters; crosses use rotated authored bend quadrants. Rotations yield all sixteen N1/E2/S4/W8 masks. Canonical four-pixel-deep connector strips retain two-dimensional source texture. No water or bank pixels are painted in code.

Five exact terrain-generation records, their preserved masters, the PNG/SVG geometry design guide and prompt record are hash registered. Prompt text and generatedFile entries remain unchanged from the parent record; selected/rejected/review-only status and portable mappings are explicit. Geometry guides are generation inputs, not production artwork. Full source crops, fragment operations and rotations are in the manifest/config.

Natural tile-assembled proofs are 130x205 and 130x270, matching the reference view sizes. The secondary junction grid is a seam fixture, not the primary visual comparison. Forest and bridge source dependencies are preserved and hashed; they are unchanged review context, not newly reference-matched production assets. The separate generated scene reconstruction is clearly labelled and never presented as tile assembled.

Independent verification checks 22 assets, eight grass phase pairings, two grass-material wraps, two woodland repeats, 290 mask-derived river pairings, 1,196 actual layered proof joins, full RGBA four pixels inward, 19–21px measured core spans, deliberate mutation rejection, native sizes, alpha, density, metadata and source/prompt/config/output/dependency hashes.

Remaining visual differences are explicit: woodland repetition forms visible rectangles; water texture is more striped and regular than the reference; some bends/junction interiors reveal source-fragment stitching. Static connector agreement does not certify retail 1:1 fidelity, animation, collision, bridge traversal, Unity import or runtime behavior.

From the art repository root:

```powershell
node Tools/terrain-components-v4/export.cjs
node Tools/terrain-components-v4/verify.cjs
```

Requires Node.js and Sharp (`npm install` inside the tools directory). Source/output paths are relative to the art repository. Staged context proofs can locate unchanged V1/V3 dependencies through `ART_DEPENDENCY_ROOT`; this workstation falls back to C:/repos/AI-Art-FF2. Review/terrain-components-v4/index.html links natural proofs, the separate reconstruction and the verification receipt.
