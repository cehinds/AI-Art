const fs = require('fs');
const path = require('path');
let sharp;
try { sharp = require('sharp'); }
catch { sharp = require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }

const root = path.resolve(__dirname, '..');
const dest = path.join(root, 'boards');
const out = path.join(dest, 'terrain-reference-vs-v3.png');
const W = 1140, rowH = 260, panelW = 540, panelH = 142;
const bg = '#111820', panel = '#202e38', ink = '#edf3f7', soft = '#b8c5ce', accent = '#9ed4ff';

const entries = [
  {
    title: 'Overworld grass',
    note: 'PR route field is brighter/limer; candidate grass reads darker and bluer/olive. Texture families are comparable, palette differs.',
    ref: path.join(root, 'crops/overworld-grass.png'), refLabel: 'FFII PR route crop · grass only',
    asset: path.join(root, 'comparison-inputs/terrain-v3/grass.png'), assetLabel: 'V3 grass tile · native 32×32, enlarged for viewing',
  },
  {
    title: 'River and bank',
    note: 'PR has a narrow cobalt channel, thin olive/earth fringe and sparse white highlights. V3 atlas uses a stronger cyan-green / orange edge; orthogonal atlas is topology proof, not natural river composition.',
    ref: path.join(root, 'crops/ffii-pr-river.png'), refLabel: 'FFII PR route crop · bend and bridge edge',
    asset: path.join(root, 'comparison-inputs/terrain-v3/river-junctions-3x.png'), assetLabel: 'V3 orthogonal river junction atlas',
  },
  {
    title: 'Forest and conifers',
    note: 'PR frame shows dense dark pointed conifer crowns. V3 forest field and city-tree preview use separate authored forms; city broadleaf is not present in this PR crop.',
    ref: path.join(root, 'crops/overworld-conifer-forest.png'), refLabel: 'FFII PR route crop · conifer forest edge',
    asset: path.join(root, 'comparison-inputs/terrain-v3/forest-field-3x.png'), assetLabel: 'V3 overworld forest field proof',
  },
  {
    title: 'Town cobble material',
    note: 'The reference town is not identified. Both show irregular stone; V3 tile appears paler and higher-contrast than the source crop.',
    ref: path.join(root, 'crops/other-town-cobble-material.png'), refLabel: 'FFII PR town crop · identity unconfirmed',
    asset: path.join(root, 'comparison-inputs/terrain-v3/city-cobble.png'), assetLabel: 'V3 city-cobble tile · native 32×32, enlarged',
  },
];

function esc(s) { return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function wrap(s, max=142) {
  const words = s.split(/\s+/), lines=[]; let line='';
  for (const word of words) { if (line && (line+' '+word).length > max) { lines.push(line); line=word; } else line += (line?' ':'')+word; }
  if (line) lines.push(line); return lines;
}

(async () => {
  const H = 110 + entries.length * rowH;
  const layers = [];
  const header = Buffer.from(`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="${bg}"/><text x="28" y="42" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="27" font-weight="700">Terrain materials · FFII PR reference and V3 candidate</text><text x="28" y="70" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="14">Actual preserved PR crops at left · native asset or current V3 proof at right · panels fit without distortion; display sizes are not a scale match</text><text x="28" y="94" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="13">Dirt-road appearance is not represented here because no matching PR route sample was found.</text></svg>`);
  layers.push({input: header, left: 0, top: 0});
  for (let i = 0; i < entries.length; i++) {
    const e = entries[i], y = 110 + i * rowH;
    const noteLines=wrap(e.note).slice(0,2).map((line,n)=>`<text x="38" y="${y+48+n*15}" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="12">${esc(line)}</text>`).join('');
    const cardSvg = Buffer.from(`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg"><rect x="20" y="${y}" width="1100" height="${rowH-10}" rx="8" fill="${panel}"/><text x="38" y="${y+26}" fill="${accent}" font-family="Segoe UI,Arial,sans-serif" font-size="18" font-weight="700">${esc(e.title)}</text>${noteLines}<text x="42" y="${y+80}" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600">ORIGINAL FFII PIXEL REMASTER · ${esc(e.refLabel)}</text><text x="600" y="${y+80}" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600">NEW V3 CANDIDATE · ${esc(e.assetLabel)}</text></svg>`);
    layers.push({input: cardSvg, left: 0, top: 0});
    for (const [file, x] of [[e.ref, 40], [e.asset, 598]]) {
      const resized = await sharp(file).resize(panelW, panelH, {fit:'inside',kernel:'nearest',background:bg}).png().toBuffer();
      const m = await sharp(resized).metadata();
      const top = y + 92 + Math.floor((panelH-m.height)/2);
      const left = x + Math.floor((panelW-m.width)/2);
      layers.push({input: resized, left, top});
    }
  }
  await sharp({create:{width:W,height:H,channels:3,background:bg}}).composite(layers).png().toFile(out);
  console.log(out);
})();
