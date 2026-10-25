#!/usr/bin/env node
// tools/manifest.mjs — art-manifest.json (schema 2): every id, every pack.
//
//   node tools/manifest.mjs --write    regenerate art-manifest.json from the trees
//   node tools/manifest.mjs --check    exit 1 when the manifest and the trees disagree
//
// THE THREE PACKS (cehinds/AshenSpire docs/EXTERNAL-ASSETS-PLAN.md §2):
//
//   pack     tree here            zip                       the record's `path`
//   high     hd/assets/<rel>      hd-assets-v<N>.zip        assets/<rel>
//   light    light/assets/<rel>   light-assets-v<N>.zip     assets-mobile/<rel>
//   common   common/<path>        common-assets-v<N>.zip    <path>
//
// An ART ID is the runtime path the game asks for, `assets/<rel>`. It has a
// `light` and a `high` record: the light twin is generated from the high file
// by tools/mobile-art.mjs. A COMMON ID (the fonts under assets/fonts/,
// licenses/OFL.txt, music/manifest.json and music/**/*.mp3, map-detail/**/*.webp)
// has one `common` record, the same file for every tier. Each record is
// `{path, bytes, sha256}`, plus `width` and `height` for an art record whose
// format carries them. A record's `path` is where the file sits in its zip.
//
// The light records keep the path AshenSpire gave them (`assets-mobile/…`), so
// the `assets` rows here are the same rows, byte for byte, as AshenSpire's own
// art-manifest.json for the same trees: the game's step 11 replaces its derived
// manifest with this one, and its readers need not change.
//
// THIS FILE IS NOT THE LIGHT TIER'S PROVENANCE. --write records whatever is on
// disk, so it cannot say whether a twin was re-encoded after its high file
// changed. tools/mobile-art.mjs keeps its own record (light/.twin-sources.json)
// and its --check fails on a twin made from another high file or policy.
// When hd/assets/ changes: node tools/mobile-art.mjs first, then --write here.
//
// DERIVED, NEVER HAND-EDITED. --check is a CI gate, and tools/pack.mjs refuses
// to pack while it is red. Text (SVG, JSON, the licence) is recorded by its LF
// form, so a CRLF checkout records the same bytes.

import { createHash } from 'node:crypto';
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, extname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { MIME, runtimeAsset } from './assetmime.mjs';
import { MOBILE_ASSET_DIR, webpDimensions } from './mobileart-policy.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const MANIFEST_PATH = 'art-manifest.json';
export const SCHEMA = 2;
export const PACKS = Object.freeze(['high', 'light', 'common']);
/** Where each pack's files live in this repository. */
export const HIGH_DIR = 'hd/assets';
export const LIGHT_DIR = 'light/assets';
export const COMMON_DIR = 'common';
/** The prefix a light record's path carries (AshenSpire's name for the light tree). */
export const LIGHT_PREFIX = MOBILE_ASSET_DIR;
/** Under assets/, the folder whose files are common ids, never art ids. */
export const COMMON_ASSET_PREFIX = 'fonts/';
export const LICENSE_ID = 'licenses/OFL.txt';

const sha256 = (buf) => createHash('sha256').update(buf).digest('hex');
const posix = (p) => p.split(/[\\/]/g).join('/');
const byteOrder = (a, b) => Buffer.compare(Buffer.from(a, 'utf8'), Buffer.from(b, 'utf8'));

/** True when a manifest entry is a `common` record rather than a light/high pair. */
export const isCommonEntry = (entry) => Boolean(entry && entry.common);

const TEXT_EXTS = new Set(['.svg', '.json', '.txt']);

/** The bytes a file is recorded and packed as: text with LF line endings, the rest untouched. */
export function canonicalBytes(abs) {
  const buf = readFileSync(abs);
  return TEXT_EXTS.has(extname(abs).toLowerCase())
    ? Buffer.from(buf.toString('utf8').replace(/\r\n?/g, '\n'), 'utf8')
    : buf;
}

/** Every file under dir, absolute, in byte order. A symlink or other non-file is an error. */
export function walk(dir, out = []) {
  if (!existsSync(dir)) return out;
  const entries = readdirSync(dir, { withFileTypes: true }).sort((a, b) => byteOrder(a.name, b.name));
  for (const e of entries) {
    const abs = join(dir, e.name);
    if (e.isDirectory()) walk(abs, out);
    else if (e.isFile()) out.push(abs);
    else throw new Error(`${abs} is neither a file nor a directory (a symlink?) — commit the file itself`);
  }
  return out;
}

/** The file in this repository a record of `pack` is read from. */
export function sourceOf(root, pack, rec) {
  if (pack === 'high') return resolve(root, 'hd', rec.path);
  if (pack === 'light') return resolve(root, LIGHT_DIR, rec.path.slice(LIGHT_PREFIX.length + 1));
  return resolve(root, COMMON_DIR, rec.path);
}

/** True when an assets/-relative path is art the game ships (AshenSpire's two rules). */
export const isArt = (rel) => runtimeAsset(rel) && Object.prototype.hasOwnProperty.call(MIME, extname(rel).toLowerCase());

/** Pixel size of an image payload, or null when the format carries none we read. */
export function dimensions(buf, ext) {
  if (ext === '.webp') {
    const d = webpDimensions(buf);
    return d ? { width: d.width, height: d.height } : null;
  }
  if (ext === '.png' && buf.length >= 24 && buf.toString('ascii', 12, 16) === 'IHDR') {
    return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
  }
  if (ext === '.gif' && buf.length >= 10 && buf.toString('ascii', 0, 3) === 'GIF') {
    return { width: buf.readUInt16LE(6), height: buf.readUInt16LE(8) };
  }
  if ((ext === '.jpg' || ext === '.jpeg') && buf.length >= 4 && buf[0] === 0xff && buf[1] === 0xd8) {
    let i = 2;
    while (i + 9 < buf.length && buf[i] === 0xff) {
      while (i + 9 < buf.length && buf[i + 1] === 0xff) i += 1;
      const marker = buf[i + 1];
      if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd8)) { i += 2; continue; }
      if (marker === 0xd9) return null;
      if (marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc) {
        return { width: buf.readUInt16BE(i + 7), height: buf.readUInt16BE(i + 5) };
      }
      i += 2 + buf.readUInt16BE(i + 2);
    }
    return null;
  }
  if (ext === '.svg') {
    const root = svgRootTag(buf.toString('utf8'));
    if (!root) return null;
    const attr = (name) => new RegExp(`\\s${name}\\s*=\\s*["']([^"']*)["']`, 'i').exec(root)?.[1];
    const px = (v) => (v !== undefined && /^\d+(?:\.\d+)?(?:px)?$/.test(v.trim()) ? Number.parseFloat(v) : null);
    const w = px(attr('width'));
    const h = px(attr('height'));
    if (w !== null && h !== null) return { width: w, height: h };
    const box = attr('viewBox')?.trim().split(/[\s,]+/).map(Number);
    return box && box.length === 4 && box.every(Number.isFinite) ? { width: box[2], height: box[3] } : null;
  }
  return null;
}

/**
 * The SVG document element's start tag, or null — AshenSpire's
 * tools/art-manifest.mjs svgRootTag, so both repositories record the same size.
 */
export function svgRootTag(text) {
  let i = text.charCodeAt(0) === 0xfeff ? 1 : 0;
  const skip = (close) => { const j = text.indexOf(close, i); return j < 0 ? -1 : j + close.length; };
  for (;;) {
    while (i < text.length && /\s/.test(text[i])) i += 1;
    if (text.startsWith('<?', i)) i = skip('?>');
    else if (text.startsWith('<!--', i)) i = skip('-->');
    else if (/^<!DOCTYPE/i.test(text.slice(i, i + 9))) {
      let depth = 0; let quote = null; let j = i + 9;
      for (; j < text.length; j++) {
        const c = text[j];
        if (!quote && depth > 0 && text.startsWith('<!--', j)) { const k = text.indexOf('-->', j + 4); if (k < 0) return null; j = k + 2; continue; }
        if (!quote && depth > 0 && text.startsWith('<?', j)) { const k = text.indexOf('?>', j + 2); if (k < 0) return null; j = k + 1; continue; }
        if (quote) { if (c === quote) quote = null; }
        else if (c === '"' || c === "'") quote = c;
        else if (c === '[') depth += 1;
        else if (c === ']') depth -= 1;
        else if (c === '>' && depth <= 0) break;
      }
      i = j < text.length ? j + 1 : -1;
    } else break;
    if (i < 0) return null;
  }
  const m = /^<svg\b(?:[^>"']|"[^"]*"|'[^']*')*>/i.exec(text.slice(i));
  return m ? m[0] : null;
}

/** An art record: path, bytes, sha256 and pixel size. */
export function fileRecord(abs, path) {
  const buf = canonicalBytes(abs);
  const dims = dimensions(buf, extname(abs).toLowerCase());
  return { path, bytes: buf.length, sha256: sha256(buf), ...(dims ? { width: dims.width, height: dims.height } : {}) };
}

/** A common record: path, bytes and sha256 only. */
export function commonRecord(abs, path) {
  const buf = canonicalBytes(abs);
  return { path, bytes: buf.length, sha256: sha256(buf) };
}

/**
 * commonFiles(root) → { files: [{ id, abs }], strays: [path] }: every file
 * under common/ that the common pack carries, and every one it does not
 * (reported by --check, so nothing there is dropped in silence).
 */
export function commonFiles(root = ROOT) {
  const base = resolve(root, COMMON_DIR);
  const files = [];
  const strays = [];
  for (const abs of walk(base)) {
    const id = posix(relative(base, abs));
    const ext = extname(id).toLowerCase();
    const ok = (id.startsWith(`assets/${COMMON_ASSET_PREFIX}`) && isArt(id.slice('assets/'.length)))
      || id === LICENSE_ID
      || id === 'music/manifest.json'
      || (id.startsWith('music/') && ext === '.mp3')
      || (id.startsWith('map-detail/') && ext === '.webp');
    (ok ? files : strays).push(ok ? { id, abs } : `${COMMON_DIR}/${id}`);
  }
  return { files, strays };
}

/**
 * commonConsistency(files) → problems: the common pack is whole. The fonts
 * never ship without their licence, and music/manifest.json names exactly the
 * MP3s the pack carries (every listed track is there; every track is listed).
 */
export function commonConsistency(files) {
  const problems = [];
  const ids = new Set(files.map((f) => f.id));
  if ([...ids].some((id) => id.startsWith(`assets/${COMMON_ASSET_PREFIX}`)) && !ids.has(LICENSE_ID)) {
    problems.push(`${COMMON_DIR}/${LICENSE_ID} is missing: the fonts (SIL OFL) must ship with their licence`);
  }
  const tracks = [...ids].filter((id) => id.startsWith('music/') && id.endsWith('.mp3'));
  const music = files.find((f) => f.id === 'music/manifest.json');
  if (!music) {
    if (tracks.length) problems.push(`${COMMON_DIR}/music/manifest.json is missing, but ${tracks.length} track(s) are present`);
    return problems;
  }
  let listed;
  try { listed = JSON.parse(canonicalBytes(music.abs).toString('utf8')); } catch (e) { return [...problems, `${COMMON_DIR}/music/manifest.json is not JSON: ${e.message}`]; }
  const named = new Set();
  for (const [context, list] of Object.entries(listed)) {
    if (context.startsWith('_')) continue;
    if (!Array.isArray(list)) { problems.push(`${COMMON_DIR}/music/manifest.json: "${context}" is not a list of tracks`); continue; }
    for (const rel of list) {
      const id = `music/${rel}`;
      named.add(id);
      if (!ids.has(id)) problems.push(`${COMMON_DIR}/music/manifest.json: "${context}" names ${rel}, which is not in ${COMMON_DIR}/music/`);
    }
  }
  for (const id of tracks) if (!named.has(id)) problems.push(`${COMMON_DIR}/${id}: no context in music/manifest.json plays it`);
  return problems;
}

/**
 * buildManifest(root) → { manifest, problems }. Ids come from hd/assets/ (the
 * source the light tree mirrors) and common/. A missing light twin is recorded
 * as `light: null` and reported, never left as a silent gap.
 */
export function buildManifest(root = ROOT) {
  const problems = [];
  const high = resolve(root, HIGH_DIR);
  const light = resolve(root, LIGHT_DIR);
  const assets = {};
  for (const abs of walk(high)) {
    const rel = posix(relative(high, abs));
    if (rel.startsWith(COMMON_ASSET_PREFIX)) { problems.push(`${HIGH_DIR}/${rel}: fonts are common ids — they live under ${COMMON_DIR}/assets/${COMMON_ASSET_PREFIX}`); continue; }
    if (!isArt(rel)) { problems.push(`${HIGH_DIR}/${rel}: not shippable art (tools/assetmime.mjs), so no pack would carry it`); continue; }
    const id = `assets/${rel}`;
    const twin = resolve(light, rel);
    assets[id] = {
      light: existsSync(twin) ? fileRecord(twin, `${LIGHT_PREFIX}/${rel}`) : null,
      high: fileRecord(abs, id),
    };
    if (!assets[id].light) problems.push(`${id}: no light twin under ${LIGHT_DIR}/ (node tools/mobile-art.mjs)`);
  }
  const { files, strays } = commonFiles(root);
  for (const s of strays) problems.push(`${s}: not a file the common pack carries (fonts, ${LICENSE_ID}, music/manifest.json, music/**/*.mp3, map-detail/**/*.webp)`);
  for (const { id, abs } of files) {
    if (assets[id]) { problems.push(`${id}: both an art id and a common id`); continue; }
    assets[id] = { common: commonRecord(abs, id) };
  }
  problems.push(...commonConsistency(files));
  const manifest = {
    _: 'DERIVED — written by node tools/manifest.mjs --write in cehinds/AshenSpire-art, never by a hand. One entry per asset id (the runtime `assets/…` path, or a `common` pack path: fonts, licenses/OFL.txt, music/, map-detail/). Each record\'s path is where the file sits in its pack\'s zip.',
    schema: SCHEMA,
    tiers: {
      placeholder: 'no file: the game draws the style guide recipe from the id',
      light: `${LIGHT_PREFIX}/ in light-assets-v<N>.zip (${LIGHT_DIR}/ in cehinds/AshenSpire-art, generated from ${HIGH_DIR}/ by tools/mobile-art.mjs) — the dev/test tier`,
      high: `assets/ in hd-assets-v<N>.zip (${HIGH_DIR}/ in cehinds/AshenSpire-art) — full resolution; release/main builds and the Local high-res setting`,
      common: `common-assets-v<N>.zip (${COMMON_DIR}/ in cehinds/AshenSpire-art) — one file for every tier: assets/${COMMON_ASSET_PREFIX} (the fonts), ${LICENSE_ID}, music/ and map-detail/`,
    },
    count: Object.keys(assets).length,
    assets,
  };
  return { manifest, problems };
}

/**
 * The bytes --write puts on disk: AshenSpire's art-manifest.json layout, the
 * header pretty-printed, then ONE LINE PER ID in id order.
 */
export function serialize(manifest) {
  const { assets, ...head } = manifest;
  const top = JSON.stringify(head, null, 2).replace(/\n}$/, '');
  const rows = Object.keys(assets).sort().map((id) => `    ${JSON.stringify(id)}: ${JSON.stringify(assets[id])}`);
  return `${top},\n  "assets": {\n${rows.join(',\n')}\n  }\n}\n`;
}

/** readManifest(root) → the committed manifest, parsed. */
export function readManifest(root = ROOT) {
  return JSON.parse(readFileSync(resolve(root, MANIFEST_PATH), 'utf8'));
}

/** checkManifest(root) → problems; empty means art-manifest.json is what --write writes. */
export function checkManifest(root = ROOT) {
  const path = resolve(root, MANIFEST_PATH);
  const { manifest, problems } = buildManifest(root);
  if (!existsSync(path)) return [...problems, `${MANIFEST_PATH} is missing — node tools/manifest.mjs --write`];
  let committed;
  try { committed = JSON.parse(readFileSync(path, 'utf8')); } catch (e) { return [...problems, `${MANIFEST_PATH} is not JSON: ${e.message}`]; }
  const have = committed.assets || {};
  const want = manifest.assets;
  for (const id of Object.keys(want)) {
    if (!have[id]) { problems.push(`${id}: in the trees but not in ${MANIFEST_PATH}`); continue; }
    for (const pack of isCommonEntry(want[id]) ? ['common'] : ['light', 'high']) {
      const a = have[id][pack];
      const b = want[id][pack];
      if (!b) continue; // reported above
      if (!a || a.sha256 !== b.sha256 || a.bytes !== b.bytes || a.path !== b.path) problems.push(`${id}: the ${pack} file changed since ${MANIFEST_PATH} was written`);
    }
  }
  for (const id of Object.keys(have)) if (!want[id]) problems.push(`${id}: in ${MANIFEST_PATH} but not in the trees`);
  if (!problems.length && serialize(manifest) !== readFileSync(path, 'utf8').replace(/\r\n?/g, '\n')) {
    problems.push(`${MANIFEST_PATH} differs from what --write produces (a field was edited by hand?)`);
  }
  return problems;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const report = (problems) => {
    console.error(`manifest: FAIL — ${problems.length} problem(s):`);
    for (const p of problems.slice(0, 20)) console.error(`  · ${p}`);
    if (problems.length > 20) console.error(`  … and ${problems.length - 20} more`);
  };
  if (args.includes('--write')) {
    const { manifest, problems } = buildManifest();
    if (problems.length) { report(problems); console.error('  Nothing was written.'); process.exit(1); }
    writeFileSync(resolve(ROOT, MANIFEST_PATH), serialize(manifest), 'utf8');
    console.log(`manifest: OK — ${manifest.count} ids written to ${MANIFEST_PATH}`);
  } else if (args.includes('--check')) {
    const problems = checkManifest();
    if (problems.length) { report(problems); console.error('  Fix: if hd/assets/ changed, node tools/mobile-art.mjs first (it re-encodes the light twins); then node tools/manifest.mjs --write'); process.exit(1); }
    console.log(`manifest: OK — ${readManifest().count} ids match the trees`);
  } else {
    console.error('usage: node tools/manifest.mjs --write | --check');
    process.exit(2);
  }
}
