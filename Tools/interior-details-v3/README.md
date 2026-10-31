# Interior Details V3 — reference review candidates

Assets only. Nine native PNGs represent seven primary components: three complete patterned rugs, two cream/timber wall styles (each at32x64 and64x128 detail sizes), and two golden wood counters (128x32 straight and128x64 corner). V1 and V2 remain unchanged. No game code, scenes, collision, door traversal, build, integration or release is included.

Rug footprints preserve reference forms: Hilda128x160, Scott96x128, Tobul160x96. Each component preserves a complete authored pattern rather than redistributing ornament across32px autotile cells. Half-size PNGs are review previews, not extra production assets. No rug autotile or nine-slice contract is claimed.

Generated masters are preserved byte-for-byte in ArtSource/InteriorDetailsV3, with generation prompts and hashes. The manifest records each declared source slot, threshold-alpha bounding crop, nearest-neighbor aspect-fit placement and output hash. Cutouts use binary alpha at128 threshold and zero invisible RGB; opaque walls retain full opacity. Wall connector bands copy two-dimensional source strips at minimal native depth, preserving the body pattern. Only same-style wall repeats are contracted. Native32x64 wall variants use32PPU and64x128 detail alternatives use64PPU to retain the same logical footprint; rugs/counters use32PPU. Counter pieces are complete detail components; furniture/counter seam certification is not claimed.

Native output and3x nearest-neighbor previews are under Review/interior-details-v3. Same-footprint V2/V3 rug boards use unchanged, hashed V2 tile dependencies. Reference/V3 boards link actual attributed FFII Pixel Remaster captures; reference pixels are not production artwork. Native detail, palette, motif density and remaining differences require visual review. These candidates do not claim retail1:1 parity.

Run from the art repository root:

```powershell
node Tools/interior-details-v3/export.cjs
node Tools/interior-details-v3/verify.cjs
```

Requires Node.js and Sharp (`npm install` inside the tools directory on a new machine). Source/output paths are relative to the art repository root. Staged comparisons can locate unchanged V2 dependencies using `ART_DEPENDENCY_ROOT`; this workstation falls back to C:/repos/AI-Art-FF2. After copying into that repository, relative dependency paths resolve directly.

The independent verifier reads emitted PNGs and checks source/prompt/config/dependency hashes, expected family inventory, source crop bounds, aspect-fit placement, native dimensions, opaque/binary alpha, zero invisible RGB, point/declared-PPU metadata, declared horizontal wall repeat bands and deliberate seam-mutation rejection. These checks do not establish decorative fidelity, Unity import behavior or runtime readiness.
