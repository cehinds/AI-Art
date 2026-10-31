let sharp;
try { sharp=require('sharp'); }
catch { sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),W=1120,gap=24,left=24,panel=524,bg='#111820',card='#202e38',ink='#edf3f7',soft='#b8c5ce',accent='#9ed4ff';
const rows=[
 {title:'Grass palette and pixel density',reference:'crops/overworld-grass.png',candidate:'proof-inputs/grass-recreation.png',w:90,h:60,scale:3,candidateTitle:'NEW V4 GRASS FIELD',note:'Same 90×60 source-relative crop; PR field sample mean RGB ≈ (106,175,55), V4 grass asset mean ≈ (105,179,54). Both displayed at 3× nearest-neighbor.'},
 {title:'Winding river tile proof · material and width',reference:'crops/overworld-river-winding.png',candidate:'proof-inputs/river-recreation.png',w:130,h:205,scale:3,candidateTitle:'NEW V4 WINDING TILE PROOF',note:'Both crops are 130×205 at 3×. The assembled candidate shows an independent winding layout; path placement differs from this screenshot crop, so compare water width, fringe and texture rather than scene composition.'},
 {title:'Canonical river scene · tile-assembled proof',reference:'crops/ffii-pr-river.png',candidate:'proof-inputs/river-canonical-recreation.png',candidateTitle:'NEW V4 CANONICAL TILE PROOF',w:130,h:270,scale:3,note:'Same 130×270 native crop and 3× display. Candidate is assembled from registered grass/river connector assets; the bridge and bend make the scene composition directly comparable.'},
 {title:'River scene art direction · matched portrait crop',reference:'crops/ffii-pr-river.png',candidate:'proof-inputs/river-art-direction-reconstruction.png',candidateTitle:'NEW REFERENCE RECONSTRUCTION',w:130,h:270,scale:3,note:'Original PR scene and new reference reconstruction use the same 130×270 native crop, each displayed at 3× nearest-neighbor. Reconstruction is newly generated, not assembled from connector tiles.'}
];
function esc(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function wrap(s,max=128){const words=s.split(/\s+/),lines=[];let line='';for(const w of words){if(line&&(line+' '+w).length>max){lines.push(line);line=w;}else line+=(line?' ':'')+w;}if(line)lines.push(line);return lines;}
async function image(file,w,h,scale){if(!fs.existsSync(file))throw new Error(`Missing candidate proof: ${file}`);const m=await sharp(file).metadata();if(m.width!==w||m.height!==h)throw new Error(`Expected ${w}×${h} at native crop scale; got ${m.width}×${m.height} for ${file}`);return sharp(file).resize(w*scale,h*scale,{kernel:'nearest'}).png().toBuffer();}
(async()=>{
 const available=rows.filter(r=>fs.existsSync(path.join(root,r.candidate)));
 if(!available.length)throw new Error('No normalized terrain proof inputs are present.');
 let H=120;for(const r of available)H+=Math.max(r.h*(r.scale||4),210)+wrap(r.note).length*15+120;
 const layers=[];
 layers.push({input:Buffer.from(`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="${bg}"/><text x="24" y="38" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="25" font-weight="700">FFII PR terrain · matched native crops and display scale</text><text x="24" y="66" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="14">Reference and candidate use identical native dimensions and equal nearest-neighbor display scale within each row.</text><text x="24" y="90" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="13">No independent perspective change or crop mismatch is accepted by this board builder.</text></svg>`),left:0,top:0});
 let y=120;
 for(const r of available){
  const scale=r.scale||4,notes=wrap(r.note),imgH=Math.max(r.h*scale,210),imageTop=79+notes.length*15,blockH=imageTop+imgH+12;
  const notesSvg=notes.map((line,i)=>`<text x="28" y="${y+47+i*15}" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="12">${esc(line)}</text>`).join('');
  layers.push({input:Buffer.from(`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg"><rect x="12" y="${y}" width="1096" height="${blockH}" rx="8" fill="${card}"/><text x="28" y="${y+25}" fill="${accent}" font-family="Segoe UI,Arial,sans-serif" font-size="18" font-weight="700">${esc(r.title)}</text>${notesSvg}<text x="28" y="${y+69+notes.length*15}" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600">ORIGINAL FFII PIXEL REMASTER · ${r.w}×${r.h} · ${scale}×</text><text x="572" y="${y+69+notes.length*15}" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600">${esc(r.candidateTitle||'NEW V2 ASSET')} · ${r.w}×${r.h} · ${scale}×</text></svg>`),left:0,top:0});
  const ref=await sharp(path.join(root,r.reference)).resize(r.w*scale,r.h*scale,{kernel:'nearest'}).png().toBuffer();
  const candidate=await image(path.join(root,r.candidate),r.w,r.h,scale);
  const top=y+imageTop+(imgH-r.h*scale)/2;
  layers.push({input:ref,left:left,top});
  layers.push({input:candidate,left:left+panel+gap,top});
  y+=blockH+22;
 }
 await sharp({create:{width:W,height:H,channels:3,background:bg}}).composite(layers).png().toFile(path.join(__dirname,'terrain-matched-scale.png'));
 const missing=rows.filter(r=>!fs.existsSync(path.join(root,r.candidate))).map(r=>r.candidate);
 console.log(`Built ${available.length} terrain comparison row(s) with equal native dimensions and matching per-row nearest-neighbor scale. Still pending: ${missing.join(', ')||'none'}`);
})();
