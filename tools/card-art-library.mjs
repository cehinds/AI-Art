#!/usr/bin/env node
// Copy the approved library exports into a new runtime namespace without
// re-encoding them or replacing any existing, different runtime image.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dimensions } from './manifest.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const library = 'art/card-art-library-60';
const check = process.argv.includes('--check');
assert(process.argv.slice(2).every(arg => arg === '--check'), 'usage: node tools/card-art-library.mjs [--check]');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const manifest = JSON.parse(readFileSync(resolve(root, library, 'manifest.json'), 'utf8'));
const expected = [];
for (const category of ['physical', 'magical']) {
  for (const type of ['attack', 'smash', 'counter', 'evade', 'sweep', 'defend']) {
    for (let variant = 1; variant <= 5; variant++) {
      expected.push(`${category}-${type}-${String(variant).padStart(2, '0')}`);
    }
  }
}
assert.deepEqual(manifest.assets.map(asset => asset.id).sort(), expected.sort(), 'exactly 60 unique library IDs required');
const rows = [];
for (const asset of [...manifest.assets].sort((a, b) => a.id.localeCompare(b.id))) {
  assert.equal(asset.id, `${asset.category}-${asset.type}-${String(asset.variant).padStart(2, '0')}`);
  assert.equal(asset.master, `masters/${asset.id}.png`);
  assert.equal(hash(readFileSync(resolve(root, library, asset.master))), asset.sha256, `${asset.id}: master hash`);
  assert.deepEqual(asset.exports.map(item => item.width).sort((a, b) => a - b), [512, 1024]);
  for (const item of [...asset.exports].sort((a, b) => a.width - b.width)) {
    const name = `${asset.id}-${item.width}.webp`;
    assert.equal(item.path, `exports/${asset.category}/${asset.type}/${name}`);
    assert.equal(item.height, item.width * 1.5);
    const source = `${library}/${item.path}`;
    const bytes = readFileSync(resolve(root, source));
    assert.equal(bytes.length, item.bytes, `${source}: byte count`);
    assert.equal(hash(bytes), item.sha256, `${source}: hash`);
    assert.deepEqual(dimensions(bytes, '.webp'), { width: item.width, height: item.height }, `${source}: dimensions`);
    const id = `assets/cards/library/${name}`;
    const target = resolve(root, 'hd', id);
    if (existsSync(target)) {
      assert.equal(hash(readFileSync(target)), item.sha256, `${id}: refusing to overwrite a different runtime image`);
    } else {
      assert(!check, `${id}: runtime export missing`);
    }
    rows.push({ id, source, master: `${library}/${asset.master}`, masterSha256: asset.sha256,
      high: { path: id, bytes: item.bytes, sha256: item.sha256, width: item.width, height: item.height } });
  }
}
const receipt = `${JSON.stringify({ schema: 1, sourceManifest: `${library}/manifest.json`,
  assetCount: 60, runtimeIdCount: 120, assets: rows }, null, 2)}\n`;
const receiptPath = resolve(root, library, 'runtime-assets.json');
if (check) {
  assert.equal(readFileSync(receiptPath, 'utf8').replace(/\r\n/g, '\n'), receipt, 'runtime receipt differs');
} else {
  // Validate every source and existing target before making any writes.
  mkdirSync(resolve(root, 'hd/assets/cards/library'), { recursive: true });
  for (const row of rows) {
    const target = resolve(root, 'hd', row.id);
    if (!existsSync(target)) copyFileSync(resolve(root, row.source), target);
  }
  writeFileSync(receiptPath, receipt);
}
console.log(`card library: OK — 60 masters, 120 byte-identical high exports${check ? ' verified' : ' installed'}`);
