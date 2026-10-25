'use strict';
const opposite={north:'south',east:'west',south:'north',west:'east'};
const roles={nw:[0,0,1,0],n:[0,0,1,1],ne:[0,0,0,1],w:[0,1,1,0],center:[1,1,1,1],e:[1,0,0,1],sw:[0,1,0,0],s:[1,1,0,0],se:[1,0,0,0],'inner-nw':[0,1,1,1],'inner-ne':[1,0,1,1],'inner-sw':[1,1,1,0],'inner-se':[1,1,0,1]};
function edge(a,b,boundary){return a===b?[a,a,a,a,a]:[a,a,boundary,b,b]}
function patch(role,inside,outside,boundary){const q=roles[role];if(!q)throw Error('Unknown patch role '+role);const [nw,ne,se,sw]=q.map(i=>i?inside:outside);return {corners:{nw,ne,se,sw},sides:{north:edge(nw,ne,boundary),east:edge(ne,se,boundary),south:edge(sw,se,boundary),west:edge(nw,sw,boundary)}}}
function full(material){return patch('center',material,material,material)}
function river(openings){const grass=Array(5).fill('grass'),water=['grass','river-bank','river-water','river-bank','grass'];return {corners:{nw:'grass',ne:'grass',se:'grass',sw:'grass'},sides:Object.fromEntries(Object.keys(opposite).map(d=>[d,openings.includes(d)?water:grass]))}}
function check(a,direction,b,policy={crossFamily:[]}){
 if(!Object.hasOwn(opposite,direction))return {match:false,reason:'invalid-direction'};
 if(!a||!b||typeof a!=='object'||typeof b!=='object')return {match:false,reason:'invalid-tile'};
 for(const tile of [a,b])if(typeof tile.family!=='string'||!tile.family.length||typeof tile.layer!=='string'||!tile.layer.length||!Array.isArray(tile.worldSize)||tile.worldSize.length!==2||!tile.worldSize.every(n=>Number.isFinite(n)&&n>0))return {match:false,reason:'invalid-tile'};
 if(a.state!=='modeled'||b.state!=='modeled')return {match:false,reason:'blocked-or-unreviewed'};
 const sideA=a.sides?.[direction],sideB=b.sides?.[opposite[direction]];
 if(sideA?.state!=='modeled'||sideB?.state!=='modeled')return {match:false,reason:'blocked-side'};
 if(![sideA.profile,sideB.profile].every(p=>Array.isArray(p)&&p.length===5&&p.every(m=>typeof m==='string'&&m.length)))return {match:false,reason:'invalid-edge-profile'};
 if(a.layer!==b.layer)return {match:false,reason:'layer-mismatch'};
 if(JSON.stringify(a.worldSize)!==JSON.stringify(b.worldSize))return {match:false,reason:'world-scale-mismatch'};
 const left=a.sides[direction].profile,right=b.sides[opposite[direction]].profile;
 if(!left||!right||JSON.stringify(left)!==JSON.stringify(right))return {match:false,reason:'edge-profile-mismatch'};
 if(a.family!==b.family){const allowed=(Array.isArray(policy?.crossFamily)?policy.crossFamily:[]).some(p=>p&&Array.isArray(p.families)&&Array.isArray(p.materials)&&p.families.includes(a.family)&&p.families.includes(b.family)&&p.layer===a.layer&&left.every(m=>p.materials.includes(m)));if(!allowed)return {match:false,reason:'family-mismatch'}}
 for(const tile of [a,b])if(tile.animation&&(!Number.isInteger(tile.animation.phase)||!Number.isInteger(tile.animation.frames)||tile.animation.phase<0||tile.animation.phase>=tile.animation.frames||!Number.isFinite(tile.animation.durationMs)||!Number.isFinite(tile.animation.cycleMs)||tile.animation.durationMs<=0||tile.animation.cycleMs<=0))return {match:false,reason:'invalid-animation'};
 if(a.animation&&b.animation&&(a.animation.phase!==b.animation.phase||a.animation.frames!==b.animation.frames||a.animation.durationMs!==b.animation.durationMs||a.animation.cycleMs!==b.animation.cycleMs))return {match:false,reason:'animation-phase-mismatch'};
 return {match:true,reason:'logical-profile-compatible',visualSeamGuaranteed:false};
}
module.exports={opposite,roles,edge,patch,full,river,check};
