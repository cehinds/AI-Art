let sharp;
try { sharp=require('sharp'); }
catch { sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const review=path.resolve(__dirname,'..');
const stage=path.resolve(review,'..');
const repo=path.resolve(__dirname,'../../../../');
const artRoot=fs.existsSync(path.join(stage,'Assets/Art/Production'))?stage:repo;
const items=[
 ['grass.png','Assets/Art/Production/TerrainComponentsV3/floors/grass.png'],
 ['city-cobble.png','Assets/Art/Production/TerrainComponentsV3/floors/city-cobble.png'],
 ['river-junctions-3x.png','Review/terrain-components-v3/river-junctions-3x.png'],
 ['forest-field-3x.png','Review/terrain-components-v3/forest-field-3x.png'],
 ['city-trees-3x.png','Review/terrain-components-v3/city-trees-3x.png'],
 ['dirt-road-junctions-3x.png','Review/terrain-components-v3/dirt-road-junctions-3x.png'],
 ['cobble-road-junctions-3x.png','Review/terrain-components-v3/cobble-road-junctions-3x.png']
];
(async()=>{
 const files=[];
 for(const [file,sourceRel] of items){
  const copied=path.join(review,'comparison-inputs/terrain-v3',file);
  const sourceCandidates=[path.join(artRoot,sourceRel),path.join(repo,'AssetWork/TerrainShopPassV1',sourceRel),path.join(repo,'References/TerrainShopPassV1',sourceRel)];
  const source=sourceCandidates.find(candidate=>fs.existsSync(candidate));
  const hash=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
  const meta=await sharp(copied).metadata(), copiedHash=hash(copied);
  if(source&&copiedHash!==hash(source)) throw new Error(`Snapshot mismatch: ${file}`);
  files.push({file,source:source?path.relative(repo,source).replace(/\\/g,'/'):sourceRel,width:meta.width,height:meta.height,sha256:copiedHash,sourceAvailable:!!source});
 }
 const manifest={snapshotDate:'2026-10-31',purpose:'Self-contained image inputs for the ReferenceReview comparison boards; copied candidate pixels are review evidence, not new art outputs.',files,notes:['Copied proof images are presented as authored asset/proof evidence; atlas views are not gameplay maps.','The road and city-tree comparison rows identify where no directly matching source crop was found.','The forest-field view is diagnostic-only and does not establish a repeatability contract.']};
 fs.writeFileSync(path.join(review,'comparison-inputs/terrain-v3/snapshot-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log(`Verified and recorded ${files.length} terrain snapshots.`);
})();
