import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync, unlinkSync, symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname, resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
import {checkedPath, decodeImages, readReceipt, verifySourceContract} from './ashenspire-source-contract.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const sourcePaths = ['pose-studio/fixtures/high.webp','pose-studio/fixtures/lite.webp'];
const stancePath = 'pose-studio/stances/registry.json';
const basePath = 'pose-studio/renewal/base-action-registry.json';
const rigPath = 'pose-studio/fixtures/stance.rig.json';
const frame = () => ({path:sourcePaths[0],lite:sourcePaths[1],size:[512,512],bounds:[20,20,400,464],anchor:[256,464]});
const classes = ['reaver','rogue','starseer','herald'];
const actions = ['attack','defense','power'];
const write = (root,path,value) => {mkdirSync(dirname(resolve(root,path)),{recursive:true});writeFileSync(resolve(root,path),Buffer.isBuffer(value)?value:JSON.stringify(value));};
const json = (root,path) => JSON.parse(readFileSync(resolve(root,path)));
const uri = bytes => 'data:image/webp;base64,' + bytes.toString('base64');

function fixture(t) {
  const root = mkdtempSync(resolve(tmpdir(),'ashenspire-contract-fixture-'));
  t.after(() => rmSync(root,{recursive:true,force:true}));
  mkdirSync(resolve(root,'pose-studio/fixtures'),{recursive:true});
  const generated = spawnSync(process.env.PYTHON || 'python3',['-c',String.raw`
import sys
from PIL import Image, ImageDraw
from pathlib import Path
folder=Path(sys.argv[1])/'pose-studio/fixtures'
image=Image.new('RGBA',(512,512)); ImageDraw.Draw(image).rectangle((20,20,399,463),fill=(70,100,170,255))
image.save(folder/'high.webp','WEBP',lossless=True)
image.resize((256,256)).save(folder/'lite.webp','WEBP',lossless=True)
image.save(folder/'sheet.png','PNG')
`,root],{encoding:'utf8',timeout:10_000,maxBuffer:65536});
  assert.equal(generated.status,0,generated.stderr);
  const high=readFileSync(resolve(root,sourcePaths[0])),lite=readFileSync(resolve(root,sourcePaths[1]));
  const frames=Object.fromEntries(['offensive','defensive','casting'].map(id=>[id,{...frame(),sha256:sha(high),liteSha256:sha(lite)}]));
  write(root,stancePath,{schemaVersion:1,stances:Object.keys(frames),actors:Object.fromEntries(Array.from({length:41},(_,i)=>['actor'+i,{rig:rigPath,frames:structuredClone(frames)}]))});
  write(root,rigPath,{schemaVersion:1,canvas:{width:512,height:512},assets:Object.fromEntries(Object.keys(frames).map(id=>[id,{src:uri(high)}]))});
  const baseFrames=Object.fromEntries(Array.from({length:12},(_,i)=>['frame'+i,{...frame(),path:'frames/base-high.webp',lite:'frames/base-lite.webp'}]));
  write(root,'pose-studio/renewal/frames/base-high.webp',high);
  write(root,'pose-studio/renewal/frames/base-lite.webp',lite);
  const baseRigPath='pose-studio/renewal/base.rig.json';
  write(root,baseRigPath,{schemaVersion:1,canvas:{width:512,height:512},assets:Object.fromEntries(Object.keys(baseFrames).map(id=>[id,{src:uri(high)}]))});
  const families={};
  for(const actor of classes){
    families[actor]={manifest:actor+'.json',rig:'base.rig.json',folder:''};
    write(root,'pose-studio/renewal/'+actor+'.json',{schemaVersion:1,classId:actor,armour:'default',equipmentIndependent:true,frames:baseFrames,sequences:Object.fromEntries(actions.map(id=>[id,{}])),bytes:{webp:12*high.length,lite:12*lite.length}});
  }
  write(root,basePath,{schemaVersion:1,classes,actions,equipmentIndependent:true,families});
  const paths=[sourcePaths[0],sourcePaths[1],stancePath,basePath,rigPath,baseRigPath,'pose-studio/renewal/frames/base-high.webp','pose-studio/renewal/frames/base-lite.webp',...classes.map(a=>'pose-studio/renewal/'+a+'.json')];
  const receipt={schemaVersion:1,origin:{repository:'cehinds/AI-Art',commit:'a'.repeat(40),tag:'ashenspire-hd-assets-v24'},files:{}};
  const pngPath='pose-studio/fixtures/sheet.png', png=readFileSync(resolve(root,pngPath));
  const source={path:pngPath,width:512,height:512,sha256:sha(png)};
  const roles=Object.keys(readReceipt().selected.weaponFrames);
  const selected={catalogOrigin:{repository:'cehinds/AshenSpire',commit:'a'.repeat(40),blob:'b'.repeat(40),sha256:'c'.repeat(64)},selections:'pose-studio/fixtures/selections.json',weaponSelections:'pose-studio/fixtures/production.json',reviewSources:'pose-studio/fixtures/sources.json',weaponProvenance:['pose-studio/fixtures/provenance.json'],weaponFrames:Object.fromEntries(roles.map(role=>[role,{sourceOption:role==='sweep'?'SW09':'choice-'+role,source,runtimePath:'assets-display/'+role+'.webp',runtimeSha256:role==='attack-3'?sha(high):'1'.repeat(64)}]))};
  write(root,selected.selections,{schemaVersion:1,choices:classes.flatMap(actor=>['attack','defend','casting'].map(stance=>({actor,stance,source:{path:'high.webp',width:512,height:512,sha256:sha(high),view:{x:0,y:0,width:512,height:512}}})))});
  write(root,selected.weaponSelections,{schemaVersion:1,choices:roles.slice(0,18).map(role=>({role,sourceOption:'choice-'+role})),reviewManifest:'pose-studio/fixtures/review.json'});
  write(root,'pose-studio/fixtures/review.json',{schemaVersion:1});
  write(root,selected.weaponProvenance[0],{schemaVersion:1,frames:[{key:'sweep',sourcePath:pngPath,sourceDimensions:[512,512],sourceSha256:sha(png),full:{sha256:'1'.repeat(64)}}]});
  write(root,selected.reviewSources,{schemaVersion:1,sources:Array.from({length:15},(_,i)=>({id:i===0?'AT3':'input'+i,source:sourcePaths[0],sha256:sha(high),size:[512,512],...(i===0?{originalSheetRecipe:source}:{})}))});
  paths.push(pngPath,selected.selections,selected.weaponSelections,selected.reviewSources,...selected.weaponProvenance,'pose-studio/fixtures/review.json');
  receipt.selected=selected;
  const refresh=path=>{const bytes=readFileSync(resolve(root,path));receipt.files[path]={mode:'100644',bytes:bytes.length,oid:createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex')};};
  paths.forEach(refresh);
  return {root,receipt,refresh,high,lite};
}

test('production receipt describes 399 immutable source inputs, not a release mutation',()=>{
  const receipt=readReceipt();
  assert.equal(receipt.origin.commit,'59663d814b62ab96cb5309b4e0720cd871782ee1');
  assert.equal(Object.keys(receipt.files).length,399);
  assert.equal(Object.values(receipt.files).reduce((n,row)=>n+row.bytes,0),55892481);
});
test('actual CLI emits only the recorded sparse source paths and fails on a missing root',()=>{
  const script=new URL('./ashenspire-source-contract.mjs',import.meta.url);
  const paths=spawnSync(process.execPath,[script.pathname,'--paths'],{encoding:'utf8',timeout:10_000,maxBuffer:65536});
  assert.equal(paths.status,0,paths.stderr);
  assert.deepEqual(paths.stdout.trim().split('\n'),Object.keys(readReceipt().files).map(p=>'/'+p));
  const missing=spawnSync(process.execPath,[script.pathname,'--root','/nonexistent-ashenspire-source-contract-root'],{encoding:'utf8',timeout:10_000,maxBuffer:65536});
  assert.equal(missing.status,1);assert.match(missing.stderr,/ENOENT/);
});
test('complete synthetic sources really decode; 41 actors and all 48 base frames pass',t=>{
  const f=fixture(t),result=verifySourceContract(f.root,f.receipt);
  assert.equal(result.stanceActors,41);assert.equal(result.stanceFrames,123);assert.equal(result.baseFrames,48);assert.equal(result.decodedImages,5);assert.equal(result.previewSources,15);
});
test('missing HIGH and LITE sources both fail closed',t=>{
  for(const path of [sourcePaths[0],sourcePaths[1]]){const f=fixture(t);unlinkSync(resolve(f.root,path));assert.throws(()=>verifySourceContract(f.root,f.receipt),/ENOENT/);}
});
test('same-size corrupt source fails frozen Git identity',t=>{
  const f=fixture(t),bytes=Buffer.from(f.high);bytes[bytes.length-1]^=1;write(f.root,sourcePaths[0],bytes);
  assert.throws(()=>verifySourceContract(f.root,f.receipt),/frozen v24 Git blob/);
});
test('base LITE substitution is protected despite having no original SHA256',t=>{
  const f=fixture(t),path='pose-studio/renewal/frames/base-lite.webp',bytes=Buffer.from(f.lite);bytes[bytes.length-1]^=1;write(f.root,path,bytes);
  assert.throws(()=>verifySourceContract(f.root,f.receipt),/frozen v24 Git blob/);
});
test('wrong source path cannot be satisfied by a mutable alternate file',t=>{
  const f=fixture(t),catalog=json(f.root,stancePath);catalog.actors.actor0.frames.offensive.path='pose-studio/other.webp';write(f.root,stancePath,catalog);f.refresh(stancePath);
  assert.throws(()=>verifySourceContract(f.root,f.receipt),/unrecorded\/wrong source path/);
});
test('path traversal and symlink substitution are rejected',t=>{
  for(const path of ['../escape.webp','pose-studio/../escape.webp','pose-studio//x','pose-studio/x\n'])assert.throws(()=>checkedPath(path));
  const f=fixture(t);unlinkSync(resolve(f.root,sourcePaths[0]));symlinkSync(resolve(f.root,sourcePaths[1]),resolve(f.root,sourcePaths[0]));assert.throws(()=>verifySourceContract(f.root,f.receipt),/regular source file/);
});
test('declared HIGH and LITE SHA256 mismatches each fail',t=>{
  for(const field of ['sha256','liteSha256']){const f=fixture(t),catalog=json(f.root,stancePath);catalog.actors.actor0.frames.offensive[field]='0'.repeat(64);write(f.root,stancePath,catalog);f.refresh(stancePath);assert.throws(()=>verifySourceContract(f.root,f.receipt),/SHA256/);}
});
test('HIGH must match embedded rig rather than LITE or a different image',t=>{
  const f=fixture(t),rig=json(f.root,rigPath);rig.assets.offensive.src=uri(f.lite);write(f.root,rigPath,rig);f.refresh(rigPath);assert.throws(()=>verifySourceContract(f.root,f.receipt),/HIGH differs from embedded rig/);
});
test('non-WebP embedded MIME is rejected',t=>{
  const f=fixture(t),rig=json(f.root,rigPath);rig.assets.offensive.src='data:image/png;base64,'+f.high.toString('base64');write(f.root,rigPath,rig);f.refresh(rigPath);assert.throws(()=>verifySourceContract(f.root,f.receipt),/not embedded WebP/);
});
test('geometry anchor, crop, decoded alpha crop and declared size remain enforced',t=>{
  for(const [field,value,pattern] of [['anchor',[256,463],/anchor/],['bounds',[0,20,400,464],/crop bounds/],['bounds',[21,20,400,464],/decoded alpha crop/],['size',[256,256],/declared size/]]){
    const f=fixture(t),catalog=json(f.root,stancePath);catalog.actors.actor0.frames.offensive[field]=value;write(f.root,stancePath,catalog);f.refresh(stancePath);assert.throws(()=>verifySourceContract(f.root,f.receipt),pattern);
  }
});
test('decoder validates actual dimensions and rejects truncated WebP payload',t=>{
  const f=fixture(t),result=decodeImages(f.root,new Map([[sourcePaths[1],{threshold:32,format:'WEBP'}]]));assert.deepEqual(result.get(sourcePaths[1]).size,[256,256]);
  write(f.root,sourcePaths[1],f.lite.subarray(0,24));assert.throws(()=>decodeImages(f.root,new Map([[sourcePaths[1],{threshold:32,format:'WEBP'}]])),/Image decode failed/);
});
test('selected PNG source hash, dimensions and MIME are checked against actual bytes',t=>{
  for(const kind of ['hash','dimensions','MIME']){
    const f=fixture(t);
    if(kind==='hash')for(const frame of Object.values(f.receipt.selected.weaponFrames))frame.source.sha256='0'.repeat(64);
    if(kind==='dimensions'){
      for(const frame of Object.values(f.receipt.selected.weaponFrames))frame.source.width=511;
      const path=f.receipt.selected.weaponProvenance[0],doc=json(f.root,path);doc.frames[0].sourceDimensions[0]=511;write(f.root,path,doc);f.refresh(path);
    }
    if(kind==='MIME'){write(f.root,'pose-studio/fixtures/sheet.png',f.high);f.refresh('pose-studio/fixtures/sheet.png');}
    assert.throws(()=>verifySourceContract(f.root,f.receipt),/selected source SHA256|decoded dimensions|PNG MIME/);
  }
});
test('actual PNG decoder rejects corrupt pixels even with a valid PNG signature',t=>{
  const f=fixture(t),path='pose-studio/fixtures/sheet.png',bytes=readFileSync(resolve(f.root,path));bytes[bytes.length-20]^=1;write(f.root,path,bytes);
  assert.throws(()=>decodeImages(f.root,new Map([[path,{threshold:32,format:'PNG'}]])),/Image decode failed/);
});
test('selected source PNG is required at the recorded path',t=>{
  const f=fixture(t);unlinkSync(resolve(f.root,'pose-studio/fixtures/sheet.png'));assert.throws(()=>verifySourceContract(f.root,f.receipt),/ENOENT/);
});
test('selected source wrong path cannot use an unrecorded matching image',t=>{
  const f=fixture(t),path='pose-studio/fixtures/unrecorded.png';
  write(f.root,path,readFileSync(resolve(f.root,'pose-studio/fixtures/sheet.png')));
  for(const frame of Object.values(f.receipt.selected.weaponFrames))frame.source.path=path;
  assert.throws(()=>verifySourceContract(f.root,f.receipt),/unrecorded\/wrong source path/);
});
test('historical preview source and original-sheet hashes remain real byte assertions',t=>{
  for(const kind of ['source','recipe','counter','attack3']){
    const f=fixture(t),path=f.receipt.selected.reviewSources,review=json(f.root,path);
    if(kind==='source')review.sources[1].sha256='0'.repeat(64);
    if(kind==='recipe')review.sources[0].originalSheetRecipe.sha256='0'.repeat(64);
    if(kind==='counter')f.receipt.selected.weaponFrames.counter.runtimeSha256=sha(f.high);
    if(kind==='attack3')f.receipt.selected.weaponFrames['attack-3'].runtimeSha256='0'.repeat(64);
    write(f.root,path,review);f.refresh(path);
    assert.throws(()=>verifySourceContract(f.root,f.receipt),/selected source SHA256|historical AT3 bytes|AT3 preserves attack-3/);
  }
});
test('wrong LITE actual dimensions fail even when receipts and declared hashes agree',t=>{
  const f=fixture(t);write(f.root,sourcePaths[1],f.high);f.refresh(sourcePaths[1]);const c=json(f.root,stancePath);
  for(const a of Object.values(c.actors))for(const v of Object.values(a.frames))v.liteSha256=sha(f.high);
  write(f.root,stancePath,c);f.refresh(stancePath);assert.throws(()=>verifySourceContract(f.root,f.receipt),/decoded dimensions/);
});
test('source RIFF length must match the actual byte length',t=>{
  const f=fixture(t),bytes=Buffer.concat([f.high,Buffer.from([0])]);write(f.root,sourcePaths[0],bytes);f.refresh(sourcePaths[0]);assert.throws(()=>verifySourceContract(f.root,f.receipt),/RIFF byte length/);
});
test('base source byte totals, complete counts and receipt coverage cannot silently shrink',t=>{
  for(const kind of ['bytes','actor','frame','receipt']){
    const f=fixture(t);
    if(kind==='bytes'){const p='pose-studio/renewal/reaver.json',m=json(f.root,p);m.bytes.lite--;write(f.root,p,m);f.refresh(p);}
    if(kind==='actor'){const c=json(f.root,stancePath);delete c.actors.actor0;write(f.root,stancePath,c);f.refresh(stancePath);}
    if(kind==='frame'){const p='pose-studio/renewal/reaver.json',m=json(f.root,p);delete m.frames.frame0;write(f.root,p,m);f.refresh(p);}
    if(kind==='receipt')f.receipt.files['pose-studio/unused.json']={mode:'100644',oid:'0'.repeat(40),bytes:1};
    assert.throws(()=>verifySourceContract(f.root,f.receipt),/byte totals|actor coverage|frame count|receipt must cover/);
  }
});
