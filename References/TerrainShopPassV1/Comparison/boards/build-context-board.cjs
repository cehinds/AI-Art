let sharp;
try { sharp = require('sharp'); }
catch { sharp = require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const path = require('path');
const root = path.resolve(__dirname, '..');
const W=1140,rowH=260,panelW=540,panelH=142,H=110+rowH*2;
const bg='#111820',panel='#202e38',ink='#edf3f7',soft='#b8c5ce',accent='#9ed4ff';
const rows=[
  {title:'City trees and settlement context', note:'The FFII PR crop establishes Fynn settlement context but is not a clean individual city-tree sprite reference. Compare palette and silhouette only.', ref:'crops/fynn-settlement-marker.png', rl:'FFII PR Fynn marker · buildings and ground context', asset:'comparison-inputs/terrain-v3/city-trees-3x.png', al:'V3 conifer + broadleaf over city cobble'},
  {title:'Dirt-road treatment', note:'No clear dirt track is visible in the sampled FFII PR route scene. V3 dirt roads are an authored proposal, not a sourced retail match.', ref:'source-frames/pr-altair-to-gatrea-02.png', rl:'PR route scene · actor and minimap retained', asset:'comparison-inputs/terrain-v3/dirt-road-junctions-3x.png', al:'V3 dirt-road junction atlas'},
];
function esc(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function wrap(s,max=130){const words=s.split(/\s+/),lines=[];let line='';for(const w of words){if(line&&(line+' '+w).length>max){lines.push(line);line=w;}else line+=(line?' ':'')+w;}if(line)lines.push(line);return lines;}
(async()=>{
 const layers=[];
 layers.push({input:Buffer.from(`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="${bg}"/><text x="28" y="42" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="26" font-weight="700">Settlement trees and route-path evidence</text><text x="28" y="70" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="14">Actual FFII PR context crops at left · V3 candidate proofs at right · mismatched context is identified in captions</text><text x="28" y="94" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="13">No direct individual city-tree sprite or open-field dirt-road reference was found in the sampled sources.</text></svg>`),left:0,top:0});
 for(let i=0;i<rows.length;i++){
  const e=rows[i],y=110+i*rowH,notes=wrap(e.note).map((s,n)=>`<text x="38" y="${y+48+n*15}" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="12">${esc(s)}</text>`).join('');
  layers.push({input:Buffer.from(`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg"><rect x="20" y="${y}" width="1100" height="${rowH-10}" rx="8" fill="${panel}"/><text x="38" y="${y+26}" fill="${accent}" font-family="Segoe UI,Arial,sans-serif" font-size="18" font-weight="700">${esc(e.title)}</text>${notes}<text x="42" y="${y+80}" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600">ORIGINAL FFII PIXEL REMASTER · ${esc(e.rl)}</text><text x="600" y="${y+80}" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600">NEW V3 CANDIDATE · ${esc(e.al)}</text></svg>`),left:0,top:0});
  for(const [rel,x] of [[e.ref,40],[e.asset,598]]){const file=path.join(root,rel);const image=await sharp(file).resize(panelW,panelH,{fit:'inside',kernel:'nearest',background:bg}).png().toBuffer();const m=await sharp(image).metadata();layers.push({input:image,left:x+Math.floor((panelW-m.width)/2),top:y+92+Math.floor((panelH-m.height)/2)});}
 }
 const out=path.join(root,'boards/settlement-and-road-context-vs-v3.png');await sharp({create:{width:W,height:H,channels:3,background:bg}}).composite(layers).png().toFile(out);console.log(out);
})();
