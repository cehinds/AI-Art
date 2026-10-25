#!/usr/bin/env node
// tools/import.mjs — import the packs' files from a cehinds/AshenSpire checkout
// (docs/ART-REPO-PLAN.md step 2 there; extended to three packs by
// docs/EXTERNAL-ASSETS-PLAN.md step 9).
//
//   node tools/import.mjs <path-to-AshenSpire-checkout>
//
// Reads the checkout's art-manifest.json (schema 2) and copies, from its
// committed tree, every file a record names:
//   · each art id's high file    assets/<rel>           → hd/assets/<rel>
//   · each art id's light twin   assets-mobile/<rel>    → light/assets/<rel>
//   · each common id             assets/fonts/*, music/, map-detail/ → common/<id>
//                                asset-data/fonts/OFL.txt → common/licenses/OFL.txt
// and, as before:
//   · art/                                     → art/
//   · assets/equipment/components/             → art/equipment-components/
//   · CREDITS.md                               → CREDITS.md, under a preamble that
//                                                maps the game's paths to this repo's
// then writes IMPORTED.json naming the source commit.
//
// hd/assets/, light/assets/ and common/ are cleared first: after an import they
// hold exactly what the checkout's manifest lists. art/ is merged (a file the
// game deleted is not deleted here). The light twins are taken as the game
// committed them; tools/mobile-art.mjs keeps a twin while the committed
// manifest says it was made from the current high file, so the import changes
// no light bytes, and --check proves the tree is complete and policy-sized.
//
// It refuses a checkout with uncommitted changes in any tree it reads, and
// refuses when a file is missing or differs from its recorded sha256: what lands
// here is exactly what that commit carried. Run node tools/manifest.mjs --write
// afterwards; its rows then equal the checkout's art-manifest.json rows.

import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { COMMON_DIR, HIGH_DIR, LICENSE_ID, LIGHT_DIR, LIGHT_PREFIX, canonicalBytes } from './manifest.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const LICENSE_SOURCE = 'asset-data/fonts/OFL.txt';
const CREDITS_PREAMBLE = `<!-- Added by tools/import.mjs in cehinds/AshenSpire-art; everything below the rule is AshenSpire's CREDITS.md, verbatim. -->

> **This is cehinds/AshenSpire's \`CREDITS.md\`, copied verbatim at the commit named in
> [\`IMPORTED.json\`](IMPORTED.json).** Its paths describe the game repository's layout.
> In this repository they are:
>
> | AshenSpire path | here | release zip |
> |---|---|---|
> | \`assets/…\` (art) | \`hd/assets/…\` | \`hd-assets-v<N>.zip\`, as \`assets/…\` |
> | \`assets-mobile/…\` | \`light/assets/…\` (made by \`tools/mobile-art.mjs\`) | \`light-assets-v<N>.zip\`, as \`assets-mobile/…\` |
> | \`assets/fonts/…\` | \`common/assets/fonts/…\` | \`common-assets-v<N>.zip\`, as \`assets/fonts/…\` |
> | \`asset-data/fonts/OFL.txt\` | \`common/licenses/OFL.txt\` | \`common-assets-v<N>.zip\`, as \`licenses/OFL.txt\` |
> | \`music/<context>/*.mp3\`, \`music/manifest.json\` | \`common/music/…\` | \`common-assets-v<N>.zip\`, as \`music/…\` |
> | \`music/score/\`, \`music/PROMPTS.md\`, \`music/README.md\` | \`art/music/…\` | none (authoring) |
> | \`map-detail/…\` | \`common/map-detail/…\` | \`common-assets-v<N>.zip\`, as \`map-detail/…\` |
> | \`assets/equipment/components/\` | \`art/equipment-components/\` | none (authoring) |
> | \`art/…\` | \`art/…\` | none (authoring) |
>
> \`asset-data/\`, \`src/\`, \`styles/\` and \`tools/\` paths not listed above are the game's and
> are not in this repository. **The \`[LICENSE](LICENSE)\` links below point at a file that
> is not here: they mean AshenSpire's \`LICENSE\`**
> (https://github.com/cehinds/AshenSpire/blob/main/LICENSE). Each release carries this
> file as \`CREDITS.md\` beside its zips.

---

`;

const src = process.argv[2] && resolve(process.argv[2]);
if (!src || !existsSync(join(src, 'art-manifest.json'))) {
  console.error('usage: node tools/import.mjs <path-to-AshenSpire-checkout>  (it must carry art-manifest.json)');
  process.exit(2);
}
const git = (...args) => execFileSync('git', ['-C', src, ...args], { encoding: 'utf8' }).trim();
const READS = ['art', 'assets', LIGHT_PREFIX, 'asset-data/fonts', 'music', 'map-detail', 'art-manifest.json', 'CREDITS.md'];
if (git('status', '--porcelain', '--', ...READS)) {
  console.error(`import: REFUSED — the checkout has uncommitted changes under ${READS.join(', ')}`);
  process.exit(1);
}
const commit = git('rev-parse', 'HEAD');
const manifest = JSON.parse(readFileSync(join(src, 'art-manifest.json'), 'utf8'));
if (manifest.schema !== 2) {
  console.error(`import: REFUSED — the checkout's art-manifest.json is schema ${manifest.schema}; this import reads schema 2`);
  process.exit(1);
}

// [from (in the checkout), to (here), record] for every file a record names.
const plan = [];
for (const [id, entry] of Object.entries(manifest.assets)) {
  if (entry.common) {
    const from = id === LICENSE_ID ? LICENSE_SOURCE : entry.common.path;
    plan.push([from, join(COMMON_DIR, entry.common.path), entry.common, id]);
    continue;
  }
  if (!entry.high || !entry.light) { plan.push([null, null, null, id]); continue; }
  plan.push([entry.high.path, join('hd', entry.high.path), entry.high, id]);
  plan.push([entry.light.path, join(LIGHT_DIR, entry.light.path.slice(LIGHT_PREFIX.length + 1)), entry.light, id]);
}
const bad = [];
const bytes = new Map();
for (const [from, to, rec, id] of plan) {
  if (!rec) { bad.push(`${id}: neither a common record nor a light and a high one`); continue; }
  const abs = join(src, from);
  if (!existsSync(abs)) { bad.push(`${id}: ${from} is missing`); continue; }
  const buf = canonicalBytes(abs);
  if (buf.length !== rec.bytes || createHash('sha256').update(buf).digest('hex') !== rec.sha256) { bad.push(`${id}: ${from} differs from art-manifest.json`); continue; }
  bytes.set(to, buf);
}
if (bad.length) {
  console.error(`import: REFUSED — ${bad.length} manifest entr${bad.length === 1 ? 'y' : 'ies'} did not match:`);
  for (const b of bad.slice(0, 20)) console.error(`  · ${b}`);
  process.exit(1);
}
for (const dir of [HIGH_DIR, LIGHT_DIR, COMMON_DIR]) rmSync(join(ROOT, dir), { recursive: true, force: true });
for (const [to, buf] of bytes) {
  const abs = join(ROOT, to);
  mkdirSync(dirname(abs), { recursive: true });
  writeFileSync(abs, buf);
}
cpSync(join(src, 'art'), join(ROOT, 'art'), { recursive: true });
const components = join(src, 'assets/equipment/components');
if (existsSync(components)) cpSync(components, join(ROOT, 'art/equipment-components'), { recursive: true });
writeFileSync(join(ROOT, 'CREDITS.md'), CREDITS_PREAMBLE + readFileSync(join(src, 'CREDITS.md'), 'utf8'));
const count = (pack) => Object.values(manifest.assets).filter((e) => e[pack]).length;
writeFileSync(join(ROOT, 'IMPORTED.json'), `${JSON.stringify({
  from: 'cehinds/AshenSpire',
  commit,
  assets: { high: count('high'), light: count('light'), common: count('common') },
  note: `hd/assets/, light/assets/ and common/ hold the files art-manifest.json listed at that commit (light from ${LIGHT_PREFIX}/, licenses/OFL.txt from ${LICENSE_SOURCE}); art/, art/equipment-components/ and CREDITS.md are merged from that commit's art/, assets/equipment/components/ and CREDITS.md.`,
}, null, 2)}\n`);
console.log(`import: OK — ${count('high')} high, ${count('light')} light and ${count('common')} common files, art/ and CREDITS.md from ${commit}`);
