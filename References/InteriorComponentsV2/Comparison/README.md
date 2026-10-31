# Interior Seams V2 reference review

Status: final static room and join proofs visually inspected on 2026-10-31. The red floor now uses the quieter source crop; the strong vertical columns seen in the earlier draft are gone. Wall/cap, doorway-threshold, floor-repeat, and rug joins are visually coherent in the shown assemblies. This is an asset-only comparison; no game integration, collision, or runtime behavior was tested.

## Sources and attribution

- Hilda audience-room capture: [RPGFan, Final Fantasy II Pixel Remaster Screenshot 005](https://www.rpgfan.com/wp-content/uploads/2021/06/Final-Fantasy-II-Pixel-Remaster-Screenshot-005.jpg).
- Scott refuge/bedroom capture: [Vorxu, Altair & Fynn](https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn), direct image `scott-gives-you-ring-960w.webp`.
- Tobul smithy capture: [Vorxu, Salamand & Semitt Falls](https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/salamand-and-semitt-falls), direct image `tobul-960w.webp`.

The scene captures and crops are copied from the attributed `AI-Art-FF2/Review/interiors-city-ui-comparison-v1/` package. They are visual comparison references, not production sprites. The sepia hideout map is excluded as a color reference; U.S. SNES FFII/FFIV imagery is not used.

## Visual findings

- **Wall profile and joints:** the tall north face is confined to the north wall run; side boundaries use separate returns. The shown long runs and inside-corner samples have no visible holes, doubled rails, or base discontinuities. North doorway and south threshold meet the adjoining floor in the shown static layouts.
- **Floor fields:** Scott's refuge uses warm flagstone; Tobul's shop uses the red field. The quieter red-floor crop removed the prior bright/dark vertical columns. Four repeated floor families align without visible gaps; natural repeat motifs remain recognizable over long runs.
- **Rug joins:** the shop L-shaped rug's inside corner reads continuous. The three rug palettes are distinct, and the revised sheets show no displaced/floating gold fragments. V2 borders/fields are simpler and more regular than PR's layered ornamental patterns. Hilda's PR carpet has denser gold geometry, while Scott/Tobul rugs carry more internal ornament.
- **Palette and finish:** warm stone and red shop floors now match the intended Scott/Tobul material roles. V2 red remains more uniformly saturated and fine-grained than the PR crop. Rug fields have simpler motif density than PR; the wall panels repeat visibly and the cutcaps retain a bold outline.
- **Limits:** proof covers three authored room layouts, declared component masks/repeats, and selected inside corners. It does not establish full-map fidelity, every wall topology, gameplay placement, collision, animation, or runtime rendering. No retail 1:1 or blanket seamlessness claim is made.

## Validation receipt and inventory

The read-only receipt reports **PASS** for 166 native assets, 8 floor-repeat checks, 9 tall-face horizontal pairs, 116 cut-cap geometric pairs, 1,176 carpet occupancy pairs, and 945 actual proof joins (4-pixel band depth); mutation rejection also passed. The receipt states that exact-color bands do not establish retail parity or runtime behavior.

- [Production component README snapshot](v2-proof/production-readme.md)
- [Production manifest snapshot](v2-proof/production-manifest.json)
- [Verification receipt snapshot](v2-proof/verification-receipt.json)
- [Visual comparison gallery](index.html)

Production manifest SHA-256 at review time: `819a143c4660d668af60ceddff7700311a1fe931d306e539d1ad6b1dcaba0df8`. Snapshots are byte-identical copies of `AssetWork/InteriorSeamsV2/Docs/InteriorComponentsV2/README.md`, `AssetWork/InteriorSeamsV2/Assets/Art/Production/InteriorComponentsV2/manifest.json`, and `AssetWork/InteriorSeamsV2/Review/interior-components-v2/verification.json` respectively.

## Included files

`reference-crops/` contains copied FFII PR scenes, material crops, and V1 wall/floor/rug repeat proofs. `v2-proof/` contains final native/3× room assemblies, floor repeats, inside-corner joins, rug/architecture contacts, and record snapshots. Earlier `draft-` room images remain as review history; the gallery uses only the refreshed final proof.
