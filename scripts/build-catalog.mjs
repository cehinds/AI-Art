import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';
import { ROOT,GAMES,TYPES,KINDS,hash,isAsset,classify,loadInventory,sourceLinks } from './lib.mjs';
import { GitBlobReader } from './git-blobs.mjs';

export async function manifestHints(folder, inventory,reader=null) {
  const paths=new Set(inventory.files.map(x=>x.path));
  const hints=new Map();
  for(const item of inventory.files.filter(x=>x.path.endsWith('.json'))) {
    let json;
    try { json=JSON.parse((reader?await reader.read(item.blob):await fs.readFile(path.join(folder,item.path))).toString('utf8')); } catch(error) {if(reader && !(error instanceof SyntaxError)) throw error;continue;}
    const base=path.posix.dirname(item.path);
    const resolve=relative=>{
      if(typeof relative!=='string' || !isAsset(relative)) return null;
      const value=relative.replaceAll('\\','/');
      if(paths.has(value)) return value;
      if(paths.has(`hd/${value}`)) return `hd/${value}`;
      const light=value.replace(/^assets-mobile\//,'light/assets/');
      if(paths.has(light)) return light;
      let parent=base;
      while(true) {
        const candidate=path.posix.normalize(path.posix.join(parent,value));
        if(paths.has(candidate)) return candidate;
        if(parent==='.') break;
        parent=path.posix.dirname(parent);
      }
      return null;
    };
    function walk(node, context='') {
      if(Array.isArray(node)) { node.forEach(value=>walk(value,context)); return; }
      if(!node || typeof node!=='object') return;
      for(const key of ['path','file','filename']) {
        const target=resolve(node[key]);
        if(target) {
          const previous=hints.get(target)||{};
          // Manifests enrich names/categories; provenance remains determined by
          // source folders unless a dedicated catalog override is supplied.
          const metadata={...previous};
          for(const field of ['label','name','category','group','owner','status','catalogKind','catalogType']) if(typeof node[field]==='string') metadata[field]=node[field];
          if(context==='sources' || context==='source') metadata.sourceManifest=true;
          hints.set(target,metadata);
        }
      }
      for(const [key,value] of Object.entries(node)) if(value && typeof value==='object') walk(value,key);
    }
    walk(json);
  }
  return hints;
}

function mediaType(format) {
  if(/^(png|jpe?g|gif|webp|avif|svg|bmp|tiff?|ico|apng|heic)$/.test(format)) return 'image';
  if(/^(mp4|webm|mov|m4v)$/.test(format)) return 'video';
  if(/^(wav|mp3|ogg|flac|aac)$/.test(format)) return 'audio';
  if(/^(glb|gltf|obj|fbx|blend|stl|dae)$/.test(format)) return 'model';
  if(/^(zip|7z|rar|tar|gz)$/.test(format)) return 'archive';
  if(/^(ttf|otf|woff|woff2)$/.test(format)) return 'font';
  return 'source';
}
export function assetName(assetPath,hint={}) {
  const original=hint.label||hint.name||path.posix.basename(assetPath,path.posix.extname(assetPath));
  const clean=original.replaceAll(/[-_]/g,' ');
  const generic=/^(\d+[ -])?(center|down|up|left|right|idle|attack|cast|frame|sheet|preview|contact|master|angled|drawn|forward|guard|guarded|lowered|neutral|raised|resting|thrust|anticipation|recovery|conversation|defend|hurt|buff)(\b|[-_ ])/i.test(original) || /^[a-z]{1,6}[-_]?\d+$/i.test(original);
  const parent=hint.owner||path.posix.basename(path.posix.dirname(assetPath));
  const initialUpper=value=>value.charAt(0).toUpperCase()+value.slice(1);
  return generic && parent!=='.' ? `${initialUpper(parent.replaceAll(/[-_]/g,' '))} · ${initialUpper(clean)}` : clean;
}
export function assetVariant(assetPath) {
  const themes={'dungeon-after-dark':'Dungeon After Dark','ink-and-lanterns':'Ink & Lanterns','pocket-dungeon':'Pocket Dungeon'};
  return assetPath.split('/').map(part=>themes[part]).find(Boolean)||(/^hd\//.test(assetPath)?'HD':/^light\//.test(assetPath)?'Light':/^common\//.test(assetPath)?'Shared':'');
}
export async function makePreview(bytes,destination) {
  const options={limitInputPixels:268402689,page:0,pages:1};
  const image=sharp(bytes,options);
  const metadata=await image.metadata();
  let crop=null;
  if(metadata.hasAlpha) {
    // Check only alpha: opaque colored borders are artwork, never background.
    // Preserve every nonzero alpha pixel, including antialiased edge pixels.
    const {data,info}=await image.clone().ensureAlpha().raw().toBuffer({resolveWithObject:true});
    let left=info.width,top=info.height,right=-1,bottom=-1;
    for(let y=0;y<info.height;y++) for(let x=0;x<info.width;x++) if(data[(y*info.width+x)*info.channels+info.channels-1]>0) {
      left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);
    }
    if(right>=left && bottom>=top && (left>0||top>0||right<info.width-1||bottom<info.height-1)) crop={left,top,width:right-left+1,height:bottom-top+1};
  }
  const pipeline=crop?image.extract(crop):image;
  const result=await pipeline.resize({width:320,height:320,fit:'inside',kernel:'nearest'}).webp({quality:82,effort:2}).toFile(destination);
  return {previewWidth:result.width,previewHeight:result.height,previewCrop:crop};
}
export async function buildCatalog({root=ROOT,out=path.join(ROOT,'_site'),gitMode=false}={}) {
  const reader=gitMode?new GitBlobReader(root):null;
  try {
  await fs.mkdir(path.join(out,'thumbs'),{recursive:true});
  const assets=[],games=[],warnings=[],thumbnailTasks=new Map();
  let previewMetadata={};
  try {previewMetadata=JSON.parse(await fs.readFile(path.join(out,'thumb-meta-v2.json'),'utf8'));} catch(error) {if(error.code!=='ENOENT')throw error;}
  sharp.cache({memory:64,files:20,items:100});
  sharp.concurrency(1);
  for(const game of GAMES) {
    const manifest=await loadInventory(game,root);
    const folder=path.join(root,'Games',game.id);
    const hints=await manifestHints(folder,manifest,reader);
    let assetCount=0;
    for(const entry of manifest.files.filter(x=>isAsset(x.path))) {
      const hint=hints.get(entry.path)||{};
      const format=path.posix.extname(entry.path).slice(1).toLowerCase();
      const classification=classify(entry.path,hint);
      const asset={id:hash(`${game.id}/${entry.path}`).slice(0,24),name:assetName(entry.path,hint),variant:assetVariant(entry.path),game:game.id,...classification,path:entry.path,localPath:`Games/${game.id}/${entry.path}`,preview:null,...sourceLinks(manifest.commit,entry.path),sourceCommit:manifest.commit,width:null,height:null,bytes:entry.bytes,sha256:entry.sha256,gitBlob:entry.blob,format,mediaType:mediaType(format)};
      if(asset.mediaType==='image') {
        if(!thumbnailTasks.has(entry.sha256)) thumbnailTasks.set(entry.sha256,{file:path.join(folder,entry.path),entry,assets:[]});
        thumbnailTasks.get(entry.sha256).assets.push(asset);
      }
      assets.push(asset);assetCount++;
    }
    games.push({...game,commit:manifest.commit,assetCount,sourceFileCount:manifest.files.length,sourceUrl:`https://github.com/${manifest.repository}/tree/${manifest.commit}`,empty:assetCount===0});
  }
  const tasks=[...thumbnailTasks.values()];let next=0,completed=0;
  async function worker() {
    while(next<tasks.length) {
      const task=tasks[next++];
      // Missing/corrupt packed objects must fail the build, never silently
      // downgrade an original to a download-only item.
      const packedBytes=reader?await reader.read(task.entry.blob):null;
      if(packedBytes && hash(packedBytes)!==task.entry.sha256) throw new Error(`Git blob SHA256 mismatch: ${task.entry.path}`);
      try {
        const bytes=packedBytes||await fs.readFile(task.file);
        if(hash(bytes)!==task.entry.sha256) throw new Error('Local original differs from pinned source inventory');
        const metadata=await sharp(bytes,{limitInputPixels:268402689}).metadata();
        const relative=`thumbs/v2-${task.entry.sha256}.webp`;
        const destination=path.join(out,relative);
        let cached=previewMetadata[task.entry.sha256];
        try { await fs.access(destination); } catch {cached=null;}
        if(!cached) cached=previewMetadata[task.entry.sha256]=await makePreview(bytes,destination);
        for(const asset of task.assets) {
          Object.assign(asset,{preview:relative,...cached,width:metadata.width||null,height:metadata.pageHeight||metadata.height||null,frames:metadata.pages||1,previewKind:metadata.pages>1?'first-frame':'thumbnail'});
          if(metadata.pages>1 && asset.kind!=='reference') asset.type='animations';
        }
      } catch(error) {
        // Preserve unsupported/corrupt originals as discoverable download entries.
        for(const asset of task.assets) asset.previewError=String(error.message);
        warnings.push({path:task.file.replace(root,''),message:error.message});
      }
      completed++;
      if(completed%500===0) console.log(`Thumbnails: ${completed}/${tasks.length}`);
    }
  }
  await Promise.all(Array.from({length:6},()=>worker()));
  await fs.writeFile(path.join(out,'thumb-meta-v2.json'),JSON.stringify(previewMetadata));
  const catalog={schemaVersion:1,games,types:TYPES,kinds:KINDS,assets};
  await fs.writeFile(path.join(out,'catalog.json'),JSON.stringify(catalog));
  const template=await fs.readFile(path.join(root,'site','index.html'),'utf8');
  for(const entry of await fs.readdir(path.join(root,'site'),{withFileTypes:true})) if(entry.name!=='index.html') await fs.cp(path.join(root,'site',entry.name),path.join(out,entry.name),{recursive:true});
  function page(base,game,title) { return template.replaceAll('__BASE__',base).replaceAll('__GAME__',game).replaceAll('__TITLE__',title); }
  await fs.writeFile(path.join(out,'index.html'),page('./','','AI Art Catalog'));
  for(const game of games) {
    const folder=path.join(out,'games',game.id);await fs.mkdir(folder,{recursive:true});
    await fs.writeFile(path.join(folder,'index.html'),page('../../',game.id,`${game.name} · AI Art Catalog`));
  }
  await fs.writeFile(path.join(out,'.nojekyll'),'');
  const report={assetCount:assets.length,uniqueImageCount:tasks.length,previewCount:assets.filter(x=>x.preview).length,downloadOnlyCount:assets.filter(x=>!x.preview).length,games,warnings};
  await fs.writeFile(path.join(out,'build-report.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({assets:assets.length,uniqueImages:tasks.length,previewWarnings:warnings.length,games:games.map(x=>({game:x.id,assets:x.assetCount}))},null,2));
  return {catalog,report};
  } finally {await reader?.close();}
}
if(process.argv[1]?.endsWith('build-catalog.mjs')) await buildCatalog({gitMode:process.argv.includes('--git')});
