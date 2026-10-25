'use strict';
const K=require('./core.cjs');
const directions=['north','east','south','west'],bits={north:1,east:2,south:4,west:8};
const cornerRoles={0:'outside-fill',1:'outer-se',2:'outer-sw',3:'edge-s',4:'outer-nw',5:'diagonal-nw-se',6:'edge-w',7:'inner-sw',8:'outer-ne',9:'edge-e',10:'diagonal-ne-sw',11:'inner-se',12:'edge-n',13:'inner-ne',14:'inner-nw',15:'inside-fill'};
function random(seed){let n=2166136261;for(const c of String(seed)){n^=c.charCodeAt(0);n=Math.imul(n,16777619)}return()=>{n=(Math.imul(n,1664525)+1013904223)>>>0;return n/4294967296}}
const aliases={path:['path','dirt-road','soil-path'],grass:['grass','meadow','meadow-turf','turf'],snow:['snow','tundra-snow','compacted-snow']};
function terrainMatches(tile,terrain,model){return model==='fill'?(tile.terrain.primary===terrain||tile.terrain.aliases?.includes(terrain)):(tile.topology.terrain===terrain||aliases[tile.topology.terrain]?.includes(terrain))}
function select(catalog,intent,seed=1){
 if(!intent||!['fill','area-corner16','route4'].includes(intent.model)||typeof intent.terrain!=='string'||typeof intent.family!=='string')return {ok:false,reason:'invalid-intent',requested:intent};
 if(intent.model!=='fill'&&(!Number.isInteger(intent.mask)||intent.mask<0||intent.mask>15))return {ok:false,reason:'invalid-mask',requested:intent};
 let candidates=catalog.tiles.filter(t=>t.state==='modeled'&&t.family===intent.family&&terrainMatches(t,intent.terrain,intent.model)&&(!t.animation||t.animation.phase===(intent.phase??0)));
 if(intent.model==='fill')candidates=candidates.filter(t=>t.shape.kind==='fill'&&(t.terrain.primary===intent.terrain||t.terrain.aliases?.includes(intent.terrain)));
 else candidates=candidates.filter(t=>t.topology.model===intent.model&&(intent.model==='route4'?t.topology.routeMask:t.topology.cornerMask)===intent.mask);
 candidates.sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
 if(!candidates.length){const availableMasks=[...new Set(catalog.tiles.filter(t=>t.state==='modeled'&&t.family===intent.family&&terrainMatches(t,intent.terrain,intent.model)&&t.topology.model===intent.model).map(t=>intent.model==='route4'?t.topology.routeMask:t.topology.cornerMask).filter(Number.isInteger))].sort((a,b)=>a-b);return {ok:false,reason:intent.model==='fill'?'unsupported-terrain-fill':'unsupported-mask',requested:intent,availableMasks,candidates:[]}}
 const total=candidates.reduce((s,t)=>s+t.variant.weight,0);let choice=random(seed)()*total,picked=candidates.at(-1);for(const t of candidates){choice-=t.variant.weight;if(choice<0){picked=t;break}}
 return {ok:true,tileId:picked.id,reason:'supported-intent',requested:intent,candidates:candidates.map(t=>t.id)};
}
function fieldIntent(vertices,options={}){
 if(!Array.isArray(vertices)||vertices.length<2||vertices.length>129||!Array.isArray(vertices[0])||vertices[0].length<2||vertices[0].length>129||vertices.some(row=>!Array.isArray(row)||row.length!==vertices[0].length||row.some(v=>v!==0&&v!==1&&v!==false&&v!==true)))return {ok:false,reason:'invalid-vertex-field'};
 const width=vertices[0].length-1,height=vertices.length-1,requests=[];
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){const q=[vertices[y][x],vertices[y][x+1],vertices[y+1][x+1],vertices[y+1][x]],mask=q.reduce((m,v,i)=>m|(Number(v)<<i),0);requests.push({x,y,family:options.family,terrain:options.terrain,model:'area-corner16',mask})}
 return {ok:true,width,height,requests,vertices};
}
function routeGraph(paths){
 if(!Array.isArray(paths))return {ok:false,reason:'invalid-route-graph'};const nodes=new Map(),edges=[];
 const node=(x,y)=>{const key=x+','+y;if(!nodes.has(key))nodes.set(key,{x,y,connections:new Set()});return nodes.get(key)};
 for(const path of paths){if(!Array.isArray(path)||!path.length||path.some(p=>!Array.isArray(p)||p.length!==2||!p.every(Number.isInteger)))return {ok:false,reason:'invalid-route-path'};for(let i=0;i<path.length;i++){const [x,y]=path[i],a=node(x,y);if(!i)continue;const [px,py]=path[i-1],dx=x-px,dy=y-py;if(Math.abs(dx)+Math.abs(dy)!==1)return {ok:false,reason:'non-cardinal-route-segment'};const d=dx===1?'east':dx===-1?'west':dy===1?'south':'north';node(px,py).connections.add(d);a.connections.add(K.opposite[d]);edges.push({from:[px,py],to:[x,y]})}}
 return {ok:true,nodes:[...nodes.values()].map(n=>({...n,connections:directions.filter(d=>n.connections.has(d)),mask:[...n.connections].reduce((m,d)=>m|bits[d],0)})),edges};
}
function validate(catalog,placements,width,height){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1)return {ok:false,reason:'invalid-dimensions',placements:[]};
 if(!Array.isArray(placements))return {ok:false,reason:'invalid-placements',placements:[]};
 const byId=new Map(catalog.tiles.map(t=>[t.id,t])),grid=new Map();let checkedNeighborPairs=0;
 for(const p of placements){if(!p||!Number.isInteger(p.x)||!Number.isInteger(p.y)||p.x<0||p.y<0||p.x>=width||p.y>=height)return {ok:false,reason:'invalid-placement-coordinate',placement:p,placements:[]};if(!byId.has(p.id))return {ok:false,reason:'unknown-tile-id',placement:p,placements:[]};if(byId.get(p.id).state!=='modeled')return {ok:false,reason:'blocked-placement',placement:p,placements:[]};const key=p.x+','+p.y;if(grid.has(key))return {ok:false,reason:'duplicate-placement',placement:p,placements:[]};grid.set(key,p)}
 for(const p of placements)for(const [d,dx,dy]of [['east',1,0],['south',0,1]]){const neighbor=grid.get((p.x+dx)+','+(p.y+dy));if(!neighbor)continue;const result=K.check(byId.get(p.id),d,byId.get(neighbor.id),catalog.policy);if(!result.match)return {ok:false,reason:'socket-validation-failed',failure:{from:p,to:neighbor,direction:d,result},placements:[],width,height};checkedNeighborPairs++}
 return {ok:true,width,height,placements,checkedNeighborPairs,visualSeamGuaranteed:false};
}
function generate(catalog,intent){
 if(!intent||typeof intent!=='object')return {ok:false,reason:'invalid-intent',placements:[]};const seed=intent.seed??1;
 if(intent.kind==='transition'){const support=transitionSupport(catalog,intent);return {ok:false,reason:support.ok?'transition-needs-area-intent':'missing-transition',support,missingRequests:support.ok?[]:[{from:intent.from,to:intent.to,reason:'missing-transition'}],placements:[]}}
 if(intent.kind==='demo'){
  if(intent.preset==='grass'||intent.preset==='snow')return generate(catalog,{kind:'field',family:'overworld-ground',terrain:intent.preset,width:9,height:7,seed});
  if(intent.preset==='path'){const vertices=Array.from({length:8},(_,y)=>Array.from({length:10},(_,x)=>Number(y>=2&&y<=5&&x>=2&&x<=7)));return generate(catalog,{kind:'area',family:'batch01-path',terrain:'path',vertices,outside:{family:'batch01-ground',terrain:'grass'},seed})}
  return {ok:false,reason:'unsupported-demo',placements:[]};
 }
 let width=intent.width,height=intent.height,requests=[];
 if(intent.kind==='field'){
  if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width>128||height>128)return {ok:false,reason:'invalid-dimensions',placements:[]};
  for(let y=0;y<height;y++)for(let x=0;x<width;x++)requests.push({x,y,model:'fill',family:intent.family,terrain:intent.terrain});
 }else if(intent.kind==='area'){
  const result=fieldIntent(intent.vertices,intent);if(!result.ok)return {...result,placements:[]};({width,height,requests}=result);
  requests=requests.map(r=>r.mask===0&&intent.outside?{x:r.x,y:r.y,model:'fill',...intent.outside}:r);
 }else if(intent.kind==='route'){
  const graph=routeGraph(intent.paths);if(!graph.ok)return {...graph,placements:[]};if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width>128||height>128)return {ok:false,reason:'invalid-dimensions',placements:[]};
  if(graph.nodes.some(n=>n.x<0||n.y<0||n.x>=width||n.y>=height))return {ok:false,reason:'route-out-of-bounds',placements:[]};
  const nodes=new Map(graph.nodes.map(n=>[n.x+','+n.y,n]));for(let y=0;y<height;y++)for(let x=0;x<width;x++){const n=nodes.get(x+','+y);if(n)requests.push({x,y,model:'route4',mask:n.mask,family:intent.family,terrain:intent.terrain});else if(intent.outside)requests.push({x,y,model:'fill',...intent.outside})}
 }else return {ok:false,reason:'unsupported-intent-kind',placements:[]};
 const missingRequests=[],placements=[];for(const request of requests){const result=select(catalog,request,seed+':'+request.x+':'+request.y);if(!result.ok)missingRequests.push({...request,reason:result.reason,availableMasks:result.availableMasks});else placements.push({x:request.x,y:request.y,id:result.tileId})}
 if(missingRequests.length)return {ok:false,reason:'unsupported-topology',missingRequests,placements:[],width,height,seed,intent};
 return {...validate(catalog,placements,width,height),seed,intent};
}
function routeRole(mask){const c=directions.filter(d=>mask&bits[d]);return c.length===0?'isolated':c.length===1?'end-opening-'+c[0]:c.length===2?(K.opposite[c[0]]===c[1]?'straight-'+c.join('-'):'bend-'+c.join('-')):c.length===3?'t-junction-'+c.join('-'):'cross'}
const materialAliases={'meadow-turf':['grass','turf'],'meadow-grass':['grass'],'compacted-soil':['soil','earth'],'compacted-snow':['snow','tundra-snow'],'frozen-tundra-earth':['frozen-earth','frozen-soil'],'rippled-dune-sand':['sand'],'pale-gravel-sand':['sand'],'warm-cave-floor':['cave-floor'],'moss-leaf-litter':['forest-floor'],'evergreen-moss-lichen':['moss'],'jungle-groundcover':['jungle-floor']};
function authoredTransitions(tiles){const rows=new Map();for(const tile of tiles.filter(t=>t.state==='modeled'&&t.transition)){const {from,to}=tile.transition,key=from+'|'+to;if(!rows.has(key))rows.set(key,{from,to,fromTags:[from,...(materialAliases[from]||[])],toTags:[to,...(materialAliases[to]||[])],families:[],tileIds:[]});const r=rows.get(key);if(!r.families.includes(tile.family))r.families.push(tile.family);r.tileIds.push(tile.id)}return [...rows.values()].sort((a,b)=>(a.from+'|'+a.to).localeCompare(b.from+'|'+b.to))}
function transitionSupport(catalog,intent){if(!intent||typeof intent.from!=='string'||typeof intent.to!=='string')return {ok:false,reason:'invalid-transition'};const candidates=authoredTransitions(catalog.tiles).filter(r=>(r.fromTags.includes(intent.from)&&r.toTags.includes(intent.to)||r.fromTags.includes(intent.to)&&r.toTags.includes(intent.from))&&(!intent.family||r.families.includes(intent.family)));return {ok:candidates.length>0,reason:candidates.length?'authored-transition-present':'missing-transition',requested:intent,candidates}}
function coverage(tiles){
 const terrains=[...new Set(tiles.flatMap(t=>[t.topology.terrain,t.terrain.primary]))].sort(),byTerrain=[],gaps=[];
 for(const terrain of terrains){const matching=tiles.filter(t=>t.topology.terrain===terrain),all=tiles.filter(t=>t.topology.terrain===terrain||t.terrain.primary===terrain),entry={terrain,families:[...new Set(all.map(t=>t.family))].sort(),fillVariants:all.filter(t=>t.state==='modeled'&&t.shape.kind==='fill'&&t.terrain.primary===terrain).length,area:[],route:[]};for(const model of ['area-corner16','route4'])for(const family of [...new Set(matching.filter(t=>t.topology.model===model).map(t=>t.family))].sort()){const supportedMasks=[...new Set(matching.filter(t=>t.state==='modeled'&&t.family===family&&t.topology.model===model).map(t=>model==='route4'?t.topology.routeMask:t.topology.cornerMask).filter(Number.isInteger))].sort((a,b)=>a-b),missingMasks=Array.from({length:16},(_,i)=>i).filter(i=>!supportedMasks.includes(i)),missingRoles=missingMasks.map(m=>model==='route4'?routeRole(m):cornerRoles[m]).sort(),record={family,model,supportedMasks,missingMasks,missingRoles};entry[model==='route4'?'route':'area'].push(record);if(missingMasks.length)gaps.push({terrain,...record,reason:'missing-authored-topology'})}
  if(terrain==='path'&&!entry.route.length)gaps.push({terrain,model:'route4',family:'batch01-path',reason:'Area boundary tiles do not supply one-cell road network art; ends, turns and junctions must not be inferred from ninepatch corners',missingMasks:Array.from({length:16},(_,i)=>i),missingRoles:Array.from({length:16},(_,i)=>routeRole(i)).sort()});byTerrain.push(entry)
 }
 if(!transitionSupport({tiles},{from:'grass',to:'snow'}).ok)gaps.push({model:'transition',from:'grass',to:'snow',reason:'missing-authored-transition; semantic tags do not imply arbitrary biome blending'});
 return {byTerrain,gaps,authoredTransitions:authoredTransitions(tiles),models:{area:'Four vertex bits NW1/NE2/SE4/SW8:16 cases, not a47-blob neighborhood grammar',route:'Four independent graph connection bits N1/E2/S4/W8:16 cases; adjacent cells are not implicit edges'}};
}
module.exports={select,generate,routeGraph,fieldIntent,validate,coverage,transitionSupport,cornerRoles,routeRole,bits};
