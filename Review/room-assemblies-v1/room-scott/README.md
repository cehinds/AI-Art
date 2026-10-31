# Existing-PNG room assembly

`comparison.png` shows the actual locked reference crop beside a room mechanically composed from the approved component PNGs listed in `layout.json`. It is an asset compatibility/layout proof, not a newly generated reference reconstruction or a retail-match claim. See the visible board captions and `assembly.json` caveats for specific gaps.

`floor.png`, `wall.png`, `rug.png`, `furniture.png`, and `npc.png` are separate transparent layers. Alpha compositing them in that order reproduces `composite.png` exactly. The local `inputs/` tree contains byte-identical snapshots of only the individual approved PNGs used, with original source paths and SHA256 in `layout.json`. No complete room image was used as an assembly input.

`reference-original.*` and `reference.png` are reference-only comparison evidence. They are never read by the room compositing path. The source URL, original hash, exact crop and crop hash are recorded in the manifest; no license transfer is asserted.

Rebuild from any working directory:

```powershell
& 'C:\Program Files\nodejs\node.exe' 'C:\repos\AI-Remake-FF2\AssetWork\RoomAssemblyReviewV1\room-scott\build.cjs'
```

Requires Node.js20+ and Sharp0.35.5. This workstation's Codex runtime Sharp fallback is recorded in the script. To run elsewhere, `npm install` in this room directory installs the declared dependency. All inputs are then local; the original Art repository is optional. For initial capture only, pass `--art-root <path-to-Assets/Art/Production>`. If the Art source exists alongside local copies, the builder checks that its bytes still match. A missing original library does not prevent rebuilding.

`assembly.json` is the editable list of source PNG operations. The builder uses only crop, alpha-bounds selection, nearest-neighbor resize, optional right-angle rotation, texture repetition, canvas clipping, and compositing. It does not paint, recolor, generate, or reconstruct hidden artwork. `layout.json` expands every placement with source hash, source crop, rotation, scale, requested placement and final viewport clipping.

`verification.json` records equal reference/candidate dimensions, source hash checks, and exact reconstruction from the five delivered PNG layers. It does not establish gameplay or retail fidelity. No runtime integration, Art-repository write, Unity build, or publication is part of this artifact.

Floor tuning selected a128x128 repeat for the existing32x32 warm-flagstone PNG. This brings major horizontal mortar spacing closer to the approximately32px reference spacing; the source's long stone shapes and grain still differ. The192/256 trials made stones oversized. Original96-repeat proofs, layer, config and manifests are preserved in `iterations/floor-before-tuning`; the256 trial comparison is also preserved. Only the repeat size changed: the chairs, rug, other assets and placements remain unchanged.
