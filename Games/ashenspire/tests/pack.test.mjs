// tests/pack.test.mjs — the zip format, the manifest and the three release packs, with known-bads.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { crc32, readZip, writeZip, extractZip } from '../tools/zip.mjs';
import { pack, packManifest, verifyZip, zipName } from '../tools/pack.mjs';
import { buildManifest, checkManifest, serialize } from '../tools/manifest.mjs';

const sha = (buf) => createHash('sha256').update(buf).digest('hex');
const tmp = () => mkdtempSync(join(tmpdir(), 'art-pack-'));

test('crc32 matches the standard check value', () => {
  assert.equal(crc32(Buffer.from('123456789')), 0xcbf43926);
});

// The known-good vector both repos pin (AshenSpire's tests/zip.test.mjs has the same one).
test('a two-entry zip has the pinned bytes, and reads back', () => {
  const dir = tmp();
  try {
    const out = join(dir, 'v.zip');
    writeZip(out, [{ name: 'b/two.txt', data: Buffer.from('two\n') }, { name: 'a.txt', data: Buffer.from('one\n') }]);
    const buf = readFileSync(out);
    assert.equal(sha(buf), 'dbe718937523d5bf1e635265ef5521109f596ec2e6762d8f01977032ea52c67c');
    assert.deepEqual(readZip(buf).map((e) => [e.name, e.data.toString()]), [['a.txt', 'one\n'], ['b/two.txt', 'two\n']]);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('known-bad: a flipped byte fails its CRC; a path that escapes is refused', () => {
  const dir = tmp();
  try {
    const out = join(dir, 'v.zip');
    writeZip(out, [{ name: 'a.txt', data: Buffer.from('one\n') }]);
    const buf = readFileSync(out);
    buf[30 + 'a.txt'.length] ^= 0xff;
    assert.throws(() => readZip(buf), /fails its CRC/);
    assert.throws(() => writeZip(join(dir, 'w.zip'), [{ name: '../x', data: Buffer.alloc(1) }]), /refusing entry name/);
    const evil = join(dir, 'e.zip');
    writeZip(evil, [{ name: 'ok.txt', data: Buffer.from('x') }]);
    const e = readFileSync(evil);
    // Rewrite the name in both headers to escape the target, and require extract to refuse.
    const i = e.indexOf('ok.txt'); const j = e.indexOf('ok.txt', i + 1);
    e.write('../bad', i, 'latin1'); e.write('../bad', j, 'latin1');
    writeFileSync(evil, e);
    assert.throws(() => extractZip(evil, join(dir, 'out')), /refusing entry name|escapes/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

// A throwaway repository: two art ids (a WebP and a CRLF SVG) with light twins,
// and one file of each common kind. The manifest is written as --write would.
function tree() {
  const root = tmp();
  const put = (rel, data) => { mkdirSync(join(root, rel, '..'), { recursive: true }); writeFileSync(join(root, rel), data); };
  put('release.json', '{ "version": 3 }\n');
  put('hd/assets/bg/a.webp', Buffer.from('RIFF-fake-webp-high'));
  put('hd/assets/bg/i.svg', '<svg viewBox="0 0 2 2">\r\n</svg>\r\n');
  put('light/assets/bg/a.webp', Buffer.from('RIFF-fake-webp-light'));
  put('light/assets/bg/i.svg', '<svg viewBox="0 0 2 2">\n</svg>\n');
  put('common/assets/fonts/x-400-normal.woff2', Buffer.from('wOF2-fake'));
  put('common/licenses/OFL.txt', 'SIL OPEN FONT LICENSE\r\n');
  put('common/music/manifest.json', '{ "combat": ["combat/c.mp3"] }\n');
  put('common/music/combat/c.mp3', Buffer.from('ID3-fake'));
  put('common/map-detail/0123456789abcdef/256/0-0.webp', Buffer.from('RIFF-fake-tile'));
  writeManifest(root);
  return root;
}
function writeManifest(root) {
  const { manifest, problems } = buildManifest(root);
  assert.deepEqual(problems, []);
  writeFileSync(join(root, 'art-manifest.json'), serialize(manifest));
}

test('the manifest lists art ids with light and high records and common ids with one record', () => {
  const root = tree();
  try {
    assert.deepEqual(checkManifest(root), []);
    const m = JSON.parse(readFileSync(join(root, 'art-manifest.json'), 'utf8'));
    assert.equal(m.schema, 2);
    assert.equal(m.count, 7);
    assert.deepEqual(Object.keys(m.assets['assets/bg/a.webp']), ['light', 'high']);
    assert.equal(m.assets['assets/bg/a.webp'].light.path, 'assets-mobile/bg/a.webp');
    assert.equal(m.assets['assets/bg/a.webp'].high.path, 'assets/bg/a.webp');
    assert.deepEqual(m.assets['assets/bg/i.svg'].high.width, 2, 'pixel size from the SVG viewBox');
    for (const id of ['assets/fonts/x-400-normal.woff2', 'licenses/OFL.txt', 'music/manifest.json', 'music/combat/c.mp3', 'map-detail/0123456789abcdef/256/0-0.webp']) {
      assert.deepEqual(Object.keys(m.assets[id]), ['common'], id);
      assert.equal(m.assets[id].common.path, id);
    }
    assert.equal(m.assets['licenses/OFL.txt'].common.bytes, 'SIL OPEN FONT LICENSE\n'.length, 'text recorded with LF');
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test('known-bad: the manifest refuses a font among the high art, a stray in common/, a missing twin, a stale row, fonts without their licence, and a music manifest that disagrees with the tracks', () => {
  const cases = [
    [(r) => writeFileSync(join(r, 'hd/assets/bg/b.webp'), 'new'), /assets\/bg\/b\.webp: no light twin/],
    [(r) => { mkdirSync(join(r, 'hd/assets/fonts'), { recursive: true }); writeFileSync(join(r, 'hd/assets/fonts/y.woff2'), 'f'); }, /fonts are common ids/],
    [(r) => writeFileSync(join(r, 'common/music/notes.md'), 'x'), /common\/music\/notes\.md: not a file the common pack carries/],
    [(r) => writeFileSync(join(r, 'light/assets/bg/a.webp'), 'changed'), /assets\/bg\/a\.webp: the light file changed/],
    [(r) => writeFileSync(join(r, 'common/music/combat/c.mp3'), 'changed'), /music\/combat\/c\.mp3: the common file changed/],

    [(r) => rmSync(join(r, 'common/licenses/OFL.txt')), /must ship with their licence/],
    [(r) => writeFileSync(join(r, 'common/music/manifest.json'), '{ "combat": ["combat/c.mp3", "combat/gone.mp3"] }\n'), /names combat\/gone\.mp3, which is not in common\/music/],
    [(r) => writeFileSync(join(r, 'common/music/combat/extra.mp3'), 'ID3'), /common\/music\/combat\/extra\.mp3: no context in music\/manifest\.json plays it/],
    [(r) => rmSync(join(r, 'common/music/manifest.json')), /music\/manifest\.json is missing, but 1 track/],
  ];
  for (const [plant, want] of cases) {
    const root = tree();
    try {
      plant(root);
      assert.match(checkManifest(root).join('\n'), want);
    } finally { rmSync(root, { recursive: true, force: true }); }
  }
});

test('pack writes three reproducible zips and the manifest; every zip verifies; text is LF', () => {
  const root = tree();
  try {
    const a = pack(root, join(root, 'out-a'));
    const b = pack(root, join(root, 'out-b'));
    const manifest = JSON.parse(readFileSync(join(root, 'art-manifest.json'), 'utf8'));
    assert.equal(readFileSync(a.manifestPath, 'utf8'), readFileSync(join(root, 'art-manifest.json'), 'utf8'), 'the release manifest is the committed one');
    const names = { high: 'hd-assets-v3.zip', light: 'light-assets-v3.zip', common: 'common-assets-v3.zip' };
    for (const [p, file] of Object.entries(names)) {
      assert.equal(zipName(p, 3), file);
      assert.equal(a.packs[p].sha256, b.packs[p].sha256, `${p} is reproducible`);
      assert.match(a.packs[p].zipPath, new RegExp(`${file.replace('.', '\\.')}$`));
      assert.equal(readFileSync(`${a.packs[p].zipPath}.sha256`, 'utf8'), `${a.packs[p].sha256}  ${file}\n`);
      assert.deepEqual(verifyZip(readFileSync(a.packs[p].zipPath), p, manifest), [], p);
    }
    const names_ = (p) => readZip(readFileSync(a.packs[p].zipPath)).map((e) => e.name);
    assert.deepEqual(names_('high'), ['art-manifest.json', 'assets/bg/a.webp', 'assets/bg/i.svg']);
    assert.deepEqual(names_('light'), ['art-manifest.json', 'assets-mobile/bg/a.webp', 'assets-mobile/bg/i.svg']);
    assert.deepEqual(names_('common'), ['art-manifest.json', 'assets/fonts/x-400-normal.woff2', 'licenses/OFL.txt', 'map-detail/0123456789abcdef/256/0-0.webp', 'music/combat/c.mp3', 'music/manifest.json']);
    const high = readZip(readFileSync(a.packs.high.zipPath));
    assert.ok(!high.find((e) => e.name === 'assets/bg/i.svg').data.toString().includes('\r'), 'SVG packed with LF');
    const embedded = JSON.parse(high.find((e) => e.name === 'art-manifest.json').data.toString());
    assert.equal(embedded.pack, 'high');
    assert.deepEqual(Object.keys(embedded.assets), ['assets/bg/a.webp', 'assets/bg/i.svg'], 'the high zip lists its own ids only');
    const common = readZip(readFileSync(a.packs.common.zipPath));
    assert.equal(common.find((e) => e.name === 'licenses/OFL.txt').data.toString(), 'SIL OPEN FONT LICENSE\n');
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test('known-bad: pack refuses while the manifest is stale', () => {
  const root = tree();
  try {
    writeFileSync(join(root, 'hd/assets/bg/a.webp'), 'edited after --write');
    assert.throws(() => pack(root, join(root, 'out')), (e) => /does not match the trees/.test(e.message) && /the high file changed/.test(e.problems.join('\n')));
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test('known-bad: a zip with a changed file, an extra file, a missing file or foreign rows is caught', () => {
  const root = tree();
  try {
    const r = pack(root, join(root, 'out'));
    const manifest = JSON.parse(readFileSync(join(root, 'art-manifest.json'), 'utf8'));
    const rezip = (p, change) => {
      const out = join(root, `bad-${p}.zip`);
      writeZip(out, change(readZip(readFileSync(r.packs[p].zipPath))));
      return verifyZip(readFileSync(out), p, manifest).join('\n');
    };
    assert.match(rezip('light', (e) => e.map((x) => (x.name === 'assets-mobile/bg/a.webp' ? { ...x, data: Buffer.from('other') } : x))), /assets\/bg\/a\.webp: the light zip's bytes differ/);
    assert.match(rezip('high', (e) => [...e, { name: 'assets/fonts/x-400-normal.woff2', data: Buffer.from('wOF2-fake') }]), /assets\/fonts\/x-400-normal\.woff2: in the high zip, not in its manifest/);
    assert.match(rezip('common', (e) => e.filter((x) => x.name !== 'music/combat/c.mp3')), /music\/combat\/c\.mp3: listed, not in the common zip/);
    // A zip that is consistent with itself but carries other rows than the release manifest.
    assert.match(rezip('common', (e) => {
      const sub = packManifest(manifest, 'common');
      delete sub.assets['music/combat/c.mp3'];
      sub.count -= 1;
      return e.filter((x) => x.name !== 'music/combat/c.mp3').map((x) => (x.name === 'art-manifest.json' ? { ...x, data: Buffer.from(serialize(sub)) } : x));
    }), /is not the release manifest's common rows/);
    assert.match(rezip('high', (e) => e.map((x) => (x.name === 'art-manifest.json' ? { ...x, data: Buffer.from(serialize(packManifest(manifest, 'light'))) } : x))), /says pack "light"/);
  } finally { rmSync(root, { recursive: true, force: true }); }
});
