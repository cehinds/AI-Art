# The score

The game's music is **written as code**: the notes live in
[`score/<id>.mjs`](score/) and `node tools/score/render.mjs` renders them on the
synthesizer in `tools/score/synth.mjs` into `common/music/<context>/<id>.mp3`
and rewrites `common/music/manifest.json`. Those files ship in the `common`
pack (`common-assets-v<N>.zip`, as `music/…`). No samples, soundfonts or
licensed music are involved. The brief each score answers is in
[PROMPTS.md](PROMPTS.md).

This folder and `tools/score/` moved here from cehinds/AshenSpire (its
`music/score/`, `music/PROMPTS.md`, `music/README.md` and `tools/score/`;
AshenSpire `docs/EXTERNAL-ASSETS-PLAN.md` step 9). The rest of this file is the
game folder's player notes, kept as they were: in the game, `music/` is the
folder a build serves beside the page.

## Changing the score

1. Edit or add `score/<id>.mjs` (`export const context = '<manifest key>'`,
   `export default` a `Score` from `tools/score/compose.mjs`).
2. `FFMPEG=/path/to/ffmpeg node tools/score/render.mjs [<id> …]` (ffmpeg on
   PATH works too). The scores read the game's beds (`src/content/music.js`)
   from an AshenSpire checkout: `ASHENSPIRE_DIR=/path/to/AshenSpire`, default
   `../AshenSpire` beside this repository (`tools/game.mjs`). Rendering is
   deterministic: the same score gives the same audio.
3. Commit the score, the MP3 and `common/music/manifest.json` together, then
   `node tools/manifest.mjs --write`.

`render.mjs --alt --out <dir>` renders the alt cut (`tools/score/alt.mjs`):
cello becomes a double bass, the game's heartbeat is brought forward, and the
reverb is tighter. It writes under `<dir>` and leaves the manifest alone.

## Setup

1. Put audio files (`.mp3` or `.ogg`) into the per-context subfolders below.
2. List them in [`manifest.json`](manifest.json) under the matching context.
3. In-game: **Settings → Audio → Music folder**, enter the path/URL to this
   folder (e.g. `music/` when the game is served from the project root, or a full
   `https://…` URL). Leave it blank to use this folder beside the page (or the
   built-in generated score where it cannot be fetched, e.g. `file://`).

The game fetches `<folder>/manifest.json`, then for each screen plays a **random
track** from that context's list, picking a fresh one each time the track ends —
so a set of tracks rotates with variety. A missing manifest, missing file, or
playback error falls back to the generated score for that context.

## Folder structure

```
music/
  manifest.json
  title/     one or more menu themes
  map/       overworld ambience (fallback for every region)
             region keys map-hollow-weald, map-pale-marches, map-cinder-reach,
             map-drowned-coast, map-ashen-crown: the map's music where you stand;
             a region left empty plays the plain `map` list
  combat/    normal battle tracks
  elite/     elite battle tracks
  boss/      boss battle tracks
  shop/      merchant theme
  rest/      shrine of grace theme
  victory/   run-cleared theme
```

## Example `manifest.json`

```json
{
  "combat": ["combat/ashen_duel.mp3", "combat/erdtree_clash.mp3"],
  "boss":   ["boss/watchful_omen.mp3"],
  "shop":   ["shop/merchant_of_grace.ogg"],
  "rest":   ["rest/lost_grace.mp3"]
}
```

## Notes

- **Local files:** when the game runs from a web server, a folder like `music/`
  served alongside it works directly. When you open the standalone
  `build/EldenSpire.html` from `file://`, most browsers block loading audio from
  arbitrary local paths — host the folder (any local static server, or a URL)
  and point the setting at that.
- **Licensing:** only add tracks you have the right to use. The built-in score is
  fully generated in-code, so the game ships with no third-party audio.
- **Cross-origin:** remote URLs must send permissive CORS headers to play.
