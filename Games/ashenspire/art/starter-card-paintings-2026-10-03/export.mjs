import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const source = fileURLToPath(new URL('.', import.meta.url));
const root = resolve(source, '../..');
const { assets } = JSON.parse(readFileSync(resolve(source, 'prompts.json'), 'utf8'));
const output = resolve(root, 'hd/assets/cards');
mkdirSync(output, { recursive: true });
const receipts = [];
for (const asset of assets) {
  const master = resolve(source, asset.sourceFile);
  const exports = [];
  for (const width of [512, 1024]) {
    const name = `${asset.slug}-${width}.webp`;
    const target = resolve(output, name);
    execFileSync('cwebp', ['-quiet', '-m', '6', '-q', '86', '-resize', String(width), '0', master, '-o', target]);
    const bytes = readFileSync(target);
    exports.push({ id: `assets/cards/${name}`, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') });
  }
  receipts.push({ cardId: asset.cardId, source: asset.sourceFile, sourceSha256: createHash('sha256').update(readFileSync(master)).digest('hex'), exports });
}
writeFileSync(resolve(source, 'exports.json'), JSON.stringify({ encoder: execFileSync('cwebp', ['-version'], { encoding: 'utf8' }).trim(), quality: 86, assets: receipts }, null, 2) + '\n');
console.log('Exported three card paintings at 512 and 1024 pixels.');
