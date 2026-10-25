'use strict';
const C=require('../remaster-expansion/common.cjs'),K=require('./core.cjs');
const {fs,path,root,sharp,json,assert}=C,folder=path.join(root,'Review/procedural-tiles');
function rng(seed){return()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296}}
exports.write=async catalog=>{
 const seed=20261025,random=rng(seed),size=8,tiles=catalog.tiles.filter(a=>a.family==='river-expansion02'&&a.state==='modeled'),byName=new Map(tiles.map(a=>[a.id.split('.').at(-1),a])),names=Array(size*size).fill('grass-center');
 const left=1+Math.floor(random()*2),top=1+Math.floor(random()*2),right=5+Math.floor(random()*2),bottom=5+Math.floor(random()*2);
 for(let x=left+1;x<right;x++)names[top*size+x]=names[bottom*size+x]='river-ew';for(let y=top+1;y<bottom;y++)names[y*size+left]=names[y*size+right]='river-ns';
 names[top*size+left]='river-bend-se';names[top*size+right]='river-bend-sw';names[bottom*size+left]='river-bend-ne';names[bottom*size+right]='river-bend-nw';names[(top+1)*size+left]='river-ford';names[(bottom-1)*size+right]='river-stepping-stones';
 const placements=names.map((name,i)=>({x:i%size,y:Math.floor(i/size),id:byName.get(name).id})),byId=new Map(tiles.map(a=>[a.id,a]));let checked=0;
 for(const p of placements)for(const [direction,dx,dy]of [['east',1,0],['south',0,1]]){if(p.x+dx>=size||p.y+dy>=size)continue;const neighbor=placements[(p.y+dy)*size+p.x+dx];assert(K.check(byId.get(p.id),direction,byId.get(neighbor.id),catalog.policy).match,'Demo adjacency failed');checked++}
 await sharp({create:{width:size*64,height:size*64,channels:4,background:'#26383d'}}).composite(await Promise.all(placements.map(async p=>({input:await fs.readFile(path.join(root,byId.get(p.id).path)),left:p.x*64,top:p.y*64})))).png().toFile(path.join(folder,'seeded-river-native.png'));
 await fs.writeFile(path.join(folder,'seeded-demo.json'),json({seed,algorithm:'Seeded rectangular river circuit with random bounds and explicit crossing variants; every adjacency checked by production socket matcher',width:size,height:size,checkedNeighborPairs:checked,placements,pixelSeamGuarantee:false}));
 const demo={seed,algorithm:'Seeded rectangular river circuit; every adjacency checked by the shared matcher',width:size,height:size,checkedNeighborPairs:checked,placements,pixelSeamGuarantee:false};
 await require('./review-page.cjs').write(catalog,demo);
};
if(require.main===module){fs.readFile(path.join(root,'Assets/Art/Production/procedural-tiles.json'),'utf8').then(JSON.parse).then(exports.write).catch(error=>{console.error(error);process.exitCode=1})}