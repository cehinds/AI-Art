let sharp;
try { sharp=require('sharp'); }
catch { sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=__dirname;
const sources=[
 {id:'tobul',file:'pr-smithy.webp',archivedOriginal:'Logs/interior-reference-20261029/tobul.webp',sourceUrl:'https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/walkthrough/salamand-and-semitt-falls/tobul-960w.webp',rect:{left:213,top:0,width:534,height:440},crop:'tobul-reference.png'},
 {id:'scott',file:'pr-refuge.webp',archivedOriginal:'Logs/interior-reference-20261029/scott.webp',sourceUrl:'https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn/scott-gives-you-ring-960w.webp',rect:{left:69,top:0,width:534,height:390},crop:'scott-reference.png'},
 {id:'hilda',file:'pr-hilda.jpg',archivedOriginal:'References/Parity20261025/rpgfan-ffii-pr-005.jpg',sourceUrl:'https://www.rpgfan.com/wp-content/uploads/2021/06/Final-Fantasy-II-Pixel-Remaster-Screenshot-005.jpg',rect:{left:430,top:355,width:1380,height:463},crop:'hilda-reference.png'}
];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const entries=[];
 for(const s of sources){
  const source=path.join(root,'sources',s.file),dest=path.join(root,'crops',s.crop);
  const meta=await sharp(source).metadata();
  if(s.rect.left+s.rect.width>meta.width||s.rect.top+s.rect.height>meta.height)throw new Error(`${s.id} crop exceeds ${meta.width}×${meta.height} source`);
  const input=fs.readFileSync(source);
  await sharp(input).extract(s.rect).png().toFile(dest);
  const crop=fs.readFileSync(dest);
  entries.push({id:s.id,sourceFile:`sources/${s.file}`,archivedOriginal:s.archivedOriginal,sourceUrl:s.sourceUrl,sourceSha256:sha(input),sourceDimensions:[meta.width,meta.height],cropFile:`crops/${s.crop}`,cropRect:s.rect,cropDimensions:[s.rect.width,s.rect.height],cropSha256:sha(crop),operation:'Exact pixel crop from preserved source capture; no scaling or retouch.'});
 }
 fs.writeFileSync(path.join(root,'reference-manifest.json'),JSON.stringify({date:'2026-10-31',scope:'Actual FFII Pixel Remaster reference captures and source-relative crops for three static room assemblies.',entries},null,2)+'\n');
 console.log(`Wrote ${entries.length} exact reference crops and provenance manifest.`);
})().catch(e=>{console.error(e);process.exitCode=1;});
