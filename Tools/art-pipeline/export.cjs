#!/usr/bin/env node
'use strict';
// Mechanical slicing only: every visible asset pixel originates in an ImageGen source.
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
let sharp;
try { sharp = require('sharp'); }
catch { sharp = require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const root = path.resolve(__dirname, '../..');
const configPath = path.resolve(root, process.argv[2] || 'Tools/art-pipeline/batch01.json');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const rel = p => path.relative(root, p).split(path.sep).join('/');
const json = obj => JSON.stringify(obj, null, 2) + '\n';
const escape = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
function inside(base, candidate) {
  const relative = path.relative(base, candidate);
  if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error(`Path escapes allowed directory: ${candidate}`);
  return candidate;
}
function bounds(data, width, height, threshold) {
  let left = width, top = height, right = -1, bottom = -1;
  for (let y=0; y<height; y++) for (let x=0; x<width; x++) {
    if (data[(y*width+x)*4+3] < threshold) continue;
    left=Math.min(left,x); top=Math.min(top,y); right=Math.max(right,x); bottom=Math.max(bottom,y);
  }
  if (right<0) throw new Error('Empty sprite cell after alpha threshold');
  return {left,top,width:right-left+1,height:bottom-top+1};
}
function edge(data,width,height,side) {
  const result=[];
  const count=side==='left'||side==='right'?height:width;
  for(let i=0;i<count;i++) {
    const x=side==='left'?0:side==='right'?width-1:i;
    const y=side==='top'?0:side==='bottom'?height-1:i;
    result.push(...data.subarray((y*width+x)*4,(y*width+x)*4+4));
  }
  return result;
}
function compare(a,b) {
  if(a.length!==b.length) throw new Error('Edge lengths differ');
  let mismatch=0, delta=0, max=0;
  for(let i=0;i<a.length;i+=4) {
    let different=false;
    for(let c=0;c<4;c++) {const d=Math.abs(a[i+c]-b[i+c]);delta+=d;max=Math.max(max,d);different ||= d!==0;}
    if(different)mismatch++;
  }
  return {exact:mismatch===0,mismatchedPixels:mismatch,pixels:a.length/4,meanChannelDifference:Number((delta/a.length).toFixed(3)),maxChannelDifference:max};
}
async function ensureMeta(file,{folder=false,sprite=false}={}) {
  const guid=sha(Buffer.from(`ff2-native-art:${rel(file)}`)).slice(0,32);
  const importer=sprite?'TextureImporter':path.extname(file)==='.json'?'TextScriptImporter':'DefaultImporter';
  const body=`fileFormatVersion: 2\nguid: ${guid}\n${folder?'folderAsset: yes\n':''}${importer}:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n`;
  try{await fs.writeFile(`${file}.meta`,body,{flag:'wx'})}catch(e){if(e.code!=='EEXIST')throw e}
}
async function main() {
  const cfg=JSON.parse(await fs.readFile(configPath,'utf8'));
  if(process.argv.includes('--tiles'))cfg.sheets=cfg.sheets.filter(s=>s.kind==='tile');
  const out=inside(root,path.resolve(root,cfg.output));
  const review=inside(root,path.resolve(root,cfg.review));
  // Read every source before producing any deliverable; missing generation is a hard stop.
  const sources=await Promise.all(cfg.sheets.map(async sheet=>{
    const file=inside(root,path.resolve(root,sheet.source));
    const bytes=await fs.readFile(file);
    const meta=await sharp(bytes).metadata();
    if(!meta.width||!meta.height)throw new Error(`Unreadable source ${sheet.source}`);
    const region=sheet.region||{left:0,top:0,width:meta.width,height:meta.height};
    if(region.left<0||region.top<0||region.width<1||region.height<1||region.left+region.width>meta.width||region.top+region.height>meta.height)throw new Error(`Invalid grid region: ${sheet.source}`);
    if(sheet.names.length!==sheet.columns*sheet.rows)throw new Error(`Name count differs from grid: ${sheet.source}`);
    return {sheet,file,bytes,meta,region,hash:sha(bytes)};
  }));
  let previous;
  try {previous=JSON.parse(await fs.readFile(path.join(out,'manifest.json'),'utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
  const oldAssets=new Map((previous?.assets||[]).map(a=>[a.path,a.sha256]));
  const planned=[];
  const ids=new Set();
  for(const src of sources) {
    const {sheet,region}=src;
    const cells=[];
    for(let i=0;i<sheet.names.length;i++) {
      const name=sheet.names[i];
      if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name))throw new Error(`Unsafe asset name ${name}`);
      const col=i%sheet.columns,row=Math.floor(i/sheet.columns);
      const left=region.left+Math.floor(col*region.width/sheet.columns);
      const top=region.top+Math.floor(row*region.height/sheet.rows);
      const rect=sheet.cellRects?.[i]||{left,top,width:Math.floor((col+1)*region.width/sheet.columns)+region.left-left,height:Math.floor((row+1)*region.height/sheet.rows)+region.top-top};
      const cell=await sharp(src.bytes).extract(rect).ensureAlpha().raw().toBuffer({resolveWithObject:true});
      if(sheet.kind==='sprite') {
        const t=sheet.alphaThreshold??128;
        for(let p=0;p<cell.data.length;p+=4) {
          if(cell.data[p+3]<t)cell.data.fill(0,p,p+4);else cell.data[p+3]=255;
        }
      }
      cells.push({name,rect,...cell,bounds:sheet.kind==='sprite'?bounds(cell.data,cell.info.width,cell.info.height,128):null});
    }
    const w=sheet.target[0],h=sheet.target[1],padding=sheet.padding??0;
    const sharedScale=sheet.kind==='sprite'?Math.min((w-padding*2)/Math.max(...cells.map(c=>c.bounds.width)),(h-padding)/Math.max(...cells.map(c=>c.bounds.height))):null;
    for(let i=0;i<cells.length;i++) {
      const cell=cells[i];
      let native,detail;
      if(sheet.kind==='sprite') {
        const b=cell.bounds;
        const bw=Math.max(1,Math.round(b.width*sharedScale)),bh=Math.max(1,Math.round(b.height*sharedScale));
        const foreground=await sharp(cell.data,{raw:cell.info}).extract(b).resize(bw,bh,{kernel:'nearest',fit:'fill'}).png().toBuffer();
        native=await sharp({create:{width:w,height:h,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite([{input:foreground,left:Math.floor((w-bw)/2),top:h-bh}]).png().toBuffer();
        const dw=Math.max(1,Math.round(b.width*sharedScale*2)),dh=Math.max(1,Math.round(b.height*sharedScale*2));
        const detailForeground=await sharp(cell.data,{raw:cell.info}).extract(b).resize(dw,dh,{kernel:'nearest',fit:'fill'}).png().toBuffer();
        detail=await sharp({create:{width:w*2,height:h*2,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite([{input:detailForeground,left:Math.floor((w*2-dw)/2),top:h*2-dh}]).png().toBuffer();
      } else native=await sharp(cell.data,{raw:cell.info}).resize(w,h,{kernel:'nearest',fit:'fill'}).png().toBuffer();
      const id=`${cfg.id}:${sheet.group}.${cell.name}`;
      if(ids.has(id))throw new Error(`Duplicate ID ${id}`);ids.add(id);
      const file=inside(out,path.join(out,sheet.group,`${String(i+1).padStart(2,'0')}-${cell.name}.png`));
      const fileRel=rel(file);
      const asset={id,name:cell.name,path:fileRel,kind:sheet.kind,group:sheet.group,width:w,height:h,ppu:16,pivot:sheet.kind==='sprite'?{x:0.5,y:0}:{x:0.5,y:0.5},filter:'point',alphaThreshold:sheet.kind==='sprite'?(sheet.alphaThreshold??128):null,sha256:sha(native),source:{path:rel(src.file),sha256:src.hash,width:src.meta.width,height:src.meta.height,rect:cell.rect,slot:i,column:i%sheet.columns,row:Math.floor(i/sheet.columns),alphaBounds:cell.bounds,sharedScale},animation:sheet.kind==='sprite'?{direction:sheet.directions[Math.floor(i/sheet.columns)],frame:i%sheet.columns}:null};
      planned.push({asset,file,native,detail,raw:(await sharp(native).ensureAlpha().raw().toBuffer())});
      try {
        const current=sha(await fs.readFile(file));
        if(current!==asset.sha256&&current!==oldAssets.get(fileRel))throw new Error(`Preserved edited/unmanaged output: ${fileRel}`);
      }catch(e){if(e.code!=='ENOENT')throw e;}
    }
  }
  const byName=new Map(planned.map(p=>[`${p.asset.group}/${p.asset.name}`,p]));
  const selfEdges=planned.filter(p=>p.asset.kind==='tile').map(p=>({id:p.asset.id,horizontal:compare(edge(p.raw,p.asset.width,p.asset.height,'right'),edge(p.raw,p.asset.width,p.asset.height,'left')),vertical:compare(edge(p.raw,p.asset.width,p.asset.height,'bottom'),edge(p.raw,p.asset.width,p.asset.height,'top'))}));
  const requiredEdges=(cfg.requiredEdges||[]).map(pair=>{
    const a=byName.get(pair.a),b=byName.get(pair.b);
    if(!a||!b)throw new Error(`Unknown required edge ${pair.a}, ${pair.b}`);
    return {...pair,...compare(edge(a.raw,a.asset.width,a.asset.height,pair.aSide),edge(b.raw,b.asset.width,b.asset.height,pair.bSide))};
  });
  const report={schema:1,batch:cfg.id,assets:planned.length,sourceCount:sources.length,dimensions:'PASS',uniqueIds:'PASS',hashes:'PASS',spriteAlpha:'PASS',edgeDiagnostic:requiredEdges.length?(requiredEdges.every(e=>e.exact)?'ALL_EXACT':'MISMATCHES'):'NOT_CONFIGURED',edgeCaution:'Exact edge equality is a conservative diagnostic, not a production quality gate or proof of visual continuity. Naturally textured neighboring pixels need not be identical. Inspect assembled tiles visually; seamlessness is not claimed.',requiredEdges,selfEdges};
  for(const p of planned) {
    const m=await sharp(p.native).metadata();
    if(m.width!==p.asset.width||m.height!==p.asset.height)throw new Error(`Wrong dimensions ${p.asset.id}`);
    if(p.asset.kind==='sprite') {
      let opaque=0,transparent=0;
      for(let i=3;i<p.raw.length;i+=4){if(p.raw[i]===255)opaque++;else if(p.raw[i]===0)transparent++;else throw new Error(`Nonbinary alpha ${p.asset.id}`);}
      if(!opaque||!transparent)throw new Error(`Sprite needs visible pixels and transparency: ${p.asset.id}`);
      p.asset.visiblePixels=opaque;
    }
  }
  await fs.mkdir(out,{recursive:true});await fs.mkdir(review,{recursive:true});
  for(const folder of [path.join(root,'Assets/Art'),path.join(root,'Assets/Art/Production'),out,...new Set(planned.map(p=>path.dirname(p.file)))]){await fs.mkdir(folder,{recursive:true});await ensureMeta(folder,{folder:true});}
  for(const p of planned){await fs.mkdir(path.dirname(p.file),{recursive:true});await fs.writeFile(p.file,p.native);}
  for(const p of planned)await ensureMeta(p.file,{sprite:true});
  const manifest={schema:1,id:cfg.id,partial:process.argv.includes('--tiles'),creativeOrigin:'ImageGen source sheets; crop, nearest-neighbor normalization and sprite alpha threshold only. No programmatic asset painting, palette replacement or edge repaint.',sourceConfig:rel(configPath),sourceConfigSha256:sha(await fs.readFile(configPath)),assets:planned.map(p=>p.asset),verification:rel(path.join(review,'validation.json')),edgeDiagnostic:report.edgeDiagnostic};
  await fs.writeFile(path.join(out,'manifest.json'),json(manifest));
  await ensureMeta(path.join(out,'manifest.json'));
  await fs.writeFile(path.join(review,'validation.json'),json(report));
  // Contact sheets and native atlases stay outside Unity's production import directory.
  const cols=8,cellW=144,cellH=152,labelH=36,rows=Math.ceil(planned.length/cols),composites=[];
  const labels=[];
  for(let i=0;i<planned.length;i++) {
    const p=planned[i],x=(i%cols)*cellW,y=Math.floor(i/cols)*cellH;
    const factor=Math.min(5,Math.floor((cellW-16)/p.asset.width),Math.floor((cellH-labelH-8)/p.asset.height));
    const width=p.asset.width*factor,height=p.asset.height*factor;
    composites.push({input:await sharp(p.native).resize(width,height,{kernel:'nearest'}).png().toBuffer(),left:x+Math.floor((cellW-width)/2),top:y+8+Math.floor((cellH-labelH-height-8)/2)});
    labels.push(`<text x="${x+8}" y="${y+cellH-23}" font-size="11">${escape(p.asset.group)} / ${escape(path.basename(p.file).slice(0,2))}</text><text x="${x+8}" y="${y+cellH-8}" font-size="10">${escape(p.asset.name)}</text>`);
  }
  composites.push({input:Buffer.from(`<svg width="${cols*cellW}" height="${rows*cellH}"><g font-family="sans-serif" fill="#f1dfbd">${labels.join('')}</g></svg>`),left:0,top:0});
  await sharp({create:{width:cols*cellW,height:rows*cellH,channels:4,background:'#283332'}}).composite(composites).png().toFile(path.join(review,'contact-sheet.png'));
  for(const src of sources) {
    const items=planned.filter(p=>p.asset.group===src.sheet.group),[w,h]=src.sheet.target;
    const atlas=await sharp({create:{width:w*src.sheet.columns,height:h*src.sheet.rows,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite(items.map((p,i)=>({input:p.native,left:(i%src.sheet.columns)*w,top:Math.floor(i/src.sheet.columns)*h}))).png().toBuffer();
    await fs.writeFile(path.join(review,`${src.sheet.group}-native-atlas.png`),atlas);
    await sharp(atlas).resize(w*src.sheet.columns*8,h*src.sheet.rows*8,{kernel:'nearest'}).png().toFile(path.join(review,`${src.sheet.group}-contact.png`));
    if(src.sheet.kind==='sprite') {
      const detailAtlas=await sharp({create:{width:w*2*src.sheet.columns,height:h*2*src.sheet.rows,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite(items.map((p,i)=>({input:p.detail,left:(i%src.sheet.columns)*w*2,top:Math.floor(i/src.sheet.columns)*h*2}))).png().toBuffer();
      await fs.writeFile(path.join(review,`${src.sheet.group}-detail-native-atlas.png`),detailAtlas);
      await sharp(detailAtlas).resize(w*src.sheet.columns*8,h*src.sheet.rows*8,{kernel:'nearest'}).png().toFile(path.join(review,`${src.sheet.group}-detail.png`));
    }
  }
  for(const sample of cfg.samples||[]) {
    const rows=sample.rows||sample.pattern.map(row=>[...row].map(key=>sample.legend[key]));
    const width=rows[0].length,height=rows.length,layer=[];
    for(let y=0;y<height;y++) {
      if(rows[y].length!==width)throw new Error('Sample rows must be rectangular');
      for(let x=0;x<width;x++){const item=byName.get(rows[y][x]);if(!item)throw new Error(`Unknown sample asset ${rows[y][x]}`);if(item.asset.width!==16||item.asset.height!==16)throw new Error('Sample expects 16x16 tiles');layer.push({input:item.native,left:x*16,top:y*16});}
    }
    const native=await sharp({create:{width:width*16,height:height*16,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite(layer).png().toBuffer();
    await fs.writeFile(path.join(review,`${sample.name}-native.png`),native);
    await sharp(native).resize(width*16*6,height*16*6,{kernel:'nearest'}).png().toFile(path.join(review,`${sample.name}.png`));
  }
  await fs.writeFile(path.join(review,'animation.html'),animationHtml(manifest));
  console.log(`${cfg.id}: ${planned.length} assets exported; dimensions, IDs, hashes and sprite alpha PASS; exact edge diagnostic ${report.edgeDiagnostic}.`);
  if(report.edgeDiagnostic==='MISMATCHES')console.log(`DIAGNOSTIC: ${requiredEdges.filter(e=>!e.exact).length}/${requiredEdges.length} neighboring edge pairs differ. Inspect ${rel(path.join(review,'path-assembly.png'))} and validation.json.`);
}
function animationHtml(manifest) {
  const frames=manifest.assets.filter(a=>a.kind==='sprite').map(a=>({...a,url:path.relative(path.join(root,'Review/production'),path.join(root,a.path)).split(path.sep).join('/')}));
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Firion native animation review</title><style>body{margin:2rem;background:#172425;color:#f1dfbd;font:16px system-ui}main{display:flex;gap:2rem;flex-wrap:wrap}figure{margin:0}img{display:block;image-rendering:pixelated;background:repeating-conic-gradient(#253332 0% 25%,#334341 0% 50%) 0/16px 16px;width:128px;height:192px;margin-bottom:1rem}button{font:inherit;padding:.5rem 1rem}small{display:block;margin:1rem 0}</style><h1>Firion walk-cycle review</h1><p>Native 16 × 24 pixels, integer enlargement. Inspect silhouette, direction, feet and costume consistency. This preview is not Unity runtime evidence.</p><button id="pause">Pause</button><small id="state"></small><main id="directions"></main><script>const frames=${JSON.stringify(frames)};const dirs=[...new Set(frames.map(f=>f.animation.direction))];const root=document.querySelector('#directions');for(const d of dirs){const fig=document.createElement('figure'),img=document.createElement('img'),cap=document.createElement('figcaption');img.alt=d+' walk';cap.textContent=d;fig.append(img,cap);root.append(fig)}let tick=0,paused=false;const cycle=[0,1,2,1];function show(){dirs.forEach((d,i)=>{const f=frames.find(f=>f.animation.direction===d&&f.animation.frame===cycle[tick%4]);root.children[i].firstChild.src=f.url});document.querySelector('#state').textContent='Step '+(tick%4+1)+' / 4 · 160 ms · left step, idle, right step, idle'}document.querySelector('#pause').onclick=()=>{paused=!paused;document.querySelector('#pause').textContent=paused?'Play':'Pause'};show();setInterval(()=>{if(!paused){tick++;show()}},160);</script></html>`;
}
main().catch(error=>{console.error(error.stack);process.exitCode=1;});
