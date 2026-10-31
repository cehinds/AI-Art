let sharp;
try { sharp=require('sharp'); }
catch { sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=__dirname,failures=[],checked=[];
const hash=f=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,f))).digest('hex');
function file(f,want,label){const p=path.join(root,f);if(!fs.existsSync(p)){failures.push(`${label}: missing ${f}`);return false;}if(want&&hash(f).toLowerCase()!==want.toLowerCase())failures.push(`${label}: SHA-256 mismatch for ${f}`);checked.push(f);return true;}
(async()=>{
 const refs=JSON.parse(fs.readFileSync(path.join(root,'reference-manifest.json'),'utf8'));
 for(const e of refs.entries){
  file(e.sourceFile,e.sourceSha256,'reference source');file(e.cropFile,e.cropSha256,'reference crop');
  const m=await sharp(path.join(root,e.cropFile)).metadata();if(m.width!==e.cropDimensions[0]||m.height!==e.cropDimensions[1])failures.push(`crop dimension mismatch ${e.cropFile}`);
 }
 const proof=JSON.parse(fs.readFileSync(path.join(root,'room-proof-manifest.json'),'utf8'));
 const pending=[];
 for(const e of proof.rooms){
  if(e.status!=='ready'){pending.push(e.id);continue;}
  file(e.referenceFile,e.referenceSha256,'board reference');file(e.proofFile,e.proofSha256,'room proof');file(e.boardFile,e.boardSha256,'comparison board');
  const pm=await sharp(path.join(root,e.proofFile)).metadata(),bm=await sharp(path.join(root,e.boardFile)).metadata();
  if(pm.width!==e.dimensions[0]||pm.height!==e.dimensions[1])failures.push(`candidate dimensions mismatch ${e.proofFile}`);
  if(bm.width<e.dimensions[0]*2)failures.push(`board width does not contain both native crops ${e.boardFile}`);
  checked.push(e.proofFile,e.boardFile);
 }
 const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
 for(const m of html.matchAll(/(?:href|src)="([^"]+)"/g)){const t=m[1];if(/^(https?:|#|data:|mailto:)/i.test(t))continue;const f=decodeURIComponent(t.split('#')[0].split('?')[0]);if(f&&!fs.existsSync(path.resolve(root,f)))failures.push(`broken HTML path ${t}`);}
 const findings=JSON.parse(fs.readFileSync(path.join(root,'review-findings.json'),'utf8'));
 const openFindings=findings.findings.filter(e=>e.state==='needs-correction').map(e=>`${e.room}: ${e.note}`);
 const status=failures.length?'FAIL':pending.length?'PASS_WITH_PENDING_ROOMS':openFindings.length?'PASS_WITH_OPEN_FINDINGS':'PASS';
 const result={status,checkedSha256Files:[...new Set(checked)].length,readyRooms:proof.rooms.filter(e=>e.status==='ready').map(e=>e.id),pendingRooms:pending,openFindings,failures};
 fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));if(failures.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
