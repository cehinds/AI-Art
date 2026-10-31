'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {sharp}=require('../remaster-expansion/common.cjs');
const root=path.resolve(__dirname,'../..'),cfg=JSON.parse(fs.readFileSync(path.join(__dirname,'kit.json')));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const dest='Assets/Art/Production/OpeningWorldV1',review='Review/opening-world-v1';
for(const dir of [dest,review])fs.mkdirSync(path.join(root,dir),{recursive:true});
(async()=>{
 const manifest={...cfg,generatedBy:'image_gen.imagegen',assets:[]};
 for(const a of cfg.assets){
  const source='ArtSource/OpeningWorldV1/sources/'+a.source,bytes=fs.readFileSync(path.join(root,source));
  const {data,info}=await sharp(bytes).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  let left=0,top=0,right=info.width-1,bottom=info.height-1;
  if(!a.opaque){left=info.width;top=info.height;right=-1;bottom=-1;for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++)if(data[(y*info.width+x)*4+3]>=cfg.alphaThreshold){left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);}}
  if(right<left)throw Error(a.id+' has no silhouette');
  const crop={left,top,width:right-left+1,height:bottom-top+1};
  const output=await sharp(bytes).extract(crop).resize(a.width,a.height,{fit:a.fit,position:'south',kernel:'nearest',background:{r:0,g:0,b:0,alpha:0}}).ensureAlpha().png().toBuffer();
  const file=dest+'/'+a.id+'.png';fs.writeFileSync(path.join(root,file),output);
  manifest.assets.push({...a,source,sourceSha256:hash(bytes),sourceSize:{width:info.width,height:info.height},crop,file,sha256:hash(output)});
 }
 fs.writeFileSync(path.join(root,dest,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 const cards=[];
 for(let i=0;i<manifest.assets.length;i++){
  const a=manifest.assets[i],input=await sharp(path.join(root,a.file)).resize(280,280,{fit:'inside',kernel:'nearest'}).png().toBuffer();
  const m=await sharp(input).metadata(),label=Buffer.from('<svg width="360" height="52"><text x="16" y="30" fill="#faf3df" font-family="monospace" font-size="19">'+a.id+' · '+a.width+'x'+a.height+'</text></svg>');
  const card=await sharp({create:{width:360,height:350,channels:4,background:'#253a36'}}).composite([{input:label,left:0,top:0},{input,left:Math.floor((360-m.width)/2),top:60}]).png().toBuffer();
  cards.push({input:card,left:i%2*360,top:Math.floor(i/2)*350});
 }
 await sharp({create:{width:720,height:700,channels:4,background:'#1c292e'}}).composite(cards).png().toFile(path.join(root,review,'contact-sheet.png'));
 fs.writeFileSync(path.join(root,review,'index.html'),'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Opening World V1</title><style>body{background:#142124;color:#eee;font:17px system-ui;max-width:1000px;margin:auto;padding:24px}img{image-rendering:pixelated;max-width:100%}article{padding:20px;margin:16px 0;background:#253a36}a{color:#91d6ff}</style><h1>Opening world components</h1><p>Generated recreations from FFII Pixel Remaster gameplay references. Ground, vegetation and settlement layers are distinct. The game owns collision and portal coordinates.</p><img src="contact-sheet.png" alt="Four generated overworld components">'+manifest.assets.map(a=>'<article><h2>'+a.id+'</h2><img width="'+a.width*2+'" src="../../'+a.file+'" alt="'+a.id+'"><p>Layer: '+a.layer+' · Anchor: '+a.anchor+' · '+a.width+'×'+a.height+'px</p></article>').join('')+'<p><a href="../world-layer-comparison-v1/index.html">Reference layer comparison</a> · <a href="../../Assets/Art/Production/OpeningWorldV1/manifest.json">Asset manifest and hashes</a></p></html>');
 console.log('Exported '+manifest.assets.length+' opening-world components.');
})().catch(e=>{console.error(e);process.exitCode=1;});

