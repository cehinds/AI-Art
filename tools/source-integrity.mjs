// Source PNG/provenance assertions moved with the original class-smash assets.
// No image decoding or metadata-only substitute: every declared source is hashed.
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const SOURCE_ACTORS = ['rogue', 'starseer', 'herald'];
export function verifyClassSmashSources(root = ROOT, actors = SOURCE_ACTORS) {
  const checked = new Map();
  const bytes = (path, actor) => {
    const prefix = 'pose-studio/stances/class-smash/' + actor + '/';
    if (typeof path !== 'string' || !path.startsWith(prefix) || path.includes('\\')
        || path.split('/').some((part) => !part || part === '.' || part === '..')) throw new Error('Invalid source package path: ' + path);
    const absolute = resolve(root, path);
    if (!absolute.startsWith(resolve(root) + sep)) throw new Error('Source path escapes root');
    return readFileSync(absolute);
  };
  const check = (path, expected, actor) => {
    if (!/^[0-9a-f]{64}$/.test(expected || '')) throw new Error('Invalid source hash: ' + path);
    const data = bytes(path, actor);
    const sha = createHash('sha256').update(data).digest('hex');
    if (sha !== expected) throw new Error('Source bytes changed: ' + path);
    checked.set(path, sha);
  };
  for (const actor of actors) {
    if (!SOURCE_ACTORS.includes(actor)) throw new Error('Unknown source actor');
    const path = 'pose-studio/stances/class-smash/' + actor + '/production.json';
    const production = JSON.parse(bytes(path, actor));
    if (production.classId !== actor) throw new Error('Production actor mismatch: ' + actor);
    check(production.sourceProvenance, production.sourceProvenanceSha256, actor);
    const roles = Object.keys(production.frames || {}).sort();
    if (JSON.stringify(roles) !== JSON.stringify(['airborne','held','impact','takeoff'])) throw new Error('Expected all four original frame sources: ' + actor);
    for (const frame of Object.values(production.frames)) check(frame.source?.path, frame.source?.sha256, actor);
    const first = production.frames.held.source.path;
    if (!first.endsWith('/01-held.png')) throw new Error('Original first bookend path missing: ' + actor);
    const last = first.slice(0, -'01-held.png'.length) + '05-held.png';
    check(first, production.sourceBookends?.first, actor);
    check(last, production.sourceBookends?.last, actor);
    if (production.sourceBookends.first !== production.sourceBookends.last) throw new Error('Source bookends differ: ' + actor);
  }
  return { actors: actors.length, sourceFiles: checked.size };
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = verifyClassSmashSources();
  console.log('Source integrity: ' + result.actors + ' actors; ' + result.sourceFiles + ' original PNG/provenance files hash-verified.');
}
