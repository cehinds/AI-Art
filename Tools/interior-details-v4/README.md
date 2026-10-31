# Interior Details V4 — five whole-component candidates

Assets only. Three complete rugs and two authored wall components refine reference-specific patterns, palettes and proportions. No floors, counters, game code, scenes, builds, integration or release changes. V1, V2 and V3 remain untouched.

Native sizes: Hilda rug 128x160, Scott rug 96x128 and Tobul rug 160x96, all 32 PPU. Hilda dark-timber wall 64x128 and Scott alternating-bay strip 128x64 both use 64 PPU, giving logical footprints of 32x64 and 64x32 pixels respectively at 32 PPU. Scott is one wide authored strip with three main bays plus narrow plaster inserts (six cream regions), not an assembly of equal-width repeated bays. The initial strip is selected; the simplified three-bay edit is preserved as rejected.

Five selected masters and four preserved iteration masters are preserved byte-for-byte: nine PNGs plus the verbatim generation-prompt record. The manifest records source hashes, source slots, alpha-bounding crops, native aspect-fit placements, density, logical footprints and output hashes. Rug alpha uses a 128 threshold with invisible RGB cleared; complete decorative patterns use nearest-neighbor scaling. Walls remain opaque as authored. No canonical edge repair, motif reconstruction or pixel painting is applied.

Native / 3x previews and equal-display-scale V3 / V4 boards are in Review/interior-details-v4. V3 PNGs remain unchanged and serve only as hashed comparison dependencies. Original FFII Pixel Remaster screenshot crops appear only on attributed comparison boards and are never production PNG pixels.

There is no new repeat, seamlessness, carpet-autotile or nine-slice contract. Mechanical checks cover dimensions, density, logical footprints, hashes, source registration, aspect, alpha and import metadata. Decorative fidelity remains a visual review decision. No Unity Editor import, runtime behavior, collision, door traversal or retail 1:1 validation is claimed.

From the art repository root:

```powershell
node Tools/interior-details-v4/export.cjs
node Tools/interior-details-v4/verify.cjs
```

Requires Node.js and Sharp (`npm install` inside the tools directory). Production and source paths are relative to the art repository root. Staged before comparisons can read V3 via `ART_DEPENDENCY_ROOT`; the workstation fallback is C:/repos/AI-Art-FF2. After copying into that repository, relative dependencies resolve directly.
