'use strict';
const K=require('./core.cjs');
const area={
 'batch01-path':['path','earth-path','grass','temperate'],
 'batch01-roof':['roof','batch01-shingles','building-exterior-unspecified','settlement'],
 'town-roof':['roof','cobalt-shingles','roof-exterior-unresolved','settlement'],
 'interior-carpet':['carpet','red-gold-carpet','room-floor-unspecified','interior'],
 cave:['rock','cave-rock-top','cave-floor','cave'],coast:['sand','sand','deep-water','coastal'],castle:['masonry','castle-masonry-top','castle-slate-floor','castle'],
 'desert-ruins':['sandstone','sandstone-top','desert-sand','desert'],
 'dungeon-transitions':['wall','stone-wall-top','flagstone-floor','dungeon'],
 'snow-ice':['ice','frozen-ice','snow','snow'],
 'ship-dock':['wood','dock-planks','dock-water','coastal'],
 'terrace-expansion02':['stone','moss-stone','umber-soil','temperate'],
 'crystal-cavern-expansion03':['cave-floor','cavern-floor','cavern-bedrock','cave'],
 'stone-building-expansion04':['flagstone','flagstone','grass','settlement'],
 'slate-roof-expansion04':['slate','blue-slate','grass','settlement']
};
const biomeFamilies={
 'biome-snow-tundra-v2':['snow','tundra'],'biome-desert-dunes':['sand','desert'],'biome-volcanic-ash':['ash','volcanic'],'biome-cavern-stone':['rock','cave'],'biome-mountain-cliffs':['rock','mountain'],
 'grassland-v2':['grass','grassland'],'temperate-forest':['forest-floor','temperate'],'conifer-highlands':['moss','highlands'],'swamp-marsh':['marsh','swamp'],'tropical-jungle':['jungle-floor','tropical']
};
biomeFamilies['biome-cavern-stone'][0]='cave-floor';
const biomeMaterials={
 'grassland-v2':['meadow-turf','compacted-soil','earthen-escarpment'],
 'temperate-forest':['moss-leaf-litter','meadow-grass','vegetation-earth-fringe'],
 'conifer-highlands':['evergreen-moss-lichen','slate-rock','granite-rim'],
 'swamp-marsh':['wetland-hummock','shallow-water-wet-mud','wet-bank'],
 'tropical-jungle':['jungle-groundcover','wet-brown-soil','vine-leaf-fringe'],
 'biome-snow-tundra-v2':['compacted-snow','frozen-tundra-earth','snowbank'],
 'biome-desert-dunes':['rippled-dune-sand','pale-gravel-sand','dune-foot-contour'],
 'biome-volcanic-ash':['cinder-ash-basalt','barren-rock','cooled-rock-lip'],
 'biome-cavern-stone':['warm-cave-floor','cavern-wall-rock','crevice-ledge-shadow'],
 'biome-mountain-cliffs':['plateau-stone','lower-gravel','cliff-ledge']
};
for(const [family,[terrain,biome]]of Object.entries(biomeFamilies))area[family]=[terrain,family+':inside',family+':outside',biome];
const alias={
 'earth-path':'path','earth':'soil','umber-soil':'soil','desert-sand':'sand','frozen-ice':'ice','moss-stone':'stone','cavern-floor':'cave-floor','cavern-bedrock':'bedrock',
 'cave-rock-top':'rock','cave-floor':'cave-floor','deep-water':'water','river-water':'water','deepwater':'water','dock-water':'water','shallow-water':'water',
 'blue-slate':'slate','cobalt-shingles':'roof','batch01-shingles':'roof','cream-masonry':'wall','cream-wall':'wall','dungeon-stone':'stone','town-cobble':'cobble','cobble':'cobble',
 'room-stone':'stone','room-wood':'wood','dock-planks':'wood','dense-forest':'forest','mountain-rock':'rock','castle-masonry-top':'masonry','castle-slate-floor':'stone','stone-wall-top':'wall','flagstone-floor':'flagstone','sandstone-top':'sandstone','red-gold-carpet':'carpet',
 'brown-room-floor-unspecified':'interior-floor','building-exterior-unspecified':'building-exterior','cream-wall-threshold':'doorway','dark-wall-substrate-unspecified':'wall','dungeon-floor-unspecified':'dungeon-floor','dungeon-wall':'wall','flagstone-wall-threshold':'doorway','grass-flagstone-mixed-unreviewed':'mixed-building-terrain','grass-slate-mixed-unreviewed':'mixed-roof-terrain','roof-exterior-unresolved':'building-exterior','roof-or-wall-substrate-unspecified':'building-feature','room-floor-unspecified':'interior-floor','wall-threshold-unspecified':'doorway','dock-planks-with-gangplank':'wood','dock-planks-with-rope-lashed-deck':'wood','red-carpet':'carpet','sandstone-sand-mix':'sandstone-sand','waterfall-flow':'water'
};
const routeNames={'river-ns':['north','south'],'river-ew':['east','west'],'river-bend-ne':['north','east'],'river-bend-nw':['north','west'],'river-bend-se':['south','east'],'river-bend-sw':['south','west'],'river-t-n':['north','east','west'],'river-t-e':['north','east','south'],'river-t-s':['east','south','west'],'river-t-w':['north','south','west'],'river-cross':['north','east','south','west'],'river-source':['north'],'river-ford':['north','south'],'river-stepping-stones':['north','south']};
const bits={north:1,east:2,south:4,west:8};
function material(token){if(alias[token])return alias[token];for(const [family,values]of Object.entries(biomeMaterials)){const slot=token===family+':inside'?0:token===family+':outside'?1:token===family+':edge'?2:-1;if(slot>=0)return values[slot]}return token}
function enrich(tile){
 const name=tile.id.split('.').at(-1),spec=area[tile.family],raw=[...new Set(Object.values(tile.sides).flatMap(s=>s.profile).concat(Object.values(tile.corners)))],materials=[...new Set(raw.map(material))].sort();
 let terrain=spec?.[0]||material(raw[0]),biome=spec?.[3]||'unspecified',model='fill',cornerMask=null,routeMask=null,connections=[],cap=null,kind='fill',orientation=null,transition=null;
 if(spec){model='area-corner16';const values=Object.values(tile.corners).map(m=>m===spec[1]?1:m===spec[2]?0:null);if(values.every(v=>v!==null))cornerMask=values.reduce((mask,n,i)=>mask|(n<<i),0);const role=cornerMask===null?null:Object.entries(K.roles).find(([,q])=>q.reduce((mask,n,i)=>mask|(n<<i),0)===cornerMask)?.[0];
  if(cornerMask===0){kind='fill';terrain=material(spec[2])}else if(cornerMask===15){kind='fill'}else if(role?.startsWith('inner-')){kind='inner-corner';orientation=role.slice(6)}else if(role&&role.length===2){kind='outer-corner';orientation=role}else if(role){kind='edge';orientation=role}else{kind='feature'}
  if(cornerMask!==0&&cornerMask!==15)transition={from:material(spec[2]),to:material(spec[1])};
 }
 if(tile.family==='river-expansion02'){
  biome='temperate';if(routeNames[name]){model='route4';terrain='water';connections=routeNames[name];routeMask=connections.reduce((m,d)=>m|bits[d],0);kind=connections.length===1?'end':connections.length===2?(K.opposite[connections[0]]===connections[1]?'straight':'bend'):connections.length===3?'t-junction':'cross';orientation=connections.join('-');cap=connections.length===1?K.opposite[connections[0]]:null;transition={from:'grass',to:'water'}}else{terrain=name==='grass-center'?'grass':'water';model='fill';kind='fill'}
 }
 if(tile.family.startsWith('animated-')){terrain=tile.family==='animated-lava'?'lava':'water';biome=terrain==='lava'?'volcanic':'aquatic';if(tile.family==='animated-waterfall'){model='feature';kind='feature'}}
 if(tile.feature&&tile.feature.kind!=='rejected-corner'){model='feature';kind='feature'}
 if(tile.family==='overworld-ground'){biome=terrain==='snow'?'snow':terrain==='sand'?'desert':terrain==='forest'?'forest':'temperate'}
 if(tile.family==='overworld-mountain'){model='feature';kind='feature';terrain='rock';biome='mountain'}
 if(tile.family==='batch01-ground')biome=terrain==='grass'?'temperate':'unspecified';
 const usage=new Set(['terrain']);if(terrain==='path'||tile.family==='batch01-path')usage.add('path');if(tile.layer==='roof')usage.add('roof');if(tile.layer==='facade'||tile.layer==='building-ground')usage.add('building');if(transition)usage.add('boundary');if(kind==='feature'||tile.feature)usage.add('feature');if(terrain==='water')usage.add('water');if(terrain==='lava'||tile.layer==='hazard-ground')usage.add('hazard');
 const target=spec?.[0]||terrain,variantGroup=[tile.family,model,target,model==='area-corner16'?cornerMask:model==='route4'?routeMask:terrain,tile.animation?tile.animation.clip+':'+tile.animation.phase:'static',tile.feature?[tile.feature.kind,tile.feature.state,tile.feature.intendedRole].join(':'):'surface'].join('|'),aliases=terrain==='path'?['path','dirt-road','soil-path']:terrain==='grass'?['grass','meadow','meadow-turf','turf']:terrain==='snow'?['snow','tundra-snow','compacted-snow']:[terrain];
 return {...tile,terrain:{primary:terrain,aliases,materials:[...new Set([terrain,...materials])].sort()},biome:[biome],usage:[...usage],shape:{kind,orientation},topology:{model,terrain:target,cornerMask,routeMask,connections,cap,opening:connections.length===1?connections[0]:null,peering:{corners:tile.corners,sides:Object.fromEntries(Object.entries(tile.sides).map(([d,s])=>[d,s.profile]))}},transition,variant:{group:variantGroup,weight:1,visualCompatibility:'unreviewed'}};
}
module.exports={enrich,area,bits};
