'use strict';
// Explicit classifications checked against native contacts and existing adjacency proofs.
// Never derive feature connectability from a tile-name substring.
const K=require('./core.cjs');
const basis='Manual legacy classification from selected source descriptors, native contact sheets and existing adjacency proofs; canonical topology, not pixel seam certification';
const patchSets={
 town:{prefix:'roof-',family:'town-roof',inside:'cobalt-shingles',outside:'roof-exterior-unresolved',boundary:'roof-eave',layer:'roof'},
 interior:{prefix:'carpet-',family:'interior-carpet',inside:'red-gold-carpet',outside:'room-floor-unspecified',boundary:'carpet-binding',layer:'ground'},
 cave:{prefix:'wall-',family:'cave',inside:'cave-rock-top',outside:'cave-floor',boundary:'raised-rock-face',layer:'ground'},
 coast:{prefix:'shore-',family:'coast',inside:'sand',outside:'deep-water',boundary:'surf-foam',layer:'ground'},
 castle:{prefix:'masonry-',family:'castle',inside:'castle-masonry-top',outside:'castle-slate-floor',boundary:'stone-platform-face',layer:'ground'},
 'desert-ruins':{prefix:'ruin-',family:'desert-ruins',inside:'sandstone-top',outside:'desert-sand',boundary:'sandstone-side-face',layer:'ground'},
 'dungeon-transitions':{prefix:'wall-',family:'dungeon-transitions',inside:'stone-wall-top',outside:'flagstone-floor',boundary:'short-wall-face',layer:'ground'}
};
const fills={
 town:{'wall-cream-a':['cream-masonry','town-wall','facade'],'wall-cream-b':['cream-masonry','town-wall','facade'],cobble:['town-cobble','town-ground','ground']},
 interior:{'stone-floor-01':['room-stone','interior-floor','ground'],'stone-floor-02':['room-stone','interior-floor','ground'],'wood-floor-01':['room-wood','interior-floor','ground'],'wood-floor-02':['room-wood','interior-floor','ground']},
 cave:{'cracked-wall':['cave-rock-top'],'floor-01':['cave-floor'],'floor-02':['cave-floor']},
 coast:{'deepwater-01':['deep-water'],'deepwater-02':['deep-water'],'deepwater-03':['deep-water'],'sand-01':['sand'],'sand-02':['sand']},
 castle:{'floor-01':['castle-slate-floor'],'floor-02':['castle-slate-floor']},
 'desert-ruins':{'sandstone-floor-01':['sandstone-top'],'sandstone-floor-02':['sandstone-top'],'sand-floor-01':['desert-sand'],'sand-floor-02':['desert-sand']},
 'dungeon-transitions':{'floor-flagstone-01':['flagstone-floor'],'floor-flagstone-02':['flagstone-floor']}
};
const features={
 town:{window:'cream-masonry','door-open':'cream-wall-threshold','door-closed':'cream-wall-threshold',chimney:'roof-or-wall-substrate-unspecified'},
 interior:{table:'brown-room-floor-unspecified',chair:'brown-room-floor-unspecified',shelf:'brown-room-floor-unspecified'},
 cave:{'stairs-up':'cave-floor','stairs-down':'cave-floor','loose-rock':'cave-floor','treasure-chest':'cave-floor'},
 coast:{'shore-center':'deep-water'},
 castle:{'red-carpet':'red-carpet',stairs:'castle-slate-floor',pillar:'castle-slate-floor',grate:'castle-slate-floor',banner:'dark-wall-substrate-unspecified'},
 'desert-ruins':{'cracked-sandstone':'sandstone-sand-mix','ruin-rubble-01':'sandstone-sand-mix','ruin-rubble-02':'sandstone-sand-mix'},
 'dungeon-transitions':{'wall-door-open':'flagstone-wall-threshold','stairs-up':'flagstone-floor','stairs-down':'flagstone-floor','door-open':'wall-threshold-unspecified','door-closed':'wall-threshold-unspecified','stone-pillar':'flagstone-floor'}
};
function feature(owner,name,material,layer='ground'){return {family:owner,layer,geometry:K.full(material),feature:{kind:name,observedSubstrate:material,boundary:'Feature footprint and facing are not resolved by substrate tags',state:name.endsWith('-open')?'open':name.endsWith('-closed')?'closed':null},blocked:'Observed substrate is tagged on every side; feature orientation, footprint continuation or traversal needs manual review',basis}}
function classify(a){
 const owner=a.owner,name=a.name;
 if(a.id.startsWith('batch01:structures.')){
  const role=name==='roof-fill'?'center':name.startsWith('roof-')?name.slice(5):null;
  if(role&&K.roles[role])return {family:'batch01-roof',layer:'roof',geometry:K.patch(role,'batch01-shingles','building-exterior-unspecified','batch01-eave'),basis};
  if(name==='cream-wall'||name==='dungeon-wall')return {family:'batch01-'+name,layer:'facade',geometry:K.full(name),basis};
  const material={'door-open':'cream-wall-threshold','door-closed':'cream-wall-threshold',window:'cream-wall','chest-open':'dungeon-floor-unspecified','chest-closed':'dungeon-floor-unspecified',torch:'dungeon-wall','stairs-down':'dungeon-floor-unspecified'}[name];
  if(material)return feature('batch01-structures',name,material,['torch','window','door-open','door-closed'].includes(name)?'facade':'ground');
 }
 if(features[owner]?.[name])return feature(owner,name,features[owner][name],owner==='town'?'facade':name==='banner'?'facade':'ground');
 if(owner==='coast'&&['bridge-horizontal','bridge-vertical'].includes(name)){
  const geometry=K.full('deep-water'),profile=['deep-water','bridge-rail','bridge-planks','bridge-rail','deep-water'];for(const d of name==='bridge-horizontal'?['east','west']:['north','south'])geometry.sides[d]=profile;
  return {family:owner,layer:'ground',geometry,feature:{kind:name,axis:name==='bridge-horizontal'?'east-west':'north-south',traversal:'unknown'},basis};
 }
 const fill=fills[owner]?.[name];if(fill)return {family:fill[1]||owner,layer:fill[2]||'ground',geometry:K.full(fill[0]),basis};
 const set=patchSets[owner];if(set&&name.startsWith(set.prefix)){const role=name.slice(set.prefix.length);if(K.roles[role])return {family:set.family,layer:set.layer,geometry:K.patch(role,set.inside,set.outside,set.boundary),basis}}
 return null;
}
module.exports={classify};
