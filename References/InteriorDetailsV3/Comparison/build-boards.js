let sharp;try{sharp=require('sharp')}catch{sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')}
const fs = require('fs');
const path = require('path');
const stageRoot=path.resolve(__dirname,'..');
const root=fs.existsSync(path.join(stageRoot,'Assets/Art/Production/InteriorDetailsV3'))?stageRoot:path.resolve(__dirname,'../../..');
const out=path.join(__dirname,'boards');
const crops=path.join(__dirname,'source-crops');
const assets=path.join(root,'Assets/Art/Production/InteriorDetailsV3');
const W=1120, BG='#151f28', PANEL='#202e38', BORDER='#405363', WHITE='#e8edf2', MUTED='#b8c5ce', GOLD='#f1c46a', TEAL='#8ad5c0';
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
function svg(w,h,body){return Buffer.from(`<svg width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg">${body}</svg>`)}
function rect(x,y,w,h,fill=PANEL,stroke=BORDER,r=9){return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" stroke="${stroke}" stroke-width="2"/>`}
function text(x,y,str,size=14,color=MUTED,weight=400,anchor='start'){return `<text x="${x}" y="${y}" fill="${color}" font-family="Segoe UI,Arial,sans-serif" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}">${esc(str)}</text>`}
function header(title,subtitle,h){let b=rect(24,84,526,34,PANEL,BORDER,8)+rect(570,84,526,34,PANEL,BORDER,8)+text(287,107,'ORIGINAL — FFII PIXEL REMASTER',14,TEAL,700,'middle')+text(833,107,'NEW ASSET — INTERIOR DETAILS V3',14,TEAL,700,'middle'); return `<rect width="${W}" height="${h}" fill="${BG}"/>${text(24,38,title,25,WHITE,700)}${text(24,66,subtitle,13,MUTED)}${b}`}
async function read(file){return sharp(file).png().toBuffer()}
async function scale(file,maxW,maxH){let m=await sharp(file).metadata();let k=Math.max(1,Math.min(Math.floor(maxW/m.width),Math.floor(maxH/m.height)));return {buf:await sharp(file).resize(m.width*k,m.height*k,{kernel:'nearest'}).png().toBuffer(),w:m.width*k,h:m.height*k}}
async function repeatWall(file){let im=await sharp(file).png().toBuffer();let m=await sharp(im).metadata();let k=4;let tile=await sharp(im).resize(m.width*k,m.height*k,{kernel:'nearest'}).png().toBuffer();let tm=await sharp(tile).metadata();let count=3;return {buf:await sharp({create:{width:tm.width*count,height:tm.height,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite(Array.from({length:count},(_,i)=>({input:tile,left:i*tm.width,top:0}))).png().toBuffer(),w:tm.width*count,h:tm.height}}
async function boardRugs(){let h=1466, b=header('Interior Details V3 — Rugs','Original FFII PR crops retain source composition; V3 rugs are native assets enlarged with nearest-neighbor sampling.',h);let jobs=[
 ['Hilda audience carpet — checker/triangle border','hilda-red-gold-rug-border.png','rugs/hilda-red-gold.png',['Original RPGFan Screenshot 005 crop:','clear checker/triangle border; no characters.'],['New V3 full rug, native 128×160.','Enlarged with nearest-neighbor sampling.']],
 ['Scott refuge rug — blue/cream lattice','scott-blue-cream-rug-context.png','rugs/scott-blue-cream.png',['Original Vorxu screenshot context:','bed/party/bubble occlude center; inset shows exposed rug pixels.'],['New V3 full rug, native 96×128.','Enlarged with nearest-neighbor sampling.']],
 ['Tobul smithy rug — cream/lilac diamonds','tobul-lilac-cream-rug-clear.png','rugs/tobul-cream-lilac.png',['Original Vorxu screenshot crop:','clear cream/lilac pattern; no characters.'],['New V3 full rug, native 160×96.','Enlarged with nearest-neighbor sampling.']]
 ];
 for(let i=0;i<jobs.length;i++){let y=132+i*438;let [title,ref,asset,l1,l2]=jobs[i];b+=text(560,y+24,title,19,GOLD,700,'middle')+rect(24,y+38,526,400)+rect(570,y+38,526,400);let im=await read(path.join(crops,ref));if(i===1){let inset=await read(path.join(crops,'scott-blue-cream-rug-exposed-corner.png'));let a=await sharp(im).metadata(), c=await sharp(inset).metadata();b+=``;let ic=await scale(path.join(crops,'scott-blue-cream-rug-exposed-corner.png'),120,180);let ctx=await sharp({create:{width:a.width+ic.w+12,height:a.height,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite([{input:im,left:0,top:0},{input:ic.buf,left:a.width+12,top:Math.max(0,Math.floor((a.height-ic.h)/2))}]).png().toBuffer();let cm=await sharp(ctx).metadata();b+=`<image/>`; b=b.replace('<image/>','');let pos={x:Math.round(287-cm.width/2),y:y+60}; b+=`<image/>`; b=b.replace('<image/>',''); b+=`<rect x="${pos.x}" y="${pos.y}" width="${cm.width}" height="${cm.height}" fill="none"/>`;
 // stage composite image separately below
 globalThis.rugScottComposite={buf:ctx,x:pos.x,y:pos.y};
 } else {let s=i===0?await (async()=>{const m=await sharp(path.join(crops,ref)).metadata();const k=0.75;return {buf:await sharp(path.join(crops,ref)).resize(Math.round(m.width*k),Math.round(m.height*k),{kernel:'nearest'}).png().toBuffer(),w:Math.round(m.width*k),h:Math.round(m.height*k)}})():await scale(path.join(crops,ref),360,290);globalThis[`rugRef${i}`]={...s,x:Math.round(287-s.w/2),y:y+50+Math.round((320-s.h)/2)};}
 let s=await scale(path.join(assets,asset),480,320);globalThis[`rugNew${i}`]={...s,x:Math.round(833-s.w/2),y:y+50+Math.round((320-s.h)/2)};
 b+=text(36,y+375,l1[0],12,MUTED)+text(36,y+393,l1[1],12,MUTED)+text(582,y+375,l2[0],12,MUTED)+text(582,y+393,l2[1],12,MUTED);
 }
 // SVG was built with image placeholders omitted; compose source/output overlays onto final canvas.
 let comps=[];for(let i=0;i<3;i++){let a=globalThis[`rugRef${i}`];if(a)comps.push({input:a.buf,left:a.x,top:a.y});let n=globalThis[`rugNew${i}`];comps.push({input:n.buf,left:n.x,top:n.y});}let sc=globalThis.rugScottComposite;comps.push({input:sc.buf,left:sc.x,top:sc.y});
 await sharp(svg(W,h,b)).composite(comps).png().toFile(path.join(out,'rugs-original-vs-v3.png'));
}
async function boardWalls(){let h=1120,b=header('Interior Details V3 — Walls','Original screenshot crops retain their source proportions; repeated V3 wall previews are centered and enlarged with nearest-neighbor sampling.',h);let jobs=[
 ['Hilda audience wall — cream panel with timber posts','hilda-wall-uncovered-panel.png','walls/hilda-cream-timber-32.png',['Original RPGFan Screenshot 005 crop:','uncovered far-right wall panel.'],['New V3 Hilda wall, native 32×64 in a repeated preview.','Repeated preview enlarged with nearest-neighbor sampling.']],
 ['Scott refuge wall — cream panels and vertical timber slats','scott-timber-cream-wall-panels.png','walls/scott-cream-slats-32.png',['Original Vorxu Scott-refuge crop:','wall panels and rails are unobstructed.'],['New V3 Scott slat wall, native 32×64 in a repeated preview.','Repeated preview enlarged with nearest-neighbor sampling.']]
 ];let elems=[];
 for(let i=0;i<2;i++){let y=132+i*470;let [title,ref,asset,l1,l2]=jobs[i];b+=text(560,y+24,title,18,GOLD,700,'middle')+rect(24,y+38,526,425)+rect(570,y+38,526,425);
 let src=path.join(crops,ref), s=await scale(src,i===0?145:430,300);let sm=await sharp(s.buf).metadata();let sx=Math.round(287-sm.width/2),sy=y+48+Math.round((300-sm.height)/2);elems.push({input:s.buf,left:sx,top:sy});
 let r=await repeatWall(path.join(assets,asset));let maxW=460,maxH=300,k=Math.min(maxW/r.w,maxH/r.h),ww=Math.round(r.w*k),hh=Math.round(r.h*k);let rb=await sharp(r.buf).resize(ww,hh,{kernel:'nearest'}).png().toBuffer();elems.push({input:rb,left:Math.round(833-ww/2),top:Math.round(y+48+(300-hh)/2)});
 b+=text(36,y+375,l1[0],12,MUTED)+text(36,y+393,l1[1],12,MUTED)+text(582,y+375,l2[0],12,MUTED)+text(582,y+393,l2[1],12,MUTED);
 }
 await sharp(svg(W,h,b)).composite(elems).png().toFile(path.join(out,'wall-floor-original-vs-v3.png'));
}async function boardCounter(){let h=870,b=header('Interior Details V3 — Tobul Counter','Original screenshot crops are unaltered except for cropping. V3 counter exports are enlarged with nearest-neighbor scaling.',h);let jobs=[
 ['Golden wood straight counter','tobul-goldwood-counter-front-clean.png','counters/golden-straight.png',['Original Vorxu screenshot crop:','dish and displayed weapons remain in the reference.'],['New V3 straight counter, native 128×32.','Screenshot top fixtures are not part of this asset.']],
 ['Golden wood L-corner counter','tobul-goldwood-counter-l-context.png','counters/golden-corner.png',['Original Vorxu screenshot context:','shopkeeper, speech bubble and fixtures remain visible.'],['New V3 L-corner counter, native 128×64.','Counter shape only; screenshot fixtures omitted.']]
 ];let comps=[];
 for(let i=0;i<2;i++){let y=132+i*360;let [title,ref,asset,l1,l2]=jobs[i];b+=text(560,y+24,title,19,GOLD,700,'middle')+rect(24,y+38,526,320)+rect(570,y+38,526,320);
 let s=await scale(path.join(crops,ref),460,200);comps.push({input:s.buf,left:Math.round(287-s.w/2),top:y+50+Math.round((190-s.h)/2)});
 let n=await scale(path.join(assets,asset),460,230);comps.push({input:n.buf,left:Math.round(833-n.w/2),top:y+45+Math.round((210-n.h)/2)});
 b+=text(36,y+270,l1[0],12,MUTED)+text(36,y+290,l1[1],12,MUTED)+text(582,y+270,l2[0],12,MUTED)+text(582,y+290,l2[1],12,MUTED);
 }
 await sharp(svg(W,h,b)).composite(comps).png().toFile(path.join(out,'counter-shop-original-vs-v3.png'));
}
(async()=>{await boardRugs();await boardWalls();await boardCounter();console.log('rendered boards');})();




