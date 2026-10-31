# Interior Details V4 — Reference Review

This package compares actual FFII Pixel Remaster reference crops with V4 native rug and wall assets in two 1120 px boards. Images use nearest-neighbor resizing only where needed to fit a panel. The Tobul source rug crop remains native-size. Captions distinguish partial/occluded source crops from complete V4 components. Screenshot crops are not production art.

## Sources

- Hilda audience rug and wall: [RPGFan, Final Fantasy II Pixel Remaster Screenshot 005](https://www.rpgfan.com/wp-content/uploads/2021/06/Final-Fantasy-II-Pixel-Remaster-Screenshot-005.jpg). The wall crop includes the dark timber assembly above the cream inset.
- Scott refuge rug and wall: [Vorxu, Altair & Fynn](https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn). The full rug capture is occluded; an inset shows visible rug pixels. The wall crop shows three broad cream bays with narrow plaster inserts between them and at the edge.
- Tobul smithy rug: [Vorxu, Salamand & Semitt Falls](https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/salamand-and-semitt-falls). The selected rug crop is clear of characters.

Crop rectangles and SHA-256 hashes are in [`source-crops/source-crops.json`](source-crops/source-crops.json). Crop images are copied unchanged from the prior reference package; hashes were checked against the crop inventory.

## Independent visual comparison

### Rugs

- **Hilda red/gold:** V4 border width is close to the visible top/right reference border. V4 gold reads brighter/oranger, and its red field grain is finer and more even. The reference is only a partial top/right crop; the board compares that crop with the complete V4 rug.
- **Scott blue/cream:** The screenshot hides much of the rug. Its exposed area shows chunkier blue lattice and larger pale motifs; V4 uses finer repeated pale-lavender diamonds/rosettes and a softer, lighter blue. The full source context and exposed-corner inset remain visible.
- **Tobul cream/lilac:** V4 preserves cream/lilac and diamond geometry, but its field repeats smaller, more regular units. V4 reads warmer/pinker than the muted source crop. The source crop is kept at native 190×150 pixels beside the complete V4 rug.

### Walls

- **Hilda:** V4 includes the dark overhead timber stack above the cream inset. Its overall silhouette is close; the V4 lower wood base occupies somewhat more of the panel height, and the timber texture is cleaner than the captured pixels.
- **Scott:** The reference shows three broad cream bays plus narrow plaster inserts between them and at the edge. V4's restored strip retains the three broad bays and narrow inserts, so its rhythm is closer than the simplified three-region trial that omitted them. The broad-right / narrower-left sequence is visible; exact bay widths and screenshot framing still differ.

## Rebuilding

[`build-boards.js`](build-boards.js) generates both boards from the local `source-crops/` and the V4 production assets. It detects the staging sibling `../Assets/Art/Production/InteriorDetailsV4/`, or the repository-level `Assets/Art/Production/InteriorDetailsV4/` directory after publication at `References/InteriorDetailsV4/Comparison/`. It shows each whole authored wall component once; no repeated panel rhythm is synthesized. Requires Node.js and Sharp, using a local install or the configured Codex runtime fallback. Run `node build-boards.js` from this directory.

Snapshots: [production manifest](v4-production-manifest.json) · [proof manifest](v4-proof-manifest.json) · [verification](v4-verification.json). Production manifest SHA-256: `94a7aa4ab636d2a201cdf8ca20643cf56d706e71145af10a978e2438d5f167b2`. Verification SHA-256: `fd22e246c01ae5e6b76ff4ff527ba2d4865309f4617dfbe213538f77b2450cc3`.

This is a component comparison, not a full-room layout or retail 1:1 claim. No game integration or runtime behavior is demonstrated.
