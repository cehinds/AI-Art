# Ricard attack and cast source candidates

Generated with the built-in ImageGen tool on 2026-10-24. Full prompts are stored alongside each source. The approved `ArtSource/Campaign/party/ricard-battle-v2.png` establishes costume and identity; `ArtSource/RemasterExpansion/party/leon-attack.png` establishes richer rendering style only. Both were visually inspected before generation. The new attack sheet then establishes casting identity/style.

- Attack original: `C:/Users/const/.codex/generated_images/01a16f90-9a1d-7252-9043-55448912149e/exec-d937d1a8-e215-4a7b-98fd-a60d4abc1ac0.png`
- Cast original: `C:/Users/const/.codex/generated_images/01a16f90-9a1d-7252-9043-55448912149e/exec-a3c1cbc2-357c-4f93-b7ba-76ad1d8f7c71.png`
- Selected compact attack v2 original: `C:/Users/const/.codex/generated_images/01a16f90-9a1d-7252-9043-55448912149e/exec-c483d6ba-fb82-42e9-8e47-04b57d34a606.png`

The initial attack failed preservation-aware fit preflight: its weapon/cape would force the established battle body height from 60.18px to 48.05px. A targeted ImageGen edit shortened the spear/cape footprint and reduced the lunge without scaling down the character. The original remains explicitly excluded and preserved. The selected v2 passed read-only fit preflight with 75.07px body capacity, above the required 60.18px; casting also passed. Native export/contact validation remains a separate gate.

Six attack poses: ready, draw back, partial extension, full thrust, retract/lift, recover. Four cast poses: ready, gather, release, settle. Both retain blue dragon helmet, gold armor trim, silver knees, blue cape and upright spear in ready poses. Cast release opens the free arm outward; it is not an exact measured Pixel Remaster gesture. Timings are authored consistently with the existing party set.

Source review: recognizable costume, coherent left facing and readable attack phases; full weapons appear present. Sprite-sheet spacing is generated, so adaptive extraction and final native contact review are required. A 128 px frame does not imply a 128 px body. Match existing battle normalization and preserve old sprites; do not resize old exports to fit these sources. Unity import and playback remain pending.

Final native contact review: attack and cast retain comparable standing body size, visible helmet/hands/spear, stable grounded feet and distinct action phases. Root inspected both exported contact sheets. Strict expansion verification passed for native reconstruction, alpha, GIF order/timing and preservation. The compact spear thrust remains stylized; real-time feel and Unity rendering are not yet approved.
