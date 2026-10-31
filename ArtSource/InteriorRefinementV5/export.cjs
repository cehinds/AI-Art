'use strict';
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname,hash=b=>crypto.createHash('sha256').update(b).digest('hex');
async function main(){
 const out=path.join(root,'components');await fs.mkdir(out,{recursive:true});
 const master=await fs.readFile(path.join(root,'furniture-palette-master.png'));
 const names=['white-sickbed','square-table','flat-crate','red-ivory-seat','tan-stool','bedside-table-jug'];const records=[];
 for(let n=0;n<6;n++){
 const cell={left:(n%3)*512,top:Math.floor(n/3)*512,width:512,height:512};
 const b=await sharp(master).extract(cell).ensureAlpha().raw().toBuffer();
 let minX=512,minY=512,maxX=-1,maxY=-1;for(let y=0;y<512;y++)for(let x=0;x<512;x++)if(b[(y*512+x)*4+3]>=128){minX=Math.min(x,minX);maxX=Math.max(x,maxX);minY=Math.min(y,minY);maxY=Math.max(y,maxY)}
 const crop={left:cell.left+minX,top:cell.top+minY,width:maxX-minX+1,height:maxY-minY+1};
 const png=await sharp(master).extract(crop).png().toBuffer();await fs.writeFile(path.join(out,names[n]+'.png'),png);
 records.push({file:'components/'+names[n]+'.png',master:'furniture-palette-master.png',crop,sha256:hash(png),alphaPolicy:'Generated alpha preserved unchanged; alpha>=128 used only to locate crop bounds.'});
 }
 const rug=await fs.readFile(path.join(root,'rug-master.png'));await fs.writeFile(path.join(out,'hilda-narrow-border-rug.png'),rug);records.push({file:'components/hilda-narrow-border-rug.png',master:'rug-master.png',sha256:hash(rug)});
 const manifest={version:5,method:'Built-in image_gen generated component masters; deterministic crop export only; no reference pixels used as production art.',sources:await Promise.all(['furniture-master.png','furniture-clean-master.png','furniture-palette-master.png','rug-master.png','prompts.json','palette-prompt.txt'].map(async file=>({file,sha256:hash(await fs.readFile(path.join(root,file)))}))),components:records};await fs.writeFile(path.join(root,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 const cards=[];for(let n=0;n<6;n++){const b=await sharp(path.join(out,names[n]+'.png')).resize(160,190,{fit:'inside',kernel:'nearest'}).toBuffer();cards.push({input:b,left:30+(n%3)*200,top:30+Math.floor(n/3)*230})}await sharp({create:{width:630,height:490,channels:4,background:'#74816e'}}).composite(cards).png().toFile(path.join(root,'furniture-contact.png'));console.log(JSON.stringify(manifest));
}
main().catch(e=>{console.error(e);process.exitCode=1});
