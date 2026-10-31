let sharp;
try { sharp=require('sharp'); }
catch { sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=__dirname,src=path.join(root,'sources'),out=path.join(root,'crops');
const crops=[
 {id:'tobul-room-viewport.png',file:'pr-smithy.webp',rect:{left:213,top:0,width:534,height:440},role:'Locked matched viewport; source 960×540 Vorxu Tobul capture.'},
 {id:'tobul-upper-room.png',file:'@crops/tobul-room-viewport.png',rect:{left:0,top:0,width:534,height:200},role:'Upper wall, stock, merchant and counter comparison; same viewport pixel scale.'},
 {id:'tobul-service-counter.png',file:'@crops/tobul-room-viewport.png',rect:{left:0,top:0,width:430,height:225},role:'Service zone comparison crop; same viewport coordinate frame.'},
 {id:'tobul-floor-rug.png',file:'@crops/tobul-room-viewport.png',rect:{left:0,top:200,width:534,height:240},role:'Red floor, foreground rug, customers and doorway-side fixtures; same viewport scale.'},
 {id:'overworld-grass.png',file:'pr-altair-to-gatrea-02.png',rect:{left:200,top:130,width:90,height:60},role:'Clear bright grass sample; actor excluded.'},
 {id:'overworld-river-winding.png',file:'pr-altair-to-gatrea-03.png',rect:{left:0,top:65,width:130,height:205},role:'Natural winding river crop; no bridge; screenshot pixel scale preserved.'}
];
function hash(file){return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');}
(async()=>{
 const entries=[];
 for(const c of crops){
  const isCrop=c.file.startsWith('@crops/');
  const sourceRel=isCrop?c.file.slice(1):`sources/${c.file}`;
  const file=isCrop?path.join(root,sourceRel):path.join(src,c.file),dest=path.join(out,c.id);
  await sharp(file).extract(c.rect).png().toFile(dest);
  const meta=await sharp(dest).metadata();
  entries.push({file:`crops/${c.id}`,source:sourceRel,sourceSha256:hash(file),cropSha256:hash(dest),sourceRect:c.rect,width:meta.width,height:meta.height,role:c.role});
 }
 fs.writeFileSync(path.join(root,'reference-crop-manifest.json'),JSON.stringify({date:'2026-10-31',entries},null,2)+'\n');
 console.log(`Wrote ${entries.length} reference crops.`);
})();
