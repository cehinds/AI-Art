const fs=require('fs'),path=require('path'),crypto=require('crypto');
let sharp;try{sharp=require('sharp')}catch{sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')}
const root=__dirname,hash=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{const rooms=[];let sourceCount=0,outputCount=0;
for(const id of ['tobul','scott','hilda']){
 const dir=path.join(root,'room-'+id),m=JSON.parse(fs.readFileSync(path.join(dir,'layout.json'),'utf8')),[w,h]=m.dimensions||m.canvas;
 for(const s of m.sources){const f=s.localFile||s.file;if(/(?:^|\/)composite\.png$/.test(f))throw Error('Flattened room used as component');if(hash(fs.readFileSync(path.join(dir,f)))!==s.sha256)throw Error('Source drift '+id+' '+f);sourceCount++}
 for(const o of m.outputs){if(hash(fs.readFileSync(path.join(dir,o.file)))!==o.sha256)throw Error('Output drift '+id+' '+o.file);outputCount++}
 const layers=m.layerOrder.map(name=>{const o=m.outputs.find(x=>x.file===name+'.png'||x.file==='layers/'+name+'.png');if(!o)throw Error('Missing layer '+name);return {input:fs.readFileSync(path.join(dir,o.file))}});
 const actual=await sharp(path.join(dir,'composite.png')).ensureAlpha().raw().toBuffer(),rebuilt=await sharp({create:{width:w,height:h,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite(layers).ensureAlpha().raw().toBuffer();if(!actual.equals(rebuilt))throw Error('Layer mismatch '+id);
 const proof=fs.readFileSync(path.join(root,'ReferenceReview/room-proofs',id+'.png'));if(hash(proof)!==hash(fs.readFileSync(path.join(dir,'composite.png'))))throw Error('Stale comparison '+id);
 rooms.push({id,dimensions:[w,h],sourcePngs:m.sources.length,layers:m.layerOrder.length,exactReconstruction:true,comparisonCurrent:true});
}
let links=0;for(const file of ['index.html','ReferenceReview/index.html']){const abs=path.join(root,file),html=fs.readFileSync(abs,'utf8');for(const a of html.matchAll(/(?:href|src)=["']([^"']+)["']/g)){if(/^(?:https?:|data:|#)/.test(a[1]))continue;const u=decodeURIComponent(a[1].split('#')[0]);if(!fs.existsSync(path.resolve(path.dirname(abs),u)))throw Error('Missing local link '+file+': '+u);links++}}
const result={status:'PASS',rooms,sourcePngChecks:sourceCount,outputChecks:outputCount,localHtmlLinks:links,noFlattenedRoomInputs:true};fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
})().catch(e=>{console.error(e);process.exitCode=1});
