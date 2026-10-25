# Higher-resolution party animation sources

Generated with the built-in image_gen tool on 2026-10-24. Eight original source sheets contain 40 chronological animation frames for Firion, Maria, Guy, and Leon. These are new higher-resolution source assets, not enlarged production PNGs.

## Source contract

| Character | Attack source (six frames) | Cast source (four frames) |
|---|---|---|
| Firion | ArtSource/RemasterExpansion/party/firion-attack-v2.png | ArtSource/RemasterExpansion/party/firion-cast.png |
| Maria | ArtSource/RemasterExpansion/party/maria-attack.png | ArtSource/RemasterExpansion/party/maria-cast.png |
| Guy | ArtSource/RemasterExpansion/party/guy-attack.png | ArtSource/RemasterExpansion/party/guy-cast.png |
| Leon | ArtSource/RemasterExpansion/party/leon-attack.png | ArtSource/RemasterExpansion/party/leon-cast.png |

Attack layout is 3 columns by 2 rows, row-major: anticipation, windup, advance, impact/release, followthrough, recover. Frame IDs are attack-01 through attack-06. Durations are 100, 120, 70, 90, 110, 150 milliseconds (640 ms total).

Cast layout is 4 columns by 1 row: gather, raise, release, settle. Frame IDs are cast-01 through cast-04. Durations are 160, 180, 100, 200 milliseconds (640 ms total).

Each descriptor requests target 128x128 pixels, PPU 64, bottom-center pivot {x:0.5,y:0}, group battle, character owner, and a non-looping timed clip. Unique owner/clip pairs distinguish all eight animations. Full prompts are sibling .prompt.txt files; generation-record.json preserves original tool output paths, reference paths, dimensions, and SHA256 hashes.

## References and preservation

ArtSource/ResolutionStudy/v1/master.png supplied Firion and Maria identity and the higher-resolution visual direction. Guy and Leon retained identity from ArtSource/Campaign/party/guy-battle-v3.png and leon-battle-v2.png, with the resolution master used as style guidance.

References/PixelRemaster/firion-trading-card-reference.jpg was visually inspected for the vocabulary of ready, action, damage and recovery poses. It was not supplied as an image generation costume reference. Its different costume and palette were not adopted, and no published game sprites were extracted into these sources.

Existing Campaign and ResolutionStudy sources remain untouched. These sheets belong to the separate RemasterExpansion library.

## Source visual QA

All eight generated tool images were inspected. Each contains the requested frame count, a single consistent character, leftward facing, chronological body/weapon motion, and the intended palette/costume family.

- Firion v2 corrects frame03 to a diagonal upper-left downswing, connecting overhead windup to horizontal impact and low-left followthrough. The first source is preserved/excluded because its frame03 prematurely lowered the sword.
- Maria visibly draws the bow before release. Frame04 has no arrow, a relaxed string, and an open drawing hand; the followthrough continues after release. Recovery lowers the bow. Frames04/05 are deliberately close but show hand/cloth motion.
- Guy's axe remains single-headed across the sequence. The advance, impact and lower followthrough form a heavy chop before recovery.
- Leon's sword rises through a leftward strike and high followthrough before lowering to guard.
- Casting strips retain weapons sheathed or on the back. Hands rise, extend left, and withdraw, with mild body/cloth motion rather than unrelated status poses.
- The exporter passed all eight initial source crops using alpha-aware extraction without silhouette cuts. The final Firion v2 source also passed export with unchanged descriptor key and frame IDs.
- Higher-resolution detail and reduced-frame readability still require normalized playback review; visual inspection of a source grid does not prove jitter-free animation or Unity runtime behavior.

## Normalized playback QA

Initial normalized contact sheets under Review/remaster-expansion were independently inspected for all eight clips. Their frame sequences are connected actions, not status-pose galleries. A substantial cross-clip scale mismatch was found: Firion and Maria casting bodies were larger than attack bodies, and Leon attack was much smaller than casting. The pipeline corrected this using owner-level body-height registration constrained by the widest weapon/cape pose, with one shared scale per strip and no per-pose resizing. All eight refreshed contact sheets were then independently inspected; the material cross-clip scale mismatch is resolved.

All eight initial native GIFs were independently decoded with Pillow. Attack clips contain six unique pixel frames and the exact requested durations; cast clips contain four unique frames and exact durations. Each GIF is 128x128 and has no looping extension, matching the one-shot contract. These checks prove encoded state/timing, not perceived smoothness.

Browser live playback was attempted but unavailable in the in-app browser; the Edge browser policy rejected local file URLs. No alternate route was used to bypass that rejection. Therefore this QA makes no claim of observed real-time playback; it uses normalized contact-frame comparison and decoded GIF state/timing.

Final post-registration contact-sheet review: FRAME_SEQUENCE_CANDIDATE_PASS. Attack/cast body and head sizes now compare consistently within each owner. Foot ground lines stay planted; the advance, wider stance and Guy crouch read as intentional body motion rather than whole-sprite jumps. Firion v2 follows overhead -> diagonal upper-left -> horizontal impact -> low-left followthrough -> recovery. Maria keeps the arrow until release, then relaxed string/open hand through followthrough. Guy retains a single axe blade. Leon carries the strike into a high followthrough before returning to guard. All four casts gather, raise, release left, and settle without obvious contact-sheet jitter.

ArtSource/RemasterExpansion/party/visual-qa.json records the final contact/GIF hashes, decoded timing and per-frame PNG ground pixels. All40 exported frames share ground pixel y=125 on their128x128 canvases. No additional source regeneration was necessary after Firion v2.

Approval boundary: this is source and normalized frame-sequence approval as a candidate library, not approval of perceived real-time smoothness, final FFII Pixel Remaster fidelity, spell integration, animation transitions or Unity runtime behavior.



