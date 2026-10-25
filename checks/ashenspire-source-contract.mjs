import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {lstatSync, readFileSync, realpathSync} from 'node:fs';
import {dirname, isAbsolute, relative, resolve, sep, posix} from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const stancePath = 'pose-studio/stances/registry.json';
const basePath = 'pose-studio/renewal/base-action-registry.json';
const baseRoot = 'pose-studio/renewal/';
const stances = ['offensive', 'defensive', 'casting'];
const classes = ['reaver', 'rogue', 'starseer', 'herald'];
const actions = ['attack', 'defense', 'power'];
const hash = (bytes, algorithm = 'sha256') => createHash(algorithm).update(bytes).digest('hex');
const keys = (object, expected, label) => assert.deepEqual(Object.keys(object).sort(), [...expected].sort(), label);
const object = value => value && typeof value === 'object' && !Array.isArray(value);

export function checkedPath(path) {
  assert.equal(typeof path, 'string', 'source path must be a string');
  assert(path.startsWith('pose-studio/') || path.startsWith('common/assets-display/'), `source outside recorded art roots: ${path}`);
  assert(!path.includes('\\') && !path.includes('\n') && !path.includes('\r') && !isAbsolute(path), `unsafe path: ${path}`);
  assert(path.split('/').every(part => part && part !== '.' && part !== '..'), `unsafe path: ${path}`);
  return path;
}

export function readReceipt(path = resolve(here, 'ashenspire-source-contract.json')) {
  const receipt = JSON.parse(readFileSync(path));
  assert.equal(receipt.schemaVersion, 1);
  assert.equal(receipt.origin.repository, 'cehinds/AI-Art');
  assert.match(receipt.origin.commit, /^[a-f0-9]{40}$/);
  assert.equal(receipt.origin.tag, 'ashenspire-hd-assets-v24');
  assert(object(receipt.files) && Object.keys(receipt.files).length > 0, 'empty source receipt');
  for (const [path, row] of Object.entries(receipt.files)) {
    checkedPath(path);
    assert.equal(row.mode, '100644', path);
    assert.match(row.oid, /^[a-f0-9]{40}$/, path);
    assert(Number.isSafeInteger(row.bytes) && row.bytes > 0 && row.bytes <= 4 * 1024 * 1024, `invalid byte length: ${path}`);
  }
  return receipt;
}

// Pillow must actually decode every image; a valid RIFF header alone is insufficient.
// Bounds use the original exporters' alpha thresholds (stances >32; base actions >8).
export function decodeImages(root, requests) {
  const python = String.raw`
import json, sys, warnings
from PIL import Image
warnings.simplefilter('error', Image.DecompressionBombWarning)
result = {}
for path, options in json.load(sys.stdin):
    with Image.open(path) as image:
        if image.format != options['format']:
            raise ValueError('Wrong image MIME: ' + path)
        image.verify()
    with Image.open(path) as image:
        if getattr(image, 'n_frames', 1) != 1:
            raise ValueError('Expected single-frame image: ' + path)
        image.load()
        alpha = image.convert('RGBA').getchannel('A')
        box = alpha.point(lambda a: 255 if a > options['threshold'] else 0).getbbox()
        result[path] = {'size': list(image.size), 'bounds': list(box) if box else None}
print(json.dumps(result))
`;
  const child = spawnSync(process.env.PYTHON || 'python3', ['-c', python], {
    input: JSON.stringify([...requests].map(([path, options]) => [resolve(root, path), options])),
    encoding: 'utf8', maxBuffer: 2 * 1024 * 1024, timeout: 120_000,
  });
  assert.ifError(child.error);
  assert.equal(child.status, 0, `Image decode failed: ${child.stderr}`);
  const decoded = JSON.parse(child.stdout);
  return new Map([...requests].map(([path]) => [path, decoded[resolve(root, path)]]));
}

function embedded(src, label) {
  assert.equal(typeof src, 'string', label);
  assert.match(src, /^data:image\/webp;base64,[A-Za-z0-9+/]+={0,2}$/, `not embedded WebP: ${label}`);
  const encoded = src.slice('data:image/webp;base64,'.length);
  const bytes = Buffer.from(encoded, 'base64');
  assert.equal(bytes.toString('base64'), encoded, `invalid base64: ${label}`);
  return bytes;
}

function geometry(frame, label) {
  assert.deepEqual(frame.anchor, [256, 464], `anchor: ${label}`);
  assert(Array.isArray(frame.bounds) && frame.bounds.length === 4 && frame.bounds.every(n => Number.isInteger(n) && n > 0 && n < 512), `crop bounds: ${label}`);
  assert(frame.bounds[0] < frame.bounds[2] && frame.bounds[1] < frame.bounds[3], `empty crop: ${label}`);
}

export function verifySourceContract(root, receipt = readReceipt()) {
  root = realpathSync(root);
  const used = new Set();
  const cache = new Map();
  const images = new Map();
  const expectations = [];
  const load = path => {
    checkedPath(path);
    const expected = receipt.files[path];
    assert(expected, `unrecorded/wrong source path: ${path}`);
    used.add(path);
    if (cache.has(path)) return cache.get(path);
    const absolute = resolve(root, path);
    const stat = lstatSync(absolute);
    assert(stat.isFile() && !stat.isSymbolicLink(), `not a regular source file: ${path}`);
    assert.equal(stat.mode & 0o111, 0, `unexpected executable source: ${path}`);
    const resolved = realpathSync(absolute);
    const rel = relative(root, resolved);
    assert(rel && rel !== '..' && !rel.startsWith('..' + sep) && !isAbsolute(rel), `source escapes root: ${path}`);
    assert.equal(stat.size, expected.bytes, `byte length: ${path}`);
    const bytes = readFileSync(absolute);
    const blob = createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');
    assert.equal(blob, expected.oid, `frozen v24 Git blob: ${path}`);
    cache.set(path, bytes);
    return bytes;
  };
  const json = path => JSON.parse(load(path));
  const image = (path, size, threshold, bounds, format = 'WEBP') => {
    const bytes = load(path);
    if (format === 'WEBP') {
      assert(bytes.length >= 20 && bytes.toString('ascii', 0, 4) === 'RIFF' && bytes.toString('ascii', 8, 12) === 'WEBP', `WebP MIME: ${path}`);
      assert.equal(bytes.readUInt32LE(4) + 8, bytes.length, `WebP RIFF byte length: ${path}`);
    } else {
      assert.equal(format, 'PNG');
      assert(bytes.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])), `PNG MIME: ${path}`);
    }
    if (images.has(path)) assert.deepEqual(images.get(path), {threshold,format}, `inconsistent decoder options: ${path}`);
    images.set(path, {threshold,format});
    expectations.push({path, size, bounds});
    return bytes;
  };
  const pair = (frame, rig, id, prefix, threshold) => {
    const path = prefix + frame.path, lite = prefix + frame.lite;
    geometry(frame, path);
    const high = image(path, [512, 512], threshold, frame.bounds);
    image(lite, [256, 256], threshold);
    assert.deepEqual(embedded(rig.assets?.[id]?.src, `${path} rig`), high, `HIGH differs from embedded rig: ${path}`);
    return high;
  };

  const catalog = json(stancePath);
  assert.equal(catalog.schemaVersion, 1);
  assert.deepEqual(catalog.stances, stances);
  assert.equal(Object.keys(catalog.actors).length, 41, 'complete stance actor coverage');
  let stanceFrames = 0;
  for (const [actor, entry] of Object.entries(catalog.actors)) {
    keys(entry.frames, stances, `stance frames: ${actor}`);
    const rig = json(entry.rig);
    assert.equal(rig.schemaVersion, 1);
    assert.deepEqual(rig.canvas, {width:512, height:512});
    keys(rig.assets, stances, `stance rig assets: ${actor}`);
    for (const [id, frame] of Object.entries(entry.frames)) {
      assert.deepEqual(frame.size, [512, 512], `declared size: ${actor}/${id}`);
      const high = pair(frame, rig, id, '', 32);
      assert.match(frame.sha256, /^[a-f0-9]{64}$/);
      assert.match(frame.liteSha256, /^[a-f0-9]{64}$/);
      assert.equal(hash(high), frame.sha256, `HIGH SHA256: ${actor}/${id}`);
      assert.equal(hash(load(frame.lite)), frame.liteSha256, `LITE SHA256: ${actor}/${id}`);
      stanceFrames++;
    }
  }
  const registry = json(basePath);
  assert.equal(registry.schemaVersion, 1);
  assert.deepEqual(registry.classes, classes);
  assert.deepEqual(registry.actions, actions);
  assert.equal(registry.equipmentIndependent, true);
  keys(registry.families, classes, 'base families');
  let baseFrames = 0;
  for (const actor of classes) {
    const entry = registry.families[actor];
    const manifest = json(baseRoot + entry.manifest), rig = json(baseRoot + entry.rig);
    assert.equal(manifest.schemaVersion, 1);
    assert.equal(manifest.classId, actor);
    assert.equal(manifest.armour, 'default');
    assert.equal(manifest.equipmentIndependent, true);
    assert.equal(rig.schemaVersion, 1);
    assert.deepEqual(rig.canvas, {width:512, height:512});
    assert.equal(Object.keys(manifest.frames).length, 12, `base frame count: ${actor}`);
    keys(rig.assets, Object.keys(manifest.frames), `base rig assets: ${actor}`);
    keys(manifest.sequences, actions, `base action sequences: ${actor}`);
    let highBytes = 0, liteBytes = 0;
    for (const [id, frame] of Object.entries(manifest.frames)) {
      highBytes += pair(frame, rig, id, baseRoot, 8).length;
      liteBytes += load(baseRoot + frame.lite).length;
      baseFrames++;
    }
    assert.deepEqual(manifest.bytes, {webp:highBytes, lite:liteBytes}, `base source byte totals: ${actor}`);
  }
  // Original selection manifests remain the authority for boards. The compact
  // weapon-source projection records the original Game catalog identity without
  // pretending that its code file was copied into this repository.
  const selected = receipt.selected;
  assert(object(selected), 'missing selected source contract');
  assert.equal(selected.catalogOrigin.repository, 'cehinds/AshenSpire');
  assert.match(selected.catalogOrigin.commit, /^[a-f0-9]{40}$/);
  assert.match(selected.catalogOrigin.blob, /^[a-f0-9]{40}$/);
  assert.match(selected.catalogOrigin.sha256, /^[a-f0-9]{64}$/);
  const destination = path => path.startsWith('assets-display/') ? 'common/' + path : path;
  const source = (path, spec, size = [spec.width, spec.height]) => {
    path = destination(path);
    assert(Array.isArray(size) && size.length === 2 && size.every(n => Number.isInteger(n) && n > 0 && n <= 8192), `source dimensions: ${path}`);
    assert.match(spec.sha256, /^[a-f0-9]{64}$/);
    const bytes = image(path, size, 32, undefined, path.endsWith('.png') ? 'PNG' : 'WEBP');
    assert.equal(hash(bytes), spec.sha256, `selected source SHA256: ${path}`);
  };
  const selections = json(selected.selections);
  assert.equal(selections.schemaVersion, 1);
  assert.equal(selections.choices.length, 12, 'complete owner-selected stance sources');
  const cells = new Set();
  for (const choice of selections.choices) {
    assert(classes.includes(choice.actor) && ['attack','defend','casting'].includes(choice.stance), 'selected stance identity');
    const id = choice.actor + '/' + choice.stance;
    assert(!cells.has(id), `duplicate selected stance source: ${id}`); cells.add(id);
    const path = posix.normalize(posix.join(posix.dirname(selected.selections), choice.source.path));
    source(path, choice.source);
    const {x,y,width,height} = choice.source.view;
    assert([x,y,width,height].every(Number.isInteger) && x >= 0 && y >= 0 && width > 0 && height > 0 && x + width <= choice.source.width && y + height <= choice.source.height, `selected source view: ${id}`);
  }
  const production = json(selected.weaponSelections);
  assert.equal(production.schemaVersion, 1);
  assert.equal(production.choices.length, 18, 'complete greatsword source choices');
  assert.equal(Object.keys(selected.weaponFrames).length, 24, 'complete selected weapon source projection');
  assert.equal(json(production.reviewManifest).schemaVersion, 1);
  for (const choice of production.choices) {
    const frame = selected.weaponFrames[choice.role];
    assert(frame, `missing weapon source role: ${choice.role}`);
    assert.equal(frame.sourceOption, choice.role === 'sweep' ? 'SW09' : choice.sourceOption, `weapon source option: ${choice.role}`);
  }
  for (const frame of Object.values(selected.weaponFrames)) source(frame.source.path, frame.source);
  for (const path of selected.weaponProvenance) {
    const provenance = json(path);
    assert.equal(provenance.schemaVersion, 1);
    for (const frame of provenance.frames) {
      const expected = selected.weaponFrames[frame.key];
      assert(expected, `missing selected production source: ${frame.key}`);
      assert.deepEqual(expected.source, {path:frame.sourcePath, width:frame.sourceDimensions[0], height:frame.sourceDimensions[1], sha256:frame.sourceSha256}, `selected production source: ${frame.key}`);
      assert.equal(expected.runtimeSha256, frame.full.sha256, `selected production output identity: ${frame.key}`);
    }
  }
  const review = json(selected.reviewSources);
  assert.equal(review.schemaVersion, 1);
  assert.equal(review.sources.length, 15, 'complete preview input sources');
  for (const input of review.sources) source(input.source, input, input.size);
  const attack3 = review.sources.find(input => input.id === 'AT3');
  assert(attack3, 'missing AT3 preview input');
  const counter = selected.weaponFrames.counter;
  assert.notEqual(destination(attack3.source), destination(counter.runtimePath), 'historical AT3 must not resolve to current Counter');
  assert.notEqual(attack3.sha256, counter.runtimeSha256, 'historical AT3 bytes must differ from current Counter');
  assert.equal(attack3.sha256, selected.weaponFrames['attack-3'].runtimeSha256, 'AT3 preserves attack-3 bytes');
  source(attack3.originalSheetRecipe.path, attack3.originalSheetRecipe);
  keys(receipt.files, [...used], 'receipt must cover exactly the required source files');
  const decoded = decodeImages(root, images);
  for (const {path, size, bounds} of expectations) {
    const actual = decoded.get(path);
    assert.deepEqual(actual?.size, size, `decoded dimensions: ${path}`);
    assert(actual.bounds && actual.bounds[0] < actual.bounds[2] && actual.bounds[1] < actual.bounds[3], `empty decoded image: ${path}`);
    if (bounds) assert.deepEqual(actual.bounds, bounds, `decoded alpha crop bounds: ${path}`);
  }
  return {origin:receipt.origin, files:used.size, stanceActors:41, stanceFrames, baseClasses:4, baseFrames, selectedStanceSources:12, weaponSources:24, previewSources:15, decodedImages:images.size,
    identity:'Frozen v24 Git blob identity for every input; declared stance SHA256 for HIGH and LITE; base HIGH equals rig bytes. Base LITE has no original declared SHA256 and is verified against frozen v24 Git identity.'};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const [command, root = '.'] = process.argv.slice(2);
    if (command === '--paths') console.log(Object.keys(readReceipt().files).map(path => '/' + path).join('\n'));
    else {
      assert.equal(command, '--root', 'usage: node checks/ashenspire-source-contract.mjs --root <checkout> | --paths');
      console.log(JSON.stringify(verifySourceContract(root), null, 2));
    }
  } catch (error) {
    console.error(error.stack || error);
    process.exitCode = 1;
  }
}
