let sharp;
try { sharp=require('sharp'); }
catch { sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=__dirname,failures=[],checked=[];
function read(name){return JSON.parse(fs.readFileSync(path.join(root,name),'utf8'));}
function hash(file){return crypto.createHash('sha256').update(fs.readFileSync(path.join(root,file))).digest('hex');}
function verifyFile(file,want,context){
 const f=path.join(root,file);
 if(!fs.existsSync(f)){failures.push(`${context}: missing ${file}`);return false;}
 if(want&&hash(file).toLowerCase()!==want.toLowerCase())failures.push(`${context}: SHA-256 mismatch for ${file}`);
 checked.push(file);return true;
}
(async()=>{
 const sources=read('source-manifest.json');
 for(const s of sources.sources||[])verifyFile(s.file,s.sha256,'source manifest');
 const crops=read('reference-crop-manifest.json');
 for(const e of crops.entries||[])verifyFile(e.file,e.cropSha256,'crop manifest');
 const store=read('store-proof-manifest.json');
 for(const e of store.files||[])verifyFile(e.sourceFile||path.join('proof-inputs',e.file),e.sha256,'store proof manifest');
 const terrainPath=path.join(root,'terrain-proof-manifest.json');
 if(fs.existsSync(terrainPath)){
  const terrain=read('terrain-proof-manifest.json');
  for(const e of terrain.entries||[]){
   verifyFile(e.file,e.sha256,'terrain proof manifest');
   if(e.provenanceFile)verifyFile(e.provenanceFile,e.provenanceSha256,'terrain proof provenance');
   if(e.sourceMasterFile)verifyFile(e.sourceMasterFile,e.sourceMasterSha256,'terrain source master');
   if(e.sourceFile&&e.sourceSha256)verifyFile(e.sourceFile,e.sourceSha256,'terrain source snapshot');
  }
  for(const e of terrain.iterations||[]){verifyFile(e.file,e.sha256,'terrain iteration');if(e.provenanceFile)verifyFile(e.provenanceFile,e.provenanceSha256,'terrain iteration provenance');if(e.sourceFile&&e.sourceSha256)verifyFile(e.sourceFile,e.sourceSha256,'terrain source iteration');}
 }
 const dimensions=[];
 for(const e of [...(crops.entries||[]).map(e=>({file:e.file,width:e.width,height:e.height})),...(store.files||[]).map(e=>({file:e.sourceFile||path.join('proof-inputs',e.file),width:e.width,height:e.height})),...(fs.existsSync(terrainPath)?(read('terrain-proof-manifest.json').entries||[]).filter(e=>e.dimensions).map(e=>({file:e.file,width:e.dimensions[0],height:e.dimensions[1]})):[])]){
  if(!fs.existsSync(path.join(root,e.file)))continue;
  const m=await sharp(path.join(root,e.file)).metadata();
  if(m.width!==e.width||m.height!==e.height)failures.push(`dimension mismatch ${e.file}: ${m.width}×${m.height}, expected ${e.width}×${e.height}`);
  dimensions.push({file:e.file,width:m.width,height:m.height});
 }
 for(const board of ['boards/tobul-viewport-matched-scale.png','boards/tobul-components-matched-scale.png','boards/tobul-individual-components.png','boards/store-variants-contact-sheet.png','boards/terrain-matched-scale.png']){
  if(!verifyFile(board,null,'board'))continue;
  const m=await sharp(path.join(root,board)).metadata();dimensions.push({file:board,width:m.width,height:m.height,sha256:hash(board)});
 }
 const productionPending=[];
 const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
 for(const match of html.matchAll(/(?:href|src)="([^"]+)"/g)){
  const target=match[1];
  if(/^(https?:|#|data:|mailto:)/i.test(target))continue;
  const local=decodeURIComponent(target.split('#')[0].split('?')[0]);
  if(local.includes('..')){
   const resolved=path.resolve(root,local);
   if(resolved.startsWith(path.resolve(root,'../../../Assets'))){
    if(!fs.existsSync(resolved)){productionPending.push(target);continue;} // Final production files are placed beside the published reference pack.
   }
   if(!fs.existsSync(resolved))failures.push(`broken HTML path: ${target}`);
  } else if(!verifyFile(local,null,'HTML path')){}
 }
 const result={status:failures.length?'FAIL':'PASS',checkedSha256Files:[...new Set(checked)].length,dimensions,failures,productionRelativeLinks:productionPending.length?`PENDING (${productionPending.length} links until production pack copy)`:'PASS (all production links resolve)'};
 fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify(result,null,2));
 if(failures.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
