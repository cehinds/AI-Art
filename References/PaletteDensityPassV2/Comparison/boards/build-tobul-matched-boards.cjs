let sharp;
try { sharp=require('sharp'); }
catch { sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const path=require('path'),fs=require('fs');
const root=path.resolve(__dirname,'..'),proof=path.join(root,'proof-inputs/tobul-recreation.png');
const source=path.join(root,'crops/tobul-room-viewport.png');
const W=1140,ink='#edf3f7',soft='#b8c5ce',bg='#111820',card='#202e38',accent='#9ed4ff';
const upper={left:0,top:0,width:534,height:200};
const service={left:0,top:0,width:430,height:225};
const floorRug={left:0,top:200,width:534,height:240};
function esc(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function normalizedProof(){
 if(!fs.existsSync(proof)) throw new Error(`Missing final normalized proof: ${proof}`);
 const m=await sharp(proof).metadata();
 if(m.width!==534||![440,441].includes(m.height)) throw new Error(`Expected 534×440 or 534×441 proof, received ${m.width}×${m.height}`);
 if(m.height===441) return {image:await sharp(proof).extract({left:0,top:0,width:534,height:440}).png().toBuffer(),note:'Candidate was 534×441; only the final bottom row was cropped to the locked 534×440 reference.'};
 return {image:fs.readFileSync(proof),note:'Candidate and locked FFII PR viewport are both 534×440; no scaling or crop applied.'};
}
function textLayer(height,lines){
 const title=lines.map(l=>`<text x="${l.x??28}" y="${l.y}" fill="${l.color||ink}" font-family="Segoe UI,Arial,sans-serif" font-size="${l.size||15}" font-weight="${l.weight||'normal'}">${esc(l.text)}</text>`).join('');
 return Buffer.from(`<svg width="${W}" height="${height}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="${bg}"/>${title}</svg>`);
}
async function imageAt(file,rect,x,y){
 const im=rect?await sharp(file).extract(rect).png().toBuffer():fs.readFileSync(file);
 return {input:im,left:x,top:y};
}
(async()=>{
 const p=await normalizedProof();
 const fullH=670,full=[];
 full.push({input:textLayer(fullH,[
  {x:28,y:35,text:'Tobul weapon shop · same viewport, same displayed pixel scale',size:25,weight:'700'},
  {x:28,y:62,text:'Actual FFII PR source crop and new candidate both shown at 534×440; no resizing.',size:14,color:soft},
  {x:24,y:110,text:'ORIGINAL FFII PIXEL REMASTER · Tobul screenshot crop',size:15,weight:'600'},
  {x:582,y:110,text:'NEW RECREATION · locked composition target',size:15,weight:'600'},
  {x:28,y:630,text:p.note,size:13,color:soft}
 ]),left:0,top:0});
 full.push(await imageAt(source,null,24,130));
 full.push({input:p.image,left:582,top:130});
 await sharp({create:{width:W,height:fullH,channels:3,background:bg}}).composite(full).png().toFile(path.join(__dirname,'tobul-viewport-matched-scale.png'));

 const rows=[
  {title:'Upper wall, stocked displays and counter',rect:upper,h:200,caption:'Same 534×200 source-relative crop from the locked viewport.'},
  {title:'Service zone · merchant and L-counter',rect:service,h:225,caption:'Same 430×225 source-relative crop; merchant/counter anchor positions remain comparable.'},
  {title:'Red floor, rug and foreground customers',rect:floorRug,h:240,caption:'Same 534×240 source-relative crop; rug, customer scale and floor coverage remain visible.'}
 ];
 let total=98;for(const r of rows)total+=r.h+90;
 const parts=[{input:textLayer(total,[
  {x:28,y:36,text:'Tobul shop components · identical source-relative crops',size:24,weight:'700'},
  {x:28,y:65,text:'Both sides use exact same crop rectangles from the 534×440 viewport; no component zoom or image resizing.',size:14,color:soft}
 ]),left:0,top:0}];
 let y=98;
 for(const row of rows){
  const cardSvg=Buffer.from(`<svg width="${W}" height="${total}" xmlns="http://www.w3.org/2000/svg"><rect x="14" y="${y}" width="1112" height="${row.h+80}" rx="8" fill="${card}"/><text x="28" y="${y+24}" fill="${accent}" font-family="Segoe UI,Arial,sans-serif" font-size="17" font-weight="700">${esc(row.title)}</text><text x="28" y="${y+45}" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="12">${esc(row.caption)}</text><text x="28" y="${y+64}" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="12" font-weight="600">FFII PR REFERENCE</text><text x="582" y="${y+64}" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="12" font-weight="600">NEW CANDIDATE</text></svg>`);
  parts.push({input:cardSvg,left:0,top:0});
  parts.push(await imageAt(source,row.rect,24,y+70));
  parts.push({input:await sharp(p.image).extract(row.rect).png().toBuffer(),left:582,top:y+70});
  y+=row.h+90;
 }
 await sharp({create:{width:W,height:total,channels:3,background:bg}}).composite(parts).png().toFile(path.join(__dirname,'tobul-components-matched-scale.png'));
 console.log(`Built matched-scale Tobul boards. ${p.note}`);
})();
