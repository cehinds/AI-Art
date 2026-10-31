# Terrain Components V3

Assets only. Fifty-five candidates: four native 32px ground materials; sixteen dirt-road masks; sixteen cobble-road masks; sixteen river masks; a 48x64 city conifer; a 64x64 city broadleaf; and a 32px overworld forest field. No game code, scenes, pathfinding, builds, integration or release changes.

Road and river masks use N1, E2, S4, W8. Each family includes an isolated pad/pond, four ends, four turns, two straights, four T junctions and a cross. Ports, directional end/corner tags, layer and collision intent are declared in the manifest. Collision descriptions are semantic intent, not generated runtime geometry.

Generated masters are preserved byte-for-byte, with prompt records and hashes. Ground crops are nearest-neighbor normalized with reflected four-pixel source bands, preserving two-dimensional interiors. The quieter grass uses a 256px source crop; the first 627px prototype is preserved in Review/iterations with a hash receipt. Shop flagstone remains unchanged from its first shared export. Transparent network cells retain the primary connected authored shape; tiny detached alpha artifacts below 0.5% of the primary component are excluded and counted per cell. Raw masters remain intact. Source alpha and original contour pixels are composited over the common grass. Cobble roads substitute shared cobble only inside a one-pixel-eroded source road mask, retaining the original transition contour. No artwork is painted in code.

Canonical road/river connector bands are four-pixel-deep two-dimensional strips from authored straight cells. Complete RGBA profiles are tested for every independently mask-derived compatible pair, including shared grass sides across different network families. The source fields and contours remain visible in native winding/turn/junction proofs. Whole cobble plazas and narrow cobble paths are separate material roles; plaza-entry adapters are not supplied.

Measured road spans are 10-11 native pixels. River spans including shore are 9-10 pixels; measured dark-blue core widths are 5-7 vertically and 7-8 horizontally, rather than the requested 8-10 throughout. Source channel width varies slightly inside cells. The verifier reports per-depth measurements rather than inferring width from a prompt.

The overworld forest preserves an authored 627x627 source crop at (416,416), about three crowns by two rows, normalized to 32px over shared grass. The first full-source prototype is retained in Review/iterations; its tiny noisy crowns and horizontal grass lanes were rejected. It has no destructive grass frame and no exact forest-to-forest or forest-to-grass join certification. Boundary differences are reported diagnostically. City trees remain separate transparent silhouettes, distinct from the forest glyphs. The V1 bridge is an unchanged, hashed visual overlay dependency; endpoint joins, deck traversal and collision are not certified.

The independent verifier checks 55 assets, 1,634 compatible mask-derived pairs, eight floor repeats, actual proof-map joins, all four pixels inward from each shared edge, deliberate mutation rejection, hashes, alpha, dimensions and point / 32 PPU metadata. Ground is opaque; city-tree alpha is binary at 128 threshold with invisible RGB cleared. Mechanical agreement is separate from visual contour quality, source-style fidelity, Unity import or runtime readiness.

Review/terrain-components-v3/index.html links native and 3x floor, winding road/river, junction, forest, city-tree and bridge proofs. Original FFII Pixel Remaster screenshots belong only in attributed comparison references; production PNGs derive from generated masters. Dirt roads are optional candidate routes, not a claim of the original retail map layout.

From the art repository root:

```powershell
node Tools/terrain-components-v3/export.cjs
node Tools/terrain-components-v3/verify.cjs
```

Requires Node.js and Sharp (`npm install` in this tools directory). Paths are relative to the art repository. In staging, `ART_DEPENDENCY_ROOT` can locate the unchanged V1 bridge; this workstation falls back to C:/repos/AI-Art-FF2. The final verifier requires the generation-prompt record. `--preflight` writes a separately labelled partial receipt while that record is pending.
