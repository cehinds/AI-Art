// tests/mobile-art.test.mjs — the light tier's provenance record and the
// --out guard, with the known-bads the PR #3 review found.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { POLICY, policyFor, twinDimensions } from '../tools/mobileart-policy.mjs';
import { OUT_MARKER, guardOut, keepable, policyDigest, readSources, runtimeArt, serializeSources, sourceRow, verify } from '../tools/mobile-art.mjs';
import { buildManifest, checkManifest, serialize } from '../tools/manifest.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const tmp = () => mkdtempSync(join(tmpdir(), 'mobile-art-test-'));

/** A syntactically valid VP8L WebP header of the given size, padded with `fill`. */
function fakeWebp(width, height, bytes = 64, fill = 0) {
  const buf = Buffer.alloc(Math.max(bytes, 30), fill);
  buf.write('RIFF', 0, 'ascii');
  buf.writeUInt32LE(buf.length - 8, 4);
  buf.write('WEBP', 8, 'ascii');
  buf.write('VP8L', 12, 'ascii');
  buf.writeUInt32LE(buf.length - 20, 16);
  buf[20] = 0x2f;
  buf.writeUInt32LE(((width - 1) & 0x3fff) | (((height - 1) & 0x3fff) << 14), 21);
  return buf;
}

// A repository whose one art id was encoded by mobile-art: twin, record and manifest all current.
function repo() {
  const root = tmp();
  const put = (rel, data) => { mkdirSync(dirname(join(root, rel)), { recursive: true }); writeFileSync(join(root, rel), data); };
  put('hd/assets/poses/x.webp', fakeWebp(200, 100, 900, 1));       // "the reaver"
  const small = twinDimensions({ width: 200, height: 100 }, policyFor('poses/x.webp'));
  put('light/assets/poses/x.webp', fakeWebp(small.width, small.height, 700, 1));
  const twins = {};
  for (const { rel, abs } of runtimeArt(join(root, 'hd/assets'))) twins[rel] = sourceRow(abs, join(root, 'light/assets', rel), rel);
  put('light/.twin-sources.json', serializeSources(twins));
  const { manifest } = buildManifest(root);
  put('art-manifest.json', serialize(manifest));
  return { root, put };
}
const check = (root, opts = {}) => verify(join(root, 'hd/assets'), join(root, 'light/assets'), { sources: readSources(join(root, 'light/.twin-sources.json')), ...opts }).findings;

test('a freshly encoded tree with its record passes, and its twins are kept', () => {
  const { root } = repo();
  try {
    assert.deepEqual(check(root), []);
    assert.deepEqual([...keepable(runtimeArt(join(root, 'hd/assets')), join(root, 'light/assets'), readSources(join(root, 'light/.twin-sources.json')))], ['poses/x.webp']);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

// B1, the review's exact sequence: the high file is replaced by another
// picture of the same size, `manifest --check` says to run --write, --write
// runs, and only then mobile-art. Before the fix the twin was kept and every
// check stayed green.
test('known-bad (B1): manifest --write before mobile-art no longer launders a stale twin', () => {
  const { root, put } = repo();
  try {
    put('hd/assets/poses/x.webp', fakeWebp(200, 100, 900, 2));      // "the rogue", same size
    assert.match(checkManifest(root).join('\n'), /the high file changed/);
    writeFileSync(join(root, 'art-manifest.json'), serialize(buildManifest(root).manifest));
    assert.deepEqual(checkManifest(root), [], 'the manifest is green again — it cannot tell');
    const sources = readSources(join(root, 'light/.twin-sources.json'));
    assert.equal(keepable(runtimeArt(join(root, 'hd/assets')), join(root, 'light/assets'), sources).size, 0, 'mobile-art re-encodes it');
    assert.match(check(root).join('\n'), /made from a different high file.*poses\/x\.webp/, 'mobile-art --check goes red');
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test('known-bad (N1): a policy change invalidates the twins it governs, and only those', () => {
  const { root } = repo();
  try {
    const stricter = { ...POLICY, overrides: POLICY.overrides.map(row => row.prefixes.includes('poses/') ? { ...row, quality: row.quality + 5 } : row) };
    assert.notEqual(policyDigest('poses/x.webp', stricter), policyDigest('poses/x.webp'));
    assert.equal(policyDigest('poses/y.webp', { ...POLICY, quality: 1 }), policyDigest('poses/y.webp'), 'an override path is governed by its override');
    assert.match(check(root, { policy: stricter }).join('\n'), /made under another policy.*poses\/x\.webp/);
    assert.equal(keepable(runtimeArt(join(root, 'hd/assets')), join(root, 'light/assets'), readSources(join(root, 'light/.twin-sources.json')), stricter).size, 0);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test('new card compression stays isolated from sprites and existing card artwork', () => {
  assert.deepEqual([policyFor('cards/extended/card-strike-1024.webp').maxEdge, policyFor('cards/extended/card-strike-1024.webp').quality], [720,44]);
  assert.equal(policyFor('cards/slashing-strike-512.webp').quality,50);
  const changed={...POLICY,overrides:POLICY.overrides.map(row=>row.prefixes.includes('cards/extended/')?{...row,quality:row.quality+1}:row)};
  assert.notEqual(policyDigest('cards/extended/card-strike-1024.webp',changed),policyDigest('cards/extended/card-strike-1024.webp'));
  assert.equal(policyDigest('poses/x.webp',changed),policyDigest('poses/x.webp'));
  assert.equal(policyDigest('cards/slashing-strike-512.webp',changed),policyDigest('cards/slashing-strike-512.webp'));
});

test('all sprite and scenery families share the 256 px ceiling', () => {
  const families = ['animations', 'sprites', 'poses', 'painted-outfits', 'readiness-poses', 'enemy-poses', 'enemy-states', 'defeated-poses', 'enemies-unity', 'enemies-expansion', 'combat-effects', 'pose-effects', 'equipment'];
  for (const family of families) {
    const policy = policyFor(`${family}/frame.webp`);
    assert.deepEqual([policy.maxEdge, policy.quality, policy.alphaQuality], [256, 12, 25]);
    assert.deepEqual(twinDimensions({ width: 200, height: 100 }, policy), { width: 200, height: 100 }, 'under 256 px keeps its size');
    assert.deepEqual(twinDimensions({ width: 512, height: 256 }, policy), { width: 256, height: 128 });
  }
  assert.deepEqual(twinDimensions({ width: 640, height: 640 }, policyFor('animations/bow/herald/BOW-01.webp')), { width: 256, height: 256 });
  assert.deepEqual(twinDimensions({ width: 1, height: 1 }, policyFor('poses/tiny.webp')), { width: 1, height: 1 });
  assert.equal(policyFor('environments/wide.webp').maxHeight, 256);
  assert.deepEqual(twinDimensions({ width: 1536, height: 1024 }, policyFor('environments/wide.webp')), { width: 256, height: 171 });
});

test('a scenery height-only policy change invalidates scenery provenance, not sprite twins', () => {
  const changed={...POLICY,overrides:POLICY.overrides.map(row=>row.prefixes.includes('bg/')?{...row,maxHeight:600}:row)};
  assert.notEqual(policyDigest('bg/title.webp',changed),policyDigest('bg/title.webp'));
  assert.equal(policyDigest('poses/x.webp',changed),policyDigest('poses/x.webp'));
  assert.equal(policyDigest('cards/extended/card-strike.webp',changed),policyDigest('cards/extended/card-strike.webp'));
});

test('known-bad: a twin edited by hand, a missing row and a missing record are each red', () => {
  const cases = [
    [({ put }) => put('light/assets/poses/x.webp', fakeWebp(200, 100, 700, 9)), /changed since .* recorded it/],
    [({ put }) => put('light/.twin-sources.json', serializeSources({})), /has no row in/],
    [({ root }) => rmSync(join(root, 'light/.twin-sources.json')), /\.twin-sources\.json is missing/],
  ];
  for (const [plant, want] of cases) {
    const r = repo();
    try {
      plant(r);
      assert.match(check(r.root).join('\n'), want);
    } finally { rmSync(r.root, { recursive: true, force: true }); }
  }
});

test('the committed light tree has a current record for every twin', () => {
  assert.deepEqual(verify(join(ROOT, 'hd/assets'), join(ROOT, 'light/assets'), { sources: readSources(join(ROOT, 'light/.twin-sources.json')) }).findings, []);
});

// N2: --all --out cleared whatever it was given.
test('known-bad (N2): --out refuses the repository, its trees, a full directory and a symlink', () => {
  const outside = tmp();
  try {
    for (const bad of ['.', 'hd/assets', 'light/assets', 'tools', 'dist']) assert.throws(() => guardOut(join(ROOT, bad), ROOT), /inside the repository only under dist\//, bad);
    mkdirSync(join(outside, 'full'));
    writeFileSync(join(outside, 'full/keep.txt'), 'mine');
    assert.throws(() => guardOut(join(outside, 'full'), ROOT), /not empty/);
    writeFileSync(join(outside, 'full', OUT_MARKER), 'a same-named file is not the marker\n');
    assert.throws(() => guardOut(join(outside, 'full'), ROOT), /not empty/);
    symlinkSync(join(ROOT, 'hd'), join(outside, 'link'));
    assert.throws(() => guardOut(join(outside, 'link', 'assets'), ROOT), /inside the repository/);
    assert.equal(guardOut(join(outside, 'new'), ROOT), join(outside, 'new'));
    mkdirSync(join(outside, 'empty'));
    assert.ok(guardOut(join(outside, 'empty'), ROOT));
    assert.ok(guardOut(join(ROOT, 'dist/regen-test-not-created'), ROOT));
    // Through the CLI: refused before any encoder is looked for, nothing deleted.
    const r = spawnSync(process.execPath, [join(ROOT, 'tools/mobile-art.mjs'), '--all', '--out', '.'], { cwd: ROOT, encoding: 'utf8' });
    assert.equal(r.status, 2);
    assert.match(r.stderr, /REFUSED/);
    assert.ok(existsSync(join(ROOT, 'hd/assets')) && existsSync(join(ROOT, 'tools/mobile-art.mjs')));
    assert.equal(readFileSync(join(outside, 'full/keep.txt'), 'utf8'), 'mine');
  } finally { rmSync(outside, { recursive: true, force: true }); }
});
