let sharp;
try { sharp=require('sharp'); }
catch { sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const review=path.resolve(__dirname,'..'),stage=path.resolve(review,'..'),repo=path.resolve(__dirname,'../../../../');
const ids=['weapon','armor','item','magic','temple'];
function findSource(id){
 const relative=`Review/shop-interiors-v1/rooms/${id}-3x.png`;
 return [path.join(stage,relative),path.join(repo,'AssetWork/TerrainShopPassV1',relative),path.join(repo,'References/TerrainShopPassV1',relative)].find(p=>fs.existsSync(p));
}
(async()=>{
 const files=[];
 for(const id of ids){
  const file=`${id}-3x.png`,copied=path.join(review,'comparison-inputs/shop-v1',file),source=findSource(id);
  const hash=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
  const meta=await sharp(copied).metadata(),copiedHash=hash(copied);
  if(source&&hash(source)!==copiedHash) throw new Error(`Snapshot mismatch: ${file}`);
  files.push({file,source:source?path.relative(repo,source).replace(/\\/g,'/'): `Review/shop-interiors-v1/rooms/${file}`,width:meta.width,height:meta.height,sha256:copiedHash,sourceAvailable:!!source});
 }
 const manifest={snapshotDate:'2026-10-31',purpose:'Self-contained final proof inputs for the shop comparison board; copied candidate pixels are review evidence, not new art outputs.',reference:{file:'../../crops/tobul-weapon-shop.png',source:'Vorxu FFII Pixel Remaster Tobul screenshot; crop source and exact rectangle are recorded in ../../crop-register.json.',url:'https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/walkthrough/salamand-and-semitt-falls/tobul-960w.webp'},files,limits:['Only Tobul has a locally inspected matching FFII PR shop interior image.','Armor, item, magic, and temple are candidate art proposals; not exact retail room comparisons.','Proof previews are 3x displays, not a gameplay or runtime capture.']};
 fs.writeFileSync(path.join(review,'comparison-inputs/shop-v1/snapshot-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log(`Verified and recorded ${files.length} shop proof snapshots.`);
})();
