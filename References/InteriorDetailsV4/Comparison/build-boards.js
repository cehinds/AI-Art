'use strict';
let sharp;try{sharp=require('sharp')}catch{sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')}
const fs=require('fs');
const path=require('path');
const stageRoot=path.resolve(__dirname,'..');
const root=fs.existsSync(path.join(stageRoot,'Assets/Art/Production/InteriorDetailsV4'))?stageRoot:path.resolve(__dirname,'../../..');
const out=path.join(__dirname,'boards');
const refs=path.join(__dirname,'source-crops');
const assets=path.join(root,'Assets/Art/Production/InteriorDetailsV4');
const W=1120, BG='#151f28', PANEL='#202e38', BORDER='#405363', WHITE='#e8edf2', MUTED='#b8c5ce', GOLD='#f1c46a', TEAL='#8ad5c0';
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
function svg(w,h,body){return Buffer.from(`<svg width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg">${body}</svg>`)}
function rect(x,y,w,h,fill=PANEL,stroke=BORDER,r=9){return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" stroke="${stroke}" stroke-width="2"/>`}
function text(x,y,s,size=14,color=MUTED,weight=400,anchor='start'){return `<text x="${x}" y="${y}" fill="${color}" font-family="Segoe UI,Arial,sans-serif" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}">${esc(s)}</text>`}
function header(title,sub,h){return `<rect width="${W}" height="${h}" fill="${BG}"/>${text(24,38,title,25,WHITE,700)}${text(24,66,sub,13,MUTED)}${rect(24,84,526,34,PANEL,BORDER,8)}${rect(570,84,526,34,PANEL,BORDER,8)}${text(287,107,'ORIGINAL — FFII PIXEL REMASTER',14,TEAL,700,'middle')}${text(833,107,'NEW ASSET — INTERIOR DETAILS V4',14,TEAL,700,'middle')}`}
async function fit(file,maxW,maxH){const m=await sharp(file).metadata();const k=Math.min(maxW/m.width,maxH/m.height);const w=Math.max(1,Math.round(m.width*k)),h=Math.max(1,Math.round(m.height*k));return {buffer:await sharp(file).resize(w,h,{kernel:'nearest'}).png().toBuffer(),width:w,height:h};}
async function nativeFit(file,maxW,maxH,scale){const m=await sharp(file).metadata();const k=Math.min(scale,maxW/m.width,maxH/m.height);const w=Math.max(1,Math.round(m.width*k)),h=Math.max(1,Math.round(m.height*k));return {buffer:await sharp(file).resize(w,h,{kernel:'nearest'}).png().toBuffer(),width:w,height:h};}
async function read(file){return sharp(file).png().toBuffer()}
async function rugs(){const H=1460;let b=header('Interior Details V4 — Rugs','Actual source crops on the left; complete native V4 rug components on the right. Images are fitted where needed with nearest-neighbor sampling; Tobul source stays native-size.',H),layers=[];const rows=[
 ['Hilda audience rug — red/gold border','hilda-red-gold-rug-border.png','rugs/hilda-red-gold.png','128×160',['RPGFan Screenshot 005 crop fitted to panel; partial top/right border.','Deep red field and narrow checker/triangle edge visible.']],
 ['Scott refuge rug — blue/cream lattice','scott-blue-cream-rug-context.png','rugs/scott-blue-cream.png','96×128',['Vorxu room context; bed, party and bubble occlude rug center.','Inset preserves exposed screenshot rug pixels.']],
 ['Tobul smithy rug — cream/lilac diamonds','tobul-lilac-cream-rug-clear.png','rugs/tobul-cream-lilac.png','160×96',['Vorxu screenshot crop; clear cream/lilac pattern.','No characters in the selected source crop.']]
 ];
 for(let i=0;i<rows.length;i++){const [title,ref,asset,dims,capL,capR]=rows[i],y=132+i*438;b+=text(560,y+24,title,19,GOLD,700,'middle')+rect(24,y+38,526,400)+rect(570,y+38,526,400);
 let src;if(i===1){const context=await read(path.join(refs,ref)),inset=await fit(path.join(refs,'scott-blue-cream-rug-exposed-corner.png'),112,176);const m=await sharp(context).metadata();const hh=Math.max(m.height,inset.height),ww=m.width+inset.width+12;const combined=await sharp({create:{width:ww,height:hh,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite([{input:context,left:0,top:Math.floor((hh-m.height)/2)},{input:inset.buffer,left:m.width+12,top:Math.floor((hh-inset.height)/2)}]).png().toBuffer();const cm=await sharp(combined).metadata();src={buffer:combined,width:cm.width,height:cm.height};}else if(i===2){const buf=await read(path.join(refs,ref)),m=await sharp(buf).metadata();src={buffer:buf,width:m.width,height:m.height};}else src=await fit(path.join(refs,ref),420,300);
 const sx=Math.round(287-src.width/2),sy=y+48+Math.round((300-src.height)/2);layers.push({input:src.buffer,left:sx,top:sy});
 const dst=await nativeFit(path.join(assets,asset),440,300,2);layers.push({input:dst.buffer,left:Math.round(833-dst.width/2),top:y+48+Math.round((300-dst.height)/2)});
 b+=text(36,y+358,capL[0],12,MUTED)+text(36,y+377,capL[1],12,MUTED)+text(582,y+358,`New V4 native ${dims} rug.`,12,MUTED)+text(582,y+377,'Complete authored component; enlarged for preview.',12,MUTED);
 }
 await sharp(svg(W,H,b)).composite(layers).png().toFile(path.join(out,'rugs-original-vs-v4.png'));
}
async function walls(){const H=1040;let b=header('Interior Details V4 — Walls','Original FFII screenshot crops compared with single V4 authored wall components. Source and V4 images are fitted with nearest-neighbor sampling; no repeated panel rhythm is synthesized.',H),layers=[];const rows=[
 ['Hilda audience wall — dark overhead timber + cream panel','hilda-wall-uncovered-panel.png','walls/hilda-dark-timber.png','64×128',['RPGFan Screenshot 005 uncovered far-right crop.','Dark overhead timber remains visible above the cream inset.']],
 ['Scott refuge wall — alternating bay widths','scott-timber-cream-wall-panels.png','walls/scott-alternating-bays.png','128×64',['Vorxu Scott refuge crop shows narrow/medium/wide bays.','Capture crop is shown as a complete reference strip.']]
 ];
 for(let i=0;i<rows.length;i++){const [title,ref,asset,dims,capL,capR]=rows[i],y=132+i*430;b+=text(560,y+24,title,18,GOLD,700,'middle')+rect(24,y+38,526,380)+rect(570,y+38,526,380);
 const src=await fit(path.join(refs,ref),430,300);layers.push({input:src.buffer,left:Math.round(287-src.width/2),top:y+48+Math.round((300-src.height)/2)});
 const dst=await nativeFit(path.join(assets,asset),430,300,3);layers.push({input:dst.buffer,left:Math.round(833-dst.width/2),top:y+48+Math.round((300-dst.height)/2)});
 b+=text(36,y+355,capL[0],12,MUTED)+text(36,y+374,capL[1],12,MUTED)+text(582,y+355,`New V4 native ${dims} authored component.`,12,MUTED)+text(582,y+374,'Shown alone; enlarged with nearest-neighbor sampling.',12,MUTED);
 }
 await sharp(svg(W,H,b)).composite(layers).png().toFile(path.join(out,'walls-original-vs-v4.png'));
}
(async()=>{await fs.promises.mkdir(out,{recursive:true});await rugs();await walls();console.log('Rendered V4 comparison boards');})().catch(e=>{console.error(e.stack);process.exitCode=1});






