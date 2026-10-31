'use strict';
const fs=require('node:fs/promises'),path=require('node:path');
const {sharp,hash,json,assert,inside}=require('../remaster-expansion/common.cjs');
const root=path.resolve(__dirname,'../..');
const sourceRoot=path.join(root,'ArtSource/WorldComponentsV1');
const outputRoot=path.join(root,'Assets/Art/Production/WorldComponentsV1');
const reviewRoot=path.join(root,'Review/world-components-v1');
const rel=file=>path.relative(root,file).split(path.sep).join('/');
const absolute=file=>path.resolve(root,file);
const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
async function exists(file){try{await fs.access(file);return true}catch(e){if(e.code==='ENOENT')return false;throw e}}
async function preserve(file,bytes){
 bytes=Buffer.isBuffer(bytes)?bytes:Buffer.from(bytes);await fs.mkdir(path.dirname(file),{recursive:true});
 if(await exists(file)){assert(hash(await fs.readFile(file))===hash(bytes),'Refusing to overwrite differing existing asset: '+rel(file));return;}
 await fs.writeFile(file,bytes,{flag:'wx'});
}
async function metadata(file){
 const dest=file+'.meta';if(await exists(dest))return;
 await preserve(dest,`fileFormatVersion: 2\nguid: ${hash(Buffer.from('ff2-world-components-v1:'+rel(file))).slice(0,32)}\n`);
}
function validateSheet(sheet){
 assert(/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(sheet.id),'Invalid sheet ID');
 assert(Number.isInteger(sheet.columns)&&sheet.columns>0&&sheet.columns<=16,'Invalid columns: '+sheet.id);
 assert(Number.isInteger(sheet.rows)&&sheet.rows>0&&sheet.rows<=16,'Invalid rows: '+sheet.id);
 assert(sheet.tileSize===32||sheet.tileSize===64,'Native tile size must be 32 or 64: '+sheet.id);
 assert(sheet.tiles?.length===sheet.columns*sheet.rows,'Every atlas cell needs a declaration: '+sheet.id);
 const ids=new Set();for(const tile of sheet.tiles){
  assert(/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(tile.id)&&!ids.has(tile.id),'Invalid/duplicate tile: '+tile.id);ids.add(tile.id);
  assert(tile.layer&&tile.terrain&&tile.cornerRole&&tile.anchor,'Missing tile semantics: '+tile.id);
  for(const side of ['north','east','south','west'])assert(typeof tile.ports?.[side]==='string','Missing side port '+side+': '+tile.id);
 }
}
async function normalize(sheet){
 validateSheet(sheet);
 const source=inside(sourceRoot,absolute(sheet.source)),bytes=await fs.readFile(source);
 const {data,info}=await sharp(bytes).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 let crop=sheet.sourceCrop;
 // Isolated objects retain the original regular source slots before each
 // silhouette is fitted; gutter width must not change the slot boundaries.
 if(!crop && sheet.kind==='cutout-atlas')crop={left:0,top:0,width:info.width,height:info.height};
 if(!crop){
  let left=info.width,top=info.height,right=-1,bottom=-1;
  for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++)if(data[(y*info.width+x)*4+3]>=(sheet.alphaThreshold??128))
  {left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);}
  assert(right>=left&&bottom>=top,'Empty generated master: '+sheet.id);
  crop={left,top,width:right-left+1,height:bottom-top+1};
 }
 assert(['left','top','width','height'].every(k=>Number.isInteger(crop[k]))&&crop.left>=0&&crop.top>=0&&crop.width>0&&crop.height>0&&crop.left+crop.width<=info.width&&crop.top+crop.height<=info.height,'Invalid group crop: '+sheet.id);
 if(sheet.kind==='cutout-atlas'){
  const size=sheet.tileSize,padding=sheet.padding??0,records=[],composites=[];
  assert(Number.isInteger(padding)&&padding>=0&&padding<size/4,'Invalid cutout padding');
  for(let index=0;index<sheet.tiles.length;index++){
   const x=index%sheet.columns,y=Math.floor(index/sheet.columns);
   const left=crop.left+Math.floor(x*crop.width/sheet.columns),top=crop.top+Math.floor(y*crop.height/sheet.rows);
   const right=crop.left+Math.floor((x+1)*crop.width/sheet.columns),bottom=crop.top+Math.floor((y+1)*crop.height/sheet.rows);
   let l=right,t=bottom,r=-1,b=-1;
   for(let yy=top;yy<bottom;yy++)for(let xx=left;xx<right;xx++)if(data[(yy*info.width+xx)*4+3]>=(sheet.alphaThreshold??128))
   {l=Math.min(l,xx);t=Math.min(t,yy);r=Math.max(r,xx);b=Math.max(b,yy);}
   assert(r>=l&&b>=t,'Empty cutout cell: '+sheet.id+'/'+index);
   const sourceCellRect={left,top,width:right-left,height:bottom-top},sourceCutout={left:l,top:t,width:r-l+1,height:b-t+1};
   const fitted=await sharp(bytes).extract(sourceCutout).resize(size-padding*2,size-padding*2,{fit:'inside',kernel:'nearest'}).ensureAlpha().png().toBuffer();
   const m=await sharp(fitted).metadata(),placement={left:Math.floor((size-m.width)/2),top:size-m.height,width:m.width,height:m.height};
   const native=await sharp({create:{width:size,height:size,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite([{input:fitted,left:placement.left,top:placement.top}]).png().toBuffer();
   records.push({definition:sheet.tiles[index],index,x,y,bytes:native,sourceCellRect,sourceCutout,placement});composites.push({input:native,left:x*size,top:y*size});
  }
  const width=sheet.columns*size,height=sheet.rows*size;
  const normalized=await sharp({create:{width,height,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite(composites).png().toBuffer();
  return {mode:'per-cell-alpha-cutout-fit',source:rel(source),sourceSha256:hash(bytes),sourceSize:{width:info.width,height:info.height},crop,width,height,normalized,records};
 }
 const ratio=(crop.width/sheet.columns)/(crop.height/sheet.rows);
 assert(Math.abs(ratio-1)<=.06||sheet.allowNonSquareSourceCells===true,'Non-square source cells require inspected crop/explicit declaration: '+sheet.id+' ratio='+ratio.toFixed(4));
 const width=sheet.columns*sheet.tileSize,height=sheet.rows*sheet.tileSize;
 // One crop and one nearest-neighbor transform for the ENTIRE atlas. Do not
 // independently trim/recenter cells: their shared edge registration matters.
 const normalized=await sharp(bytes).extract(crop).resize(width,height,{fit:'fill',kernel:'nearest'}).ensureAlpha().png().toBuffer();
 const records=[];
 for(let index=0;index<sheet.tiles.length;index++){
  const x=index%sheet.columns,y=Math.floor(index/sheet.columns);
  const tile=await sharp(normalized).extract({left:x*sheet.tileSize,top:y*sheet.tileSize,width:sheet.tileSize,height:sheet.tileSize}).png().toBuffer();
  records.push({definition:sheet.tiles[index],index,x,y,bytes:tile});
 }
 return {mode:'whole-atlas-resize-before-slice',source:rel(source),sourceSha256:hash(bytes),sourceSize:{width:info.width,height:info.height},crop,width,height,normalized,records};
}
async function edgeAudit(a,b,direction){
 const aa=await sharp(a).ensureAlpha().raw().toBuffer({resolveWithObject:true}),bb=await sharp(b).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 assert(aa.info.width===bb.info.width&&aa.info.height===bb.info.height,'Edge audit requires equal native sizes');
 const w=aa.info.width,h=aa.info.height,n=direction==='east'?h:w;let sum=0,max=0,samples=0;
 for(let i=0;i<n;i++){
  const pa=direction==='east'?(i*w+w-1)*4:((h-1)*w+i)*4,pb=direction==='east'?i*w*4:i*4;
  if(aa.data[pa+3]<128||bb.data[pb+3]<128)continue;
  for(let c=0;c<3;c++){const delta=Math.abs(aa.data[pa+c]-bb.data[pb+c]);sum+=delta;max=Math.max(max,delta);}samples++;
 }
 return {opaqueSamples:samples,meanRgbDelta:samples?Number((sum/(samples*3)).toFixed(3)):null,maxRgbDelta:samples?max:null};
}
async function alphaStats(bytes){
 const {data,info}=await sharp(bytes).ensureAlpha().raw().toBuffer({resolveWithObject:true});let transparent=0,below128=0,atLeast128=0,minNonzero=255,max=0,left=info.width,top=info.height,right=-1,bottom=-1;
 for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++){
  const a=data[(y*info.width+x)*4+3];if(a===0)transparent++;else{minNonzero=Math.min(minNonzero,a);if(a<128)below128++;else{atLeast128++;left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);}}max=Math.max(max,a);
 }
 return {transparent,below128,atLeast128,minNonzero:max?minNonzero:null,max,bbox128:atLeast128?{left,top,width:right-left+1,height:bottom-top+1}:null};
}
module.exports={fs,path,sharp,hash,json,assert,inside,root,sourceRoot,outputRoot,reviewRoot,rel,absolute,escape,exists,preserve,metadata,normalize,edgeAudit,alphaStats};
