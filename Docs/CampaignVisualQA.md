# Campaign Visual QA

Independent visual pass over the exported `Review/campaign/*-contact.png` sheets on 2026-10-24. This pass did not change art or code. All reviewed assets remain candidates; contact-sheet inspection does not verify Unity import or runtime animation.

## Findings

| Group | Order and scale | Visual read | Follow-up |
|---|---|---|---|
| NPCs | All five sheets show four identities by row and down/left/right/up idle-step pairs by column. Crops fit the 16 × 24 target; no obvious clipping. | Edited step frames are visibly different for many actors, and there are no exact duplicate pairs apparent in the contacts. Step readability varies: skirts, robes, capes, and rear-facing poses conceal foot changes, so Hilda, Elina, elder woman, and robed mage read closer to idle with a slight shift than a strong walk at native size. | Keep as 2-pose candidates. For a playable walk cycle, strengthen leg separation/hem movement on those rows and inspect in-engine at actual scale. |
| Transport | Four columns are canoe, ship, airship, chocobo; rows are down, left, right, up. Each sprite fits 32 × 32 without obvious clipping. | All four subjects are recognizable. Canoe/ship direction pairs mix overhead and side/three-quarter cues, so the row-direction mapping is less consistent than the NPC sheets. Chocobo front/back and side views read clearly. | Treat transport orientations as candidates; verify map-view conventions before wiring directions to movement. |
| Equipment | Row-major order matches sword, axe, spear, bow, staff, dagger, shield, unarmed, two poses each. Individual items fit the 16 × 16 target. | Standalone silhouettes are readable in the 4× contact view. Thin spear, dagger and staff detail compresses at native size; paired changes are mostly angle/stance changes and need a native-size check. | Keep candidate icons; confirm each pair stays distinguishable at 16 × 16 in the inventory/equipment UI. |
| Props | The 4 × 4 row-major ordering matches the 16 listed props. No obvious clipping at 32 × 32. | Wyvern orientations, egg, Sunfire, bell, pendant, mask, mirror, torches, raft, gates, throne, bed and coffin are recognizable. The open gate occupies one cell as a two-leaf open gate, which reads as one prop. | No cell-order correction indicated. Verify prop naming against campaign content before use. |
| Spell effects | Four sheets each show four effect columns and frames 1–4 top-to-bottom. All effects fit 32 × 32. | Family colors/shapes are distinct. Fire, blizzard, poison, sleep, protect, shell and teleport show visible growth/decay. Thunder, haste and drain retain a similar silhouette across frames, so their animation reads as subtle scale/pulse variation. | Keep as reusable family candidates. Review the weaker sequences at runtime; do not infer spell coverage from these art families. |

## Evidence reviewed

- `Review/campaign/campaign-world-named-npcs-a-contact.png`
- `Review/campaign/campaign-world-named-npcs-b-contact.png`
- `Review/campaign/campaign-world-generic-adults-contact.png`
- `Review/campaign/campaign-world-generic-services-contact.png`
- `Review/campaign/campaign-world-guards-and-roles-contact.png`
- `Review/campaign/campaign-world-transport-contact.png`
- `Review/campaign/campaign-world-weapons-contact.png`
- `Review/campaign/campaign-world-props-contact.png`
- `Review/campaign/campaign-world-fx-fire-blizzard-thunder-cure-4x4-contact.png`
- `Review/campaign/campaign-world-fx-poison-stone-sleep-silence-4x4-contact.png`
- `Review/campaign/campaign-world-fx-protect-shell-haste-berserk-revised-4x4-contact.png`
- `Review/campaign/campaign-world-fx-holy-ultima-drain-teleport-4x4-contact.png`

The contact sheets confirm exported crop order and broad silhouettes only. Native-size UI readability, original-game fidelity, and Unity animation behavior remain unverified.
