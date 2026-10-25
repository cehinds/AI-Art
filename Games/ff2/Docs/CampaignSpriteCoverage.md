# Original FFII campaign sprite coverage

This is a candidate library and a reproducible inventory, not a claim that every original map, animation, event state, silhouette, palette, or runtime use has been reconstructed. Original Famicom roster enumeration is grounded in [Gamer Corner's 128-monster table](https://guides.gamercorner.net/ffii/monsters/). Emperor first form (entry 85) and final form (entry 128) are separate owners. Soul of Rebirth additions are outside scope.

## Current measured delivery

Campaign: **744 PNG sprites from 48 generated source sheets**. Batch 01 remains separate: **44 PNGs**, including 32 environment tiles and 12 Firion field frames. Counts are read from manifests rather than assumed from a plan.

| Group | Owners | Exported PNGs |
| --- | ---: | ---: |
| effects | 32 | 128 |
| enemies | 128 | 128 |
| world-icons | 1 | 16 |
| item-icons | 1 | 16 |
| party-field | 8 | 96 |
| party-battle | 9 | 72 |
| status-icons | 16 | 16 |
| npc | 20 | 160 |
| transport | 4 | 16 |
| weapon | 8 | 16 |
| prop | 12 | 16 |
| effect-family | 16 | 64 |

Enemy candidates: **128 / 128** original roster entries exported as static idle combat sprites. Missing: None. Enemy silhouette and palette fidelity remains unverified; target dimensions are this remake's normalization contract, not a claim of canonical original dimensions.

Party field candidate sets: **9 / 9** with twelve declared directional states, including existing Batch 01 Firion. Party battle sets: **9 / 9** with all eight required states (idle, windup, attack, cast, hit, critical, victory, ko). Distinct state names and file counts cannot prove readable motion or pose quality. Identical exported pixel-state groups: **0**; inspect coverage.json before approving animation.

Spell visual families: **40 / 40 learnable spells** and **29 / 29 Special/item/monster entries** are explicitly mapped to **48 exported families (192 frames)**. Mappings distinguish direct visual families, translation aliases (Scourge to poison, Break to stone), and shared visual families. Reuse is recorded in Tools/campaign-art/spell-effect-mapping.json and Review/campaign/coverage.json; it does not establish original animation, level variants, reverse effects or spell behavior. [Original spell catalog](https://guides.gamercorner.net/ffii/spells/).

## Reproduce and review

Run from repository root:

```powershell
node Tools/campaign-art/export.cjs
node Tools/campaign-art/verify.cjs
node Tools/campaign-art/coverage.cjs
```

Open Review/campaign/index.html offline. It compares each generated source sheet with its native atlas, provides owner/state filtering, individually links every native PNG, and cycles directional walks or authored state comparisons. Review/campaign/validation.json records file checks; coverage.json lists every owner and state plus all 128 expected enemy entries. These are file and browser review evidence, not Unity runtime evidence.

Descriptors live under ArtSource/Campaign/**/sheets.json. Supported contracts: owner plus frameNames; names for a static multi-owner atlas; owners per row plus states per column; or explicit cells with owner/state/target. Source SHA-256, config SHA-256, exact crop, alpha bounds and scale are recorded. Transparent or disconnected-ink cuts are chosen separately per row and column to accommodate uneven generated spacing; cellRects and row/column boundaries can override visually inspected cases. FX extra01 uses exact 8-connected alpha components to separate overlapping rectangular bounds: each visible component is assigned to the nearest measured main-component anchor, with ambiguous assignments rejected and component IDs/anchors recorded for independent reconstruction. Every retained visible pixel comes directly from its generated source. Shared scale is retained across each owner's frames within a sheet. Static multi-owner enemies use independent owner scales and a verified one-pixel transparent safety margin on every edge. Nearest-neighbor resampling and alpha thresholding are mechanical; no pixels are painted, mirrored, recolored, or synthesized.

Every source PNG must be registered to an exported descriptor or excluded with an explicit reason. Existing edited/unmanaged production PNGs are protected, existing .meta files and GUIDs are preserved, and no stale files are deleted. The verifier rejects stale unregistered output and checks unique IDs/GUIDs, source/config/output hashes, crop bounds, complete descriptor states, binary alpha, and native sizes. Binary transparency can retain generated edge halos: visual review remains necessary.

## Known candidate limitations

[Independent contact-sheet visual QA](CampaignVisualQA.md) found subtle walking on robe/skirt/cape and rear-view NPC poses, inconsistent overhead versus side/three-quarter transport orientations, compressed thin equipment details, and subtle thunder/haste/drain changes. Native 24 × 32 party battle bodies vary in visible size because long weapons participate in each owner's shared scale. Registration and in-game readability need approval. The 16 status icons are optional modern readability candidates, not original FFII icon reproductions, and have no original-UI wiring approval.

The delivery includes 20 NPC owners with eight declared directional idle/step states each, four transports with four directions, eight equipment families with two poses, 16 prop states, 16 world markers, 16 item icons, and 16 status icons. Counts describe selected candidates rather than an audited original map/event inventory.

## Remaining approval and coverage work

- Compare each candidate with the original character, enemy, equipment, transport and effect references; approve or regenerate specific failures.
- Audit every original map's tiles, transitions, interiors, object variants and story event states against actual requirements. Existing environmental samples and generic props are not exhaustive map coverage.
- Confirm readable walking and combat states, consistent scale, outlines and alignment in motion. Direction-only NPC sheets do not establish walking completeness.
- Import and reimport Campaign art in Unity after export. Use FF2 > Art > Validate Campaign Sprite Imports to check the manifest-driven pivots, native dimensions, point filtering, full rects, 16 PPU and uncompressed textures.
- Verify scene/gameplay wiring and playable builds separately. .NET compilation against Unity API assemblies is not Unity Editor import or Play mode. Unity license activation has been blocked (exit 198); no successful Unity import/play/build is claimed by this report.

The pipeline does not publish or release assets.
