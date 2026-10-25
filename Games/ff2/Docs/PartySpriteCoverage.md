# Party sprite coverage

Generated 2026-10-24 with the built-in image_gen tool, using the approved Firion study as the visual direction. Original new artwork; official FFII character names and roles checked against https://na.finalfantasy.com/titles/finalfantasy2.

## Scope and state

17 selected source sheets, 168 new poses: eight field sheets (96 poses) and nine battle sheets (72 poses). Firion's existing 12-frame field sheet remains in ArtSource/Batch01/firion-walk.png. Together the selected library covers the original nine playable characters with 108 field poses and 72 battle poses (180 poses).

Sources are saved locally. This document describes source generation and visual inspection, not Unity import or runtime approval. Normalization, crop validation, manifests, previews and engine integration are handled by the campaign pipeline.

| Character | Field source | Battle source | Poses |
|---|---|---|---:|
| Firion | ArtSource/Batch01/firion-walk.png (preserved) | ArtSource/Campaign/party/firion-battle.png | 12 + 8 |
| Maria | ArtSource/Campaign/party/maria-field.png | ArtSource/Campaign/party/maria-battle-v2.png | 12 + 8 |
| Guy | ArtSource/Campaign/party/guy-field.png | ArtSource/Campaign/party/guy-battle-v3.png | 12 + 8 |
| Leon | ArtSource/Campaign/party/leon-field.png | ArtSource/Campaign/party/leon-battle-v2.png | 12 + 8 |
| Minwu | ArtSource/Campaign/party/minwu-field.png | ArtSource/Campaign/party/minwu-battle.png | 12 + 8 |
| Josef | ArtSource/Campaign/party/josef-field.png | ArtSource/Campaign/party/josef-battle.png | 12 + 8 |
| Gordon | ArtSource/Campaign/party/gordon-field.png | ArtSource/Campaign/party/gordon-battle.png | 12 + 8 |
| Leila | ArtSource/Campaign/party/leila-field.png | ArtSource/Campaign/party/leila-battle.png | 12 + 8 |
| Ricard | ArtSource/Campaign/party/ricard-field.png | ArtSource/Campaign/party/ricard-battle-v2.png | 12 + 8 |

## Frame contract

Field: three columns, four rows. Rows face down, left, right, up. Columns are left-step, idle, right-step. Frame names are down-left/down-idle/down-right, left-left/left-idle/left-right, right-left/right-idle/right-right, up-left/up-idle/up-right. Target frame size 16x24.

Battle: four columns, two rows, row-major order idle, windup, attack, cast, hit, critical, victory, ko. Target frame size 24x32. Poses primarily face left; KO head is left and feet right. All sources requested real alpha, no backgrounds or painted checkerboards. Source field canvases are 1086x1448 and battle canvases 1774x887; importer must use the descriptor contract rather than infer pixel-perfect divisibility.

ArtSource/Campaign/party/sheets.json is the selected descriptor list. Each selected source has its full request in a sibling .prompt.txt file. generation-record.json records reference inputs, original tool output path and SHA256. Originals in the Codex generated_images folder remain preserved.

## Visual inspection and limitations

Every generated source was inspected in the tool output. Each selected field source contains the intended twelve visible figures, and each selected battle source contains eight visible poses. No source is a claim of completed animation timing or gameplay validation.

- Maria revision v2 corrects the duplicated drawn-bow action: attack has a relaxed string, no nocked arrow, and open release hand. The original remains preserved/excluded; use the separate bow-shot projectile family when animating the shot.
- Guy revision v3 corrects the double-headed attack axe to one upper blade. The original and unsuccessful v2 correction remain preserved/excluded.
- Several hit/victory poses turn slightly toward the viewer while still oriented left. They are not strict side-profile silhouettes.
- Palette and costume identity were retained through each character's own field reference for battle. Weapons/capes can shift detail between poses and need final small-scale visual review.
- Initial Leon battle source had a cape/sword bounding-box overlap across the windup/attack columns. Preserved as ArtSource/Campaign/party/leon-battle.png and listed in excluded-sources.json. Selected replacement is leon-battle-v2.png with wider transparent gaps; exporter crop preflight passed. Initial Ricard battle had the same spear overlap issue; ricard-battle.png is preserved and excluded, replaced by ricard-battle-v2.png. Final full-set exporter verification, including Maria/Guy corrections, is pending.
- Eight poses per battle character are a reusable starting state library, not every possible configurable equipment sprite, condition overlay, transition frame or cutscene action.



