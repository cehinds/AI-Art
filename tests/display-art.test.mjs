import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildManifest, commonConsistency, commonRecord, isDisplayArtId, serialize } from '../tools/manifest.mjs';
import { packManifest } from '../tools/pack.mjs';
import { commonIndexText, displayRecords, packRecords, projectDisplayManifest, verifyDisplayManifest } from '../tools/display-snapshot.mjs';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const frozenContract = JSON.parse(readFileSync(join(root, 'migration/ashenspire-v24-display-contract.json'), 'utf8'));
const clone = (v) => structuredClone(v);
const sha = (value) => createHash('sha256').update(value).digest('hex');
// Keep the real frozen 146 common rows and all 675 display records. One tiny
// high/light pair tests projection mechanics without freezing future art edits.
const old = { _: 'Fixture historical header', schema: 2, tiers: { high: 'high', light: 'light', common: 'common' },
  assets: { 'assets/fixture.webp': { light: {path:'assets-mobile/fixture.webp',bytes:1,sha256:'0'.repeat(64)},
    high: {path:'assets/fixture.webp',bytes:2,sha256:'1'.repeat(64)} },
    ...Object.fromEntries(Object.entries(frozenContract.base.commonRecords).map(([id,row])=>[id,{common:row}])) } };
old.count=Object.keys(old.assets).length;
const contract=clone(frozenContract);
contract.base.headerDigest=sha(JSON.stringify({_:old._,schema:old.schema,tiers:old.tiers}));
for(const pack of ['high','light','common']) {
  const rows=packRecords(old,pack);
  contract.base.packs[pack]={count:Object.keys(rows).length,payloadBytes:Object.values(rows).reduce((n,r)=>n+r.bytes,0),recordDigest:sha(JSON.stringify(rows))};
}
contract.projected.manifestCount=old.count+675;
const projected=projectDisplayManifest(old,contract);
const baseline=()=>clone(old);
function png(width = 9, height = 7) {
  const b = Buffer.alloc(24);
  Buffer.from([137,80,78,71,13,10,26,10]).copy(b);
  b.write('IHDR',12); b.writeUInt32BE(width,16); b.writeUInt32BE(height,20);
  return b;
}
function webp() {
  const b = Buffer.alloc(30);
  b.write('RIFF'); b.write('WEBP',8); b.write('VP8X',12);
  b.writeUIntLE(8,24,3); b.writeUIntLE(6,27,3);
  return b;
}
test('source-backed snapshot preserves schema2 and exactly all six owners/675 common triples', () => {
  assert.equal(contract.source.commit, 'eaf770ce494655831273169e875c26daf9a0d095');
  assert.deepEqual(Object.values(contract.source.catalogOwners), [266,180,66,24,44,95]);
  const rows = displayRecords(contract);
  assert.equal(Object.keys(rows).length,675);
  assert.equal(Object.values(rows).reduce((n,r)=>n+r.bytes,0),53411291);
  for (const row of Object.values(rows)) assert.deepEqual(Object.keys(row),['path','bytes','sha256']);
  assert.equal(verifyDisplayManifest(projected,contract),true);
  assert.equal(projected.schema,2);
  assert.equal(frozenContract.projected.manifestCount,8169);
  assert.equal(projected.count,822);
});
test('projection keeps legacy rows and high/light pack manifests byte-for-byte', () => {
  const old = baseline();
  const before=serialize(old);
  const next = projectDisplayManifest(old,contract);
  for (const pack of ['high','light']) {
    assert.equal(serialize(packManifest(old,pack)),serialize(packManifest(next,pack)));
    assert.equal(Object.keys(packRecords(next,pack)).length,1);
  }
  assert.equal(serialize(old),before);
  assert.equal(serialize(next),serialize(projected));
});
test('normalized common index exactly matches the existing game augmentation', () => {
  const records=packRecords(projected,'common');
  assert.equal(Object.keys(records).length,821);
  assert.equal(Object.values(records).reduce((n,r)=>n+r.bytes,0),85568599);
  assert.equal(sha(commonIndexText(records)),'ed667bd375bba917f8f6581d7bbd094e9d4af216b1bb94d4be4913258c34fbb3');
});
test('duplicate display IDs and changed source hashes/dimensions/payload counts are rejected', () => {
  const duplicate=clone(contract); duplicate.images[1]=clone(duplicate.images[0]);
  assert.throws(()=>displayRecords(duplicate),/Duplicate/);
  for (const mutate of [
    c=>c.images[0].sha256='not-a-hash', c=>c.images[0].width=0,
    c=>c.images[0].height=-2, c=>c.displayCount++, c=>c.displayPayloadBytes++,
  ]) { const c=clone(contract);mutate(c);assert.throws(()=>displayRecords(c)); }
  const hash=clone(projected);hash.assets[contract.images[0].id].common.sha256='0'.repeat(64);
  assert.throws(()=>verifyDisplayManifest(hash,contract),/record mismatch/);
});
test('existing high/light/common rows, historical header and unexpected dimension fields remain protected', () => {
  for (const pack of ['high','light','common']) {
    const m=clone(projected), id=Object.keys(packRecords(m,pack,id=>!id.startsWith('assets-display/')))[0];
    m.assets[id][pack].bytes++;
    assert.throws(()=>verifyDisplayManifest(m,contract),/Existing/);
  }
  const header=clone(projected);header._+='changed';assert.throws(()=>verifyDisplayManifest(header,contract),/header/);
  const dimensions=clone(projected);dimensions.assets[contract.images[0].id].common.width=9;
  assert.throws(()=>verifyDisplayManifest(dimensions,contract),/record mismatch/);
});
test('display path grammar admits the source-backed images and refuses other games, traversal and metadata files', () => {
  for(const row of contract.images)assert.equal(isDisplayArtId(row.id),true,row.id);
  for(const id of ['assets-display/../escape.webp','assets-display/layered/x.json','assets-display/ff2/x.webp','assets-display/card-cutouts/sub/x.png','assets-display/alternative/x.png'])assert.equal(isDisplayArtId(id),false,id);
});
test('common records hash real payload bytes, validate PNG/WebP headers and keep dimensions out of schema2', () => {
  const dir=mkdtempSync(join(tmpdir(),'display-record-'));
  try{
    for(const [name,buf] of [['x.png',png()],['x.webp',webp()]]){
      const path=join(dir,name);writeFileSync(path,buf);
      const id='assets-display/'+(name.endsWith('.png')?'card-cutouts/':'layered/')+name;
      assert.deepEqual(commonRecord(path,id),{path:id,bytes:buf.length,sha256:sha(buf)});
    }
    const path=join(dir,'bad.png');
    writeFileSync(path,png(0,9));assert.throws(()=>commonRecord(path,'assets-display/card-cutouts/x.png'),/dimensions/);
    const noSignature=png();noSignature.fill(0,0,8);writeFileSync(path,noSignature);
    assert.throws(()=>commonRecord(path,'assets-display/card-cutouts/x.png'),/dimensions/);
  }finally{rmSync(dir,{recursive:true,force:true});}
});
test('full-tree manifest logic carries allowed display records, reports stray files and catches duplicate inputs',()=>{
  const dir=mkdtempSync(join(tmpdir(),'display-manifest-'));
  try{
    const target=join(dir,'common/assets-display/card-cutouts');mkdirSync(target,{recursive:true});
    writeFileSync(join(target,'A.1.png'),png());
    const valid=buildManifest(dir);assert.deepEqual(valid.problems,[]);
    assert.deepEqual(Object.keys(valid.manifest.assets['assets-display/card-cutouts/A.1.png']),['common']);
    writeFileSync(join(target,'notes.json'),'{}');
    assert.match(buildManifest(dir).problems.join('\n'),/not a file the common pack carries/);
    assert.match(commonConsistency([{id:'x'},{id:'x'}]).join('\n'),/duplicate/);
  }finally{rmSync(dir,{recursive:true,force:true});}
});
