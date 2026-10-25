# World Sprite Coverage

Status: **generated review candidates; none are canonically verified or approved for runtime**. The boards in `Review/art/02-firion-study.png` and `Review/art/03-environment-kit.png` were used as style references only. Costumes, props and effects are visual approximations; this ledger does not claim historical accuracy or gameplay implementation.

The actual PNG dimensions below were read from the generated files. All selected source sheets have PNG alpha. The native targets are production conventions for the remake, not verified dimensions of original FFII assets. Use the crop/normalization exporter for cell extraction; do not alter source pixels by hand.

## Active source sheets

| Group | Source | Source dimensions | Layout and coverage | Target |
|---|---|---:|---|---:|
| Named field NPCs A | `ArtSource/Campaign/world/npc-named-hilda-scott-cid-paul-edited-transparent-8x4.png` | 1774 × 887 | 8 columns × 4 rows; rows Hilda, Scott, Cid, Paul; columns down-idle, down-step, left-idle, left-step, right-idle, right-step, up-idle, up-step | 16 × 24 |
| Named field NPCs B | `ArtSource/Campaign/world/npc-named-king-nelly-elina-kain-edited-transparent-8x4.png` | 1774 × 887 | Same 8 × 4 states; rows King of Fynn, Nelly, Elina, Kain | 16 × 24 |
| Generic adults and service roles A | `ArtSource/Campaign/world/npc-generic-adult-edited-transparent-8x4.png` | 1774 × 887 | Same 8 × 4 states; rows man, woman, elder man, elder woman | 16 × 24 |
| Generic adults and service roles B | `ArtSource/Campaign/world/npc-generic-child-services-edited-transparent-8x4.png` | 1774 × 887 | Same 8 × 4 states; rows boy, girl, shopkeeper, innkeeper | 16 × 24 |
| Guards and distinctive roles | `ArtSource/Campaign/world/npc-guards-pirate-mage-edited-transparent-8x4.png` | 1774 × 887 | Same 8 × 4 states; rows imperial guard, rebel guard, pirate, robed mage | 16 × 24 |
| Transport | `ArtSource/Campaign/world/transport-canoe-ship-airship-chocobo-4x4.png` | 1263 × 1245 | 4 columns × 4 rows; columns canoe, ship, airship, chocobo; rows down, left, right, up | 32 × 32 |
| Equipment | `ArtSource/Campaign/world/weapons-equipment-only-4x4.png` | 1274 × 1234 | 4 × 4 row-major: sword guarded/raised, axe resting/raised, spear resting/thrust, bow lowered/drawn, staff resting/raised, dagger lowered/thrust, shield forward/angled, unarmed neutral/guard | 16 × 16 |
| World props | `ArtSource/Campaign/world/world-props-4x4.png` | 1274 × 1235 | 4 × 4 row-major: wyvern left/right, wyvern egg, Sunfire, bell, pendant, mask, mirror, unlit torch, lit torch, raft, closed gate, open gate, throne, bed, coffin | 32 × 32 |
| Spell-effect families A | `ArtSource/Campaign/world/fx-fire-blizzard-thunder-cure-4x4.png` | 1254 × 1254 | 4 columns × 4 rows; columns fire, blizzard, thunder, cure; rows frames 1–4 | 32 × 32 |
| Spell-effect families B | `ArtSource/Campaign/world/fx-poison-stone-sleep-silence-4x4.png` | 1295 × 1214 | Columns poison, stone, sleep, silence; rows frames 1–4 | 32 × 32 |
| Spell-effect families C | `ArtSource/Campaign/world/fx-protect-shell-haste-berserk-revised-4x4.png` | 1261 × 1247 | Columns protect, shell, haste, berserk; rows frames 1–4 | 32 × 32 |
| Spell-effect families D | `ArtSource/Campaign/world/fx-holy-ultima-drain-teleport-4x4.png` | 1295 × 1214 | Columns holy, ultima, drain, teleport; rows frames 1–4 | 32 × 32 |

The five edited NPC sheets now provide two visibly different poses per direction for all 20 requested identities. Direction order is repeated as down, left, right, up. The second pose in each pair uses an opposite-foot-forward step. They are still candidate walk cycles and need native-size review and runtime evaluation.

Each effect sheet is a reusable visual family atlas. It does not establish that every listed spell is implemented, define spell mechanics, or complete a spell-to-effect mapping. The campaign content owner should map supported families to exact spell IDs later.

## Provenance and review limits

- Generated with the built-in ImageGen tool. Prompt text, references, source paths, edit history and superseded candidates are recorded in [`ArtSource/Campaign/world/generation-prompts.md`](../ArtSource/Campaign/world/generation-prompts.md) and [`ArtSource/Campaign/world/excluded-sources.json`](../ArtSource/Campaign/world/excluded-sources.json).
- Source art uses transparent PNG output. ImageGen generated the cells; a later mechanical exporter may crop, resize and normalize them to the targets above.
- All source images were visually inspected at sheet scale. The NPC movement edit improved pose separation, but no native-size spritesheet preview or Unity scene import was performed in this task. Crop boundaries, per-cell consistency, small-size legibility and runtime animation remain to be verified.
- `wyvern`, `egg`, `Sunfire`, `bell`, `pendant`, `mask`, `mirror`, `raft`, `gate`, `throne`, `bed` and `coffin` are prompts/labels for useful original-game campaign concepts. Their generated appearance is not confirmation of a source-game design or proof of completeness.
- The transport and weapons prompt sheets are proposed visual assets. Target sizes are review conventions, not sourced original FFII dimensions.
- This inventory covers reusable world NPC, transport, equipment, effects and prop sources only. It does not include the separately assigned enemy library or assert complete campaign coverage.

## Asset approval state

Every selected source remains `candidate` until native-size crops are inspected and accepted by the project owner. No generated sheet in this library should be described as canonically verified, historically exact, shipped, or playable based on this package alone.
