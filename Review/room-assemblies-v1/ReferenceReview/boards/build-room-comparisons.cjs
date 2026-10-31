let sharp;
try { sharp=require('sharp'); }
catch { sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),ink='#edf3f7',soft='#b8c5ce',bg='#111820',accent='#9ed4ff';
const rooms=[
 {id:'tobul',name:'Tobul weapon shop',note:'Static room assembly; PR reference includes two customers and a dialogue bubble.',w:534,h:440},
 {id:'scott',name:'Scott refuge room',note:'Static room assembly; reference crop includes transient character/dialogue and clips at the lower viewport edge.',w:534,h:390},
 {id:'hilda',name:'Hilda throne room',note:'Static room assembly; reference crop excludes dialogue/menu overlays but retains the party and attendant.',w:1380,h:463}
];
function esc(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function labelSvg(width,height,rows){const text=rows.map(r=>`<text x="${r.x}" y="${r.y}" fill="${r.color||ink}" font-family="Segoe UI,Arial,sans-serif" font-size="${r.size||15}" font-weight="${r.weight||'normal'}">${esc(r.text)}</text>`).join('');return Buffer.from(`<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="${bg}"/>${text}</svg>`);}
(async()=>{
 const entries=[];
 for(const r of rooms){
  const ref=path.join(root,'crops',`${r.id}-reference.png`),proof=path.join(root,'room-proofs',`${r.id}.png`);
  if(!fs.existsSync(proof)){entries.push({id:r.id,status:'pending',expectedDimensions:[r.w,r.h],proofFile:`room-proofs/${r.id}.png`});continue;}
  const rm=await sharp(ref).metadata(),pm=await sharp(proof).metadata();
  if(rm.width!==r.w||rm.height!==r.h)throw new Error(`${r.id} reference crop must be ${r.w}×${r.h}, got ${rm.width}×${rm.height}`);
  if(pm.width!==r.w||pm.height!==r.h)throw new Error(`${r.id} normalized composite must be exactly ${r.w}×${r.h}, got ${pm.width}×${pm.height}. No resizing/cropping allowed.`);
  const W=2*r.w+72,top=126,H=top+r.h+64;
  const board=labelSvg(W,H,[
   {x:24,y:34,text:`${r.name} · reference vs static room assembly`,size:24,weight:'700'},
   {x:24,y:61,text:`Both native crops are ${r.w}×${r.h}; no resize or crop applied.`,size:14,color:soft},
   {x:24,y:92,text:'ORIGINAL FFII PIXEL REMASTER',size:15,weight:'600'},
   {x:r.w+48,y:92,text:'NEW STATIC ROOM ASSEMBLY',size:15,weight:'600'},
   {x:24,y:H-20,text:r.note,size:13,color:soft}
  ]);
  const layers=[{input:board,left:0,top:0},{input:fs.readFileSync(ref),left:24,top},{input:fs.readFileSync(proof),left:r.w+48,top}];
  const out=path.join(__dirname,`${r.id}-side-by-side.png`);
  await sharp({create:{width:W,height:H,channels:3,background:bg}}).composite(layers).png().toFile(out);
  entries.push({id:r.id,status:'ready',dimensions:[r.w,r.h],referenceFile:`crops/${r.id}-reference.png`,referenceSha256:sha(fs.readFileSync(ref)),proofFile:`room-proofs/${r.id}.png`,proofSha256:sha(fs.readFileSync(proof)),boardFile:`boards/${r.id}-side-by-side.png`,boardSha256:sha(fs.readFileSync(out)),display:'Native pixel dimensions, equal 1× display factor.'});
 }
 fs.writeFileSync(path.join(root,'room-proof-manifest.json'),JSON.stringify({date:'2026-10-31',scope:'Static reference-based room assembly comparison; no gameplay/UI fidelity claim.',rooms:entries},null,2)+'\n');
 console.log(`Room boards: ${entries.filter(e=>e.status==='ready').length} ready; ${entries.filter(e=>e.status==='pending').length} pending.`);
})().catch(e=>{console.error(e);process.exitCode=1;});
