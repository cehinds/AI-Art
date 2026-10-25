#!/usr/bin/env node
// tools/mobile-art.mjs — hd/assets/ → light/assets/, and the proof the light
// tree is complete. Moved from cehinds/AshenSpire (where it made assets-mobile/
// from assets/; docs/EXTERNAL-ASSETS-PLAN.md step 9). The policy is
// tools/mobileart-policy.mjs, kept aligned with the game's copy (the art repo
// lists the same sprite families locally instead of importing game runtime code).
//
//   node tools/mobile-art.mjs            bring light/assets/ up to date: encode a
//                                        twin for every high file that is new or
//                                        changed, keep the rest, drop strays
//                                        (needs `cwebp` from libwebp on PATH)
//   node tools/mobile-art.mjs --all      re-encode every twin
//   node tools/mobile-art.mjs --all --out <dir>
//                                        re-encode every twin into <dir> instead,
//                                        leaving light/assets/ alone (to compare).
//                                        <dir> must be outside the repository or
//                                        under dist/, and new, empty, or one an
//                                        earlier --out wrote (its marker file)
//   node tools/mobile-art.mjs --check    every runtime asset has a twin of the
//                                        policy's size, made from the current
//                                        high file under the current policy
//                                        (light/.twin-sources.json), nothing
//                                        else is there, and the tree fits the
//                                        budget. Node core only — CI runs it.
//   node tools/mobile-art.mjs --selftest the check catches its known-bads
//
// WHY A COMMITTED TREE AND NOT A BUILD STEP. Node cannot encode WebP, and two
// libwebp versions do not agree byte for byte, so the shrinking happens here,
// by whoever changes art, and the result is committed beside hd/assets/. CI
// proves what can be proven without an encoder: the light tree is a complete,
// correctly sized mirror of the runtime art.
//
// WHY IT KEEPS TWINS (not in the game's copy, which rewrote every twin).
// light/.twin-sources.json is this tool's own provenance record: per twin, the
// sha256 of the high file it was made from, its own sha256, and a digest of
// the policy it was made under (policyDigest: the rule policyFor gives that
// path, plus how this tool encodes). Only this tool writes it, as it encodes.
// A twin whose record names the current high file, its current bytes and the
// current policy is kept as it is: an art change re-encodes only the twins it
// touches, a policy change re-encodes the twins it governs, and a different
// cwebp on the next machine never rewrites the other 5,000.
//
// The record is deliberately NOT art-manifest.json: that file is rewritten
// from the trees by tools/manifest.mjs --write, which cannot know whether a
// twin was re-encoded, so trusting it kept a stale twin (the wrong picture)
// after `manifest --write` ran first. --check now fails on any twin whose
// record does not name the current high file and policy.
//
// The record was seeded once, when the light tier was imported byte-identical
// from AshenSpire's assets-mobile/ (dev 52503a0a7), from that commit's
// art-manifest.json rows. It includes the 224 bow twins AshenSpire's bow importer
// wrote directly (Pillow, not this encoder): they are recorded under today's
// policy, so they are kept until their source or the bow policy changes, and
// --all re-encodes them. After any change: node tools/manifest.mjs --write.
//
// FONTS are `common` ids (common/assets/fonts/), not art with twins: they have
// no high or light file. They still count toward the light budget, because the
// light single file inlines them through its CSS.

import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync, statSync, mkdtempSync, lstatSync, readdirSync, realpathSync } from 'node:fs';
import { spawnSync, execFile } from 'node:child_process';
import { resolve, relative, dirname, extname, join, basename, isAbsolute, sep } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import {
  POLICY, MOBILE_ART_INLINED_BUDGET_BYTES,
  inlinedBytes, distinctInlinedBytes, webpDimensions, twinDimensions, policyFor,
} from './mobileart-policy.mjs';
import { COMMON_ASSET_PREFIX, COMMON_DIR, HIGH_DIR, LIGHT_DIR, canonicalBytes, isArt, walk } from './manifest.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const ARGV = process.argv.slice(2);
const has = (f) => ARGV.includes(f);
const flag = (f, d) => { const i = ARGV.indexOf(f); return i >= 0 && ARGV[i + 1] ? ARGV[i + 1] : d; };
const TREE = resolve(flag('--root', ROOT));
const SOURCE_DIR = resolve(TREE, HIGH_DIR);
const TWIN_DIR = resolve(TREE, LIGHT_DIR);
const FONT_DIR = resolve(TREE, COMMON_DIR, 'assets', COMMON_ASSET_PREFIX);

const posix = (p) => p.split(/[\\/]/g).join('/');
const sha256 = (buf) => createHash('sha256').update(buf).digest('hex');

// ---------------------------------------------------------------------------
// Provenance: which high file, and which policy, each twin was made from.
// ---------------------------------------------------------------------------
export const SOURCES_PATH = 'light/.twin-sources.json';
// How encodeOne turns a policy into bytes. Change this string whenever
// encodeOne's arguments or rules change, so every twin made the old way is
// re-encoded (or fails --check) rather than kept.
const ENCODER = 'cwebp -m 6 -q <quality> -alpha_q <alphaQuality> -alpha_filter best [-resize to maxEdge]; source kept when an unresized re-encode is not smaller; non-webp copied (v2)';

/** The digest of the rule a twin at `rel` is made under: policyFor(rel) and the encoder. */
export function policyDigest(rel, policy = POLICY) {
  const p = policyFor(rel, policy);
  const webp = extname(rel).toLowerCase() === '.webp';
  const rule = webp
    ? { encoder: ENCODER, maxEdge: p.maxEdge, maxHeight: p.maxHeight, quality: p.quality, alphaQuality: p.alphaQuality }
    : { encoder: ENCODER, copy: true };
  return sha256(Buffer.from(JSON.stringify(rule), 'utf8')).slice(0, 16);
}

/** The record { rel: { high, twin, policy } }, or null when the file is missing. */
export function readSources(path) {
  if (!existsSync(path)) return null;
  const parsed = JSON.parse(readFileSync(path, 'utf8'));
  return parsed && typeof parsed.twins === 'object' && parsed.twins ? parsed.twins : {};
}

/** The record's bytes: a header, then one line per twin in byte order. */
export function serializeSources(twins) {
  const rels = Object.keys(twins).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  const head = JSON.stringify({ _: 'WRITTEN BY tools/mobile-art.mjs as it encodes, never by hand or by tools/manifest.mjs. Per light twin: the sha256 of the hd/assets/ file it was made from, its own sha256, and the digest of the policy it was made under. --check fails when any of the three is not current.' }, null, 2).replace(/\n}$/, '');
  const rows = rels.map((rel) => `    ${JSON.stringify(rel)}: ${JSON.stringify({ high: twins[rel].high, twin: twins[rel].twin, policy: twins[rel].policy })}`);
  return `${head},\n  "twins": {\n${rows.join(',\n')}\n  }\n}\n`;
}

/** A record row for a twin made now from `srcAbs`. */
export function sourceRow(srcAbs, twinAbs, rel, policy = POLICY) {
  return { high: sha256(canonicalBytes(srcAbs)), twin: sha256(canonicalBytes(twinAbs)), policy: policyDigest(rel, policy) };
}

/**
 * keepable(wanted, twinDir, sources) → Set of rels whose twin the record says
 * was made from the current high file, is unchanged, and follows the current
 * policy. Nothing else is consulted: never art-manifest.json.
 */
export function keepable(wanted, twinDir, sources, policy = POLICY) {
  const keep = new Set();
  if (!sources) return keep;
  for (const { rel, abs } of wanted) {
    const rec = sources[rel];
    const twin = resolve(twinDir, rel);
    if (!rec || !existsSync(twin)) continue;
    const now = sourceRow(abs, twin, rel, policy);
    if (rec.high === now.high && rec.twin === now.twin && rec.policy === now.policy) keep.add(rel);
  }
  return keep;
}

// ---------------------------------------------------------------------------
// --out: never a directory this tool may not clear.
// ---------------------------------------------------------------------------
export const OUT_MARKER = '.mobile-art-out';
const OUT_MARKER_TEXT = 'Written by tools/mobile-art.mjs --all --out. Everything beside this file is cleared and rewritten on every such run.\n';

/** realOut(p) → p with every existing component resolved through symlinks. */
function realOut(p) {
  let head = resolve(p);
  const rest = [];
  while (!existsSync(head)) {
    const up = dirname(head);
    if (up === head) break;
    rest.unshift(basename(head));
    head = up;
  }
  return join(existsSync(head) ? realpathSync(head) : head, ...rest);
}

/**
 * guardOut(out, root) → the real directory --out may clear and write, or an
 * error. Inside the repository only under dist/ (ignored); anywhere, only a
 * directory that does not exist, is empty, or carries this tool's own marker.
 * So `.`, hd/assets, light/assets or a home directory are refused.
 */
export function guardOut(out, root = ROOT) {
  const realRoot = realOut(root);
  const real = realOut(out);
  const rel = relative(realRoot, real);
  const r = posix(rel);
  const outside = r === '..' || r.startsWith('../') || rel.startsWith(`..${sep}`) || isAbsolute(rel);
  if (!outside && !/^dist\/./.test(r)) {
    throw new Error(`--out ${r || '.'}: inside the repository only under dist/ (ignored); use dist/<name> or a directory outside the checkout`);
  }
  let st = null;
  try { st = lstatSync(real); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  if (!st) return real;
  if (st.isSymbolicLink() || !st.isDirectory()) throw new Error(`--out ${out}: not a plain directory`);
  const names = readdirSync(real);
  if (!names.length) return real;
  const marker = join(real, OUT_MARKER);
  let marked = false;
  try { marked = lstatSync(marker).isFile() && readFileSync(marker, 'utf8') === OUT_MARKER_TEXT; } catch { marked = false; }
  if (!marked) throw new Error(`--out ${out}: not empty, and not a directory an earlier --out wrote (no ${OUT_MARKER}); it will not be cleared`);
  return real;
}

/** Clear a guarded --out directory, keeping only a fresh marker. */
function prepareOut(real) {
  mkdirSync(real, { recursive: true });
  for (const name of readdirSync(real)) rmSync(join(real, name), { recursive: true, force: true });
  writeFileSync(join(real, OUT_MARKER), OUT_MARKER_TEXT, { flag: 'wx' });
}

/** Every high file that gets a twin: shippable art, fonts excluded (they are common ids). */
export function runtimeArt(srcDir) {
  return walk(srcDir)
    .map((abs) => ({ abs, rel: posix(relative(srcDir, abs)) }))
    .filter(({ rel }) => isArt(rel) && !rel.startsWith(COMMON_ASSET_PREFIX));
}

const canonicalText = (buf) => buf.toString('utf8').replace(/\r\n?/g, '\n');

/**
 * verify(srcDir, twinDir, { fontDir }) → { findings, checks, files, rawBytes, inlined }.
 * Pure over the directories; never throws on a bad tree, it names it.
 */
export function verify(srcDir, twinDir, { fontDir = null, sources, budget = MOBILE_ART_INLINED_BUDGET_BYTES, policy = POLICY, listAtMost = 5 } = {}) {
  // `sources`: the provenance record (readSources), null when its file is
  // missing, or undefined to skip provenance (a --out comparison tree).
  const findings = [];
  const missing = [];
  let checks = 0;
  let rawBytes = 0;
  let inlined = 0;
  const inlinedFiles = [];
  const wanted = runtimeArt(srcDir);
  const name = (rel) => `${LIGHT_DIR}/${rel}`;
  if (!wanted.length) findings.push(`no runtime art found under ${posix(relative(TREE, srcDir) || srcDir)} — nothing to twin`);
  const twins = new Set(walk(twinDir).map((abs) => posix(relative(twinDir, abs))).filter((rel) => rel !== OUT_MARKER));
  const prov = { none: [], source: [], twin: [], policy: [] };
  if (sources === null) findings.push(`${SOURCES_PATH} is missing: no twin can be shown to come from its high file`);
  for (const { rel, abs } of wanted) {
    checks += 1;
    if (!twins.has(rel)) { missing.push(name(rel)); continue; }
    twins.delete(rel);
    const src = readFileSync(abs);
    const out = readFileSync(resolve(twinDir, rel));
    rawBytes += out.length;
    inlinedFiles.push({ buf: out, ext: extname(rel) });
    if (sources) {
      const rec = sources[rel];
      if (!rec) prov.none.push(name(rel));
      else {
        const now = sourceRow(abs, resolve(twinDir, rel), rel, policy);
        if (rec.high !== now.high) prov.source.push(name(rel));
        else if (rec.twin !== now.twin) prov.twin.push(name(rel));
        else if (rec.policy !== now.policy) prov.policy.push(name(rel));
      }
    }
    if (extname(rel).toLowerCase() === '.webp') {
      const s = webpDimensions(src);
      const t = webpDimensions(out);
      if (!s) findings.push(`source is not a WebP the policy can size: ${HIGH_DIR}/${rel}`);
      else if (!t) findings.push(`twin is not a WebP: ${name(rel)}`);
      else {
        const want = twinDimensions(s, policyFor(rel, policy));
        if (t.width !== want.width || t.height !== want.height) {
          findings.push(`twin is ${t.width}×${t.height}, the policy wants ${want.width}×${want.height} of a ${s.width}×${s.height} source: ${name(rel)}`);
        }
      }
      // Only an UNRESIZED twin is held to its source's byte count (the encoder
      // keeps the source bytes when a same-size re-encode grows).
      const resized = s && t && (t.width !== s.width || t.height !== s.height);
      if (!resized && out.length > src.length) findings.push(`twin is larger than its source (${out.length} > ${src.length} bytes): ${name(rel)}`);
    } else {
      const same = extname(rel).toLowerCase() === '.svg' ? canonicalText(src) === canonicalText(out) : src.equals(out);
      if (!same) findings.push(`twin differs from a source the policy copies verbatim: ${name(rel)}`);
    }
  }
  if (missing.length) {
    findings.push(...missing.slice(0, listAtMost).map((m) => `missing twin: ${m}`));
    if (missing.length > listAtMost) findings.push(`… and ${missing.length - listAtMost} more missing twins`);
  }
  const say = (list, what) => {
    findings.push(...list.slice(0, listAtMost).map((n) => `${what}: ${n}`));
    if (list.length > listAtMost) findings.push(`… and ${list.length - listAtMost} more: ${what}`);
  };
  say(prov.none, `twin has no row in ${SOURCES_PATH} (nothing shows which high file it came from)`);
  say(prov.source, 'twin was made from a different high file than the one now in hd/assets/ (run node tools/mobile-art.mjs)');
  say(prov.twin, `twin changed since ${SOURCES_PATH} recorded it (only tools/mobile-art.mjs writes twins)`);
  say(prov.policy, 'twin was made under another policy than tools/mobileart-policy.mjs now gives it (run node tools/mobile-art.mjs)');
  if (sources) {
    const want = new Set(wanted.map((w) => w.rel));
    say(Object.keys(sources).filter((rel) => !want.has(rel)).sort(), `${SOURCES_PATH} names a twin with no source under ${HIGH_DIR}/`);
  }
  const stray = [...twins].sort();
  findings.push(...stray.slice(0, listAtMost).map((s) => `stray file with no source under ${HIGH_DIR}/: ${name(s)}`));
  if (stray.length > listAtMost) findings.push(`… and ${stray.length - listAtMost} more stray files`);
  checks += 1;
  // The light single file inlines each distinct image once, and every font face.
  inlined += distinctInlinedBytes(inlinedFiles);
  if (fontDir) for (const abs of walk(fontDir)) inlined += inlinedBytes(statSync(abs).size);
  if (inlined > budget) findings.push(`the light tree inlines to ${inlined} bytes, over the ${budget}-byte budget — tighten tools/mobileart-policy.mjs or cut art`);
  return { findings, checks, files: wanted.length, rawBytes, inlined };
}

// ---------------------------------------------------------------------------
// Generation — the only part that needs an encoder.
// ---------------------------------------------------------------------------
const run = promisify(execFile);

async function encodeOne(srcAbs, destAbs, rel, basePolicy) {
  const policy = policyFor(rel, basePolicy);
  const src = readFileSync(srcAbs);
  mkdirSync(dirname(destAbs), { recursive: true });
  if (extname(srcAbs).toLowerCase() !== '.webp') { writeFileSync(destAbs, src); return; }
  const dims = webpDimensions(src);
  if (!dims) throw new Error(`not a WebP: ${srcAbs}`);
  const want = twinDimensions(dims, policy);
  const resized = want.width !== dims.width || want.height !== dims.height;
  // No -mt: multithreaded encoding is what could make two runs disagree, and
  // the parallelism lives across files instead (WORKERS below).
  const args = ['-quiet', '-m', '6', '-q', String(policy.quality), '-alpha_q', String(policy.alphaQuality), '-alpha_filter', 'best'];
  if (resized) args.push('-resize', String(want.width), String(want.height));
  args.push(srcAbs, '-o', destAbs);
  await run('cwebp', args);
  // A re-encode at the same size that grew is worse than the source; keep the
  // source bytes. A resized one is always taken.
  if (!resized && statSync(destAbs).size >= src.length) writeFileSync(destAbs, src);
}

async function generate(srcDir, twinDir, { all = false, out = false, policy = POLICY } = {}) {
  const probe = spawnSync('cwebp', ['-version'], { encoding: 'utf8' });
  if (probe.error || probe.status !== 0) {
    console.error('mobile-art: cwebp is not on PATH — install libwebp (apt: webp; brew: webp; https://developers.google.com/speed/webp/download) and retry.');
    console.error('mobile-art: nothing was written. --check needs no encoder and still runs.');
    process.exit(2);
  }
  console.log(`mobile-art: cwebp ${probe.stdout.trim().split('\n')[0]} — policy q${policy.quality} alpha_q${policy.alphaQuality}, longer side at most ${policy.maxEdge}px (overrides per family)`);
  const wanted = runtimeArt(srcDir);
  const sourcesFile = resolve(TREE, SOURCES_PATH);
  const sources = out ? null : readSources(sourcesFile);
  const keep = all ? new Set() : keepable(wanted, twinDir, sources, policy);
  if (out) prepareOut(twinDir); // guarded by guardOut before we got here
  else if (all) rmSync(twinDir, { recursive: true, force: true });
  else {
    // Strays: a twin with no source is removed, so the tree mirrors hd/assets/.
    const want = new Set(wanted.map((w) => w.rel));
    for (const abs of walk(twinDir)) if (!want.has(posix(relative(twinDir, abs)))) rmSync(abs);
  }
  const todo = wanted.filter((w) => !keep.has(w.rel));
  let next = 0;
  let done = 0;
  // Independent single-threaded encoders retain deterministic file bytes.
  const WORKERS = 8;
  const worker = async () => {
    while (next < todo.length) {
      const item = todo[next++];
      await encodeOne(item.abs, resolve(twinDir, item.rel), item.rel, policy);
      done += 1;
      if (done % 500 === 0) console.log(`  ${done}/${todo.length}`);
    }
  };
  await Promise.all(Array.from({ length: WORKERS }, worker));
  if (!out) {
    // The record is rewritten whole: kept twins keep their row, encoded ones
    // get a new row, and a twin that left hd/assets/ leaves the record.
    const rows = {};
    for (const { rel, abs } of wanted) rows[rel] = keep.has(rel) ? sources[rel] : sourceRow(abs, resolve(twinDir, rel), rel, policy);
    mkdirSync(dirname(sourcesFile), { recursive: true });
    writeFileSync(sourcesFile, serializeSources(rows));
  }
  console.log(`mobile-art: encoded ${done} twin(s), kept ${keep.size} → ${posix(relative(TREE, twinDir))}`);
}

// ---------------------------------------------------------------------------
// Selftest — the check against a fixture whose right answer is typed here.
// ---------------------------------------------------------------------------
/** A syntactically valid VP8L WebP header of the given size, padded to `bytes`. */
function fakeWebp(width, height, bytes = 64) {
  const buf = Buffer.alloc(Math.max(bytes, 30));
  buf.write('RIFF', 0, 'ascii');
  buf.writeUInt32LE(buf.length - 8, 4);
  buf.write('WEBP', 8, 'ascii');
  buf.write('VP8L', 12, 'ascii');
  buf.writeUInt32LE(buf.length - 20, 16);
  buf[20] = 0x2f;
  buf.writeUInt32LE(((width - 1) & 0x3fff) | (((height - 1) & 0x3fff) << 14), 21);
  return buf;
}

function selftest() {
  const dir = mkdtempSync(join(tmpdir(), 'mobile-art-selftest-'));
  const src = resolve(dir, 'hd');
  const twin = resolve(dir, 'light');
  const fonts = resolve(dir, 'fonts');
  const put = (base, rel, bytes) => { const p = resolve(base, rel); mkdirSync(dirname(p), { recursive: true }); writeFileSync(p, bytes); };
  const big = twinDimensions({ width: 512, height: 512 }, policyFor('animations/x/ATK-01.webp', POLICY));
  const small = twinDimensions({ width: 600, height: 300 }, policyFor('poses/small.webp', POLICY));
  const backdrop = twinDimensions({ width: 1536, height: 1024 }, policyFor('environments/', POLICY));
  const good = () => {
    for (const d of [src, twin, fonts]) rmSync(d, { recursive: true, force: true });
    put(src, 'animations/x/ATK-01.webp', fakeWebp(512, 512, 4000));
    put(src, 'poses/small.webp', fakeWebp(600, 300, 900));
    put(src, 'bg/mask.svg', Buffer.from('<svg/>\r\n'));
    put(src, 'environments/wide.webp', fakeWebp(1536, 1024, 9000));
    put(src, 'equipment/components/experiment.webp', fakeWebp(512, 512, 4000)); // authoring-only: no twin wanted
    put(src, 'animations/README.md', Buffer.from('not art\n'));                 // no MIME: no twin wanted
    put(twin, 'animations/x/ATK-01.webp', fakeWebp(big.width, big.height, 800));
    put(twin, 'environments/wide.webp', fakeWebp(backdrop.width, backdrop.height, 2000));
    put(twin, 'poses/small.webp', fakeWebp(small.width, small.height, 700));
    put(twin, 'bg/mask.svg', Buffer.from('<svg/>\n'));
    put(fonts, 'a.woff2', Buffer.alloc(300));
    // The provenance record, as generate() writes it.
    sources = {};
    for (const { rel, abs } of runtimeArt(src)) sources[rel] = sourceRow(abs, resolve(twin, rel), rel, POLICY);
  };
  let sources = {};
  const stricter = { ...POLICY, overrides: POLICY.overrides.map(row => row.prefixes.includes('poses/') ? { ...row, quality: row.quality + 1 } : row) };
  const plants = [
    ['control: a complete twin tree passes', () => {}, null],
    ['a twin is missing', () => rmSync(resolve(twin, 'poses/small.webp')), /missing twin: light\/assets\/poses\/small\.webp/],
    ['a twin nothing sources', () => put(twin, 'poses/ghost.webp', fakeWebp(10, 10)), /stray file .*light\/assets\/poses\/ghost\.webp/],
    ['a big source was not shrunk', () => put(twin, 'animations/x/ATK-01.webp', fakeWebp(512, 512, 800)), new RegExp(`twin is 512×512, the policy wants ${big.width}×${big.height}`)],
    ['a backdrop shrunk below its 720 px ceiling', () => put(twin, 'environments/wide.webp', fakeWebp(480, 320, 2000)), new RegExp(`twin is 480×320, the policy wants ${backdrop.width}×${backdrop.height}`)],
    ['a cropped sprite escaped its 480 px ceiling', () => put(twin, 'poses/small.webp', fakeWebp(600, 300, 700)), new RegExp(`twin is 600×300, the policy wants ${small.width}×${small.height}`)],
    ['a twin grew past its source', () => put(twin, 'poses/small.webp', fakeWebp(600, 300, 901)), /larger than its source \(901 > 900 bytes\)/],
    ['a verbatim copy that is not verbatim', () => put(twin, 'bg/mask.svg', Buffer.from('<svg id="x"/>\n')), /differs from a source the policy copies verbatim/],
    ['a twin that is not a WebP', () => put(twin, 'poses/small.webp', Buffer.from('not a webp at all, but long enough to read')), /twin is not a WebP/],
    ['the tree is over budget', () => {}, /over the 1000-byte budget/, { budget: 1000 }],
    ['the fonts count toward the budget', () => put(fonts, 'b.woff2', Buffer.alloc(20000)), /over the 20000-byte budget/, { budget: 20000 }],
    ['an empty source tree', () => rmSync(src, { recursive: true, force: true }), /no runtime art found/],
    // Provenance: the review's sequence (art changed, manifest rewritten, twin
    // never re-encoded) — the same-size high file now holds another picture.
    ['a twin made from the old high file', () => put(src, 'poses/small.webp', fakeWebp(200, 100, 950)), /made from a different high file.*poses\/small\.webp/],
    ['a twin edited after it was recorded', () => put(twin, 'poses/small.webp', fakeWebp(200, 100, 650)), /changed since .* recorded it.*poses\/small\.webp/],
    ['a twin with no row in the record', () => { delete sources['poses/small.webp']; }, /has no row in .*poses\/small\.webp/],
    ['a record row for a source that left', () => { sources['poses/gone.webp'] = sources['poses/small.webp']; }, /names a twin with no source.*poses\/gone\.webp/],
    ['a policy change the kept twins were not made under', () => {}, /made under another policy/, { policy: stricter }],
    ['the record itself is missing', () => { sources = null; }, /\.twin-sources\.json is missing/],
  ];
  let bad = 0;
  let caught = 0;
  for (const [label, plant, want, opts] of plants) {
    good();
    plant();
    const r = verify(src, twin, { fontDir: fonts, sources, ...opts });
    const ok = want ? r.findings.some((f) => want.test(f)) : r.findings.length === 0;
    if (ok && want) caught += 1;
    console.log(`  ${ok ? 'OK  ' : 'BAD '} ${label}${ok ? '' : `\n         findings: ${r.findings.join(' | ') || '(none)'}`}`);
    if (!ok) bad += 1;
  }
  rmSync(dir, { recursive: true, force: true });
  if (bad) {
    console.error(`mobile-art --selftest: ${bad} case(s) landed on the wrong verdict`);
    process.exit(1);
  }
  console.log('  (plus 1 control: a complete twin tree passes)');
  console.log(`mobile-art --selftest: OK — ${caught} known-bads, ${caught} caught`);
}

function boundary() {
  console.log('BOUNDARY: this proves the light tree MIRRORS the runtime art at the policy\'s');
  console.log('          sizes and fits the art budget. It does not look at a pixel, so a');
  console.log('          twin of the right size, made from the current high file under the current');
  console.log('          policy (light/.twin-sources.json), passes even if the encoder drew it badly.');
}

const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (!isMain) {
  // imported (tests): no CLI
} else if (has('--selftest')) {
  selftest();
} else if (has('--check')) {
  const r = verify(SOURCE_DIR, TWIN_DIR, { fontDir: FONT_DIR, sources: readSources(resolve(TREE, SOURCES_PATH)) });
  for (const f of r.findings) console.log(`  FAIL  ${f}`);
  if (r.findings.length) {
    console.error(`mobile-art --check: FAILED — ${r.findings.length} finding(s) across ${r.files} runtime assets.`);
    console.error('  Fix: node tools/mobile-art.mjs   (brings light/assets/ up to date with cwebp on PATH)');
    boundary();
    process.exit(1);
  }
  console.log(`  ${r.files} twins, ${r.rawBytes} bytes raw, inlining (with the fonts) to ${r.inlined} of the ${MOBILE_ART_INLINED_BUDGET_BYTES}-byte budget`);
  console.log(`mobile-art --check: OK — ${r.checks} checks passed.`);
  boundary();
} else {
  const out = flag('--out', null);
  if (out && !has('--all')) { console.error('mobile-art: --out needs --all (it writes a whole tree elsewhere)'); process.exit(2); }
  let twinDir = TWIN_DIR;
  if (out) {
    try { twinDir = guardOut(out, TREE); } catch (e) { console.error(`mobile-art: REFUSED — ${e.message}`); process.exit(2); }
  }
  await generate(SOURCE_DIR, twinDir, { all: has('--all'), out: Boolean(out) });
  const r = verify(SOURCE_DIR, twinDir, { fontDir: FONT_DIR, sources: out ? undefined : readSources(resolve(TREE, SOURCES_PATH)) });
  for (const f of r.findings) console.log(`  FAIL  ${f}`);
  if (r.findings.length) {
    console.error(`mobile-art: generated, but the tree does not pass its own check — ${r.findings.length} finding(s).`);
    process.exit(1);
  }
  console.log(`mobile-art: OK — ${r.files} twins, ${r.rawBytes} bytes raw, inlines to ${r.inlined} of ${MOBILE_ART_INLINED_BUDGET_BYTES}`);
  if (!out) console.log('mobile-art: next, node tools/manifest.mjs --write');
  boundary();
}
