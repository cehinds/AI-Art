#!/usr/bin/env node
// Reproduce the library's WebP derivatives; PNG masters and manifest are read-only.
// Usage: node export.mjs [--sharp /path/to/node_modules/sharp]
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const root = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
if (args.length && (args.length !== 2 || args[0] !== '--sharp' || !args[1])) {
  throw new Error('Usage: node export.mjs [--sharp /path/to/node_modules/sharp]');
}
const sharp = require(args.length ? path.resolve(args[1]) : 'sharp');
const manifest = JSON.parse(await readFile(path.join(root, 'manifest.json'), 'utf8'));
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const sameHash = (actual, expected) =>
  typeof expected === 'string' && actual === expected.toLowerCase();
function localPath(relative, prefix) {
  if (typeof relative !== 'string' || !relative.startsWith(prefix + '/')) {
    throw new Error('Unexpected library path: ' + relative);
  }
  const resolved = path.resolve(root, relative);
  const within = path.relative(root, resolved);
  if (!within || within.startsWith('..') || path.isAbsolute(within)) {
    throw new Error('Path escapes library: ' + relative);
  }
  return resolved;
}
if (!Array.isArray(manifest.assets) || manifest.assets.length !== manifest.count) {
  throw new Error('Invalid manifest asset count');
}
for (const name of ['sharp', 'webp']) {
  if (manifest.encoder?.[name] && manifest.encoder[name] !== sharp.versions[name]) {
    throw new Error('Encoder version mismatch: ' + name + ' needs ' +
      manifest.encoder[name] + ', installed ' + sharp.versions[name]);
  }
}
let created = 0;
let verified = 0;
const paths = new Set();
for (const asset of manifest.assets) {
  const master = await readFile(localPath(asset.master, 'masters'));
  if (!sameHash(sha256(master), asset.sha256)) {
    throw new Error('Master SHA256 mismatch: ' + asset.id);
  }
  const metadata = await sharp(master).metadata();
  if (metadata.width !== 1024 || metadata.height !== 1536) {
    throw new Error('Master must be 1024x1536: ' + asset.id);
  }
  if (!Array.isArray(asset.exports) || asset.exports.length !== 2 ||
      new Set(asset.exports.map(item => item.width)).size !== 2) {
    throw new Error('Expected exactly two export sizes: ' + asset.id);
  }
  for (const item of asset.exports) {
    if (![512, 1024].includes(item.width) || item.height !== item.width * 1.5) {
      throw new Error('Unexpected export dimensions: ' + item.path);
    }
    const destination = localPath(item.path, 'exports');
    const key = process.platform === 'win32' ? destination.toLowerCase() : destination;
    if (paths.has(key)) throw new Error('Duplicate export path: ' + item.path);
    paths.add(key);
    const encoded = await sharp(master)
      .resize(item.width, item.height)
      .webp({ quality: item.width === 512 ? 84 : 88, effort: 6 })
      .toBuffer();
    if (encoded.length !== item.bytes || !sameHash(sha256(encoded), item.sha256)) {
      throw new Error('Encoded bytes differ from manifest: ' + item.path);
    }
    try {
      const existing = await readFile(destination);
      if (!existing.equals(encoded)) {
        throw new Error('Existing file differs; refusing to overwrite: ' + item.path);
      }
      verified++;
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
      await mkdir(path.dirname(destination), { recursive: true });
      // Exclusive creation also protects a file added after the read above.
      await writeFile(destination, encoded, { flag: 'wx' });
      created++;
    }
  }
}
console.log(JSON.stringify({
  mastersVerified: manifest.assets.length, exportsVerified: verified, exportsCreated: created,
  encoder: { sharp: sharp.versions.sharp, webp: sharp.versions.webp }
}));
