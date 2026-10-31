let sharp;
try { sharp=require('sharp'); }
catch { sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const path=require('path'),fs=require('fs'),crypto=require('crypto');
const root=path.resolve(__dirname,'..');
const stageSourceRoot=path.resolve(root,'../Review/shop-interiors-v2/rooms');
const outRoot=path.join(root,'proof-inputs');
const ids=['weapon','armor','item','magic'];
const W=1120, panelW=534, panelH=440, scale=1, gap=24;
const bg='#111820', ink='#edf3f7', soft='#b8c5ce', card='#202e38', accent='#9ed4ff';
function esc(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const images=[];
 for(const id of ids){
  const snapshot=path.join(outRoot,`${id}-store-534x440.png`);
  const staged=path.join(stageSourceRoot,`${id}-reference-matched-534x440.png`);
  const f=fs.existsSync(snapshot)?snapshot:staged;
  if(!fs.existsSync(f)) throw new Error(`Missing copied snapshot or staged normalized proof for ${id}`);
  const meta=await sharp(f).metadata();
  if(meta.width!==534||meta.height!==440) throw new Error(`${id}: expected 534x440, got ${meta.width}x${meta.height}`);
  const b=fs.readFileSync(f), dst=snapshot;
  if(path.resolve(f)!==path.resolve(dst))fs.writeFileSync(dst,b);
  images.push({id,b,dst,hash:sha(b)});
 }
 const cellH=panelH+86, rows=2, H=88+rows*(cellH+18)+24;
 const layers=[{input:Buffer.from(`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="${bg}"/><text x="24" y="34" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="24" font-weight="700">Additional proposed shop-room variants</text><text x="24" y="60" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="14">Weapon is the Tobul-anchored recreation; armor, item and magic are proposed adaptations, not individually verified retail layouts.</text></svg>`),left:0,top:0}];
 for(let i=0;i<images.length;i++){
  const col=i%2,row=Math.floor(i/2),x=18+col*(panelW+26),y=78+row*(cellH+18);
  const title=images[i].id[0].toUpperCase()+images[i].id.slice(1)+' shop';
  const svg=Buffer.from(`<svg width="${panelW+16}" height="${cellH}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" rx="8" fill="${card}"/><text x="10" y="23" fill="${accent}" font-family="Segoe UI,Arial,sans-serif" font-size="16" font-weight="700">${esc(title)}</text><text x="10" y="44" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="12">New proposal · normalized 534×440 proof · shown 1:1</text><text x="10" y="65" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="12">NO MATCHING ORIGINAL ROOM CLAIM</text></svg>`);
  layers.push({input:svg,left:x,top:y});
  layers.push({input:images[i].b,left:x+8,top:y+74});
 }
 const dest=path.join(__dirname,'store-variants-contact-sheet.png');
 await sharp({create:{width:W,height:H,channels:3,background:bg}}).composite(layers).png().toFile(dest);
 fs.writeFileSync(path.join(root,'store-proof-manifest.json'),JSON.stringify({title:'Normalized proposed shop-room proof snapshots',source:'Copied normalized snapshots in proof-inputs/; these are review images, not generated reference captures.',files:images.map(x=>({file:path.basename(x.dst),width:534,height:440,sha256:x.hash,sourceFile:path.relative(root,x.dst).replaceAll('\\','/')})),note:'These are review snapshots only. Weapon is compared with the locked Tobul reference; armor, item and magic are concept adaptations without a matching room capture.'},null,2)+'\n');
 console.log(`Wrote ${dest} and ${images.length} snapshots.`);
})().catch(e=>{console.error(e);process.exitCode=1;});
