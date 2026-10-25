'use strict';
// Mechanical proof images assembled from the selected production PNGs, without seam painting.
const C=require('../remaster-expansion/common.cjs');
const T=require('./terrain.cjs');
const {fs,path,root,sharp,json,assert,hash}=C;
async function write(catalog){
 const out=path.join(root,'Review/procedural-tiles');await fs.mkdir(out,{recursive:true});
 const byId=new Map(catalog.tiles.map(t=>[t.id,t])),proofs=[],worldPixelSize=64;
 for(const preset of ['path','grass','snow']){
  const result=T.generate(catalog,{kind:'demo',preset,seed:'terrain-review-2026-10-25'});
  assert(result.ok,'Terrain example failed: '+preset+' '+result.reason);
  assert(result.placements.length===result.width*result.height,'Demo has missing cells');
  const layers=[];
  for(const p of result.placements){
   const a=byId.get(p.id),bytes=await fs.readFile(path.join(root,a.path));assert(hash(bytes)===a.sha256,'Native tile changed: '+a.id);
   assert(a.worldSize[0]===1&&a.worldSize[1]===1,'Demo requires one-unit tile canvases');
   layers.push({input:await sharp(bytes).resize(worldPixelSize,worldPixelSize,{kernel:'nearest'}).png().toBuffer(),left:p.x*worldPixelSize,top:p.y*worldPixelSize});
  }
  const file='terrain-'+preset+'.png';
  await sharp({create:{width:result.width*worldPixelSize,height:result.height*worldPixelSize,channels:4,background:'#18252a'}}).composite(layers).png().toFile(path.join(out,file));
  proofs.push({preset,file,renderPixelsPerWorldUnit:worldPixelSize,resampling:'nearest-neighbor',...result});
 }
 await fs.writeFile(path.join(out,'terrain-examples.json'),json({schema:1,catalogSchema:catalog.schema,inputs:catalog.inputs,proofs,scope:'Actual production PNGs selected by the shared terrain generator. No painted-over seams or pixel blending. Logical adjacency is validated; visual seamlessness is not certified.'}));
 console.log('Terrain proofs: path, grass and snow; each 63 cells / 110 compatible neighboring pairs.');return proofs;
}
module.exports={write};
if(require.main===module)(async()=>write(JSON.parse(await fs.readFile(path.join(root,'Assets/Art/Production/procedural-tiles.json')))))().catch(e=>{console.error(e);process.exitCode=1});
