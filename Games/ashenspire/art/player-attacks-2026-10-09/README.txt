PLAYER ATTACK SPRITE PACKAGE — 2026-10-09

36 sequences / 144 distinct frame files. 32 visually reviewed candidates; four spear sets need repair. No missing coverage cells, but spear quality is incomplete. Owner approval and runtime acceptance remain pending.

OPEN PREVIEW: http://127.0.0.1:8847/
Offline: open index.html directly. To use Sprite Workshop, run python serve.py, then open the URL above.

DELIVERABLES
frames/<class>/<weapon>/<phase>.png — 512x512 RGBA exports
sheets/<class>-<weapon>.png — 2048x512 transparent sheets
contacts/ — labeled four-frame contact sheets
projects/<class>.rig.json — four embedded-art portable Sprite Workshop projects
workshop/ — portable editor runtime; Reaver is the starter. Open other projects via File > Open project.
manifest.json — every action, pose, duration, event, provenance, alias, review finding and hash
qa/visual-review.json — visual observations and limitations
qa/file-validation.json — decode, alpha, bounds and unique-art checks
source/ — built-in imagegen prompts, generated sheets, repair attempts and rejected versions
references/ — copied canonical default appearance references

AUTHORING
Every sequence has four independent paintings: anticipation, strike/release, follow-through, recovery. No transformed duplicates substitute for poses. 128 final frames were newly generated; 16 reuse existing painted Reaver sword, Herald shield, Rogue dual-dagger and Starseer casting artwork. Stable IDs use <class>.<weapon>.attack.<phase>. Timings vary by weapon and are explicit in the manifest. Reused-source aliases are listed under sharedPoseAliases; no cross-weapon aliases are implied.

Editable projects contain full painted figure layers, floor anchors, animation sets and queues. They do not claim independently painted hidden limbs or editable weapon partitions. Sprite Workshop can cut/import parts, edit timing and save revisions; hidden surfaces would require further artwork.

REVIEW
All 36 sets received contact-sheet review. Browser review checked frame stepping, playback, alpha on light/dark backgrounds and small 256px canvases. The responsive game has no single fixed actor size; runtime validation remains outside this authoring task. Four spear sequences remain provisional because support-hand/shaft transitions do not read convincingly after repair attempts. No source checkout was edited; no integration, merge, promotion or publication occurred.

COVERAGE (four frames in every cell)
REAVER: greatsword [REVIEWED CANDIDATE], sword-shield [REVIEWED CANDIDATE], bow [REVIEWED CANDIDATE], staff-casting [REVIEWED CANDIDATE], energy-blade [REVIEWED CANDIDATE], spear [NEEDS REPAIR], dual-daggers [REVIEWED CANDIDATE], single-dagger [REVIEWED CANDIDATE], single-sword [REVIEWED CANDIDATE]
STARSEER: greatsword [REVIEWED CANDIDATE], sword-shield [REVIEWED CANDIDATE], bow [REVIEWED CANDIDATE], staff-casting [REVIEWED CANDIDATE], energy-blade [REVIEWED CANDIDATE], spear [NEEDS REPAIR], dual-daggers [REVIEWED CANDIDATE], single-dagger [REVIEWED CANDIDATE], single-sword [REVIEWED CANDIDATE]
HERALD: greatsword [REVIEWED CANDIDATE], sword-shield [REVIEWED CANDIDATE], bow [REVIEWED CANDIDATE], staff-casting [REVIEWED CANDIDATE], energy-blade [REVIEWED CANDIDATE], spear [NEEDS REPAIR], dual-daggers [REVIEWED CANDIDATE], single-dagger [REVIEWED CANDIDATE], single-sword [REVIEWED CANDIDATE]
ROGUE: greatsword [REVIEWED CANDIDATE], sword-shield [REVIEWED CANDIDATE], bow [REVIEWED CANDIDATE], staff-casting [REVIEWED CANDIDATE], energy-blade [REVIEWED CANDIDATE], spear [NEEDS REPAIR], dual-daggers [REVIEWED CANDIDATE], single-dagger [REVIEWED CANDIDATE], single-sword [REVIEWED CANDIDATE]