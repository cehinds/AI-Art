import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

function inside(root, relativePath) {
  assert.equal(typeof relativePath, 'string', 'File path must be a string');
  assert(!relativePath.includes('\\') && !relativePath.includes(':'), `Non-portable path: ${relativePath}`);
  const target = path.resolve(root, relativePath);
  assert(target.startsWith(path.resolve(root) + path.sep), `Path escapes archive: ${relativePath}`);
  return target;
}

export function verifyArchive(root, manifest) {
  assert.equal(manifest.schemaVersion, 1, 'Unsupported manifest schema');
  assert.equal(manifest.sourceRepository, 'cehinds/ff2_core');
  assert.deepEqual(manifest.destination, { repository: 'cehinds/AI-Art', branch: 'Dovakiin' });
  const snapshots = new Map(manifest.snapshots.map(snapshot => [snapshot.branch, snapshot.commit]));
  const paths = new Set();
  let totalBytes = 0;
  for (const file of manifest.files) {
    assert(!paths.has(file.path.toLowerCase()), `Duplicate path: ${file.path}`);
    paths.add(file.path.toLowerCase());
    const bytes = readFileSync(inside(root, file.path));
    assert.equal(bytes.length, file.bytes, `Size mismatch: ${file.path}`);
    assert.equal(createHash('sha256').update(bytes).digest('hex'), file.sha256, `SHA-256 mismatch: ${file.path}`);
    assert.equal(createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex'), file.gitBlobSha1,
      `Original Git blob mismatch: ${file.path}`);
    assert(file.sources.length > 0, `Missing provenance: ${file.path}`);
    for (const source of file.sources) {
      assert.equal(source.commit, snapshots.get(source.branch), `Unrecorded snapshot: ${file.path}`);
      assert(/^[a-f0-9]{40}$/.test(source.commit), `Invalid commit: ${file.path}`);
      inside(root, source.path);
    }
    if (file.path.endsWith('.svg')) {
      const svg = bytes.toString('utf8');
      assert(/<svg\b[^>]*xmlns="http:\/\/www\.w3\.org\/2000\/svg"/.test(svg), `Invalid SVG: ${file.path}`);
      assert(svg.includes('</svg>'), `Incomplete SVG: ${file.path}`);
    } else if (file.path.endsWith('.png')) {
      assert(bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])), `Invalid PNG: ${file.path}`);
      assert.equal(bytes.subarray(12, 16).toString('ascii'), 'IHDR', `Missing PNG header: ${file.path}`);
    } else if (file.path.endsWith('.json')) {
      JSON.parse(bytes.toString('utf8'));
    }
    totalBytes += bytes.length;
  }
  assert.equal(snapshots.size, manifest.counts.branches, 'Branch count mismatch');
  assert.equal(manifest.files.filter(file => file.role === 'image').length, manifest.counts.uniqueImages);
  assert.equal(manifest.files.filter(file => file.role === 'art-definition').length, manifest.counts.artDefinitions);
  assert.equal(manifest.files.filter(file => file.role === 'source-documentation').length, manifest.counts.sourceDocuments);
  for (const [directory, property] of [['sprites', 'sprites'], ['bg', 'backgrounds']]) {
    const manifestPath = `assets/${directory}/manifest.json`;
    if (!paths.has(manifestPath)) continue;
    const entries = JSON.parse(readFileSync(inside(root, manifestPath), 'utf8'))[property];
    assert(Array.isArray(entries), `Invalid ${directory} manifest`);
    for (const key of entries) {
      const candidates = ['svg', 'png', 'jpg', 'jpeg', 'webp'].map(ext => `assets/${directory}/${key}.${ext}`);
      assert(candidates.some(candidate => paths.has(candidate.toLowerCase()) && existsSync(inside(root, candidate))),
        `Missing referenced image: ${directory}/${key}`);
    }
  }
  return { files: manifest.files.length, images: manifest.counts.uniqueImages, branches: snapshots.size, bytes: totalBytes };
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const root = fileURLToPath(new URL('../', import.meta.url));
  const manifest = JSON.parse(readFileSync(path.join(root, 'asset-manifest.json'), 'utf8'));
  const result = verifyArchive(root, manifest);
  console.log(`PASS: ${result.files} imported files, ${result.images} images, ${result.branches} branch snapshots; ${result.bytes} bytes verified.`);
}
