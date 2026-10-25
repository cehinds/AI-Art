import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { SOURCE_ACTORS, verifyClassSmashSources } from '../tools/source-integrity.mjs';
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
function fixture() {
  const root=mkdtempSync(join(tmpdir(),'source-integrity-'));
  for(const actor of SOURCE_ACTORS) {
    const prefix='pose-studio/stances/class-smash/'+actor+'/';
    const frames=prefix+(actor==='herald'?'frames/':'');
    const put=(path,bytes)=>{mkdirSync(join(root,path,'..'),{recursive:true});writeFileSync(join(root,path),bytes);};
    const provenance=JSON.stringify({actor,origin:'original synthetic source fixture'})+'\n';
    put(prefix+'provenance.json',provenance);
    const production={classId:actor,sourceProvenance:prefix+'provenance.json',sourceProvenanceSha256:hash(provenance),sourceBookends:{},frames:{}};
    for(const [i,role] of ['held','takeoff','airborne','impact','held'].entries()) {
      const data=Buffer.from(role==='held'?'original-bookend':'original-'+role);
      const path=frames+String(i+1).padStart(2,'0')+'-'+role+'.png';put(path,data);
      if(i<4)production.frames[role]={source:{path,sha256:hash(data)}};
      if(i===0)production.sourceBookends.first=hash(data);
      if(i===4)production.sourceBookends.last=hash(data);
    }
    put(prefix+'production.json',JSON.stringify(production));
  }
  return root;
}
test('all three packages hash actual source PNG and provenance bytes including both original bookends',()=>{
  const root=fixture();
  try{assert.deepEqual(verifyClassSmashSources(root),{actors:3,sourceFiles:18});}
  finally{rmSync(root,{recursive:true,force:true});}
});
test('corrupt source PNG, original last bookend and provenance JSON each fail independently',()=>{
  for(const file of [
    'pose-studio/stances/class-smash/rogue/02-takeoff.png',
    'pose-studio/stances/class-smash/herald/frames/05-held.png',
    'pose-studio/stances/class-smash/starseer/provenance.json',
  ]) {
    const root=fixture();
    try{writeFileSync(join(root,file),'changed source bytes');assert.throws(()=>verifyClassSmashSources(root),/Source bytes changed/);}
    finally{rmSync(root,{recursive:true,force:true});}
  }
});
test('changed source hash, mismatched bookend metadata and path escape cannot pass',()=>{
  for(const mutate of [
    p=>p.frames.held.source.sha256='0'.repeat(64),
    p=>p.sourceBookends.last='0'.repeat(64),
    p=>p.frames.takeoff.source.path='../outside.png',
  ]) {
    const root=fixture(),path=join(root,'pose-studio/stances/class-smash/rogue/production.json');
    try{const p=JSON.parse(readFileSync(path,'utf8'));mutate(p);writeFileSync(path,JSON.stringify(p));assert.throws(()=>verifyClassSmashSources(root));}
    finally{rmSync(root,{recursive:true,force:true});}
  }
});
