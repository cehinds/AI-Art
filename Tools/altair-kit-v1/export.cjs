'use strict';

// Export normalized, transparent Altair layers from preserved generated masters.
// Generated source creation and roof-mask authoring are separate.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { sharp } = require('../remaster-expansion/common.cjs');

const root = path.resolve(__dirname, '../..');
const cfgPath = path.join(__dirname, 'kit.json');
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
const layerOrder = ['ground', 'terrain-edge', 'facade', 'trim', 'roof', 'detail', 'sign'];
const slug = value => /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value);
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const resolveUnder = (base, rel) => {
  if (typeof rel !== 'string' || !rel || path.isAbsolute(rel)) throw Error('Expected repository-relative path: ' + rel);
  const full = path.resolve(root, rel);
  const fromBase = path.relative(path.resolve(root, base), full);
  if (fromBase === '..' || fromBase.startsWith('..' + path.sep) || path.isAbsolute(fromBase)) throw Error('Path escapes ' + base + ': ' + rel);
  return full;
};
const ensureDir = rel => fs.mkdirSync(path.join(root, rel), { recursive: true });
function save(rel, bytes, replaceGenerated = false) {
  const file = path.join(root, rel);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const next = Buffer.from(bytes);
  if (fs.existsSync(file)) {
    if (!fs.readFileSync(file).equals(next)) {
      if (!replaceGenerated) throw Error('Preserving existing file; choose a new versioned ID: ' + rel);
      fs.writeFileSync(file, next);
      return;
    }
    return;
  }
  fs.writeFileSync(file, next);
}
function refreshReview(rel, bytes) {
  const file = path.join(root, rel);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, Buffer.from(bytes));
}
function point(p, label, width, height) {
  if (!p || !Number.isInteger(p.x) || !Number.isInteger(p.y) || p.x < 0 || p.y < 0 || p.x > width || p.y > height)
    throw Error(label + ' must be integer source pixels inside the canvas');
}
function rect(r, label, width, height) {
  if (!r || !['x', 'y', 'width', 'height'].every(k => Number.isInteger(r[k])) || r.x < 0 || r.y < 0 || r.width <= 0 || r.height <= 0 || r.x + r.width > width || r.y + r.height > height)
    throw Error(label + ' must be a positive pixel rectangle inside the canvas');
}
function alphaBounds(pixels, width, height, alphaThreshold = 128) {
  let left = width, top = height, right = -1, bottom = -1;
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
    if (pixels[(y * width + x) * 4 + 3] < alphaThreshold) continue;
    if (x < left) left = x;
    if (x > right) right = x;
    if (y < top) top = y;
    if (y > bottom) bottom = y;
  }
  if (right < left || bottom < top) throw Error('Source cutout has no opaque pixels');
  return { x: left, y: top, width: right - left + 1, height: bottom - top + 1 };
}
async function normalizeLayer(bytes, crop, width, height) {
  return sharp(bytes).extract({ left: crop.x, top: crop.y, width: crop.width, height: crop.height }).resize(width, height, { kernel: 'nearest' }).png().toBuffer();
}

async function main() {
  if (cfg.schemaVersion !== 1 || cfg.kit !== 'altair-kit-v1' || !Array.isArray(cfg.objects)) throw Error('Unsupported kit manifest');
  const ids = new Set();
  if (!Number.isInteger(cfg.tileSize) || cfg.tileSize <= 0) throw Error('tileSize must be a positive integer');
  const cropAlphaThreshold = cfg.cropAlphaThreshold ?? 128;
  if (!Number.isInteger(cropAlphaThreshold) || cropAlphaThreshold < 1 || cropAlphaThreshold > 255) throw Error('cropAlphaThreshold must be 1..255');
  const compiled = { schemaVersion: 1, kit: cfg.kit, tileSize: cfg.tileSize, cropAlphaThreshold, sourcePolicy: 'Original generated PNG masters are preserved byte-for-byte under ArtSource; runtime layers crop to alpha >= cropAlphaThreshold and resize with nearest-neighbor sampling.', layerOrder, dependencies: [], objects: [] };

  for (const object of cfg.objects) {
    if (!slug(object.id) || ids.has(object.id)) throw Error('Invalid or duplicate object id: ' + object.id);
    ids.add(object.id);
    const layers = object.layers || {};
    const present = layerOrder.filter(layer => layers[layer]);
    if (layers.facade || layers.roof) throw Error(object.id + ' facade and roof are derived from source + roofMask, not supplied as separate layers');
    if (!object.source || !object.roofMask) throw Error(object.id + ' requires a complete source cutout and a roof mask');
    const records = {};
    const sourcePath = object.source.path;
    const maskPath = object.roofMask.path;
    const sourceFile = resolveUnder('ArtSource/AltairKitV1', sourcePath);
    const maskFile = resolveUnder('ArtSource/AltairKitV1', maskPath);
    if (!fs.existsSync(sourceFile) || !fs.existsSync(maskFile)) throw Error(object.id + ' source cutout or roof mask is missing');
    const sourceBytes = fs.readFileSync(sourceFile);
    const maskBytes = fs.readFileSync(maskFile);
    const sourceMeta = await sharp(sourceBytes).metadata();
    const maskMeta = await sharp(maskBytes).metadata();
    if (sourceMeta.format !== 'png' || !sourceMeta.hasAlpha || !sourceMeta.width || !sourceMeta.height) throw Error(sourcePath + ' must be a transparent RGBA PNG');
    if (maskMeta.format !== 'png' || maskMeta.width !== sourceMeta.width || maskMeta.height !== sourceMeta.height) throw Error(maskPath + ' must be a same-size PNG roof mask');
    if (object.source.sha256 && object.source.sha256 !== sha256(sourceBytes)) throw Error('Source hash mismatch: ' + sourcePath);
    if (object.roofMask.sha256 && object.roofMask.sha256 !== sha256(maskBytes)) throw Error('Mask hash mismatch: ' + maskPath);
    const sourceCanvas = { width: sourceMeta.width, height: sourceMeta.height };
    const sourcePixels = await sharp(sourceBytes).flop(Boolean(object.flipX)).ensureAlpha().raw().toBuffer();
    const crop = object.crop || alphaBounds(sourcePixels, sourceCanvas.width, sourceCanvas.height, cropAlphaThreshold);
    rect(crop, object.id + '.crop', sourceCanvas.width, sourceCanvas.height);
    if (!object.tileFootprint || !Number.isInteger(object.tileFootprint.width) || !Number.isInteger(object.tileFootprint.height) || object.tileFootprint.width <= 0 || object.tileFootprint.height <= 0)
      throw Error(object.id + '.tileFootprint must declare positive width and height in map tiles');
    const canvas = { width: object.tileFootprint.width * cfg.tileSize, height: object.tileFootprint.height * cfg.tileSize };
    const maskPixels = await sharp(maskBytes).flop(Boolean(object.flipX)).removeAlpha().greyscale().raw().toBuffer();
    const facadePixels = Buffer.alloc(sourcePixels.length);
    const roofPixels = Buffer.alloc(sourcePixels.length);
    for (let i = 0, m = 0; i < sourcePixels.length; i += 4, m++) {
      if (maskPixels[m] !== 0 && maskPixels[m] !== 255) throw Error(maskPath + ' must use a hard binary mask (only black and white)');
      const roofA = Math.round(sourcePixels[i + 3] * maskPixels[m] / 255);
      for (let c = 0; c < 3; c++) { facadePixels[i + c] = sourcePixels[i + c]; roofPixels[i + c] = sourcePixels[i + c]; }
      roofPixels[i + 3] = roofA;
      facadePixels[i + 3] = sourcePixels[i + 3] - roofA;
    }
    const layerBuffers = {
      facade: await normalizeLayer(await sharp(facadePixels, { raw: { ...sourceCanvas, channels: 4 } }).png().toBuffer(), crop, canvas.width, canvas.height),
      roof: await normalizeLayer(await sharp(roofPixels, { raw: { ...sourceCanvas, channels: 4 } }).png().toBuffer(), crop, canvas.width, canvas.height)
    };
    for (const layer of present) {
      const src = layers[layer];
      const input = resolveUnder('ArtSource/AltairKitV1', src.path);
      if (!fs.existsSync(input)) throw Error('Missing source layer: ' + src.path);
      const bytes = fs.readFileSync(input);
      const meta = await sharp(bytes).metadata();
      if (meta.format !== 'png' || !meta.hasAlpha || !meta.width || !meta.height) throw Error(src.path + ' must be a transparent RGBA PNG');
      if (sourceCanvas.width !== meta.width || sourceCanvas.height !== meta.height) throw Error(object.id + ' layers must share the complete source canvas');
      if (src.sha256 && src.sha256 !== sha256(bytes)) throw Error('Source hash mismatch: ' + src.path);
      layerBuffers[layer] = await normalizeLayer(bytes, crop, canvas.width, canvas.height);
    }
    present.push('facade', 'roof');
    point(object.anchor, object.id + '.anchor', canvas.width, canvas.height);
    rect(object.footprint, object.id + '.footprint', canvas.width, canvas.height);
    if (object.collision?.type === 'rect') rect(object.collision, object.id + '.collision', canvas.width, canvas.height);
    else if (!object.collision || !['none', 'footprint'].includes(object.collision.type)) throw Error(object.id + ' collision must be none, footprint, or a rectangle');

    for (const layer of layerOrder) {
      const bytes = layerBuffers[layer];
      if (!bytes) continue;
      const outputPath = `Assets/Art/Production/AltairKitV1/buildings/${object.id}-${layer}.png`;
      save(outputPath, bytes, true);
      records[layer] = { source: layer === 'facade' || layer === 'roof' ? sourcePath : layers[layer].path, file: outputPath, sha256: sha256(bytes), derivedFrom: layer === 'facade' || layer === 'roof' ? { source: sourcePath, mask: maskPath, split: layer === 'roof' ? 'source alpha multiplied by binary mask' : 'source alpha outside binary mask' } : undefined };
    }

    const inputLayers = layerOrder.filter(layer => layerBuffers[layer]).map(layer => ({ input: layerBuffers[layer], left: 0, top: 0 }));
    const composite = await sharp({ create: { ...canvas, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } }).composite(inputLayers).png().toBuffer();
    const compositePath = `Assets/Art/Production/AltairKitV1/buildings/${object.id}.png`;
    save(compositePath, composite, true);
    const previewPath = `Review/altair-kit-v1/${object.id}.png`;
    refreshReview(previewPath, composite);
    const record = {
      id: object.id, name: object.name, role: object.role, canvas, sourceCanvas, crop, transform: { flipX: Boolean(object.flipX) },
      source: { file: sourcePath, sha256: sha256(sourceBytes) },
      roofMask: { file: maskPath, sha256: sha256(maskBytes) },
      anchor: { ...object.anchor, origin: 'source pixels at door threshold; top-left origin, x right, y down' },
      footprint: { ...object.footprint, units: 'source pixels; ground-contact area' },
      tileFootprint: { ...object.tileFootprint, units: 'map tiles' },
      collision: object.collision.type === 'rect' ? { ...object.collision, units: 'source pixels' } : object.collision,
      runtimeCollision: object.runtimeCollision || null,
      composition: object.composition || null,
      layers: records,
      composite: { file: compositePath, sha256: sha256(composite) },
      review: previewPath,
      reference: object.reference || null
    };
    compiled.objects.push(record);
  }

  compiled.extras = [];
  const extraIds = new Set();
  for (const extra of (cfg.extras || [])) {
    if (!slug(extra.id) || extraIds.has(extra.id)) throw Error('Invalid or duplicate extra id: ' + extra.id);
    extraIds.add(extra.id);
    if (!['signs', 'props', 'terrain'].includes(extra.kind)) throw Error(extra.id + ' kind must be signs, props, or terrain');
    if (!extra.source?.path || !extra.size || !Number.isInteger(extra.size.width) || !Number.isInteger(extra.size.height) || extra.size.width <= 0 || extra.size.height <= 0) throw Error(extra.id + ' requires a source and positive output size');
    const sourceFile = resolveUnder('ArtSource/AltairKitV1', extra.source.path);
    if (!fs.existsSync(sourceFile)) throw Error('Missing extra source: ' + extra.source.path);
    const sourceBytes = fs.readFileSync(sourceFile);
    const meta = await sharp(sourceBytes).metadata();
    if (meta.format !== 'png' || !meta.width || !meta.height) throw Error(extra.source.path + ' must be a PNG');
    const pixels = await sharp(sourceBytes).ensureAlpha().raw().toBuffer();
    const crop = extra.crop || alphaBounds(pixels, meta.width, meta.height, cropAlphaThreshold);
    rect(crop, extra.id + '.crop', meta.width, meta.height);
    if (extra.source.sha256 && extra.source.sha256 !== sha256(sourceBytes)) throw Error('Source hash mismatch: ' + extra.source.path);
    let pipeline = sharp(sourceBytes).extract({ left: crop.x, top: crop.y, width: crop.width, height: crop.height });
    if (extra.flatten) pipeline = pipeline.flatten({ background: extra.flatten.background || { r: 139, g: 90, b: 32 } }).removeAlpha();
    const bytes = await pipeline.resize(extra.size.width, extra.size.height, { kernel: 'nearest' }).png().toBuffer();
    const outputPath = `Assets/Art/Production/AltairKitV1/${extra.kind}/${extra.id}.png`;
    save(outputPath, bytes, true);
    const previewPath = `Review/altair-kit-v1/${extra.kind}-${extra.id}.png`;
    refreshReview(previewPath, bytes);
    compiled.extras.push({ id: extra.id, kind: extra.kind, source: { file: extra.source.path, sha256: sha256(sourceBytes) }, sourceCanvas: { width: meta.width, height: meta.height }, crop, canvas: extra.size, flatten: Boolean(extra.flatten), file: outputPath, sha256: sha256(bytes), review: previewPath, notes: extra.notes || null });
  }

  for (const dependency of (cfg.dependencies || [])) {
    const file = resolveUnder('.', dependency.file);
    if (!fs.existsSync(file)) throw Error('Missing referenced dependency: ' + dependency.file);
    const bytes = fs.readFileSync(file);
    const digest = sha256(bytes);
    if (digest !== dependency.sha256) throw Error('Referenced dependency hash mismatch: ' + dependency.file);
    compiled.dependencies.push({ ...dependency, sha256: digest });
  }

  if (!compiled.objects.length && !compiled.extras.length) throw Error('No objects or extras registered in Tools/altair-kit-v1/kit.json; wait for generated layers and metadata.');
  ensureDir('Assets/Art/Production/AltairKitV1');
  // The manifest is this exporter's mutable index of immutable, conflict-checked outputs.
  refreshReview('Assets/Art/Production/AltairKitV1/manifest.json', Buffer.from(JSON.stringify(compiled, null, 2) + '\n', 'utf8'));
  const gallery = renderGallery(compiled);
  refreshReview('Review/altair-kit-v1/index.html', Buffer.from(gallery, 'utf8'));
  const contactSheet = await renderContactSheet(compiled);
  refreshReview('Review/altair-kit-v1/contact-sheet.png', contactSheet);
  console.log(`Exported ${compiled.objects.length} Altair objects and ${Object.values(compiled.objects).reduce((n, o) => n + Object.keys(o.layers).length, 0)} source layers.`);
}

async function renderContactSheet(manifest) {
  const cardW = 320, cardH = 400, cols = 3, rows = Math.ceil(manifest.objects.length / cols);
  const cards = [];
  for (let i = 0; i < manifest.objects.length; i++) {
    const o = manifest.objects[i];
    const art = await sharp(fs.readFileSync(path.join(root, o.composite.file))).resize(280, 310, { fit: 'contain', kernel: 'nearest', background: { r: 23, g: 32, b: 42, alpha: 0 } }).png().toBuffer();
    const title = String(o.id).replace(/&/g, '&amp;').replace(/</g, '&lt;');
    const svg = Buffer.from(`<svg width="${cardW}" height="${cardH}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" rx="12" fill="#263441"/><text x="16" y="28" fill="#f4efe2" font-family="sans-serif" font-size="18">${title}</text><text x="16" y="48" fill="#bac4ce" font-family="sans-serif" font-size="12">${o.tileFootprint.width}×${o.tileFootprint.height} tiles · anchor ${o.anchor.x},${o.anchor.y}</text></svg>`);
    cards.push({ input: await sharp(svg).composite([{ input: art, left: 20, top: 70 }]).png().toBuffer(), left: (i % cols) * cardW, top: Math.floor(i / cols) * cardH });
  }
  return sharp({ create: { width: cols * cardW, height: rows * cardH, channels: 4, background: { r: 23, g: 32, b: 42, alpha: 1 } } }).composite(cards).png().toBuffer();
}

function renderGallery(manifest) {
  const h = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const cards = manifest.objects.map(o => `<article><h2>${h(o.name)}</h2><p>${h(o.role)} · ${o.canvas.width}×${o.canvas.height}px · tile footprint ${o.tileFootprint.width}×${o.tileFootprint.height}</p><img class="composite" src="${h(path.basename(o.review))}" alt="${h(o.name)} assembled"><p>Anchor ${o.anchor.x},${o.anchor.y}px · Ground footprint ${o.footprint.x},${o.footprint.y},${o.footprint.width}×${o.footprint.height}px · Collision ${h(o.collision.type)}</p><details><summary>Inspect layers</summary><div class="layers">${Object.entries(o.layers).map(([name, layer]) => `<figure><img src="../../${h(layer.file.replaceAll('\\', '/'))}" alt="${h(name)} layer"><figcaption>${h(name)} · sha256 ${h(layer.sha256.slice(0, 12))}…</figcaption></figure>`).join('')}</div></details></article>`).join('\n');
  const extras = (manifest.extras || []).map(o => `<article><h2>${h(o.id)}</h2><p>${h(o.kind)} · ${o.canvas.width}×${o.canvas.height}px · source crop ${o.crop.x},${o.crop.y},${o.crop.width}×${o.crop.height} · ${o.flatten ? 'opaque square' : 'transparent'}</p><img class="composite" src="${h(path.basename(o.review))}" alt="${h(o.id)}"><p>Source sha256 ${h(o.source.sha256)} · output sha256 ${h(o.sha256)}${o.notes ? ' · ' + h(o.notes) : ''}</p></article>`).join('\n');
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Altair Kit V1</title><style>body{margin:0;background:#17202a;color:#f4efe2;font:16px system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:24px}h1{margin-bottom:4px}small,.meta{color:#bac4ce}article{background:#263441;border:1px solid #455765;border-radius:12px;padding:18px;margin:18px 0}img.composite{display:block;max-width:100%;max-height:480px;image-rendering:pixelated;background:linear-gradient(45deg,#35434d 25%,transparent 25%),linear-gradient(-45deg,#35434d 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#35434d 75%),linear-gradient(-45deg,transparent 75%,#35434d 75%);background-size:16px 16px;background-position:0 0,0 8px,8px -8px,-8px 0}.layers{display:flex;gap:12px;flex-wrap:wrap}figure{margin:0;padding:8px;background:#17202a}figure img{max-width:250px;max-height:250px;image-rendering:pixelated}figcaption{font-size:12px}.warning{padding:12px;border-left:4px solid #e6b450;background:#283b4a}</style><main><h1>Altair Kit V1</h1><p class="meta">Layered building and sign study · generated sources preserved byte-for-byte · bound in the Unity chapter build</p><p class="warning">Review the assembled building PNGs, each separate layer, sign/prop/terrain tiles, source hashes, entrance anchors, and runtime collision references. Reference matches remain approximate; the Unity chapter imports these layers from the AI-Art checkout.</p><p><a href="contact-sheet.png">Nine-building contact sheet</a></p>${cards}${extras}</main></html>`;
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
