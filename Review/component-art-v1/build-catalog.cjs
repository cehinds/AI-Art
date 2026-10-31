const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '../..');
const reviewRoot = __dirname;
const out = path.join(__dirname, 'index.html');
const packs = {
  altair: path.join(root, 'Assets/Art/Production/AltairKitV1/manifest.json'),
  opening: path.join(root, 'Assets/Art/Production/OpeningWorldV1/manifest.json'),
  world: path.join(root, 'Assets/Art/Production/WorldComponentsV1/manifest.json'),
  seams: path.join(root, 'Assets/Art/Production/WorldComponentsV2/manifest.json'),
  interior: path.join(root, 'Assets/Art/Production/InteriorComponentsV1/manifest.json'),
  interiorV2: path.join(root, 'Assets/Art/Production/InteriorComponentsV2/manifest.json'),
  details: path.join(root, 'Assets/Art/Production/InteriorDetailsV3/manifest.json'),
};

function readManifest(file) {
  if (!fs.existsSync(file)) return null;
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}
function rel(file) { return path.relative(reviewRoot, path.resolve(root, file)).replaceAll(path.sep, '/'); }
function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function toCard({id, label, file, category, detail = '', pack, children = []}) {
  const exists = file && fs.existsSync(path.resolve(root, file));
  const href = exists ? rel(file) : '';
  const nested = children.map(child => {
    const childExists = child.file && fs.existsSync(path.resolve(root, child.file));
    const childHref = childExists ? rel(child.file) : '';
    return `<article class="childcard"><a class="checker" ${childExists ? `href="${esc(childHref)}"` : ''}><img loading="lazy" src="${esc(childHref)}" alt="${esc(child.label)}"></a><b>${esc(child.label)}</b><small>${esc(child.detail)}</small>${!childExists ? '<em>Manifest output missing</em>' : ''}</article>`;
  }).join('');
  const nestedHtml = nested ? `<details class="children"><summary>Layer and slice PNGs (${children.length})</summary><div class="childgrid">${nested}</div></details>` : '';
  return `<article class="card"><a class="checker" ${exists ? `href="${esc(href)}"` : ''} aria-label="${esc(label)}"><img loading="lazy" src="${esc(href)}" alt="${esc(label)}"></a><div class="cardtext"><b>${esc(label)}</b><span>${esc(detail || category)}</span>${!exists ? '<em>Manifest output missing</em>' : ''}<small>${esc(pack)} · ${esc(id)}</small></div>${nestedHtml}</article>`;
}
function altairCards(j) {
  if (!j) return [];
  const cards = [];
  for (const o of j.objects || []) {
    for (const [layer, data] of Object.entries(o.layers || {})) cards.push({id:`${o.id}-${layer}`,label:`${o.name}: ${layer}`,file:data.file,category:'city',detail:`${o.tileFootprint?.width}×${o.tileFootprint?.height} tiles · ${layer} layer`,pack:'AltairKitV1'});
    if (o.composite?.file) cards.push({id:`${o.id}-composite`,label:`${o.name}: assembled preview`,file:o.composite.file,category:'city',detail:`${o.tileFootprint?.width}×${o.tileFootprint?.height} tiles · roof + facade composite`,pack:'AltairKitV1'});
  }
  for (const x of j.extras || []) cards.push({id:x.id || x.key || path.basename(x.file || ''),label:x.name || x.id || x.key || path.basename(x.file || ''),file:x.file || x.output,category:(x.file || '').includes('/signs/')?'city':'world',detail:x.role || x.kind || x.file,pack:'AltairKitV1'});
  return cards;
}
function openingCards(j) {
  return (j?.assets || []).map(x => ({id:x.id,label:x.name || x.id,file:x.file,category:'world',detail:`${x.width}×${x.height}px · ${x.role || x.kind || 'opening-region component'}`,pack:'OpeningWorldV1'}));
}
function worldCards(j, pack = 'WorldComponentsV1') {
  return (j?.assets || []).map(x => {
    const f = x.file || '';
    const category = /river|coast|ocean|water|mouth/i.test(f + ' ' + (x.terrain || '')) ? 'water' : /mountain|forest|conifer|vegetation/i.test(f + ' ' + (x.terrain || '')) ? 'world' : /bridge/i.test(f + ' ' + (x.terrain || '')) ? 'water' : 'world';
    return {id:x.id || x.key,label:x.key || x.id,file:f,category,detail:`${x.width}×${x.height}px · ${x.terrain || x.layer || 'world component'} · ${x.visualStatus || 'candidate'}`,pack};
  });
}
function interiorCards(j) {
  if (!j) return [];
  const raw = j.assets || j.components || j.outputs || [];
  const entries = Array.isArray(raw) ? raw : Object.values(raw);
  return entries.map(x => {
    const subpath = x.file || x.output || x.path;
    const f = subpath && subpath.startsWith('Assets/') ? subpath : subpath && `Assets/Art/Production/InteriorComponentsV1/${subpath}`;
    const text = `${x.group || ''} ${x.category || ''} ${x.role || ''} ${x.kind || ''} ${f || ''}`;
    const category = /(^|[\s/_-])(ui|panel|tab|button|window)([\s/_.-]|$)/i.test(text) ? 'ui' : 'interior';
    const children = [
      ...Object.entries(x.layers || {}).map(([name,y])=>({name,kind:'layer',...y})),
      ...Object.entries(x.slices || {}).map(([name,y])=>({name,kind:'slice',...y})),
    ].map(y=>({id:`${x.id}-${y.kind}-${y.name}`,label:`${y.name} · ${y.kind}`,file:y.file,detail:`${y.size?.[0] || '?'}×${y.size?.[1] || '?'}px`,category,pack:'InteriorComponentsV1'}));
    return {id:x.id,label:x.name || x.id,file:f,category,detail:`${x.size?.[0] || '?'}×${x.size?.[1] || '?'}px · ${x.kind || x.role || x.group || 'interior component'}`,pack:'InteriorComponentsV1',children};
  });
}

function interiorV2Cards(j, pack = 'InteriorComponentsV2') {
  return (j?.assets || []).map(x=>({id:x.id,label:x.id,file:x.file,category:'interior',detail:x.width+'×'+x.height+'px · '+x.family,pack}));
}
const manifests = Object.fromEntries(Object.entries(packs).map(([k,v]) => [k,readManifest(v)]));
const groups = {
  world: [...openingCards(manifests.opening), ...worldCards(manifests.world), ...altairCards(manifests.altair).filter(x=>x.category==='world')].filter(x=>x.category==='world'),
  water: [...worldCards(manifests.world), ...worldCards(manifests.seams, 'WorldComponentsV2')].filter(x=>x.category==='water'),
  city: altairCards(manifests.altair).filter(x=>x.category==='city'),
  interior: [...interiorCards(manifests.interior).filter(x=>x.category==='interior'), ...interiorV2Cards(manifests.interiorV2), ...interiorV2Cards(manifests.details, 'InteriorDetailsV3')],
  ui: interiorCards(manifests.interior).filter(x=>x.category==='ui'),
};
const allCards = Object.values(groups).flat();
const uniqueFiles = new Set(allCards.flatMap(x=>[x.file,...(x.children||[]).map(c=>c.file)]).filter(Boolean));
const interiorManifestCount = Object.keys(manifests.interior?.components || {}).length;
const interiorPngCount = new Set(Object.values(manifests.interior?.components || {}).flatMap(x=>[x.file,...Object.values(x.layers||{}).map(y=>y.file),...Object.values(x.slices||{}).map(y=>y.file)]).filter(Boolean)).size;
const packPngCounts = {AltairKitV1:altairCards(manifests.altair).length,OpeningWorldV1:openingCards(manifests.opening).length,WorldComponentsV1:worldCards(manifests.world).length,WorldComponentsV2:worldCards(manifests.seams, 'WorldComponentsV2').length,InteriorComponentsV1:interiorPngCount,InteriorComponentsV2:interiorV2Cards(manifests.interiorV2).length,InteriorDetailsV3:interiorV2Cards(manifests.details, 'InteriorDetailsV3').length};
const categoryTitles = {world:'World terrain, vegetation and settlements',water:'Water, coasts, rivers and bridge candidates',city:'Altair buildings, signs and props',interior:'Interior walls, floors and furniture',ui:'UI panels and controls'};
const knownCounts = Object.fromEntries(Object.entries(groups).map(([k,v])=>[k,v.length]));
const total = allCards.length;
const missingPacks = Object.entries(manifests).filter(([,v])=>!v).map(([k])=>k);
const docs = '../../Docs/ComponentArtV1/README.md';
const links = [
  ['AltairKitV1 gallery','../altair-kit-v1/index.html'],
  ['OpeningWorldV1 contact sheet','../opening-world-v1/contact-sheet.png'],
  ['WorldComponentsV1 gallery','../world-components-v1/index.html'],
  ['WorldComponentsV2 seam-corrected tiles','../world-components-v2/index.html'],
  ['V2 Pixel Remaster comparison','../../References/WorldComponentsV2/Comparison/index.html'],
  ['InteriorComponentsV2 joined room kit','../interior-components-v2/index.html'],
  ['V2 interior reference comparison','../../References/InteriorComponentsV2/Comparison/index.html'],
  ['V3 refined interior assets','../interior-details-v3/index.html'],
  ['Original vs V3 side-by-side','../../References/InteriorDetailsV3/Comparison/index.html'],
  ['World layer comparison','../world-layer-comparison-v1/index.html'],
  ['WorldComponentsV1 visual limits','../../Docs/WorldComponentsV1/visual-review.md'],
].map(([a,b])=>`<a href="${b}">${a}</a>`);
links.push(manifests.interior ? '<a href="../interior-components-v1/index.html">InteriorComponentsV1 gallery</a>' : '<span>InteriorComponentsV1 gallery pending export</span>');
const sections = Object.entries(groups).map(([key,cards]) => {const childCount=cards.reduce((n,x)=>n+(x.children||[]).length,0);const countLabel=(key==='interior'||key==='ui')?`${cards.length} components · ${cards.length+childCount} PNG files (${childCount} layer/slice PNGs)`: `${cards.length} PNG files`;return `<section id="${key}"><h2>${categoryTitles[key]} <span>${countLabel}</span></h2>${cards.length?`<div class="grid">${cards.map(c=>toCard(c)).join('')}</div>`:`<p class="empty">No exported manifest entries yet. Rerun this generator after the pack export.</p>`}</section>`;}).join('\n');
const data = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FFII Component Art Review</title><style>
:root{color-scheme:dark;--bg:#15191d;--panel:#20262c;--line:#39434c;--text:#edf2f5;--muted:#aeb8c1;--accent:#9ed0ec}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:24px}header{padding:24px;background:linear-gradient(125deg,#29343d,#192126);border:1px solid var(--line);border-radius:12px}h1{margin:0 0 6px;font-size:30px}h2{margin:32px 0 12px;font-size:22px}h2 span{font-size:13px;color:var(--muted);font-weight:500;margin-left:8px}.status{display:inline-block;border:1px solid #c9995b;color:#ffd493;background:#3b2d1b;padding:4px 9px;border-radius:99px;font-weight:700}.notice{color:#f4d4a4;margin:12px 0}.links{color:var(--muted);margin-top:12px}.links a{color:var(--accent)}.summary{display:flex;gap:16px;flex-wrap:wrap;margin-top:14px;color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px}.card{overflow:hidden;background:var(--panel);border:1px solid var(--line);border-radius:8px}.checker{height:170px;display:grid;place-items:center;background-color:#e9e9e9;background-image:linear-gradient(45deg,#c7c7c7 25%,transparent 25%),linear-gradient(-45deg,#c7c7c7 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#c7c7c7 75%),linear-gradient(-45deg,transparent 75%,#c7c7c7 75%);background-size:16px 16px;background-position:0 0,0 8px,8px -8px,-8px 0}.checker img{max-width:100%;max-height:100%;object-fit:contain;image-rendering:pixelated}.cardtext{padding:9px;display:grid;gap:3px}.cardtext span,.cardtext small{color:var(--muted)}.cardtext small{font-size:11px;overflow-wrap:anywhere}.cardtext em{color:#ffcc87;font-style:normal}.children{padding:0 9px 10px}.children summary{cursor:pointer;color:var(--accent);font-size:12px}.childgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:6px;margin-top:7px}.childcard{min-width:0;background:#181d21;border:1px solid var(--line);border-radius:5px;padding:4px;display:grid;gap:3px;font-size:10px}.childcard .checker{height:68px;background-size:12px 12px}.childcard b,.childcard small{overflow-wrap:anywhere}.childcard small{color:var(--muted)}.empty{padding:16px;color:var(--muted);background:var(--panel);border-radius:8px}footer{color:var(--muted);border-top:1px solid var(--line);margin-top:36px;padding-top:15px;font-size:13px}
</style></head><body><main><header><h1>FFII component art review</h1><div class="status">CANDIDATES FOR REVIEW · GAME INTEGRATION ON HOLD</div><p>Combined native-scale inventory for world, city, interior and UI component packs. Checkerboard previews show transparency; select a preview to open its production PNG. Interior component cards expand to show their separately exported layers and slices.</p><p class="notice">The component art is not integrated into the game. V1 world tiles retain their recorded visual limitations. V2 coast and river tiles have verified four-pixel boundary continuity; the new comparison records remaining differences from Pixel Remaster.</p><div class="summary"><span>${uniqueFiles.size} unique production PNG files</span><span>${total} top-level manifest entries</span><span>InteriorComponentsV1: ${interiorManifestCount} components / ${interiorPngCount} PNG files</span><span>Pack PNG counts: ${Object.entries(packPngCounts).map(([k,v])=>`${k} ${v}`).join(' · ')}</span><span>Generated ${new Date().toISOString().slice(0,10)}</span><span>${missingPacks.length?`Manifest missing: ${missingPacks.join(', ')}`:'All configured pack manifests found'}</span></div><div class="links">${links.join(' · ')}<br><a href="${docs}">Catalog notes and refresh command</a></div></header>${sections}<footer>Inventory is generated from production manifests. Each pack retains its own source records and visual limitations. This page is for review only and makes no runtime, release, licensing or seamless-tiling claim.</footer></main></body></html>`;
fs.mkdirSync(__dirname,{recursive:true});
fs.writeFileSync(out,data);
console.log(`Wrote ${path.relative(root,out)} (${total} entries): ${JSON.stringify(knownCounts)}`);
if (missingPacks.length) console.log(`Missing manifests: ${missingPacks.join(', ')}`);
