#!/usr/bin/env node
// tools/pack.mjs — build the three release packs and the manifest.
//
//   node tools/pack.mjs           write into dist/ (N from release.json):
//                                   hd-assets-v<N>.zip      + .sha256   the high tier
//                                   light-assets-v<N>.zip   + .sha256   the light tier
//                                   common-assets-v<N>.zip  + .sha256   fonts, licence, music, tiles
//                                   art-manifest.json                   every id, every pack
//   node tools/pack.mjs --check   pack twice into temp dirs, require identical bytes,
//                                 then read every zip back and verify it against
//                                 the manifest; exit 1 on any mismatch
//
// THE RELEASE LAYOUT (cehinds/AshenSpire docs/EXTERNAL-ASSETS-PLAN.md §2; read
// by that repository's tools/fetch-art.mjs and, from its step 11, by
// tools/asset-pack.mjs through the fetch cache):
//
//   art-manifest.json   (attached to the release) the committed manifest, byte
//                       for byte: schema 2, one row per id (tools/manifest.mjs)
//   each zip holds      art-manifest.json — that manifest's rows for this pack
//                       only, with `"pack": "<pack>"` in its header — and every
//                       file of the pack at its record's `path`:
//     hd-assets-v<N>.zip      assets/<…>          (each art id's `high` record)
//     light-assets-v<N>.zip   assets-mobile/<…>   (each art id's `light` record)
//     common-assets-v<N>.zip  assets/fonts/<…>, licenses/OFL.txt,
//                             music/manifest.json, music/<…>.mp3, map-detail/<…>
//
// An art id's row carries both its light and high records, so the high and
// light zips embed the same rows; the common zip embeds the common rows. The
// high zip is the one the game already knows: unpacked as `hd/` beside the
// game, its embedded manifest lists every id with a high file, and
// fetch-art.mjs accepts it as it accepts hd-assets-v1 (common ids absent from
// the high zip are not the high release's to carry).
//
// Every file is hashed as it is packed and must match its record, and the
// pack refuses to start while tools/manifest.mjs --check is red, so a zip
// never carries bytes the manifest does not describe. Text (SVG, JSON, the
// licence) is packed with LF line endings. Zips are deterministic
// (tools/zip.mjs): the same trees always give the same bytes.

import { createHash } from 'node:crypto';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readZip, writeZip } from './zip.mjs';
import { MANIFEST_PATH, PACKS, canonicalBytes, checkManifest, isCommonEntry, readManifest, serialize, sourceOf } from './manifest.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

const sha256 = (buf) => createHash('sha256').update(buf).digest('hex');

/** The zip each pack is released as. The tag stays hd-assets-v<N> for all three. */
export function zipName(pack, version) {
  const stem = { high: 'hd', light: 'light', common: 'common' }[pack];
  if (!stem) throw new Error(`pack: unknown pack ${JSON.stringify(pack)}`);
  return `${stem}-assets-v${version}.zip`;
}

export function releaseVersion(root = ROOT) {
  const v = JSON.parse(readFileSync(join(root, 'release.json'), 'utf8')).version;
  if (!Number.isInteger(v) || v < 1) throw new Error('release.json: "version" must be a positive integer');
  return v;
}

/** True when a manifest entry belongs in `pack`'s zip. */
const inPack = (entry, pack) => (pack === 'common' ? isCommonEntry(entry) : Boolean(entry && !isCommonEntry(entry) && entry[pack]));

/** The manifest a pack's zip embeds: the release manifest's header, `pack`, and this pack's rows. */
export function packManifest(manifest, pack) {
  const assets = {};
  for (const id of Object.keys(manifest.assets || {})) if (inPack(manifest.assets[id], pack)) assets[id] = manifest.assets[id];
  const { _, schema, tiers } = manifest;
  return { _, schema, pack, tiers, count: Object.keys(assets).length, assets };
}

/**
 * pack(root, outDir, version) → { packs: { high|light|common: { zipPath, sha256,
 * bytes, files } }, manifestPath }.
 */
export function pack(root = ROOT, outDir = join(root, 'dist'), version = releaseVersion(root)) {
  const stale = checkManifest(root);
  if (stale.length) {
    throw Object.assign(new Error(`${MANIFEST_PATH} does not match the trees (node tools/manifest.mjs --write); nothing was packed`), { problems: stale });
  }
  const manifest = readManifest(root);
  mkdirSync(outDir, { recursive: true });
  const packs = {};
  for (const name of PACKS) {
    const sub = packManifest(manifest, name);
    if (!sub.count) throw new Error(`pack: the ${name} pack is empty`);
    const entries = [{ name: MANIFEST_PATH, data: Buffer.from(serialize(sub), 'utf8') }];
    for (const [id, entry] of Object.entries(sub.assets)) {
      const rec = entry[name];
      entries.push({
        name: rec.path,
        data: () => {
          const buf = canonicalBytes(sourceOf(root, name, rec));
          if (buf.length !== rec.bytes || sha256(buf) !== rec.sha256) throw new Error(`pack: ${id}: the ${name} file changed while packing`);
          return buf;
        },
      });
    }
    const file = zipName(name, version);
    const zipPath = join(outDir, file);
    const { bytes } = writeZip(zipPath, entries);
    const digest = sha256(readFileSync(zipPath));
    writeFileSync(`${zipPath}.sha256`, `${digest}  ${file}\n`);
    packs[name] = { zipPath, sha256: digest, bytes, files: sub.count };
  }
  const manifestPath = join(outDir, MANIFEST_PATH);
  writeFileSync(manifestPath, serialize(manifest));
  return { packs, manifestPath };
}

/**
 * verifyZip(zipBuf, pack, manifest?) → problems; empty means every entry
 * matches the manifest the zip carries, nothing else is in it, and (given the
 * release manifest) the embedded rows are exactly that manifest's rows for the
 * pack.
 */
export function verifyZip(zipBuf, pack, manifest = null) {
  const problems = [];
  let entries;
  try { entries = readZip(zipBuf); } catch (e) { return [e.message]; }
  const byName = new Map(entries.map((e) => [e.name, e.data]));
  const text = byName.get(MANIFEST_PATH);
  if (!text) return [`the ${pack} zip has no ${MANIFEST_PATH}`];
  let embedded;
  try { embedded = JSON.parse(text.toString('utf8')); } catch { return [`the ${pack} zip's ${MANIFEST_PATH} is not JSON`]; }
  if (embedded.pack !== pack) problems.push(`the ${pack} zip's ${MANIFEST_PATH} says pack ${JSON.stringify(embedded.pack)}`);
  const ids = Object.keys(embedded.assets || {});
  if (embedded.count !== ids.length) problems.push(`the ${pack} zip's manifest says count ${embedded.count} but lists ${ids.length}`);
  const listed = new Set();
  for (const id of ids) {
    const rec = inPack(embedded.assets[id], pack) ? embedded.assets[id][pack] : null;
    if (!rec) { problems.push(`${id}: no ${pack} record in the ${pack} zip's manifest`); continue; }
    listed.add(rec.path);
    const data = byName.get(rec.path);
    if (!data) { problems.push(`${id}: listed, not in the ${pack} zip`); continue; }
    if (data.length !== rec.bytes || sha256(data) !== rec.sha256) problems.push(`${id}: the ${pack} zip's bytes differ from its manifest`);
  }
  for (const name of byName.keys()) if (name !== MANIFEST_PATH && !listed.has(name)) problems.push(`${name}: in the ${pack} zip, not in its manifest`);
  if (manifest && serialize(packManifest(manifest, pack)) !== text.toString('utf8')) {
    problems.push(`the ${pack} zip's ${MANIFEST_PATH} is not the release manifest's ${pack} rows`);
  }
  return problems;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const fail = (e) => {
    console.error(`pack: FAIL — ${e.message}`);
    for (const p of (e.problems || []).slice(0, 20)) console.error(`  · ${p}`);
    if ((e.problems || []).length > 20) console.error(`  … and ${e.problems.length - 20} more`);
    process.exit(1);
  };
  if (process.argv.includes('--check')) {
    const a = mkdtempSync(join(tmpdir(), 'pack-a-'));
    const b = mkdtempSync(join(tmpdir(), 'pack-b-'));
    try {
      const first = pack(ROOT, a);
      const second = pack(ROOT, b);
      const manifest = readManifest(ROOT);
      const problems = [];
      if (readFileSync(first.manifestPath, 'utf8') !== readFileSync(join(ROOT, MANIFEST_PATH), 'utf8').replace(/\r\n?/g, '\n')) {
        problems.push(`the release's ${MANIFEST_PATH} is not the committed one`);
      }
      for (const name of PACKS) {
        if (first.packs[name].sha256 !== second.packs[name].sha256) problems.push(`two packs of the same trees differ (${name}): ${first.packs[name].sha256} vs ${second.packs[name].sha256}`);
        // Read back and check the second copy, so the bytes verified are bytes a
        // fresh run wrote, not the ones the first run still held.
        problems.push(...verifyZip(readFileSync(second.packs[name].zipPath), name, manifest));
      }
      if (problems.length) throw Object.assign(new Error(`${problems.length} problem(s)`), { problems });
      for (const name of PACKS) {
        const p = first.packs[name];
        console.log(`  ${name.padEnd(6)} ${relative(a, p.zipPath).padEnd(24)} ${String(p.files).padStart(5)} files  ${String(p.bytes).padStart(10)} bytes  sha256 ${p.sha256}`);
      }
      console.log(`pack: OK — 3 zips reproducible, every entry verifies against ${MANIFEST_PATH} (${manifest.count} ids)`);
    } catch (e) {
      fail(e);
    } finally {
      rmSync(a, { recursive: true, force: true });
      rmSync(b, { recursive: true, force: true });
    }
  } else {
    try {
      const r = pack();
      for (const [name, p] of Object.entries(r.packs)) console.log(`pack: wrote ${relative(ROOT, p.zipPath)} — ${p.files} files, ${p.bytes} bytes, sha256 ${p.sha256} (${name})`);
      console.log(`pack: wrote ${relative(ROOT, r.manifestPath)}`);
    } catch (e) { fail(e); }
  }
}
