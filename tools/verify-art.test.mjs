import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { verifyArchive } from './verify-art.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const original = JSON.parse(readFileSync(new URL('../asset-manifest.json', import.meta.url), 'utf8'));
const copy = () => structuredClone(original);

test('all imported art and source references verify', () => {
  const result = verifyArchive(root, original);
  assert.equal(result.images, 45);
  assert.equal(result.files, 51);
});

test('rejects modified content hashes', () => {
  const manifest = copy();
  manifest.files[0].sha256 = '0'.repeat(64);
  assert.throws(() => verifyArchive(root, manifest), /SHA-256 mismatch/);
});

test('rejects wrong original Git blobs', () => {
  const manifest = copy();
  manifest.files[0].gitBlobSha1 = '0'.repeat(40);
  assert.throws(() => verifyArchive(root, manifest), /Original Git blob mismatch/);
});

test('rejects missing branch provenance', () => {
  const manifest = copy();
  manifest.files[0].sources[0].commit = '0'.repeat(40);
  assert.throws(() => verifyArchive(root, manifest), /Unrecorded snapshot/);
});

test('rejects file paths outside the archive', () => {
  const manifest = copy();
  manifest.files[0].path = '../outside.svg';
  assert.throws(() => verifyArchive(root, manifest), /Path escapes archive/);
});

test('rejects duplicate destination paths', () => {
  const manifest = copy();
  manifest.files.push(manifest.files[0]);
  assert.throws(() => verifyArchive(root, manifest), /Duplicate path/);
});

test('rejects dropped images still referenced by source manifests', () => {
  const manifest = copy();
  manifest.files = manifest.files.filter(file => file.path !== 'assets/sprites/dovahkiin.svg');
  manifest.counts.uniqueImages--;
  assert.throws(() => verifyArchive(root, manifest), /Missing referenced image/);
});
