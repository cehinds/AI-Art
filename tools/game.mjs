// tools/game.mjs — where an AshenSpire checkout is, for the authoring tools
// that still read the game's own content.
//
// Two authoring tools moved here from cehinds/AshenSpire read game data they
// do not own: the score (art/music/score/_motifs.mjs) keeps the game's tempo,
// key and walk by reading src/content/music.js, and tools/map-detail-build.mjs
// reads the tile policy in src/content/mapPresentation.js. That data stays in
// the game, so these tools read it from a checkout rather than from a copy that
// could drift (AshenSpire docs/ART-REPO-PLAN.md: "a path setting").
//
//   ASHENSPIRE_DIR=/path/to/AshenSpire   the checkout (default: ../AshenSpire,
//                                        beside this repository)
//
// The checkout must hold every file these tools read (GAME_FILES). The one in
// use, and its commit, are printed once, so a stale checkout is visible. A
// missing checkout or file ends the tool with one line naming ASHENSPIRE_DIR,
// not a stack trace. Only these authoring tools need it; packing, the light
// tier and CI do not.

import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
/** Every file of the game's that a tool here imports. */
export const GAME_FILES = Object.freeze(['src/content/music.js', 'src/content/mapPresentation.js']);

let announced = false;

/** Print one line and stop: the tools cannot run without the game's content. */
function refuse(message) {
  console.error(`AshenSpire checkout: ${message}`);
  process.exit(1);
}

/** missingGameFiles(dir) → the GAME_FILES (and `also`) that dir lacks. */
export function missingGameFiles(dir, also = []) {
  return [...new Set([...GAME_FILES, ...also])].filter((rel) => !existsSync(resolve(dir, rel)));
}

/** The AshenSpire checkout these tools read; ends the process when it is not one. */
export function gameDir(also = []) {
  const dir = resolve(process.env.ASHENSPIRE_DIR || resolve(ROOT, '..', 'AshenSpire'));
  const missing = missingGameFiles(dir, also);
  if (missing.length) {
    refuse(`${dir} is missing ${missing.join(', ')} — set ASHENSPIRE_DIR to a cehinds/AshenSpire checkout (default ../AshenSpire beside this repository)`);
  }
  if (!announced) {
    announced = true;
    let commit = 'not a git checkout';
    try { commit = execFileSync('git', ['-C', dir, 'rev-parse', '--short', 'HEAD'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); } catch { /* reported as such */ }
    console.error(`AshenSpire checkout: ${dir} (${commit})`);
  }
  return dir;
}

/** A file: URL for a module in the checkout, for `await import(...)`. */
export function gameModule(rel) {
  return pathToFileURL(resolve(gameDir([rel]), rel)).href;
}
