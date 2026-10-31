# Shop Interiors V2 mechanical export

Requires Node.js20+ and Sharp0.35.5 (the exact verified version). The working executable is `C:\Program Files\nodejs\node.exe`, version24.16.0; this workstation has Sharp in the Codex runtime fallback path recorded in `build.cjs`. For a standalone checkout, run `npm install --ignore-scripts=false` in this tool directory to install its declared dependency locally.

From the staging root (or replace with absolute script paths):

```powershell
& 'C:\Program Files\nodejs\node.exe' '.\Tools\shop-interiors-v2\build.cjs' export
& 'C:\Program Files\nodejs\node.exe' '.\Tools\shop-interiors-v2\build.cjs' verify
```

The script resolves its root from its own location. Verification works from any current directory. Rebuild reads the five preserved masters under `ArtSource/ShopInteriorsV2/sources/` and the five selected records in `ArtSource/ShopInteriorsV2/generation-prompts.json`. It does not require root-level `Incoming/` or the parent combined generation record after initial capture. If an incoming file also exists, it must match the preserved bytes. Initial capture alone can read `Incoming/{tobul-scene,shop-fixtures,armor-scene,item-scene,magic-scene}-master.png` and the root generation record. It rewrites only its own derived outputs.

Operations are mechanical: exact source copy, nearest-neighbor resize, explicit rectangular crop, alpha threshold128, alpha-bounds trim, aspect-preserving contain, disjoint pixel selection, and review labels. There is no artwork painting, inpainting, palette replacement, hidden-pixel reconstruction, or seam repair. Scene polygons are selection masks, not drawn game artwork.

`verify` checks all manifest source/output hashes, binary cutout alpha, zero invisible RGB, and exhaustive mutually exclusive scene layers. Adding the five layer pixel buffers must reproduce every normalized composite byte exactly. This proves decomposition, not retail fidelity or runtime correctness.

The production manifest is the authoritative asset inventory. HTML and contact sheets are review artifacts. Review provenance and retail reference crops belong to the sibling `ReferenceReview` package and are not copied into runtime art.
