// Run from the repo root: node art/footer-atelier/export.mjs <path-to-sharp>
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const sharp = require(process.argv[2] || 'sharp');
const here = dirname(fileURLToPath(import.meta.url));
const dest = resolve(here, '../../hd/assets/ui/footer');
mkdirSync(dest, { recursive: true });
const sha256 = (file) => createHash('sha256').update(readFileSync(file)).digest('hex');
const rows = [];
for (const id of ['plate', 'draw', 'spent-cards', 'potions', 'connector']) {
  const source = resolve(here, `${id}.png`);
  const { data, info } = await sharp(source).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  let left = info.width, top = info.height, right = -1, bottom = -1;
  for (let y = 0; y < info.height; y++) for (let x = 0; x < info.width; x++) {
    if (data[(y * info.width + x) * 4 + 3] > 20) {
      left = Math.min(left, x); top = Math.min(top, y);
      right = Math.max(right, x); bottom = Math.max(bottom, y);
    }
  }
  if (right < left) throw new Error(`${id}: no visible alpha`);
  const crop = { left, top, width: right - left + 1, height: bottom - top + 1 };
  const max = id === 'plate' ? 768 : 512;
  const target = resolve(dest, `${id}.webp`);
  await sharp(source).extract(crop).resize({ width: max, height: max, fit: 'inside', withoutEnlargement: true })
    .webp({ quality: 90, alphaQuality: 100, effort: 6 }).toFile(target);
  const metadata = await sharp(target).metadata();
  rows.push({ id: `assets/ui/footer/${id}.webp`, source: `${id}.png`, sourceSha256: sha256(source),
    sourceSize: { width: info.width, height: info.height }, crop,
    high: { width: metadata.width, height: metadata.height, bytes: readFileSync(target).length, sha256: sha256(target), alpha: metadata.hasAlpha } });
}
writeFileSync(resolve(here, 'export-receipt.json'), JSON.stringify({
  alphaThreshold: 20, encoding: 'Sharp WebP quality 90, alphaQuality 100, effort 6; fit inside maximum dimensions without enlargement',
  sharpVersions: sharp.versions, components: rows,
}, null, 2) + '\n');
console.log(JSON.stringify(rows, null, 2));
