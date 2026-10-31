# V2 shop asset freeze

Production PNGs and source selections are frozen after the final mechanical export and visual review. No game integration or publication performed by this agent.

- Production:59PNG =24 scene/layer outputs +28 material/context samples +7 independent transparent atlas props.
- Preserved raw selected masters:5PNG; exact original-file comparisons passed.
- Review:11PNG =8 room proofs +2 contact sheets +1 floor repeat proof, plus HTML gallery.
- Generation records:5 exact selected records, with original generated filenames and parent record SHA256.
- Verification:73 source/output hashes;4 exact scene reconstructions;418656 pixels covered once; exact production inventory; binary prop alpha and zero invisible RGB; complete source lineage.
- Production manifest SHA256: `69fffb273fd2db1c289e37ad99886c4baf3fde2b41f0324978222980ce6a3ed2`.
- Parent generation record SHA256: `1e06f7a19e0a40f90f5e08dc4c72d5a64969070ae26ff5729934656f1f0bc169`.

Primary weapon comparison proof: `Review/shop-interiors-v2/rooms/weapon-reference-matched-534x440.png`.

Final command, works from any current directory:

```powershell
& 'C:\Program Files\nodejs\node.exe' 'C:\repos\AI-Remake-FF2\AssetWork\PaletteDensityPassV2\Tools\shop-interiors-v2\build.cjs' verify
```

An export invoked from `C:\` passed with the same manifest SHA256. Rebuild reads its own preserved ArtSource masters/prompts first. Staging-only Incoming files are optional and, if present, must match. The source-relative artifact roots remain portable when moved together.

Retail reference scope is Tobul weapon shop. Armor/item/magic are Tobul-layout adaptations. Visible scene fragments do not supply hidden pixels or autonomous collision. The isolated fixture atlas is a generated approximation; wall stock remains baked into panels. Floor swatches are sampled, not repaired or guaranteed seamless. The lower rug is viewport-clipped, not a complete repeat or nine-slice. No temple or Altair1:1 retail layout claim.
