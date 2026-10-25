import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { allocateReleaseVersion, artifactNames, combinedCredits, migrationPolicyNote, nextVersion, readReleaseConfig, requireReleaseEnvironment, tagFor, verifyFrozenArchives, verifyMigrationSnapshot, verifyReleaseMetadata, verifyTag } from '../tools/ashenspire-release.mjs';
import { commonIndexText, CONTRACT, packRecords } from '../tools/display-snapshot.mjs';
const sha='a'.repeat(40),env={GITHUB_REPOSITORY:'cehinds/AI-Art',GITHUB_REF:'refs/heads/ashenspire',GITHUB_SHA:sha};
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const hash=value=>createHash('sha256').update(typeof value==='string'?value:JSON.stringify(value)).digest('hex');
function frozenFixture(dir) {
  const row=(path)=>({path,bytes:1,sha256:'0'.repeat(64)});
  const manifest={_:'fixture header',schema:2,tiers:{high:'high',light:'light',common:'common'},count:2,assets:{
    'assets/fixture.webp':{high:row('assets/fixture.webp'),light:row('assets-mobile/fixture.webp')},
    'assets-display/layered/fixture.webp':{common:row('assets-display/layered/fixture.webp')},
  }};
  const common=packRecords(manifest,'common');
  const contract={schema:1,manifestSchema:2,displayCount:1,displayPayloadBytes:1,
    images:[{id:'assets-display/layered/fixture.webp',bytes:1,sha256:'0'.repeat(64),width:1,height:1}],
    base:{headerDigest:hash({_:manifest._,schema:2,tiers:manifest.tiers}),packs:{}},
    projected:{manifestCount:2,commonCount:1,commonRecordDigest:hash(common),commonPackIndexSha256:hash(commonIndexText(common))},
    preservedZipSha256:{high:hash('tiny high fixture'),light:hash('tiny light fixture')},
  };
  for(const pack of ['high','light','common']){
    const rows=packRecords(manifest,pack,id=>!id.startsWith('assets-display/'));
    contract.base.packs[pack]={count:Object.keys(rows).length,payloadBytes:Object.values(rows).reduce((n,r)=>n+r.bytes,0),recordDigest:hash(rows)};
  }
  mkdirSync(join(dir,'migration'),{recursive:true});mkdirSync(join(dir,'dist'),{recursive:true});
  writeFileSync(join(dir,'release.json'),JSON.stringify({version:24,preserveMigratedAssetBytes:true,reviewMarker:'retained'}));
  writeFileSync(join(dir,'art-manifest.json'),JSON.stringify(manifest));
  writeFileSync(join(dir,CONTRACT),JSON.stringify(contract));
  // Deliberately tiny arbitrary bytes, not packed art archives.
  writeFileSync(join(dir,'dist/hd-assets-v25.zip'),'tiny high fixture');
  writeFileSync(join(dir,'dist/light-assets-v25.zip'),'tiny light fixture');
  return {manifest,contract};
}
test('release environment rejects other games, other repositories and mutable targets',()=>{
  assert.doesNotThrow(()=>requireReleaseEnvironment(env));
  for(const change of [{GITHUB_REF:'refs/heads/ff2'},{GITHUB_REF:'refs/heads/main'},{GITHUB_REPOSITORY:'cehinds/elsewhere'},{GITHUB_SHA:'ashenspire'}])assert.throws(()=>requireReleaseEnvironment({...env,...change}));
});
test('version allocation scopes tags to AshenSpire, preserves v23 and keeps ZIP names unprefixed',()=>{
  assert.equal(nextVersion(['ashenspire-hd-assets-v23','ff2-hd-assets-v999','hd-assets-v900'],24),24);
  assert.equal(nextVersion(['ashenspire-hd-assets-v24'],24),25);
  assert.equal(tagFor(24),'ashenspire-hd-assets-v24');
  assert.deepEqual(artifactNames(24),['hd-assets-v24.zip','hd-assets-v24.zip.sha256','light-assets-v24.zip','light-assets-v24.zip.sha256','common-assets-v24.zip','common-assets-v24.zip.sha256','art-manifest.json','CREDITS.md']);
  assert.throws(()=>nextVersion(['ashenspire-hd-assets-v999999999999999999'],24));
});
test('publication requires exact eight assets, hashes, sizes, target and release state',()=>{
  const expected=artifactNames(24).map((name,i)=>({name,bytes:i+1,sha256:String(i).repeat(64)}));
  const release={id:1,tag_name:tagFor(24),target_commitish:sha,draft:true,prerelease:false,assets:expected.map(r=>({name:r.name,size:r.bytes,digest:'sha256:'+r.sha256}))};
  assert.equal(verifyReleaseMetadata(release,expected,24,sha,true),1);
  for(const change of [{draft:false},{tag_name:'ff2-hd-assets-v24'},{target_commitish:'b'.repeat(40)},{assets:release.assets.slice(1)},{assets:release.assets.map((a,i)=>i?a:{...a,digest:'sha256:'+'f'.repeat(64)})},{assets:release.assets.map((a,i)=>i?a:{...a,size:999})}])assert.throws(()=>verifyReleaseMetadata({...release,...change},expected,24,sha,true));
  assert.throws(()=>verifyTag({object:{type:'commit',sha:'b'.repeat(40)}},sha));
  assert.throws(()=>verifyTag({object:{type:'tag',sha}},sha),/lightweight/);
  assert.doesNotThrow(()=>verifyTag({object:{type:'commit',sha}},sha));
});
test('an occupied v24 allocates v25 without losing the required reviewed policy or other fields',()=>{
  const dir=mkdtempSync(join(tmpdir(),'release-policy-'));
  try{
    frozenFixture(dir);
    assert.equal(allocateReleaseVersion(dir,['ashenspire-hd-assets-v24']),25);
    assert.deepEqual(readReleaseConfig(dir),{version:25,preserveMigratedAssetBytes:true,reviewMarker:'retained'});
    assert.match(migrationPolicyNote(dir),/regardless of allocated version/);
    assert.doesNotMatch(migrationPolicyNote(dir),/Initial v24/);
  }finally{rmSync(dir,{recursive:true,force:true});}
});
test('v25 retries enforce the actual frozen snapshot and high/light artifact hashes',async()=>{
  const dir=mkdtempSync(join(tmpdir(),'release-freeze-'));
  try{
    const {manifest}=frozenFixture(dir);
    const version=allocateReleaseVersion(dir,['ashenspire-hd-assets-v24']);
    assert.equal(verifyMigrationSnapshot(dir),true);
    await verifyFrozenArchives(dir,version);
    manifest.assets['assets/fixture.webp'].high.bytes++;
    writeFileSync(join(dir,'art-manifest.json'),JSON.stringify(manifest));
    await assert.rejects(verifyFrozenArchives(dir,version),/Existing high records/);
    frozenFixture(dir);allocateReleaseVersion(dir,['ashenspire-hd-assets-v24']);
    for(const name of ['hd','light']){
      const file=join(dir,`dist/${name}-assets-v25.zip`),original=readFileSync(file);
      writeFileSync(file,'corrupt fixture');
      await assert.rejects(verifyFrozenArchives(dir,25),/Migration policy: release v25 changed/);
      writeFileSync(file,original);
    }
  }finally{rmSync(dir,{recursive:true,force:true});}
});
test('missing or mistyped migration policy fails closed; only an explicit false lifts the freeze',async()=>{
  const dir=mkdtempSync(join(tmpdir(),'release-invalid-policy-'));
  try{
    frozenFixture(dir);
    for(const flag of [undefined,null,'true',1,{},[]]){
      const config={version:24,preserveMigratedAssetBytes:flag};
      writeFileSync(join(dir,'release.json'),JSON.stringify(config));
      assert.throws(()=>readReleaseConfig(dir),/requires boolean/);
      assert.throws(()=>allocateReleaseVersion(dir,['ashenspire-hd-assets-v24']),/requires boolean/);
      assert.throws(()=>verifyMigrationSnapshot(dir),/requires boolean/);
      await assert.rejects(verifyFrozenArchives(dir,25),/requires boolean/);
      assert.deepEqual(JSON.parse(readFileSync(join(dir,'release.json'),'utf8')),JSON.parse(JSON.stringify(config)));
    }
    writeFileSync(join(dir,'release.json'),JSON.stringify({version:25,preserveMigratedAssetBytes:false}));
    assert.equal(verifyMigrationSnapshot(dir),false);
    assert.match(migrationPolicyNote(dir),/explicitly disabled/);
  }finally{rmSync(dir,{recursive:true,force:true});}
});
test('real CLI retry preserves policy, rejects invalid config and checks v25 archive corruption',()=>{
  const dir=mkdtempSync(join(tmpdir(),'release-cli-'));
  try{
    frozenFixture(dir);mkdirSync(join(dir,'tools'));
    for(const file of ['ashenspire-release','pack','zip','manifest','assetmime','mobileart-policy','display-snapshot']){
      copyFileSync(join(root,'tools',file+'.mjs'),join(dir,'tools',file+'.mjs'));
    }
    const cliInput=(args,input)=>spawnSync(process.execPath,[join(dir,'tools/ashenspire-release.mjs'),...args],
      {env:{...process.env,...env},input,encoding:'utf8'});
    const cli=(...args)=>cliInput(args,'ashenspire-hd-assets-v24\n');
    const allocated=cli('--allocate-version');assert.equal(allocated.status,0,allocated.stderr);assert.equal(allocated.stdout.trim(),'25');
    assert.equal(readReleaseConfig(dir).preserveMigratedAssetBytes,true);
    assert.equal(readReleaseConfig(dir).reviewMarker,'retained');
    for(const ref of [null,{}, {object:null}, {object:{type:'commit',sha:''}},
      {object:{type:'commit',sha:'b'.repeat(40)}}, {object:{type:'tag',sha}}]){
      const result=cliInput(['--verify-tag'],JSON.stringify(ref));
      assert.notEqual(result.status,0);assert.match(result.stderr,/lightweight and name the event commit/);
    }
    assert.notEqual(cliInput(['--verify-tag'],'').status,0);
    assert.equal(cliInput(['--verify-tag'],JSON.stringify({object:{type:'commit',sha}})).status,0);
    assert.equal(cli('--verify-snapshot').status,0);
    assert.equal(cli('--verify-archives','25').status,0);
    const manifestPath=join(dir,'art-manifest.json'),manifest=readFileSync(manifestPath);
    const changed=JSON.parse(manifest);changed.assets['assets/fixture.webp'].high.bytes++;
    writeFileSync(manifestPath,JSON.stringify(changed));
    const stale=cli('--verify-snapshot');assert.notEqual(stale.status,0);assert.match(stale.stderr,/Existing high records/);
    writeFileSync(manifestPath,manifest);
    writeFileSync(join(dir,'dist/light-assets-v25.zip'),'corrupt');
    const corrupt=cli('--verify-archives','25');assert.notEqual(corrupt.status,0);assert.match(corrupt.stderr,/release v25 changed the original light/);
    for(const config of ['{"version":24}','{"version":24,"preserveMigratedAssetBytes":"true"}']){
      writeFileSync(join(dir,'release.json'),config);
      for(const args of [['--allocate-version'],['--verify-snapshot'],['--verify-archives','25'],['--policy-note']]){
        const result=cli(...args);assert.notEqual(result.status,0);assert.match(result.stderr,/requires boolean/);
      }
      assert.equal(readFileSync(join(dir,'release.json'),'utf8'),config);
    }
  }finally{rmSync(dir,{recursive:true,force:true});}
});
test('workflow reserves a fresh lightweight ref after artifact checks and verifies the actual ref before publication',()=>{
  const workflow=readFileSync(join(root,'.github/workflows/ashenspire-art.yml'),'utf8');
  const ordered=[
    'node tools/ashenspire-release.mjs --verify-archives "$VERSION"',
    'node tools/ashenspire-release.mjs --credits',
    'test -z "$existing"',
    'gh api --method POST "repos/$GITHUB_REPOSITORY/git/refs"',
    '-f ref="refs/tags/$TAG" -f sha="$GITHUB_SHA"',
    'node tools/ashenspire-release.mjs --verify-tag < dist/tag-reservation.json',
    'gh release create "$TAG" --verify-tag --draft',
    'node tools/ashenspire-release.mjs --verify-draft "$VERSION"',
    'gh api "repos/$GITHUB_REPOSITORY/git/ref/tags/$TAG" > dist/tag.json',
    'node tools/ashenspire-release.mjs --verify-tag < dist/tag.json',
    'gh api --method PATCH "repos/$GITHUB_REPOSITORY/releases/$id" -F draft=false',
  ];
  let offset=0;
  for(const command of ordered){const index=workflow.indexOf(command,offset);assert.ok(index>=offset,command);offset=index+command.length;}
  assert.doesNotMatch(workflow,/--method PATCH[^\n]*git\/refs|--force|tag_sha/);
  assert.match(workflow,/set -euo pipefail/);
});
test('both original credit ledgers survive verbatim without inferred relicensing',()=>{
  const old='# Old\nOriginal notice.\n',game='# Game\nUnresolved provenance stays unresolved.\n';
  const output=combinedCredits(old,game);
  assert.ok(output.includes(old));assert.ok(output.includes(game));assert.match(output,/does not relicense/);
  assert.throws(()=>combinedCredits(old,''));
});
