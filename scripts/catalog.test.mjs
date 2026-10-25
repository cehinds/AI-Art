import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import sharp from 'sharp';
import { ROOT,GAMES,hash,blobHash,isAsset,classify,sourceLinks,loadInventory,git } from './lib.mjs';
import { manifestHints,buildCatalog,assetName,assetVariant,makePreview } from './build-catalog.mjs';
import { importGame } from './import-snapshots.mjs';
import { verifySnapshots } from './verify-snapshots.mjs';
import { GitBlobReader } from './git-blobs.mjs';

test('critical categories and provenance do not promote references and review sheets',()=>{
  const cases=[
    ['Assets/Art/Production/Campaign/weapons/sword.png','weapons','production'],
    ['Assets/Art/Production/Campaign/effects/bow-shot/frame01.png','effects','production'],
    ['ArtSource/Campaign/party/firion-battle.png','characters','source'],
    ['References/terrain.png','references','reference'],
    ['Review/art/party.gif','animations','review'],
    ['Review/art/fx-fire.apng','animations','review'],
    ['References/party.gif','references','reference'],
    ['ArtSource/Batch01/revisions/terrain-v1.png','tiles','archive'],
    ['assets/sprites/draugr.svg','creatures','production'],
    ['assets/sprites/lydia.svg','characters','production'],
    ['assets/bg/bg-crypt.svg','environments','production'],
    ['assets/sprites/chest.svg','props','production'],
    ['dungeon-crawler-tactics/originals/exec-id.png','source-sheets','source'],
    ['packs/gear.zip','props','archive'],
    ['assets/ui-kit/card.png','ui','production'],
    ['Docs/ConceptArt/Styles/dungeon-after-dark.png','concepts','concept'],
    ['Docs/Screenshots/fidelity-home-mobile.png','other','review'],
    ['Assets/Art/Production/Campaign/transport/airship/down.png','props','production'],
    ['UnityPackage/Runtime/Resources/Art/alchemist.png','characters','production'],
    ['UnityPackage/Runtime/Resources/RoomKit/doors/door-closed-ne.png','tiles','production'],
    ['UnityPackage/Runtime/Resources/RoomKit/overlays/fire-overlay.png','effects','production'],
    ['hd/assets/animations/bow/herald/BOW-01.webp','characters','production'],
    ['light/assets/enemy-poses/expansion/archer.webp','creatures','production'],
    ['hd/assets/equipment/weapon_halberd.webp','weapons','production'],
    ['hd/assets/cards/default-outline/icons/sword.svg','ui','production'],
    ['art/card-portraits-2026-10-05/roadWarden.png','characters','source'],
    ['art/sword-shield-outfits-2026-09-19/rogue/ATK-01.webp','characters','source'],
    ['art/twin-sword-reference-2026-09-19/rogue/ATK-01.webp','characters','source'],
    ['art/creation-feats-2026-10-12/preview.png','other','review']
  ];
  for(const [file,type,kind] of cases) assert.deepEqual(classify(file),{type,kind},file);
  assert.equal(classify('components/rope.png',{status:'concept-component',category:'equipment'}).kind,'concept');
  assert.equal(classify('assets/tiles/contact-sheet.png').kind,'review');
  assert.equal(assetName('Assets/Art/firion/01-down-left-foot.png'),'Firion · 01 down left foot');
  assert.equal(assetName('assets/book-tiles/crypt/center.png',{label:'Center'}),'Crypt · Center');
  assert.equal(assetName('Assets/Art/Production/Campaign/weapon/bow/drawn.png'),'Bow · Drawn');
  assert.equal(assetName('Assets/Art/Production/Campaign/effects/bow-shot/frame01.png',{group:'effects'}),'Bow shot · Frame01');
  assert.equal(assetName('Assets/Art/Production/Campaign/weapon/shield/angled.png'),'Shield · Angled');
  assert.equal(assetName('assets/props/ancient-chest.png'),'ancient chest');
  assert.equal(assetVariant('assets/book-tiles/ink-and-lanterns/crypt/center.png'),'Ink & Lanterns');
  assert.equal(assetVariant('assets/sprites/lydia.svg'),'');
  assert.equal(assetVariant('hd/assets/animations/bow/herald/BOW-01.webp'),'HD');
  assert.equal(assetVariant('light/assets/animations/bow/herald/BOW-01.webp'),'Light');
  assert.equal(assetVariant('common/fonts/font.woff2'),'Shared');
  assert.equal(assetName('hd/assets/animations/bow/herald/BOW-01.webp'),'Herald · BOW 01');
});
test('supported extensions include authoring formats and archives; downloads pin exact commits',()=>{
  for(const file of ['sprite.ASEPRITE','model.blend','scene.glb','pack.zip','loop.gif','background.svg','font.woff2']) assert.ok(isAsset(file));
  assert.ok(!isAsset('source.png.meta'));
  assert.equal(sourceLinks('abc123','a b/#sprite.png').downloadUrl,'https://raw.githubusercontent.com/cehinds/AI-Art/abc123/a%20b/%23sprite.png');
  const data=Buffer.from([0,255,13,10]);assert.equal(blobHash(data).length,40);assert.equal(hash(data).length,64);
});
test('manifest resolution retains descriptive names and statuses for pack-root files',async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'art-manifest-test-'));
  await fs.mkdir(path.join(root,'pack','collections','gear'),{recursive:true});
  await fs.writeFile(path.join(root,'pack','collections','gear','manifest.json'),JSON.stringify({assets:[{file:'components/gear-rope.png',label:'Rope coil',category:'equipment',status:'concept-component'}]}));
  const hints=await manifestHints(root,{files:[{path:'pack/collections/gear/manifest.json'},{path:'pack/components/gear-rope.png'}]});
  assert.equal(hints.get('pack/components/gear-rope.png').label,'Rope coil');
  assert.equal(classify('pack/components/gear-rope.png',hints.get('pack/components/gear-rope.png')).kind,'concept');
});
test('all imported media paths are catalogued once, duplicate bytes preserve separate identities',async()=>{
  try { await fs.access(path.join(ROOT,'Games','ff2','_source.json')); } catch { return; }
  for(const game of GAMES) {
    const manifest=await loadInventory(game);
    const paths=manifest.files.filter(x=>isAsset(x.path)).map(x=>`${game.id}/${x.path}`);
    assert.equal(new Set(paths).size,paths.length);
    for(const entry of manifest.files) assert.match(entry.sha256,/^[a-f0-9]{64}$/);
  }
});
test('generated catalog covers every imported asset path and all previews exist',async t=>{
  let catalog;
  try {catalog=JSON.parse(await fs.readFile(path.join(ROOT,'_site','catalog.json'),'utf8'));} catch(error) { if(error.code==='ENOENT') {t.skip('Run npm run build for integration coverage');return;}throw error; }
  const expected=[];
  for(const game of GAMES) {
    const manifest=await loadInventory(game);
    expected.push(...manifest.files.filter(x=>isAsset(x.path)).map(x=>`${game.id}/${x.path}`));
  }
  assert.equal(catalog.assets.length,expected.length,'Generated catalog is stale: run npm run build');
  const expectedSet=new Set(expected);
  for(const asset of catalog.assets) assert.ok(expectedSet.has(`${asset.game}/${asset.path}`),`Unexpected catalog path: ${asset.game}/${asset.path}`);
  assert.equal(new Set(catalog.assets.map(x=>x.id)).size,expected.length);
  for(const asset of catalog.assets) if(asset.preview) {
    assert.match(asset.preview,/^thumbs\/(v2-)?[a-f0-9]{64}\.webp$/);
    await fs.access(path.join(ROOT,'_site',asset.preview));
  }
});
test('previews trim only transparent margins and enlarge visible pixels while retaining opaque borders',async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'art-crop-test-'));
  const data=Buffer.alloc(100*100*4);
  for(let y=40;y<60;y++)for(let x=20;x<60;x++) {const at=(y*100+x)*4;data[at]=220;data[at+3]=255;}
  // Faint edge pixels must survive, regardless of their color.
  data[(39*100+19)*4+3]=1;
  const bytes=await sharp(data,{raw:{width:100,height:100,channels:4}}).png().toBuffer();
  const result=await makePreview(bytes,path.join(root,'trimmed.webp'));
  assert.deepEqual(result.previewCrop,{left:19,top:39,width:41,height:21});
  assert.equal(result.previewWidth,320);assert.equal(result.previewHeight,164);
  const opaque=await sharp({create:{width:100,height:80,channels:4,background:'#fff'}}).png().toBuffer();
  const whole=await makePreview(opaque,path.join(root,'opaque.webp'));
  assert.equal(whole.previewCrop,null);assert.equal(whole.previewWidth,320);assert.equal(whole.previewHeight,256);
  const transparent=await sharp({create:{width:8,height:8,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).png().toBuffer();
  assert.equal((await makePreview(transparent,path.join(root,'empty.webp'))).previewCrop,null);
});
test('build covers duplicate paths, makes local thumbnails and preserves source bytes',async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'art-build-test-'));
  const pixels=await sharp({create:{width:12,height:8,channels:4,background:{r:200,g:40,b:20,alpha:.5}}}).png().toBuffer();
  const framePixels=Buffer.alloc(12*16*4);
  for(let pixel=0;pixel<12*16;pixel++){framePixels[pixel*4+(pixel<96?0:2)]=240;framePixels[pixel*4+3]=255;}
  const animated=await sharp(framePixels,{raw:{width:12,height:16,pageHeight:8,channels:4}}).webp({loop:0,delay:[100,100]}).toBuffer();
  await fs.mkdir(path.join(root,'site'));
  await fs.writeFile(path.join(root,'site','index.html'),'__BASE__ __GAME__ __TITLE__');
  for(const game of GAMES) {
    const folder=path.join(root,'Games',game.id);await fs.mkdir(folder,{recursive:true});
    const entries=[];
    if(game.id==='ff2') for(const name of ['sword.png','sword-copy.png','source.zip','animated.webp']) {
      const bytes=name.endsWith('.png')?pixels:name.endsWith('.webp')?animated:Buffer.from('archive');
      await fs.writeFile(path.join(folder,name),bytes);
      entries.push({path:name,sha256:hash(bytes),blob:blobHash(bytes),bytes:bytes.length});
    }
    await fs.writeFile(path.join(folder,'_source.json'),JSON.stringify({repository:'cehinds/AI-Art',commit:'a'.repeat(40),files:entries}));
  }
  const out=path.join(root,'output');const {catalog}=await buildCatalog({root,out});
  assert.equal(catalog.assets.length,4);
  assert.equal(new Set(catalog.assets.map(x=>x.id)).size,4);
  const images=catalog.assets.filter(x=>x.format==='png');assert.equal(images[0].preview,images[1].preview);
  for(const asset of images) { await fs.access(path.join(out,asset.preview));assert.equal(asset.width,12);assert.equal(asset.height,8); }
  assert.equal(catalog.assets.find(x=>x.format==='zip').preview,null);
  const clip=catalog.assets.find(x=>x.format==='webp');
  assert.equal(clip.frames,2);assert.equal(clip.type,'animations');assert.equal(clip.previewKind,'first-frame');assert.equal(clip.height,8);
  const firstFrame=await sharp(await fs.readFile(path.join(out,clip.preview))).raw().toBuffer();
  assert.ok(firstFrame[0]>firstFrame[2],'Thumbnail must show the red first frame');
  assert.equal(catalog.games.find(x=>x.id==='ashenspire').assetCount,0);
  assert.equal(hash(await fs.readFile(path.join(root,'Games','ff2','sword.png'))),hash(pixels));
  assert.match(await fs.readFile(path.join(out,'games','ff2','index.html'),'utf8'),/^\.\.\/\.\.\/ ff2/);
});
test('snapshot import defeats autocrlf and refuses local edits or a changed upstream',async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'art-import-test-'));
  git(['init','--quiet'],root);
  git(['config','core.autocrlf','true'],root);
  const binary=Buffer.from([0,255,13,10,0]);
  await fs.writeFile(path.join(root,'sprite.png'),binary);
  await fs.writeFile(path.join(root,'README.md'),'source text\n');
  git(['-c','core.autocrlf=false','add','.'],root);
  git(['-c','user.name=Catalog Test','-c','user.email=catalog-test@example.invalid','commit','--quiet','-m','Fixture'],root);
  git(['update-ref','refs/remotes/origin/fixture','HEAD'],root);
  const game={id:'fixture',branch:'fixture'};
  const manifest=await importGame(game,root);
  assert.equal(manifest.files.length,2);
  assert.deepEqual(await fs.readFile(path.join(root,'Games','fixture','sprite.png')),binary);
  assert.equal(await fs.readFile(path.join(root,'Games','fixture','README.md'),'utf8'),'source text\n');
  await importGame(game,root);
  await fs.writeFile(path.join(root,'Games','fixture','sprite.png'),'local user edit');
  await assert.rejects(importGame(game,root),/Local snapshot changed/);
  assert.equal(await fs.readFile(path.join(root,'Games','fixture','sprite.png'),'utf8'),'local user edit');
  git(['-c','user.name=Catalog Test','-c','user.email=catalog-test@example.invalid','commit','--quiet','--allow-empty','-m','New upstream'],root);
  git(['update-ref','refs/remotes/origin/fixture','HEAD'],root);
  await assert.rejects(importGame(game,root),/Upstream changed/);
});
test('reviewed updates require committed exact originals and retain an explicit change inventory',async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'art-update-test-'));
  git(['init','--quiet'],root);
  git(['config','core.autocrlf','false'],root);
  const commit=message=>git(['-c','user.name=Catalog Test','-c','user.email=catalog-test@example.invalid','commit','--quiet','-m',message],root);
  await fs.writeFile(path.join(root,'sprite.png'),'first original');
  await fs.writeFile(path.join(root,'removed.png'),'removed original');
  git(['add','.'],root);commit('Initial source');
  const first=git(['rev-parse','HEAD'],root).toString().trim();
  await fs.writeFile(path.join(root,'sprite.png'),'updated original');
  await fs.writeFile(path.join(root,'new.png'),'new original');
  await fs.unlink(path.join(root,'removed.png'));
  git(['add','--all'],root);commit('Updated source');
  const second=git(['rev-parse','HEAD'],root).toString().trim();
  git(['update-ref','refs/remotes/origin/fixture',first],root);
  const game={id:'fixture',branch:'fixture'};
  await importGame(game,root);
  git(['update-ref','refs/remotes/origin/fixture',second],root);
  await assert.rejects(importGame(game,root,{update:true}),/must be committed before update/);
  git(['add','Games'],root);commit('Preserved previous snapshot');
  const preserved=git(['rev-parse','HEAD'],root).toString().trim();
  const result=await importGame(game,root,{update:true});
  assert.equal(result.commit,second);
  assert.equal(result.update.previousCatalogCommit,preserved);
  assert.deepEqual(result.update.added,['new.png']);assert.deepEqual(result.update.changed,['sprite.png']);assert.deepEqual(result.update.deleted,['removed.png']);
  assert.equal(git(['show',`${preserved}:Games/fixture/removed.png`],root).toString(),'removed original');
  assert.equal(await fs.readFile(path.join(root,'Games','fixture','sprite.png'),'utf8'),'updated original');
  await assert.rejects(fs.access(path.join(root,'Games','fixture','removed.png')));
});
test('Git-backed sparse builds and verification match filesystem output and detect missing blobs',async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'art-git-build-test-'));
  git(['init','--quiet'],root);git(['config','core.autocrlf','false'],root);
  const pixels=await sharp({create:{width:12,height:8,channels:4,background:'#f02030'}}).png().toBuffer();
  await fs.mkdir(path.join(root,'site'));
  await fs.writeFile(path.join(root,'site','index.html'),'__BASE__ __GAME__ __TITLE__');
  const originals=new Map();
  await fs.writeFile(path.join(root,'package.json'),'{}');
  await fs.writeFile(path.join(root,'package-lock.json'),'{}');
  await fs.mkdir(path.join(root,'scripts'));
  await fs.writeFile(path.join(root,'scripts','fixture.txt'),'fixture');
  for(const game of GAMES) {
    const folder=path.join(root,'Games',game.id);await fs.mkdir(folder,{recursive:true});
    const entries=[];
    if(game.id==='ff2') for(const [name,data] of [['sword.png',pixels],['manifest.json',Buffer.from(JSON.stringify({assets:[{file:'sword.png',label:'Manifest sword'}]}))]]) {
      await fs.writeFile(path.join(folder,name),data);
      originals.set(path.join(folder,name),data);
      entries.push({path:name,mode:'100644',sha256:hash(data),blob:blobHash(data),bytes:data.length});
    }
    await fs.writeFile(path.join(folder,'_source.json'),JSON.stringify({repository:'cehinds/AI-Art',commit:'a'.repeat(40),files:entries}));
  }
  git(['add','.'],root);git(['-c','user.name=Catalog Test','-c','user.email=catalog-test@example.invalid','commit','--quiet','-m','Sparse fixture'],root);
  const filesystem=await buildCatalog({root,out:path.join(root,'fs-output')});
  // Exercise the exact non-cone patterns used by CI, in this disposable repo.
  // The only original asset copies remaining are Git objects.
  execFileSync('git',['sparse-checkout','set','--no-cone','--stdin'],{cwd:root,input:'/package.json\n/package-lock.json\n/scripts/\n/site/\n/Games/*/_source.json\n'});
  for(const filename of originals.keys()) await assert.rejects(fs.access(filename));
  for(const game of GAMES) await fs.access(path.join(root,'Games',game.id,'_source.json'));
  for(const filename of ['package.json','package-lock.json','scripts/fixture.txt','site/index.html']) await fs.access(path.join(root,filename));
  const packed=await buildCatalog({root,out:path.join(root,'git-output'),gitMode:true});
  assert.deepEqual(packed.catalog,filesystem.catalog);
  assert.equal(packed.catalog.assets[0].name,'Manifest sword');
  const filename=packed.catalog.assets[0].preview;
  assert.deepEqual(await fs.readFile(path.join(root,'fs-output',filename)),await fs.readFile(path.join(root,'git-output',filename)));
  assert.deepEqual(await verifySnapshots(root,{gitMode:true}),{count:2,bytes:[...originals.values()].reduce((sum,data)=>sum+data.length,0)});
  const reader=new GitBlobReader(root);
  try {
    const requested=await Promise.all([reader.read(blobHash(pixels)),reader.read(blobHash(pixels))]);
    assert.deepEqual(requested,[pixels,pixels]);
    await assert.rejects(reader.read('0'.repeat(40)),/Missing Git blob/);
    assert.deepEqual(await reader.read(blobHash(pixels)),pixels,'Reader must remain usable after a missing object');
  } finally {await reader.close();}
  const broken=JSON.parse(await fs.readFile(path.join(root,'Games','ff2','_source.json'),'utf8'));
  broken.files.find(entry=>entry.path==='sword.png').blob='0'.repeat(40);
  await fs.writeFile(path.join(root,'Games','ff2','_source.json'),JSON.stringify(broken));
  await assert.rejects(buildCatalog({root,out:path.join(root,'broken-output'),gitMode:true}),/Missing Git blob/);
  await assert.rejects(verifySnapshots(root,{gitMode:true}),/HEAD inventory mismatch/);
});
