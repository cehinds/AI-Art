import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const family = 'provenance/recipient-effects/v5';
const catalog = JSON.parse(readFileSync(resolve(root, family, 'recipient-effects-catalog.json'), 'utf8'));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const expected = ['advance','bleed-drops','block','block-break','block-hit','buff','counter','decay','debuff','earth','evade','fire','force','frost','heal','heal-plus','illusion','lightning','multi-slash','poise-break','poise-hit','retreat','skill','slash','smash','spell','spell-circle','status','status-apply','status-clear','status-resist','status-tick','sweep','thrust','ward'].sort();

test('approved recipient strips retain exact PNG bytes, three-frame layout and light twins', () => {
  assert.equal(catalog.schemaVersion, 1);
  assert.equal(catalog.frameCount, 3);
  assert.deepEqual(Object.keys(catalog.entries).sort(), expected);
  for (const tier of ['hd', 'light']) {
    assert.deepEqual(readdirSync(resolve(root, tier, 'assets/recipient-effects/v5')).sort(), expected.map(name => `${name}.png`).sort());
  }
  for (const [name, entry] of Object.entries(catalog.entries)) {
    assert.equal(entry.asset, `assets/recipient-effects/v5/${name}.png`);
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

test('original generated sources, prompts and extraction records retain catalog hashes', () => {
  assert.equal(Object.keys(catalog.provenance).length, 22);
  for (const [source, record] of Object.entries(catalog.provenance)) {
    assert.equal(record.path, `${family}/${source}`);
    assert.equal(digest(readFileSync(resolve(root, record.path))), record.sha256, source);
  }
  assert.equal(catalog.entries['evade-afterimage'], undefined, 'demonstration mask never ships');
});
