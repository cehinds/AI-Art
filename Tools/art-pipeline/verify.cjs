#!/usr/bin/env node
'use strict';
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
let sharp;try{sharp=require('sharp')}catch{sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')}
const root=path.resolve(__dirname,'../..');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const assert=(condition,message)=>{if(!condition)throw new Error(message)};
async function main(){
  const manifest=JSON.parse(await fs.readFile(path.join(root,'Assets/Art/Production/Batch01/manifest.json'),'utf8'));
  const ids=new Set(),files=new Set(),sources=new Map(),guids=new Set();
  let spriteCount=0,tileCount=0;
  assert(hash(await fs.readFile(path.join(root,manifest.sourceConfig)))===manifest.sourceConfigSha256,'Source config changed after export');
  for(const a of manifest.assets){
    assert(/^[a-z0-9._-]+:[a-z0-9._-]+$/.test(a.id),`Invalid Core.ContentId ${a.id}`);
    assert(!ids.has(a.id),`Duplicate ID ${a.id}`);ids.add(a.id);
    assert(!files.has(a.path),`Duplicate file ${a.path}`);files.add(a.path);
    const absolute=path.resolve(root,a.path);
    assert(absolute.startsWith(path.join(root,'Assets','Art','Production','Batch01')+path.sep),`Asset outside output ${a.path}`);
    const bytes=await fs.readFile(absolute),meta=await sharp(bytes).metadata();
    assert(hash(bytes)===a.sha256,`Output hash changed ${a.id}`);
    const metaText=await fs.readFile(absolute+'.meta','utf8'),guid=/^guid: ([0-9a-f]{32})$/m.exec(metaText)?.[1];
    assert(guid&&!guids.has(guid),`Missing or duplicate UnityGUID ${a.id}`);guids.add(guid);
    assert(meta.width===a.width&&meta.height===a.height,`Dimension mismatch ${a.id}`);
    assert(a.ppu===16&&a.filter==='point',`Import declaration mismatch ${a.id}`);
    assert(a.width===16&&a.height===(a.kind==='sprite'?24:16),`Native contract mismatch ${a.id}`);
    assert(a.pivot.x===.5&&a.pivot.y===(a.kind==='sprite'?0:.5),`Pivot mismatch ${a.id}`);
    if(!sources.has(a.source.path)){
      const source=await fs.readFile(path.join(root,a.source.path));
      sources.set(a.source.path,{hash:hash(source),meta:await sharp(source).metadata()});
    }
    const source=sources.get(a.source.path),r=a.source.rect;
    assert(source.hash===a.source.sha256,`Source hash changed ${a.source.path}`);
    assert(r.left>=0&&r.top>=0&&r.width>0&&r.height>0&&r.left+r.width<=source.meta.width&&r.top+r.height<=source.meta.height,`Crop outside source ${a.id}`);
    if(a.kind==='sprite'){
      spriteCount++;
      assert(['down','left','right','up'].includes(a.animation.direction)&&[0,1,2].includes(a.animation.frame),`Animation contract ${a.id}`);
      const raw=await sharp(bytes).ensureAlpha().raw().toBuffer();let visible=0,empty=0;
      for(let i=3;i<raw.length;i+=4){if(raw[i]===255)visible++;else if(raw[i]===0)empty++;else throw new Error(`Soft alpha ${a.id}`)}
      assert(visible>0&&empty>0&&visible===a.visiblePixels,`Alpha coverage mismatch ${a.id}`);
    }else{tileCount++;assert(a.kind==='tile',`Unknown kind ${a.kind}`)}
  }
  assert(tileCount===32,`Expected32tiles, got${tileCount}`);
  assert(spriteCount===(manifest.partial?0:12),`Expected${manifest.partial?0:12}sprites, got${spriteCount}`);
  for(const file of ['contact-sheet.png','terrain-native-atlas.png','structures-native-atlas.png','path-assembly-native.png','path-assembly.png','repeat-materials.png','animation.html','validation.json'])await fs.access(path.join(root,'Review/production',file));
  if(!manifest.partial)for(const file of ['firion-native-atlas.png','firion-detail.png','firion-detail-native-atlas.png','hut-assembly.png','town-dungeon-sample.png'])await fs.access(path.join(root,'Review/production',file));
  const report=JSON.parse(await fs.readFile(path.join(root,'Review/production/validation.json'),'utf8'));
  assert(report.assets===manifest.assets.length,'Evidence count differs');
  assert(report.requiredEdges.length===12,'Expected12path-edge diagnostics');
  console.log(`PASS: ${manifest.assets.length} native assets (${tileCount} tiles, ${spriteCount} frames); IDs, paths, source/output/config hashes, crop bounds, dimensions, pivot declarations, binary sprite alpha and review outputs verified.`);
  console.log(`Exact-edge diagnostic: ${report.requiredEdges.filter(e=>e.exact).length}/${report.requiredEdges.length} identical adjacent pairs. Visual seam review remains separate.`);
}
main().catch(e=>{console.error(e.stack);process.exitCode=1});
