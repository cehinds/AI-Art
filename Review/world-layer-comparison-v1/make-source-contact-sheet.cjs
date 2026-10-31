'use strict';

const path = require('node:path');
const { sharp } = require('../../Tools/remaster-expansion/common.cjs');

const sourceRoot = 'C:/repos/AI-Remake-FF2/Logs/opening-reference-20261030';
const items = [];
for (let i = 1; i <= 4; i++) items.push({ label: `PR Altair to Gatrea ${String(i).padStart(2, '0')}`, file: path.join(sourceRoot, `altair-to-gatrea-${String(i).padStart(2, '0')}.png`) });
for (let i = 1; i <= 6; i++) items.push({ label: `PR Gatrea to Fynn ${String(i).padStart(2, '0')}`, file: path.join(sourceRoot, `gatrea-to-fynn-${String(i).padStart(2, '0')}.png`) });
items.push({ label: 'CURRENT GAME · BEFORE ocean fix', file: 'C:/repos/AI-Remake-FF2/Logs/altair-coast-before-20261030.png' });

(async () => {
  const cardW = 440, cardH = 220, cols = 2, rows = Math.ceil(items.length / cols), cards = [];
  for (let i = 0; i < items.length; i++) {
    const thumbnail = await sharp(items[i].file).resize(410, 180, { fit: 'contain', kernel: 'nearest', background: { r: 22, g: 30, b: 40, alpha: 1 } }).png().toBuffer();
    const label = items[i].label.replace(/&/g, '&amp;').replace(/</g, '&lt;');
    const svg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${cardW}" height="${cardH}"><rect width="100%" height="100%" fill="#17202a"/><text x="12" y="22" fill="#f4efe2" font-family="sans-serif" font-size="15">${label}</text></svg>`);
    const card = await sharp(svg).composite([{ input: thumbnail, left: 15, top: 32 }]).png().toBuffer();
    cards.push({ input: card, left: (i % cols) * cardW, top: Math.floor(i / cols) * cardH });
  }
  const out = path.join(__dirname, 'source-contact-sheet.png');
  await sharp({ create: { width: cardW * cols, height: cardH * rows, channels: 4, background: { r: 13, g: 19, b: 26, alpha: 1 } } }).composite(cards).png().toFile(out);
  console.log(out);
})().catch(error => { console.error(error.stack || error.message); process.exitCode = 1; });
