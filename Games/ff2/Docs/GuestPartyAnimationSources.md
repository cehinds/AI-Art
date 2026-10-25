# Guest party animation sources

Eight selected built-in image_gen sheets contain 40 higher-resolution frames for Minwu, Josef, Gordon and Leila. Source generation, source visual QA and final native contact-frame QA are complete as candidates. These are production candidates, not runtime-approved art. Ricard is generated separately in ArtSource/RemasterExpansion/ricard-party/.

## Selected sources

| Owner | Attack (six frames) | Cast (four frames) | Visual identity |
|---|---|---|---|
| minwu | ArtSource/RemasterExpansion/guest-party/minwu-attack.png | ArtSource/RemasterExpansion/guest-party/minwu-cast-v2.png | White turban/veil/robes, red trim, orb staff |
| josef | ArtSource/RemasterExpansion/guest-party/josef-attack.png | ArtSource/RemasterExpansion/guest-party/josef-cast.png | Bald head, brown beard, orange-brown tunic, unarmed |
| gordon | ArtSource/RemasterExpansion/guest-party/gordon-attack-v2.png | ArtSource/RemasterExpansion/guest-party/gordon-cast.png | Red hair, gold circlet, green-gold royal clothing, spear |
| leila | ArtSource/RemasterExpansion/guest-party/leila-attack.png | ArtSource/RemasterExpansion/guest-party/leila-cast.png | Purple hair, red pirate bandana, gold hoop, red-purple outfit, cutlass |

The exact existing Campaign character sheets were the primary identity references. ArtSource/RemasterExpansion/party/firion-attack-v2.png supplied the richer pixel-art style only. No published game pixels were extracted or copied, and the existing Campaign sources were not changed.

The official character roster confirms their identities and roles: [FINAL FANTASY II official character page](https://na.finalfantasy.com/titles/finalfantasy2). Minwu is a white mage, Josef is a Salamand rebel ally, Gordon is a Kashuan prince, and Leila is a pirate captain. Visual costumes follow the approved project sources.

## Frame contract

Attack sheets use three columns by two rows, row-major: anticipation, windup, advance, impact, followthrough, recover. IDs are attack-01 through attack-06; durations are 100/120/70/90/110/150 ms (640 ms total).

Cast sheets use four columns in one row: gather, raise, release, settle. IDs are cast-01 through cast-04; durations are 160/180/100/200 ms (640 ms total).

Every descriptor requests group battle, exact lowercase character owner, 128x128 target, PPU 64, bottom-center pivot {x:0.5,y:0}, and a non-looping clip. Eight owner/clip pairs are unique. Full prompts, tool original paths, source dimensions, reference paths, official roster link and SHA256 hashes are in sibling prompt files and generation-record.json.

The existing global humanoid body-height cohort remains fixed at 60.177966570489886 native pixels. The pipeline handles shared strip scale, lower-body anchors, binary alpha and mechanical source extraction. The final exporter accepted all eight selected guest strips at this frozen cohort without changing existing production assets; final inventory and strict file/GIF verification passed in the pipeline.

## Source visual QA and revisions

All generated sheets were inspected in the image tool output for frame count, anatomy, identity and action chronology.

- Minwu attack moves an orb staff from ready through raised windup, forward swing/impact, low followthrough and recovery. Cast v2 keeps the staff fixed on his back while free hands gather, rise, release and settle. The first casting candidate visibly swapped the staff between hands; it is preserved and excluded.
- Josef performs one leftward punch. His fist advances to full extension, begins retracting in followthrough and returns to guard. The casting strip uses open hands; no weapon was introduced. Bald head, beard and broad build remain stable.
- Gordon performs one spear thrust rather than unrelated combat poses. The original attack footprint could fit only a 51.8648-pixel body height and would have shrunk the character. Compact v2 shortens the spear and tucks the cape while retaining the body poses; pipeline preflight reports an 80-pixel capacity, comfortably above the frozen 60.178-pixel requirement. The original is preserved/excluded. Casting keeps the spear inactive on his back.
- Leila performs ready -> overhead windup -> upper-left advance -> horizontal impact -> down-left followthrough -> recovery. Casting hands gather, rise, extend left and settle while the cutlass remains inactive at the side. Her purple hair, bandana and pirate clothing remain recognizable. An additional independent raw-source review confirmed the readability of Josef's punch and Leila's slash and found no obvious source anatomy issue.

These sources use a leftward combat orientation, with some three-quarter face/body presentation inherited from the approved project style. They are not strict flat-profile silhouettes. Cast and attack sources can differ slightly in cloth/head shape; normalization and frame review must distinguish intended motion from unwanted scale changes.

Preserved rejected candidates are listed in ArtSource/RemasterExpansion/guest-party/excluded-sources.json. There are currently ten source PNGs, eight selected sheets, and two excluded candidates.

## Native frame review

All eight normalized contacts under Review/remaster-expansion were independently inspected after final export: FRAME_SEQUENCE_CANDIDATE_PASS. Attack/cast head and body sizes match within each owner. Feet stay planted without whole-sprite baseline jumps; no obvious silhouette cuts, extra limbs or prop hand-swaps remain. Minwu staff motion, Josef straight punch, Gordon compact spear thrust and Leila descending slash preserve chronological phase order. All four casts gather, rise, release and settle.

Independent Pillow decoding confirms each native GIF is128x128, each attack has six unique frames, each cast has four unique frames, timing matches the exact640ms declarations, and no looping extension exists. Every one of the40 native PNGs has ground pixel y=125. ArtSource/RemasterExpansion/guest-party/visual-qa.json records final contact/GIF hashes and per-frame source/PNG evidence.

Remaining caveats: Gordon attack02/03 and casting gather/settle changes are subtle at native scale; cloth/head contours vary mildly with pose. Weapon held/inactive placement differs across attack and cast; separate stow/ready transitions are outside this source task. No new browser file-URL attempt was made. Perceived real-time smoothness, exact original-game fidelity, animation transitions and gameplay/Unity runtime remain unverified.


