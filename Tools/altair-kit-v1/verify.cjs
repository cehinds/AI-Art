'use strict';

// Read-only validation for the frozen Altair Kit V1 production export.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { sharp } = require('../remaster-expansion/common.cjs');

const root = path.resolve(__dirname, '../..');
const manifestPath = path.join(root, 'Assets/Art/Production/AltairKitV1/manifest.json');
const expectedBuildings = {
  'item-shop': [3, 5], inn: [5, 5], headquarters: [7, 9], sanctuary: [7, 5],
  'magic-shop': [3, 5], 'armor-shop': [5, 5], home: [3, 5], 'weapon-shop': [5, 5], smithy: [3, 4]
};
const expectedExtras = {
  'signs/item': [32, 32], 'signs/inn': [32, 32], 'signs/sanctuary': [32, 32],
  'signs/magic': [32, 32], 'signs/armor': [32, 32], 'signs/weapon': [32, 32],
  'props/fountain': [64, 64], 'terrain/steps': [32, 32]
};
const expectedDependencies = [
  'Assets/Art/Production/RemasterExpansion/tiles/town/wall-cream-a.png',
  'Assets/Art/Production/RemasterExpansion/tiles/town/wall-cream-b.png',
  'Assets/Art/Production/RemasterExpansion/world-tiles/terrace-expansion02/terrace-n.png',
  'Assets/Art/Production/RemasterExpansion/world-tiles/terrace-expansion02/terrace-s.png',
  'Assets/Art/Production/RemasterExpansion/world-tiles/terrace-expansion02/terrace-e.png',
  'Assets/Art/Production/RemasterExpansion/world-tiles/terrace-expansion02/terrace-w.png',
  'Assets/Art/Production/RemasterExpansion/tiles/coast/bridge-vertical.png',
  'Assets/Art/Production/RemasterExpansion/tiles/coast/bridge-horizontal.png',
  'Assets/Art/Production/Batch01/structures/16-stairs-down.png',
  'Assets/Art/Production/RemasterExpansion/tiles/castle/stairs.png'
];
const issues = [];
const checked = { outputFiles: 0, sourceFiles: 0, dependencies: 0, buildingLayers: 0, extras: 0 };
const fail = message => issues.push(message);
const fullPath = rel => {
  if (typeof rel !== 'string' || !rel || path.isAbsolute(rel)) throw Error('Expected repository-relative path: ' + rel);
  const full = path.resolve(root, rel);
  const relative = path.relative(root, full);
  if (relative === '..' || relative.startsWith('..' + path.sep) || path.isAbsolute(relative)) throw Error('Path escapes repository: ' + rel);
  return full;
};
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function requireFile(rel) {
  const file = fullPath(rel);
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) throw Error('Missing file: ' + rel);
  return file;
}
async function png(rel) {
  const file = requireFile(rel);
  const bytes = fs.readFileSync(file);
  const meta = await sharp(bytes).metadata();
  if (meta.format !== 'png' || !meta.width || !meta.height) throw Error('Not a valid PNG: ' + rel);
  return { file, bytes, meta };
}
function assertHash(rel, expected, bytes) {
  if (!/^[a-f0-9]{64}$/i.test(expected || '')) throw Error('Invalid SHA-256 in manifest for ' + rel);
  if (sha256(bytes) !== expected.toLowerCase()) throw Error('SHA-256 mismatch: ' + rel);
}
function assertSize(rel, meta, width, height) {
  if (meta.width !== width || meta.height !== height) throw Error(`${rel} size ${meta.width}x${meta.height}; expected ${width}x${height}`);
}

async function main() {
  const manifest = JSON.parse(fs.readFileSync(requireFile('Assets/Art/Production/AltairKitV1/manifest.json'), 'utf8'));
  if (manifest.schemaVersion !== 1 || manifest.kit !== 'altair-kit-v1' || manifest.tileSize !== 32) throw Error('Unsupported/incomplete manifest header');
  const buildingById = new Map((manifest.objects || []).map(o => [o.id, o]));
  const expectedBuildingIds = Object.keys(expectedBuildings).sort();
  if (buildingById.size !== expectedBuildingIds.length || expectedBuildingIds.some(id => !buildingById.has(id)))
    fail('Manifest building IDs must be exactly: ' + expectedBuildingIds.join(', '));

  const listedOutputFiles = new Set();
  for (const [id, [tileW, tileH]] of Object.entries(expectedBuildings)) {
    const object = buildingById.get(id);
    if (!object) continue;
    if (object.tileFootprint?.width !== tileW || object.tileFootprint?.height !== tileH) fail(`${id} tile footprint must be ${tileW}x${tileH}`);
    const width = tileW * manifest.tileSize, height = tileH * manifest.tileSize;
    if (object.canvas?.width !== width || object.canvas?.height !== height) fail(`${id} manifest canvas must be ${width}x${height}`);
    if (!object.layers?.facade || !object.layers?.roof) fail(`${id} must include facade and roof layers`);
    if (!object.source?.file || !object.roofMask?.file) fail(`${id} source/mask provenance is missing`);

    const source = await png(object.source.file);
    assertHash(object.source.file, object.source.sha256, source.bytes);
    checked.sourceFiles++;
    if (source.meta.width !== object.sourceCanvas?.width || source.meta.height !== object.sourceCanvas?.height) fail(`${id} source dimensions disagree with manifest`);
    const mask = await png(object.roofMask.file);
    assertHash(object.roofMask.file, object.roofMask.sha256, mask.bytes);
    checked.sourceFiles++;
    if (mask.meta.width !== source.meta.width || mask.meta.height !== source.meta.height) fail(`${id} roof mask must match source dimensions`);
    const maskPixels = await sharp(mask.bytes).removeAlpha().greyscale().raw().toBuffer();
    if (maskPixels.some(v => v !== 0 && v !== 255)) fail(`${id} roof mask is not hard binary`);

    const layerInputs = [];
    const layerRaws = [];
    for (const layerName of manifest.layerOrder || []) {
      const record = object.layers[layerName];
      if (!record) continue;
      const result = await png(record.file);
      assertHash(record.file, record.sha256, result.bytes);
      assertSize(record.file, result.meta, width, height);
      listedOutputFiles.add(record.file);
      layerInputs.push({ input: result.bytes, left: 0, top: 0 });
      layerRaws.push(await sharp(result.bytes).ensureAlpha().raw().toBuffer());
      checked.outputFiles++;
      checked.buildingLayers++;
    }

    const assembled = await png(object.composite.file);
    assertHash(object.composite.file, object.composite.sha256, assembled.bytes);
    assertSize(object.composite.file, assembled.meta, width, height);
    listedOutputFiles.add(object.composite.file);
    checked.outputFiles++;
    const actualRaw = await sharp(assembled.bytes).ensureAlpha().raw().toBuffer();
    const expectedRaw = await sharp({ create: { width, height, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } })
      .composite(layerInputs).ensureAlpha().raw().toBuffer();
    if (!actualRaw.equals(expectedRaw)) fail(`${id} assembled PNG does not equal its layer composite`);
    if (layerRaws.length) {
      const pixelCount = width * height;
      for (let p = 0; p < pixelCount; p++) {
        let alphaSum = 0;
        for (const layer of layerRaws) alphaSum += layer[p * 4 + 3];
        if (alphaSum !== actualRaw[p * 4 + 3]) { fail(`${id} layer alpha does not match assembled alpha at pixel ${p}`); break; }
      }
    }
  }

  const headquarters = buildingById.get('headquarters');
  if (headquarters) {
    const expectedAnchor = { x: 112, y: 160 };
    if (headquarters.anchor?.x !== expectedAnchor.x || headquarters.anchor?.y !== expectedAnchor.y || !String(headquarters.anchor?.origin || '').includes('door threshold'))
      fail('Headquarters door anchor must be (112,160) source pixels at the door threshold');
    const image = await sharp(requireFile(headquarters.composite.file)).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
    for (let y = 5 * manifest.tileSize; y < 9 * manifest.tileSize; y++) {
      for (let x = 0; x < 4 * manifest.tileSize; x++) {
        if (image.data[(y * image.info.width + x) * 4 + 3] !== 0) {
          fail(`Headquarters southwest notch is not transparent at (${x},${y})`);
          y = image.info.height;
          break;
        }
      }
    }
  }

  const extras = new Map((manifest.extras || []).map(e => [`${e.kind}/${e.id}`, e]));
  const expectedExtraKeys = Object.keys(expectedExtras).sort();
  if (extras.size !== expectedExtraKeys.length || expectedExtraKeys.some(key => !extras.has(key)))
    fail('Manifest extras must be exactly: ' + expectedExtraKeys.join(', '));
  for (const [key, [width, height]] of Object.entries(expectedExtras)) {
    const extra = extras.get(key);
    if (!extra) continue;
    const source = await png(extra.source?.file);
    assertHash(extra.source.file, extra.source.sha256, source.bytes);
    checked.sourceFiles++;
    if (source.meta.width !== extra.sourceCanvas?.width || source.meta.height !== extra.sourceCanvas?.height) fail(`${key} source dimensions disagree with manifest`);
    const crop = extra.crop;
    if (!crop || crop.x < 0 || crop.y < 0 || crop.width <= 0 || crop.height <= 0 || crop.x + crop.width > source.meta.width || crop.y + crop.height > source.meta.height)
      fail(`${key} crop is outside its source image`);
    const result = await png(extra.file);
    assertHash(extra.file, extra.sha256, result.bytes);
    assertSize(extra.file, result.meta, width, height);
    if (extra.file !== `Assets/Art/Production/AltairKitV1/${key}.png`) fail(`${key} output path does not match binder contract`);
    listedOutputFiles.add(extra.file);
    checked.outputFiles++;
    checked.extras++;
    const raw = await sharp(result.bytes).ensureAlpha().raw().toBuffer();
    if (key.startsWith('signs/')) {
      for (let i = 3; i < raw.length; i += 4) if (raw[i] !== 255) { fail(`${extra.file} must be fully opaque`); break; }
    } else if (key === 'props/fountain') {
      if (!result.meta.hasAlpha) fail('Fountain must preserve transparency');
      let transparent = false;
      for (let i = 3; i < raw.length; i += 4) if (raw[i] < 255) { transparent = true; break; }
      if (!transparent) fail('Fountain output has no transparent pixels');
    } else if (key === 'terrain/steps') {
      for (let i = 3; i < raw.length; i += 4) if (raw[i] !== 255) { fail('Steps tile must be fully opaque'); break; }
    }
  }

  const dependencies = new Map((manifest.dependencies || []).map(d => [d.file, d]));
  if (dependencies.size !== expectedDependencies.length || expectedDependencies.some(file => !dependencies.has(file)))
    fail('Manifest dependency references are incomplete');
  for (const file of expectedDependencies) {
    const dependency = dependencies.get(file);
    if (!dependency) continue;
    const bytes = fs.readFileSync(requireFile(file));
    assertHash(file, dependency.sha256, bytes);
    checked.dependencies++;
  }

  const productionRoot = path.join(root, 'Assets/Art/Production/AltairKitV1');
  const discoveredOutputs = [];
  function walk(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.isFile() && entry.name.toLowerCase().endsWith('.png')) discoveredOutputs.push(path.relative(root, full).replaceAll(path.sep, '/'));
    }
  }
  walk(productionRoot);
  const discoveredSet = new Set(discoveredOutputs);
  for (const file of listedOutputFiles) if (!discoveredSet.has(file)) fail('Manifest output missing from production directory: ' + file);
  for (const file of discoveredSet) if (!listedOutputFiles.has(file)) fail('Production PNG is absent from manifest: ' + file);
  for (const rel of ['Review/altair-kit-v1/index.html', 'Review/altair-kit-v1/contact-sheet.png']) requireFile(rel);

  if (issues.length) {
    console.error(JSON.stringify({ status: 'FAIL', checked, errors: issues }, null, 2));
    process.exitCode = 1;
    return;
  }
  console.log(JSON.stringify({ status: 'PASS', checked, headquartersAnchor: headquarters.anchor, hqNotch: 'transparent x<128,y>=160', contactSheet: 'Review/altair-kit-v1/contact-sheet.png' }, null, 2));
}

main().catch(error => { console.error(error.stack || error.message); process.exitCode = 1; });
