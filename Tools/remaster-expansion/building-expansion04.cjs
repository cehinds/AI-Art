'use strict';
// Mechanical extraction review. All artwork is generated source, never painted by this script.
const C=require('./common.cjs');
const {fs,path,sharp,root,output,review,hash,json,assert}=C;
const batch='building-expansion04',dir=path.join(review,batch),baselinePath=path.join(__dirname,batch+'-baseline.json');
async function main(){
 if(process.argv.includes('--capture-baseline')){
  assert(!await C.exists(baselinePath),'Baseline already exists');const assets=[];
  for(const library of ['Batch01','Campaign','RemasterExpansion']){
   const m=JSON.parse(await fs.readFile(path.join(root,'Assets/Art/Production',library,'manifest.json')));
   for(const a of m.assets)assets.push({path:a.path,sha256:hash(await fs.readFile(path.join(root,a.path))),metadataSha256:hash(await fs.readFile(path.join(root,a.path)+'.meta'))});
  }
  assert(assets.length===1326,'Expected 1326 previous PNGs');await fs.writeFile(baselinePath,json({assets}));console.log('Captured 1326 PNG/meta pairs');return;
 }
 const old=JSON.parse(await fs.readFile(baselinePath));
 for(const a of old.assets){assert(hash(await fs.readFile(path.join(root,a.path)))===a.sha256,'Old PNG changed '+a.path);assert(hash(await fs.readFile(path.join(root,a.path)+'.meta'))===a.metadataSha256,'Old metadata changed '+a.path)}
 const manifest=JSON.parse(await fs.readFile(path.join(output,'manifest.json'))),assets=manifest.assets.filter(a=>a.source.path.includes('/'+batch+'/'));
 assert(assets.length===37,'Expected 32 selected building tiles plus 5 retained corner candidates');await fs.mkdir(dir,{recursive:true});
 const owners=[...new Set(assets.map(a=>a.owner))],proofs=[];
 const room=['outer-nw','edge-n','edge-n','edge-n','edge-n','edge-n','outer-ne', ...Array.from({length:5},()=>['edge-w','center','center-alt','center','center-worn','center','edge-e']).flat(),'outer-sw','edge-s','edge-s','edge-s','edge-s','edge-s','outer-se'];
 const court=[...room];
 const cut=[['inner-se-v2','edge-s','inner-sw-v2'],['edge-e','outside-fill','edge-w'],['inner-ne','edge-n','inner-nw']];
 for(let y=0;y<3;y++)for(let x=0;x<3;x++)court[(y+2)*7+x+2]=cut[y][x];
 for(const owner of owners){
  const all=assets.filter(a=>a.owner===owner),tiles=all.filter(a=>!/-v[23]$/.test(a.name)).sort((a,b)=>a.source.slot-b.source.slot).map(a=>['inner-sw','inner-se'].includes(a.name)?all.find(b=>b.name===a.name+(owner==='stone-building-expansion04'&&a.name==='inner-se'?'-v3':'-v2')):a),buffers=new Map();
  for(const a of tiles){const b=await fs.readFile(path.join(root,a.path)),m=await sharp(b).metadata();assert(hash(b)===a.sha256&&m.width===64&&m.height===64&&a.ppu===64,'Tile contract '+a.id);const raw=await sharp(b).ensureAlpha().raw().toBuffer();assert([...raw.filter((_,i)=>i%4===3)].every(v=>v===255),'Nonopaque tile '+a.id);buffers.set(a.name,b)}
  const contact=owner+'-native.png';await sharp({create:{width:256,height:256,channels:4,background:'#20343c'}}).composite(tiles.map((a,i)=>({input:buffers.get(a.name),left:i%4*64,top:Math.floor(i/4)*64}))).png().toFile(path.join(dir,contact));
  for(const [key,layout] of [['room',room],['courtyard',court]]){const cells=layout.map(n=>owner==='stone-building-expansion04'&&n==='inner-se-v2'?'inner-se-v3':n),name=owner+'-'+key+'.png';await sharp({create:{width:448,height:448,channels:4,background:'#20343c'}}).composite(cells.map((n,i)=>({input:buffers.get(n),left:i%7*64,top:Math.floor(i/7)*64}))).png().toFile(path.join(dir,name));proofs.push({owner,name,columns:7,cells,kind:key})}
 }
 await sharp({create:{width:512,height:256,channels:4,background:'#20343c'}}).composite(owners.map((o,i)=>({input:path.join(dir,o+'-native.png'),left:i*256,top:0}))).png().toFile(path.join(dir,'overview-native.png'));
 await sharp(path.join(dir,'overview-native.png')).resize(1024,512,{kernel:'nearest'}).png().toFile(path.join(dir,'overview-2x.png'));
 const inventory={batch,assets,proofs,preservation:{state:'PASS',pngs:old.assets.length,metadata:old.assets.length},limitations:['Logical edge tags are separate from pixel seam quality.','These are full opaque grass/wall or grass/roof tiles, not transparent overlays.','Unity import and procedural generation runtime are not validated.']};await fs.writeFile(path.join(dir,'inventory.json'),json(inventory));
 await fs.writeFile(path.join(dir,'index.html'),`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>FFII building corners</title><style>body{background:#18252a;color:#efdfbd;font:16px system-ui;margin:2rem;max-width:1100px}img{image-rendering:pixelated;max-width:100%;height:auto}a{color:#93ddd1}.maps{display:flex;flex-wrap:wrap;gap:24px}figure{margin:0}p{max-width:80ch}</style><h1>32 building tiles · 64px</h1><p>Stone walls and blue slate roofs: outer corners, straight edges, fills, and four inner corners each. Actual native exports; no painted-over seams.</p><p><a href="../../procedural-tiles/index.html">Browse edge tags and compatible neighbors</a> · <a href="inventory.json">Inventory and map placements</a></p><img src="overview-2x.png" alt="All 32 new building tiles"><div class="maps">${proofs.map(p=>`<figure><h2>${p.owner} / ${p.kind}</h2><img src="${p.name}" width="448" height="448" alt="Actual tile assembly"></figure>`).join('')}</div><p>Texture phase and wall offsets can remain visible. Edge sockets describe logical compatibility, not pixel-perfect seams. Unity import and runtime remain unverified.</p></html>`);
 console.log('PASS: 32 selected 64px tiles plus 5 retained corner candidates, 4 actual map proofs, 1326 earlier PNG/meta pairs unchanged');
}
main().catch(e=>{console.error(e);process.exitCode=1});
