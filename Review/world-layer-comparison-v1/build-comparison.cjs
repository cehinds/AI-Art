'use strict';

// Build reference-only crops, a contact sheet, and an HTML catalog. Never writes to Assets/.
const fs = require('node:fs');
const path = require('node:path');
const { sharp } = require('../../Tools/remaster-expansion/common.cjs');

const root = path.resolve(__dirname, '../..');
const refRoot = path.join(root, 'References/WorldLayerComparisonV1');
const register = JSON.parse(fs.readFileSync(path.join(refRoot, 'crop-register.json'), 'utf8'));
const sourceManifest = JSON.parse(fs.readFileSync(path.join(refRoot, 'sources.json'), 'utf8'));
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

async function crop(source, rect, output) {
  const input = path.join(refRoot, source);
  const meta = await sharp(input).metadata();
  if (!rect || rect.x < 0 || rect.y < 0 || rect.width <= 0 || rect.height <= 0 || rect.x + rect.width > meta.width || rect.y + rect.height > meta.height)
    throw Error(`Crop out of bounds in ${source}: ${JSON.stringify(rect)}`);
  const out = path.join(refRoot, 'crops', output);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  await sharp(input).extract({ left: rect.x, top: rect.y, width: rect.width, height: rect.height }).png().toFile(out);
  return `../../References/WorldLayerComparisonV1/crops/${output}`;
}

async function main() {
  const records = [];
  for (const item of register.categories) {
    const prFile = `${item.id}-pr.png`;
    const prRel = await crop(item.reference.file, item.reference.rect, prFile);
    let currentRel = null;
    if (item.current) currentRel = await crop(item.current.file, item.current.rect, `${item.id}-before.png`);
    records.push({ ...item, generatedCrops: { reference: prRel, current: currentRel } });
  }

  const cardW = 1720, cardH = 230, leftX = 18, midX = 586, rightX = 1154, imageW = 548, imageH = 158, topY = 55;
  const cards = [];
  for (let i = 0; i < records.length; i++) {
    const item = records[i];
    const refCropPath = path.join(root, records[i].generatedCrops.reference.replace('../../', ''));
    const refThumb = await sharp(refCropPath).resize(imageW, imageH, { fit: 'contain', kernel: 'nearest', background: { r: 22, g: 30, b: 40, alpha: 1 } }).png().toBuffer();
    const currentThumb = item.generatedCrops.current
      ? await sharp(path.join(root, item.generatedCrops.current.replace('../../', ''))).resize(imageW, imageH, { fit: 'contain', kernel: 'nearest', background: { r: 22, g: 30, b: 40, alpha: 1 } }).png().toBuffer()
      : await sharp(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${imageW}" height="${imageH}"><rect width="100%" height="100%" fill="#222c36"/><text x="24" y="86" fill="#c9d3dd" font-family="sans-serif" font-size="20">Not visible in the supplied current BEFORE viewport</text></svg>`)).png().toBuffer();
    const candidateFiles = item.asset.candidates || [];
    let candidateThumb;
    if (candidateFiles.length === 1) {
      candidateThumb = await sharp(path.join(root, candidateFiles[0])).resize(imageW, imageH, { fit: 'contain', kernel: 'nearest', background: { r: 22, g: 30, b: 40, alpha: 1 } }).png().toBuffer();
    } else if (candidateFiles.length > 1) {
      const half = await Promise.all(candidateFiles.map(file => sharp(path.join(root, file)).resize(Math.floor(imageW / 2) - 6, imageH, { fit: 'contain', kernel: 'nearest', background: { r: 22, g: 30, b: 40, alpha: 0 } }).png().toBuffer()));
      candidateThumb = await sharp({ create: { width: imageW, height: imageH, channels: 4, background: { r: 22, g: 30, b: 40, alpha: 1 } } }).composite(half.map((input, n) => ({ input, left: n * Math.floor(imageW / 2), top: 0 }))).png().toBuffer();
    } else {
      const message = item.asset.status?.replace(/&/g, '&amp;').replace(/</g, '&lt;') || 'No new V1 candidate art yet';
      candidateThumb = await sharp(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${imageW}" height="${imageH}"><rect width="100%" height="100%" fill="#222c36"/><text x="18" y="48" fill="#d2dce6" font-family="sans-serif" font-size="17">No new candidate art</text><text x="18" y="78" fill="#aab8c4" font-family="sans-serif" font-size="13">${escapeHtml(message).slice(0, 85)}</text></svg>`)).png().toBuffer();
    }
    const label = escapeHtml(item.label);
    const cardSvg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${cardW}" height="${cardH}"><rect width="100%" height="100%" rx="10" fill="#263441"/><text x="18" y="27" fill="#f4efe2" font-family="sans-serif" font-size="18">${label}</text><text x="${leftX}" y="48" fill="#a9d3ff" font-family="sans-serif" font-size="13">PIXEL REMASTER REFERENCE</text><text x="${midX}" y="48" fill="#f2c27b" font-family="sans-serif" font-size="13">CURRENT · BEFORE OCEAN FIX</text><text x="${rightX}" y="48" fill="#c4f1be" font-family="sans-serif" font-size="13">OPENINGWORLD V1 · NOT INTEGRATED</text><rect x="${leftX}" y="${topY}" width="${imageW}" height="${imageH}" fill="#111820"/><rect x="${midX}" y="${topY}" width="${imageW}" height="${imageH}" fill="#111820"/><rect x="${rightX}" y="${topY}" width="${imageW}" height="${imageH}" fill="#111820"/></svg>`);
    const card = await sharp(cardSvg).composite([{ input: refThumb, left: leftX, top: topY }, { input: currentThumb, left: midX, top: topY }, { input: candidateThumb, left: rightX, top: topY }]).png().toBuffer();
    cards.push({ input: card, left: 0, top: i * cardH });
  }
  const contact = path.join(__dirname, 'comparison-contact-sheet.png');
  await sharp({ create: { width: cardW, height: cardH * records.length, channels: 4, background: { r: 18, g: 25, b: 34, alpha: 1 } } }).composite(cards).png().toFile(contact);

  const rows = records.map(item => {
    const refName = path.basename(item.generatedCrops.reference);
    const curName = item.generatedCrops.current ? path.basename(item.generatedCrops.current) : null;
    const ref = item.reference.rect;
    const current = item.current?.rect;
    const source = escapeHtml(item.reference.file);
    const candidates = item.asset.candidates || [];
    const candidateHtml = candidates.length
      ? candidates.map(file => `<figure class="candidate"><figcaption>Candidate · ${escapeHtml(file.split('/').pop())} · not integrated</figcaption><img src="../../${escapeHtml(file)}" alt="${escapeHtml(file.split('/').pop())} candidate artwork"></figure>`).join('')
      : '<div class="missing">No generated OpeningWorldV1 art for this layer yet. Existing assets and pending replacements are listed below.</div>';
    const currentAssets = (item.asset.currentAssets || []).map(file => `<code>${escapeHtml(file)}</code>`).join('<br>') || 'None recorded.';
    return `<section class="layer"><h2>${escapeHtml(item.label)}</h2><div class="pair three"><figure><figcaption>Pixel Remaster crop · ${source} · x=${ref.x}, y=${ref.y}, ${ref.width}×${ref.height}</figcaption><img src="../../References/WorldLayerComparisonV1/crops/${escapeHtml(refName)}" alt="${escapeHtml(item.label)} Pixel Remaster reference crop"></figure><figure><figcaption>${item.current ? `Current BEFORE crop · x=${current.x}, y=${current.y}, ${current.width}×${current.height}` : 'No matching settlement visible in current BEFORE viewport'}</figcaption>${curName ? `<img src="../../References/WorldLayerComparisonV1/crops/${escapeHtml(curName)}" alt="${escapeHtml(item.label)} current before crop">` : '<div class="missing">Not visible in supplied current viewport</div>'}</figure><div><div class="candidate-pair">${candidateHtml}</div><p class="asset-state">${escapeHtml(item.asset.status || 'No new candidate art yet.')}</p><details><summary>Existing/frozen asset paths</summary>${currentAssets}</details></div></div><p>${escapeHtml(item.reading)}</p><div class="contract"><strong>Recommended stable asset contract</strong><br><code>${escapeHtml(item.asset.id)}</code> · ${escapeHtml(item.asset.layer)}<br><b>Size:</b> ${escapeHtml(item.asset.nativeSize)}<br><b>Edge ports / anchors:</b> ${escapeHtml(item.asset.ports)}<br><b>Gap:</b> ${escapeHtml(item.asset.gap)}</div></section>`;
  }).join('\n');
  const html = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FFII PR World Layer Comparison V1</title><style>body{margin:0;background:#101820;color:#edf2f7;font:16px/1.5 system-ui,sans-serif}main{max-width:1600px;margin:auto;padding:28px}h1{margin-bottom:6px}.lead,.source{color:#c1ccd8}a{color:#93c5fd}.warning{background:#382c1a;border-left:4px solid #eab95e;padding:14px;margin:18px 0}.contact{display:block;max-width:100%;image-rendering:pixelated}.layer{border:1px solid #405260;background:#1c2832;padding:18px;margin:24px 0;border-radius:12px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}.pair.three{grid-template-columns:1fr 1fr 1fr}figure{margin:0;background:#111820;padding:10px}figcaption{font-size:13px;color:#b9c7d4;margin-bottom:8px}figure img{max-width:100%;max-height:280px;display:block;image-rendering:pixelated}.candidate-pair{display:flex;gap:8px}.candidate{flex:1;min-width:0}.asset-state{color:#c4f1be;font-size:13px}.missing{min-height:158px;display:grid;place-items:center;text-align:center;color:#bdc7d2;background:#222c36;padding:8px}.contract{background:#15212a;padding:12px;border-radius:8px}.contract code{color:#ffd88b;overflow-wrap:anywhere}.source li{margin:4px 0}details{font-size:12px;overflow-wrap:anywhere}@media(max-width:1000px){.pair.three{grid-template-columns:1fr}}</style><main><h1>FFII Pixel Remaster world layers · comparison V1</h1><p class="lead">Pixel Remaster reference crops, the supplied current game capture labeled BEFORE ocean fix, and generated OpeningWorldV1 candidates. The generated candidates are AI-Art assets only and have not been integrated into the game.</p><div class="warning"><b>Evidence limit:</b> the current screenshot predates the ocean fix and the current renderer binding is frozen/unbuilt. Do not treat its ocean, coast, or settlement visibility as a post-fix runtime result. The Gatrea-to-Fynn 06 source is a black frame and excluded from visual comparisons. Candidate asset thumbnails below do not establish runtime fidelity.</div><h2>Annotated crop contact sheet</h2><img class="contact" src="comparison-contact-sheet.png" alt="Annotated comparison contact sheet"><h2>Current OpeningWorldV1 candidate sheet</h2><p><a href="../../Review/opening-world-v1/contact-sheet.png">Open the four new world art candidates</a> · shown separately here against the reference and BEFORE capture.</p><h2>Source provenance</h2><ul class="source"><li><a href="${escapeHtml(sourceManifest.pixelRemasterSource.walkthrough)}">Vorxu Altair &amp; Fynn guide</a> · <a href="${escapeHtml(sourceManifest.pixelRemasterSource.clips.altairToGatrea)}">Altair to Gatrea clip</a> · <a href="${escapeHtml(sourceManifest.pixelRemasterSource.clips.gatreaToFynn)}">Gatrea to Fynn clip</a>.</li><li><a href="${escapeHtml(sourceManifest.pixelRemasterSource.routeTextCrossCheck)}">Pro Game Guides route cross-check</a>.</li><li>Local raw captures and asset hashes: <a href="../../References/WorldLayerComparisonV1/sources.json">sources.json</a>. Exact per-frame timestamps were unavailable.</li><li>Reference crops are exact rectangle extractions under <code>References/WorldLayerComparisonV1/crops/</code>; the contact sheet scales them only for display. Crops are not production art.</li></ul>${rows}</main></html>`;
  fs.writeFileSync(path.join(__dirname, 'index.html'), html, 'utf8');
  fs.writeFileSync(path.join(refRoot, 'crop-catalog.json'), JSON.stringify({ ...register, categories: records }, null, 2) + '\n', 'utf8');
  console.log(`Wrote ${records.length} crop comparisons, HTML catalog and ${contact}`);
}

main().catch(error => { console.error(error.stack || error.message); process.exitCode = 1; });
