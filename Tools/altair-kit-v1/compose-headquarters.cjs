'use strict';

// Compose the full generated HQ hall plus a doorless left-side hall section.
// The original generated masters remain untouched under ArtSource.
const fs = require('node:fs');
const path = require('node:path');
const { sharp } = require('../remaster-expansion/common.cjs');

const root = path.resolve(__dirname, '../..');
async function trimResize(file, width, height) {
  const { data, info } = await sharp(file).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  let left = info.width, top = info.height, right = -1, bottom = -1;
  for (let y = 0; y < info.height; y++) for (let x = 0; x < info.width; x++) {
    if (data[(y * info.width + x) * 4 + 3] < 128) continue;
    left = Math.min(left, x); top = Math.min(top, y); right = Math.max(right, x); bottom = Math.max(bottom, y);
  }
  if (right < left || bottom < top) throw Error('HQ source has no visible pixels');
  return sharp(file).extract({ left, top, width: right - left + 1, height: bottom - top + 1 }).resize(width, height, { kernel: 'nearest' }).png().toBuffer();
}

(async () => {
  const master = 'ArtSource/AltairKitV1/sources/headquarters-centered.png';
  const normalized = await trimResize(path.join(root, master), 224, 160);
  const { data: sectionPixels, info: section } = await sharp(normalized).extract({ left: 0, top: 0, width: 96, height: 160 }).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  let left = section.width, top = section.height, right = -1, bottom = -1;
  for (let y = 0; y < section.height; y++) for (let x = 0; x < section.width; x++) {
    if (sectionPixels[(y * section.width + x) * 4 + 3] < 128) continue;
    left = Math.min(left, x); top = Math.min(top, y); right = Math.max(right, x); bottom = Math.max(bottom, y);
  }
  if (right < left || bottom < top) throw Error('Doorless HQ wing crop has no solid pixels');
  const wingCrop = { x: left, y: top, width: right - left + 1, height: bottom - top + 1 };
  const leftWingSection = await sharp(normalized).extract({ left: wingCrop.x, top: wingCrop.y, width: wingCrop.width, height: wingCrop.height }).resize(96, 160, { kernel: 'nearest' }).png().toBuffer();
  const composite = await sharp({ create: { width: 224, height: 288, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } })
    .composite([{ input: normalized, left: 0, top: 0 }, { input: leftWingSection, left: 128, top: 128 }]).png().toBuffer();
  const sourcePath = path.join(root, 'ArtSource/AltairKitV1/sources/headquarters-l-source-v4.png');
  const maskPath = path.join(root, 'ArtSource/AltairKitV1/masks/headquarters-l-roof-mask-v4.png');
  for (const p of [sourcePath, maskPath]) if (fs.existsSync(p)) throw Error('Preserving existing file; choose new version: ' + p);
  fs.writeFileSync(sourcePath, composite);

  const mask = Buffer.alloc(224 * 288);
  for (let y = 0; y < 288; y++) for (let x = 0; x < 224; x++) {
    const mainRoof = x < 224 && y < 90;
    const wingRoof = x >= 128 && y >= 128 && y < 212;
    mask[y * 224 + x] = mainRoof || wingRoof ? 255 : 0;
  }
  await sharp(mask, { raw: { width: 224, height: 288, channels: 1 } }).png().toFile(maskPath);
  console.log('Wrote HQ L source/mask V4: main hall 224x160, alpha-threshold-trimmed doorless left crop ' + JSON.stringify(wingCrop) + ' resized 96x160 at x128,y128; southwest notch remains transparent.');
})().catch(error => { console.error(error.message); process.exitCode = 1; });

