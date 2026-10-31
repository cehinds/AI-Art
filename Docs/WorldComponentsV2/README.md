# World Components V2 assembly

Assets-only candidate pack. No Unity project, game code, build, integration, or release change.

Run from the art repository root:

```powershell
node Tools/world-components-v2/export.cjs
node Tools/world-components-v2/verify.cjs
```

Requires Node.js and Sharp (`npm install` inside this tools directory on a new machine). The exporter resolves all art paths relative to the repository containing `Tools/`; the optional installed Codex Sharp fallback supports this workstation.

68 native 32px opaque PNGs: 47 land-center blob coast masks, ocean, 16 four-cardinal river masks including isolated pond at mask0, and four directional river mouths. Coast bits: N1 E2 S4 W8 NE16 SE32 SW64 NW128. Diagonals only count with both adjacent cardinals. River bits: N1 E2 S4 W8. A mouth's name is its ocean-facing side; its opposite side connects to a river.

Generated art is preserved byte-for-byte in ArtSource/WorldComponentsV2. Source-layer operations: declared crops, nearest-neighbor resize, quadrant reflections/assembly, common grass substitution for source grass only, and four-pixel canonical connector bands sampled from two-dimensional source strips. No synthetic painted color artwork. River authored curves, endcaps and pool come from the separate generated 4x4 master. The initial thin bank master and wrong-side cyan master remain preserved and marked superseded in generation-prompts.json.

The manifest records source hashes, prompt record hash, source crop rectangles, native asset hashes, tags, masks, corner roles, ports and source registration. PNG metadata GUIDs derive deterministically from each V2 asset ID. V1 is untouched.

Independent verifier derives coast compatibility from every possible 4x3 world occupancy patch (4096), rather than trusting port labels. It tests 392 distinct coast/ocean pairs and 256 river pairs with exact complete RGBA equality at all four pixels inward from each shared edge. It checks another700 joins in actual coast, river and four-direction mouth proofs, preserved source hashes, alpha, dimensions and an in-memory deliberately damaged seam rejection. It reads the emitted PNGs and does not invoke the exporter. Mechanical PASS is separate from visual acceptance.

Review/world-components-v2/index.html shows the inventory and native/3x proofs. River connector blue cores measure about5-7px in the selected source strip, with cream banks1-2px and variable cyan fringe; the requested12px core was not achieved by generation. Repeating grass/water material and bold pale outlines are visible at high enlargement. These are structurally complete candidates, not a claim of FFII retail-quality visual parity, runtime behavior, collision, or game readiness.
