import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const reviewedCatalogs = [
  ['v5', ['advance','bleed-drops','block','block-break','block-hit','buff','counter','decay','debuff','earth','evade','fire','force','frost','heal','heal-plus','illusion','lightning','multi-slash','poise-break','poise-hit','retreat','skill','slash','smash','spell','spell-circle','status','status-apply','status-clear','status-resist','status-tick','sweep','thrust','ward'], 22],
  ['v6', ['bind', 'blight', 'counter-gain', 'evade-gain', 'frail', 'magic-vulnerable', 'mirrors', 'poison', 'reflect', 'vulnerable', 'ward-shatter', 'weak'], 9],
];

for (const [version, shapes, provenanceCount] of reviewedCatalogs) {
  const namespace = `recipient-effects/${version}`;
  const family = `provenance/${namespace}`;
  const catalog = JSON.parse(readFileSync(resolve(root, family, 'recipient-effects-catalog.json'), 'utf8'));
  const expected = [...shapes].sort();

  test(`${version} approved recipient strips retain exact PNG bytes, three-frame layout and light twins`, () => {
    assert.equal(catalog.schemaVersion, 1);
    assert.equal(catalog.catalog, namespace);
    assert.equal(catalog.frameCount, 3);
    assert.deepEqual(Object.keys(catalog.entries).sort(), expected);
    for (const tier of ['hd', 'light']) {
      assert.deepEqual(readdirSync(resolve(root, tier, `assets/${namespace}`)).sort(), expected.map(name => `${name}.png`).sort());
    }
    for (const [name, entry] of Object.entries(catalog.entries)) {
      assert.equal(entry.asset, `assets/${namespace}/${name}.png`);
      assert.deepEqual([entry.columns, entry.rows, entry.row], [3, 1, 0]);
      assert.deepEqual(entry.frameSize, [256, 256]);
      for (const tier of ['hd', 'light']) {
        assert.equal(entry.tiers[tier], `${tier}/${entry.asset}`);
        const png = readFileSync(resolve(root, entry.tiers[tier]));
        assert.equal(digest(png), entry.sha256, `${tier}/${name} approved bytes`);
        assert.equal(png.subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
        assert.equal(png.readUInt32BE(16), 768);
        assert.equal(png.readUInt32BE(20), 256);
        assert.equal(png[25], 6, `${tier}/${name} RGBA`);
      }
    }
  });

  test(`${version} generated sources and prompts retain catalog hashes`, () => {
    assert.equal(Object.keys(catalog.provenance).length, provenanceCount);
    for (const [source, record] of Object.entries(catalog.provenance)) {
      assert.equal(record.path, `${family}/${source}`);
      assert.equal(digest(readFileSync(resolve(root, record.path))), record.sha256, source);
    }
    assert.equal(catalog.entries['evade-afterimage'], undefined, 'demonstration mask never ships');
  });
}
