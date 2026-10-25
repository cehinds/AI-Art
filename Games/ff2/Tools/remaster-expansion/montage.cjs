'use strict';
const {fs,path,sharp,review,json,assert}=require('./common.cjs');
async function writeSet(m,planned,heroes,key){
 const clips=heroes.map(owner=>m.clips.find(c=>c.group==='battle'&&c.owner===owner&&c.name==='attack'));if(clips.some(c=>!c))return false;
 const byId=new Map(planned.map(p=>[p.asset.id,p])),w=heroes.length*128,h=180,count=clips[0].frames.length,frames=[];
 assert(clips.every(c=>c.frames.length===count&&JSON.stringify(c.frames.map(f=>f.durationMs))===JSON.stringify(clips[0].frames.map(f=>f.durationMs))),'Review montage attack timing must match');
 const labels=Buffer.from(`<svg width="${w}" height="${h}"><g fill="#f1e8d6" font-family="sans-serif"><text x="8" y="17" font-size="12">REVIEW LOOP · original attacks remain nonlooping · 600 ms recovery hold</text>${heroes.map((hero,i)=>`<text x="${i*128+8}" y="172" font-size="13">${hero}</text>`).join('')}</g></svg>`);
 for(let i=0;i<count;i++){const parts=clips.map((c,j)=>({input:byId.get(c.frames[i].id).native,left:j*128,top:28}));parts.push({input:labels,left:0,top:0});frames.push(await sharp({create:{width:w,height:h,channels:4,background:'#17262a'}}).composite(parts).png().toBuffer())}
 const delays=clips[0].frames.map(f=>f.durationMs);delays[delays.length-1]+=600;
 for(const factor of [1,3]){const raws=await Promise.all(frames.map(p=>sharp(p).resize(w*factor,h*factor,{kernel:'nearest'}).ensureAlpha().raw().toBuffer()));await sharp(Buffer.concat(raws),{raw:{width:w*factor,height:h*factor*frames.length,channels:4,pageHeight:h*factor}}).gif({delay:delays,loop:0,dither:0,effort:7}).toFile(path.join(review,key+(factor===1?'-native.gif':'-3x.gif')))}
 await fs.writeFile(path.join(review,key+'.json'),json({scope:'review-only composite of actual native PNGs; production clip flags/timing unchanged',heroes,sourceClipIds:clips.map(c=>c.id),sourceFrames:clips.map(c=>c.frames.map(f=>f.id)),actionDurationMs:clips[0].frames.reduce((n,f)=>n+f.durationMs,0),additionalRecoveryHoldMs:600,reviewCycleMs:delays.reduce((a,b)=>a+b,0),reviewDurationsMs:delays,reviewLoop:true,productionClipsLoop:clips.map(c=>c.loop)}));return true;
}
exports.write=async(m,planned)=>{const results=[];for(const [key,heroes]of [['party-attacks-review',['firion','maria','guy','leon']],['guest-attacks-review',['minwu','josef','gordon','leila','ricard']]])if(await writeSet(m,planned,heroes,key))results.push({key,heroes,native:key+'-native.gif',enlarged:key+'-3x.gif'});await fs.writeFile(path.join(review,'montages.json'),json(results));};
