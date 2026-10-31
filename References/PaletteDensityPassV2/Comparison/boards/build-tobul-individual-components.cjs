let sharp;
try { sharp=require('sharp'); }
catch { sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),source=path.join(root,'crops/tobul-room-viewport.png'),proof=path.join(root,'proof-inputs/tobul-recreation.png');
const W=1140,bg='#111820',card='#202e38',ink='#edf3f7',soft='#b8c5ce',accent='#9ed4ff';
const rows=[
 {name:'Cream and timber wall bay',r:{left:90,top:0,width:90,height:105},scale:3,note:'One stocked wall display bay with cream panel and timber framing.'},
 {name:'Bare red-floor swatch',r:{left:390,top:260,width:42,height:60},scale:5,note:'Bare floor texture between the rug edge and stool/workbench; no fixture enters this sample.'},
 {name:'Full rug crop',r:{left:45,top:240,width:370,height:200},scale:1,note:'Full available rug area; the reference crop contains customers/dialogue overlap at its top edge, omitted in the static candidate.'},
 {name:'Chest fixture',r:{left:210,top:65,width:105,height:75},scale:3,note:'Chest-like fixture behind the service counter; same source-relative crop.'},
 {name:'Display racks',r:{left:340,top:45,width:115,height:95},scale:3,note:'Weapon display racks and timber framing; same source-relative crop.'},
 {name:'Gold L-counter context',r:{left:0,top:75,width:350,height:140},scale:1,note:'Counter and its return shown in room context; crop dimensions and scale match.'}
];
function esc(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function svg(w,h,body){return Buffer.from(`<svg width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg">${body}</svg>`);}
(async()=>{
 if(!fs.existsSync(proof))throw new Error(`Missing normalized weapon-shop proof ${proof}`);
 const meta=await sharp(proof).metadata();
 if(meta.width!==534||![440,441].includes(meta.height))throw new Error(`Expected 534×440 or 534×441 candidate, got ${meta.width}×${meta.height}`);
 const candidate=meta.height===441?await sharp(proof).extract({left:0,top:0,width:534,height:440}).png().toBuffer():fs.readFileSync(proof);
 let y=105, parts=[{input:svg(W,100,`<rect width="100%" height="100%" fill="${bg}"/><text x="28" y="36" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="24" font-weight="700">Tobul shop · component details at matched scale</text><text x="28" y="64" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="14">Every pair uses the same source-relative rectangle; both sides enlarged by the same nearest-neighbor factor shown per row.</text>`),left:0,top:0}];
 for(const row of rows){
  const {width,height}=row.r,dispW=width*row.scale,dispH=height*row.scale,cardH=Math.max(dispH,210)+90;
  const txt=svg(W,cardH+20,`<rect x="12" y="0" width="1116" height="${cardH}" rx="8" fill="${card}"/><text x="28" y="25" fill="${accent}" font-family="Segoe UI,Arial,sans-serif" font-size="17" font-weight="700">${esc(row.name)}</text><text x="28" y="45" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="12">${esc(row.note)}</text><text x="28" y="65" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="12" font-weight="600">ORIGINAL FFII PR · ${width}×${height} · ${row.scale}×</text><text x="582" y="65" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="12" font-weight="600">NEW STATIC RECREATION · ${width}×${height} · ${row.scale}×</text>`);
  parts.push({input:txt,left:0,top:y});
  const top=y+76+(dispH<210?(210-dispH)/2:0);
  const ref=await sharp(source).extract(row.r).resize(dispW,dispH,{kernel:'nearest'}).png().toBuffer();
  const cand=await sharp(candidate).extract(row.r).resize(dispW,dispH,{kernel:'nearest'}).png().toBuffer();
  if(dispW>534)throw new Error(`${row.name} image too wide for comparison column`);
  parts.push({input:ref,left:24,top});parts.push({input:cand,left:582,top});
  y+=cardH+18;
 }
 await sharp({create:{width:W,height:y+10,channels:3,background:bg}}).composite(parts).png().toFile(path.join(__dirname,'tobul-individual-components.png'));
 console.log(`Built six matched source-relative component pairs; candidate source ${meta.width}×${meta.height}${meta.height===441?' (trimmed one final bottom row)':''}.`);
})().catch(e=>{console.error(e);process.exitCode=1;});
