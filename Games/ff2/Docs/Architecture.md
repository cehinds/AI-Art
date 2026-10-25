# FFII remake foundation: implemented boundaries

This project targets **Final Fantasy II, the Famicom game with Firion, Maria and Guy**, using a proposed GBA-quality pixel-art direction. The current implementation is a technical sandbox, not a complete remake, campaign slice, faithful rules simulation or production visual implementation.

## Project

- Unity Editor: **6000.4.10f1**, Windows review target.
- Core: `Assets/FF2/Core`, plain C# with an assembly definition that forbids Unity engine references.
- Unity adapter: `Assets/FF2/Runtime`, IMGUI review screen, technical movement grid and explicit button actions.
- Authoring/automation: `Assets/FF2/Editor`, isolated editor assembly.
- Content: `Assets/FF2/Resources/Content`, two JSON packs containing ten sample records.
- Behavioral tests: `Tools/core-tests`, .NET 10 runner using the exact core source files, with no third-party test dependency.

```text
JSON content packs --> catalog validation --> immutable catalog snapshots
                                                  |
                      battle / keyword state / sample progression
                                                  |
                        Unity review UI --> validated save DTO --> XML codec
                                                                    |
                                                        replace-with-backup storage
```

## Stable content IDs and extension packs

IDs use lowercase namespaced identifiers such as `ff2:firion` and `demo:patrol`. Display names are not save keys. `ContentId` rejects uppercase characters, missing or multiple namespace separators and unsafe characters.

Every pack declares its own ID, content schema version `1`, dependency IDs and entries. The catalog rejects duplicate packs, duplicate entries, missing dependencies, dependency cycles, unknown kinds, invalid actor stats, missing display names, unresolved references and cross-pack references without a declared direct or transitive dependency. Merge order does not decide winners: implicit overrides are rejected. Catalog reads return copies so authoring objects and consumers cannot mutate already validated records.

Implemented entry kinds: character, enemy, item, spell, keyword, location, encounter, dialogue and quest. These are **record categories**, not nine complete gameplay systems. Item use, spell combat, authored map loading, encounter composition, quest interpretation and dialogue execution remain future work. The runtime patrol deliberately selects sample enemy records directly.

To add content, create another JSON pack with a unique pack ID, declare dependencies, give each entry a stable ID, and list content references. Add it under the existing resource folder, then run the behavioral runner or the Unity validation method. New mechanics need explicit core behavior and adapters; new record kinds are deliberately rejected until supported. Version constraints, localization tables, downloadable packs, asset bundles, signed mods and safe explicit override policies are not implemented.

Authoring limitation: Unity `JsonUtility` ignores unknown JSON fields. Catalog validation validates the recognized model and references, but does not currently reject misspelled/unrecognized property names. Strict JSON-schema authoring validation is deferred; do not treat a successful merge as proof that every authored property was consumed.

## Battle and progression

`BattleSession` owns deterministic action sequencing, speed order, stable instance-ID tie breaking, enemy turns, living-target checks, guard duration, skipped defeated actors, damage clamping and terminal victory/defeat. Combatant instance IDs distinguish multiple enemies sharing one content ID. Actors expose readable state with controlled mutation.

Attack and Guard are implemented. Enemies use a deterministic first-living-party-member targeting rule. There are no random hits, magic, MP, equipment bonuses, statuses, rows, escape, rewards or campaign balance.

**Temporary mechanics deviation:** this sandbox resolves an individual actor's command immediately. The original game collects party commands before resolving the turn; replace the immediate action surface with command collection, target selection/retargeting and a separate resolution phase before a faithful battle implementation. The original command structure is documented in Nintendo's [FFII battle instructions](https://www.nintendo.co.jp/wii/vc/vc_ff2/vc_ff2_09.html).

`IProgressionRule` is the explicit replacement boundary for original usage-driven progression research. `SampleUsageProgression` counts attacks and grants one weapon rank per three uses, capped at rank 99. This is a **placeholder**, not a canonical FFII formula. HP, MP, attributes, weapon types and spell-level growth are not implemented. There is no conventional shared character-level system.

## Keyword state

`KeywordJournal` learns validated keyword IDs once and answers whether a learned keyword may be asked about. The sandbox NPC teaches Wild Rose when approached; Ask is enabled only after learning and while nearby. The response is original technical placeholder text, not reconstructed campaign dialogue. Dialogue trees, item-giving, quests, event flags and full original conversational state are future work.

## Saves and compatibility

`SaveDocument` schema version **2** stores content pack IDs, location ID, coordinates, party character IDs, HP, sample weapon rank/use and known keyword IDs. The runtime records only the owning packs and transitive dependencies of actual saved content; removing an unrelated optional pack does not invalidate progress. XML serialization uses BCL APIs shared by Unity and the .NET runner. DTDs are disabled, save size is bounded, unknown XML elements/attributes and future schema versions are rejected. Loaded IDs, pack ownership/dependency closure, stat bounds, duplicate records and coordinates are validated before the UI replaces running state.

The included version-1 fixture preserves character IDs/HP and migrates absent location, keyword and pack-list data to sandbox defaults. This fixture is this project's own demonstration schema; compatibility with retail-game saves or other remakes is not claimed.

`SaveFileStore` writes a unique adjacent temporary file, then atomically replaces an existing slot with a previous-version `.bak` on Windows. Invalid documents are rejected before disk writes. The Unity adapter uses one `review-slot.xml` under `Application.persistentDataPath`, catches load errors and keeps the running state unchanged on failure. Automatic backup recovery, crash/power-loss durability testing, checksums, cloud sync and multi-slot UI are future work.

**Temporary save deviation:** the sandbox allows saving on its technical grid and uses one review slot. The original allows saving on the world map and supplies four slots; production save gates and slot UI must be implemented separately. See Nintendo's [FFII save instructions](https://www.nintendo.co.jp/wii/vc/vc_ff2/vc_ff2_08.html).

## Unity review entry point

1. Open the repository with Unity **6000.4.10f1**.
2. Choose **FFII Review > Create or Open Core Sandbox**. The editor creates `Assets/FF2/Scenes/CoreReview.unity` when absent, adds it to build settings and opens it. Existing scenes are preserved during creation; opening prompts before discarding unsaved edits.
3. Enter Play mode. Move with arrows/WASD or the directional buttons. Approach NPC tile `(7,2)` to learn/ask Wild Rose.
4. Start the patrol drill; select attacks or Guard until victory/defeat. Return to the grid and save/load state. Reset Sandbox restores technical starting state without deleting a saved file.
5. **FFII Review > Build Windows Review Player** validates content/battle/save, ensures the review scene and builds `Builds/Review/FF2Review.exe`.

The presentation uses technical boxes/labels. It contains **no production pixel-art sprites** and does not establish screenshot or visual-quality evidence. A texture importer applies point filtering, no mipmaps, uncompressed sprites and 16 pixels/unit only under `Assets/Art/Production/`. Concept/reference images are excluded. Sprite-sheet slicing, pivots, animation and asset-specific scale remain explicit authoring work.

## Next production boundaries

1. Replace immediate battle actions with party-command collection and faithful resolution.
2. Research and validate original/GBA formula differences behind progression and battle-rule boundaries.
3. Build authored maps, NPC/event/dialogue execution, inventory/equipment and magic against stable IDs.
4. Replace the grid and IMGUI sandbox with approved pixel-art assets and a production Unity UI.
5. Add a small authored playable story segment before populating a full campaign.
6. Add EditMode/PlayMode integration suites and target-player smoke tests; keep the fast pure-core runner.

Local files only. No commit, push, pull request, merge, release or publication is performed by this foundation work.
