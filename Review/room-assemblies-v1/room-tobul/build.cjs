'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
let sharp;try{sharp=require('sharp')}catch{sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')}
const root=__dirname,art=process.env.AI_ART_ROOT||'C:/repos/AI-Art-FF2',W=534,H=440;
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const S='Assets/Art/Production/ShopInteriorsV2/';
const sources={floor:S+'samples/red-floor-swatch.png',wall:S+'scenes/weapon/wall.png',rug:S+'samples/rug-visible.png',merchant:S+'scenes/weapon/merchant.png',counter:S+'fixtures/gold-l-counter.png',chest:S+'fixtures/chest.png',rackLeft:S+'fixtures/sword-rack-left.png',rackRight:S+'fixtures/sword-rack-right.png',furnace:S+'fixtures/furnace.png',bench:S+'fixtures/east-workbench.png',stool:S+'fixtures/stool.png'};
const items=[
 {id:'floor',layer:'floor',x:0,y:0,width:24,height:24,repeat:true,role:'Existing red-floor sample repeated; no seamlessness claim'},
 {id:'rug',layer:'rug',x:50,y:246,width:339,height:195,role:'Visible rug crop; lower edge remains clipped by selected viewport'},
 {id:'wall',layer:'wall',x:0,y:0,width:W,height:H,role:'Existing transparent stocked-wall layer; left cabinet is baked into this component'},
 {id:'merchant',layer:'merchant',x:0,y:0,width:W,height:H,role:'Existing visible shopkeeper layer; fixed source framing'},
 {id:'bench',layer:'furniture',x:486,y:90,width:48,height:270,role:'Independent workbench scaled to reference footprint; aspect differs from original prop'},
 {id:'chest',layer:'furniture',x:219,y:78,width:72,height:51,role:'Independent chest'},
 {id:'rackLeft',layer:'furniture',x:340,y:75,width:44,height:54,role:'Independent left weapon rack'},
 {id:'rackRight',layer:'furniture',x:386,y:75,width:44,height:54,role:'Independent right weapon rack'},
 {id:'furnace',layer:'furniture',x:435,y:150,width:99,height:99,role:'Independent furnace including authored top objects'},
 {id:'stool',layer:'furniture',x:447,y:300,width:27,height:30,role:'Independent stool'},
 {id:'counter',layer:'furniture',x:0,y:75,width:340,height:146,role:'Independent L-counter fitted to measured reference footprint'}
];
async function blank(){return sharp({create:{width:W,height:H,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).png().toBuffer()}
async function main(){
 fs.mkdirSync(path.join(root,'inputs'),{recursive:true});fs.mkdirSync(path.join(root,'layers'),{recursive:true});
 const records=[];const inputs={};
 for(const [id,file]of Object.entries(sources)){const p=path.join(root,'inputs',id+'.png');if(!fs.existsSync(p))fs.copyFileSync(path.join(art,file),p);const b=fs.readFileSync(p),m=await sharp(b).metadata();inputs[id]=b;records.push({id,originalRepository:'cehinds/AI-Art',originalFile:file,file:'inputs/'+id+'.png',sha256:hash(b),width:m.width,height:m.height})}
 const order=['floor','rug','wall','merchant','furniture'],layers={};
 for(const name of order){const ops=[];for(const p of items.filter(x=>x.layer===name)){const b=await sharp(inputs[p.id]).resize(p.width,p.height,{fit:'fill',kernel:'nearest'}).png().toBuffer();if(p.repeat){for(let y=p.y;y<H;y+=p.height)for(let x=p.x;x<W;x+=p.width){ops.push({input:await sharp(b).extract({left:0,top:0,width:Math.min(p.width,W-x),height:Math.min(p.height,H-y)}).png().toBuffer(),left:x,top:y})}}else{const w=Math.min(p.width,W-p.x),h=Math.min(p.height,H-p.y);ops.push({input:await sharp(b).extract({left:0,top:0,width:w,height:h}).png().toBuffer(),left:p.x,top:p.y})}}
 const b=await sharp(await blank()).composite(ops).png().toBuffer();fs.writeFileSync(path.join(root,'layers',name+'.png'),b);layers[name]=b;
 }
 const comp=await sharp(await blank()).composite(order.map(n=>({input:layers[n]}))).png().toBuffer();fs.writeFileSync(path.join(root,'composite.png'),comp);
 const outputs=[{file:'composite.png',sha256:hash(comp)},...order.map(n=>({file:'layers/'+n+'.png',sha256:hash(layers[n])}))];
 const layout={id:'tobul',title:'Tobul weapon shop',status:'existing-asset assembly; assets only',dimensions:[W,H],reference:{source:'pr-smithy.webp',rect:[213,0,534,440]},operation:'Existing PNG crops, nearest-neighbor scaling, tile repetition and alpha compositing only; no newly generated or painted room art.',sources:records,layerOrder:order,placements:items,outputs,limitations:['Original customers and dialogue omitted from static assembly.','Wall artwork and mounted stock remain a baked visible component.','The independent counter, furnace and workbench differ from the generated scene; measured footprint fitting is recorded.','Floor repetition and prop silhouettes require visual review; not a retail 1:1 or runtime claim.']};
 fs.writeFileSync(path.join(root,'layout.json'),JSON.stringify(layout,null,2)+'\n');
 const raw=await sharp(comp).raw().toBuffer(),rebuilt=await sharp(await blank()).composite(order.map(n=>({input:fs.readFileSync(path.join(root,'layers',n+'.png'))}))).raw().toBuffer();if(!raw.equals(rebuilt))throw Error('Layer reconstruction mismatch');
 fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify({status:'PASS',sourceFiles:records.length,placements:items.length,layerReconstruction:'exact RGBA',compositeSha256:hash(comp),dimensions:[W,H]},null,2)+'\n');console.log('Built Tobul from '+records.length+' existing component PNGs.');
}
main().catch(e=>{console.error(e);process.exitCode=1});
