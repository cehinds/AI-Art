# Enemy sprite integration handoff — 2026-10-09

Owner request: integrate the current package into the game on `dev`, merge what exists, and leave a handoff. Enemy direction is toward the viewer, angled slightly **screen-left**. The player's intended direction is screen-right; player artwork is outside this package.

## Package

- 33 canonical enemies, 24 independently painted poses each: 792 transparent frames.
- Per enemy: attack (4), counterattack (4), magic attack (3), physical ranged attack (2), sweep (4), block (2), wounded, hit, defeated, preparing and idle.
- Six sequences use a 260 ms authoring duration; runtime scales to the existing action window. The stage introduces no gameplay delay or mechanical events.
- All exported frames use a 512-square canvas and floor at y=480. Source cells are smaller and have been upscaled; these are not native 512-detail paintings.
- Runtime paths: `assets/enemy-poses/expansion/<enemyId>/<pose>.webp`, resolved through the existing art-pack loader.
- Art authoring location: `AshenSpire-art/art/enemy-expansion-2026-10-09/`. The rebuild tool generates projects with embedded whole-pose layers, not articulated anatomy or weapon rigs.
- Local complete package: `D:/repos/.codex/outputs/sprite-expansion-2026-10-09/enemies`. Original preview at `http://127.0.0.1:8807/` while its local server runs.

## Runtime and coverage boundary

`src/ui/enemyExpansionStage.js` registers the shared stage for enemy sprites. Current HP, block and statuses select resting wounded, guard and afflicted art. Defeat remains terminal; reduced motion keeps a static pose. Committed action events select melee, physical ranged, spell and guard sequences through `src/model/enemyActionPose.js`; no future move or hidden-intent data is read.

Counterattack, sweep and preparing frames exist in the package. Their use depends on an explicit matching runtime call/family. Do not claim every enemy move now has a bespoke mapping. Status-effect art aliases wounded; guard-hit reuses block. Sleep/prone alias defeated when explicitly requested. Player sprite production remains separate.

## Known art work to continue

1. Review every contact sheet at game size and during playback. Generated metadata deliberately records zero owner-approved sets; automated alpha and boundary checks do not establish anatomy, grip or visual acceptance.
2. Repair source cell intersections, clipped weapon/effect tips and stray fragments. `manifest.json` records per-frame source-boundary flags. Soldier sweep-02/block-01 were repaired, but sweep-03/04 still need inspection.
3. Inspect Glass Regent and Valkyrie Shade for gray/cyan matte halos; inspect winged silhouettes and long spears for edge intersections.
4. Stitched King uses a fully clothed patchwork-armored variant. Its body design differs from the original exposed stitched figure and needs an explicit art decision before calling it canonical/approved.
5. Eclipse Cantor ranged-02 was replaced with a full-body physical-throw pose after the source cell contained only a projectile.
6. Continue angle-fidelity review: Stitched Hound idle remains more side-on than the supplied soldier reference. The target is front three-quarter/screen-left; generation is not owner acceptance. Validate on a physical phone.
7. The portable project schema passed validation. The earlier workshop browser screenshot remained at “Loading workshop”; do not treat it as a successful editor import. Serve `.mjs` with JavaScript MIME and verify actual project loading.

## Continue safely

Use the isolated game checkout `D:/repos/.codex/worktrees/enemy-sprite-integration/AshenSpire` and art checkout `D:/repos/.codex/worktrees/enemy-sprite-art`. Preserve the dirty primary checkout and the original reference checkout `D:/repos/.codex/worktrees/0460/AshenSpire` at `bcfa0eab3ef60681bb92106b9ada5480fd5ae602`.

Follow the art repository's normal PR/automatic pack publication, then pin the resulting release in the game. Regenerate `art-manifest.json` and build receipts with repository tooling. Merge only after review and required checks, then follow current `CONTRIBUTING.md` for `dev` → `test`. The retired root `alternative/dev` and `alternative/test` branches must remain frozen. This handoff does not authorize a game release or claim owner art acceptance.

### Rebuilding exports

Install `sharp@0.35.5` in your tooling environment, set `SHARP_MODULE` to that
module's absolute path if it is not locally resolvable, and run `node build.cjs`
from this folder. The checked-in local copy of Sprite Workshop `core.mjs`
validates the embedded project schema. The script regenerates PNG frames,
contact sheets and portable projects from the source sheets and overrides.
Do not treat cached visual flags as owner approval. The local original package
also contains the playback page and PNG exports; this repository preserves the
source sheets and rebuild tooling. Generated projects, contact sheets and PNG frames remain in the local complete package and can be recreated with the command above. The full export branch is preserved locally at f1ecc42 (codex/enemy-sprite-expansion). Omitting these duplicated exports does not change runtime pack hashes.
