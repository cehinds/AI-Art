'use strict';
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const K=require('./core.cjs');
const root=path.resolve(__dirname,'../..');
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const scriptJSON=value=>JSON.stringify(value).replace(/</g,'\\u003c').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');
async function render(catalog,demo){
 const matcher=await fs.readFile(path.join(__dirname,'core.cjs'),'utf8');
 if(/require\s*\(/.test(matcher)||/<\/script/i.test(matcher))throw Error('Shared matcher must remain browser-safe pure CJS');
 const template=await fs.readFile(path.join(__dirname,'review.template.html'),'utf8');
 const values={__CATALOG__:scriptJSON(catalog),__SEEDED__:scriptJSON({...demo,building:buildingDemo(catalog,demo.seed)}),__MATCHER__:matcher,__MATCHER_HASH__:hash(matcher)};
 return template.replace(/__CATALOG__|__SEEDED__|__MATCHER__|__MATCHER_HASH__/g,token=>values[token]);
}
function buildingDemo(catalog,seed=20261025){
 const tiles=catalog.tiles.filter(tile=>tile.family==='stone-building-expansion04'&&tile.state==='modeled'),byName=new Map(tiles.map(tile=>[tile.id.split('.').at(-1),tile]));
 const required=['outside-fill','outer-nw','edge-n','outer-ne','edge-w','center','edge-e','outer-sw','edge-s','outer-se'];
 if(required.some(name=>!byName.has(name)))return null;
 const width=5+seed%2,height=5,placements=[];
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  let name='outside-fill';
  if(x>0&&x<width-1&&y>0&&y<height-1){
   if(y===1)name=x===1?'outer-nw':x===width-2?'outer-ne':'edge-n';
   else if(y===height-2)name=x===1?'outer-sw':x===width-2?'outer-se':'edge-s';
   else name=x===1?'edge-w':x===width-2?'edge-e':'center';
  }
  placements.push({x,y,id:byName.get(name).id});
 }
 const byId=new Map(tiles.map(tile=>[tile.id,tile]));let checkedNeighborPairs=0;
 for(const placement of placements)for(const [direction,dx,dy]of [['east',1,0],['south',0,1]]){
  if(placement.x+dx>=width||placement.y+dy>=height)continue;
  const neighbor=placements[(placement.y+dy)*width+placement.x+dx];
  if(!K.check(byId.get(placement.id),direction,byId.get(neighbor.id),catalog.policy).match)return null;
  checkedNeighborPairs++;
 }
 return {seed,width,height,checkedNeighborPairs,placements,pixelSeamGuarantee:false,algorithm:'Seeded building width; explicit corner, wall, floor and grass placements, every adjacency checked by the shared matcher'};
}
async function write(catalog,demo){
 const folder=path.join(root,'Review/procedural-tiles');await fs.mkdir(folder,{recursive:true});
 await fs.writeFile(path.join(folder,'index.html'),await render(catalog,demo));
 const building=buildingDemo(catalog,demo.seed);if(building)await fs.writeFile(path.join(folder,'seeded-building-demo.json'),JSON.stringify(building,null,2)+'\n');
}
module.exports={render,write,scriptJSON,buildingDemo};
