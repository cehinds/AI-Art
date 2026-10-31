'use strict';
const C=require('./common.cjs');
const {fs,path,sharp,hash,json,assert,root,sourceRoot,outputRoot,reviewRoot,rel,escape,exists,preserve,metadata,normalize,edgeAudit,alphaStats}=C;
async function renderCell(ref,assets,size){
 const keys=Array.isArray(ref)?ref:[ref];
 const layers=keys.filter(Boolean).map(key=>{const a=assets.get(key);assert(a,'Unknown assembly tile: '+key);assert(a.width===size&&a.height===size,'Mixed native sizes need a separate assembly: '+key);return {input:a.bytes,left:0,top:0};});
 return sharp({create:{width:size,height:size,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite(layers).png().toBuffer();
}
async function main(){
 const cfgBytes=await fs.readFile(path.join(__dirname,'kit.json')),cfg=JSON.parse(cfgBytes);
 assert(cfg.schemaVersion===1&&cfg.kit==='world-components-v1','Unsupported kit schema');
 assert(cfg.sheets.length>0,'No generated masters registered yet. Add inspected atlas definitions before export.');
 // Finish the complete plan before writing any asset.
 const plans=[],sheetIds=new Set();for(const sheet of cfg.sheets){assert(!sheetIds.has(sheet.id),'Duplicate atlas ID: '+sheet.id);sheetIds.add(sheet.id);plans.push({sheet,plan:await normalize(sheet)});}
 const assets=new Map(),manifest={...cfg,status:'candidate-assets-not-integrated',configSha256:hash(cfgBytes),sheets:[],assets:[],validationLimits:'Semantic ports and edge statistics do not prove WFC suitability, seamlessness, runtime collision, Unity import or visual approval.'};
 if(cfg.generationPrompts){const promptFile=path.resolve(root,cfg.generationPrompts);C.inside(sourceRoot,promptFile);manifest.generationPromptRecord={file:cfg.generationPrompts,sha256:hash(await fs.readFile(promptFile))};}
 for(const {sheet,plan} of plans){
  manifest.sheets.push({id:sheet.id,normalization:plan.mode,source:plan.source,sourceSha256:plan.sourceSha256,sourceSize:plan.sourceSize,crop:plan.crop,columns:sheet.columns,rows:sheet.rows,tileSize:sheet.tileSize,normalizedSize:{width:plan.width,height:plan.height},normalizedSha256:hash(plan.normalized)});
  for(const r of plan.records){
   const key=sheet.id+'/'+r.definition.id,file='Assets/Art/Production/WorldComponentsV1/'+key+'.png';
   assert(!assets.has(key),'Duplicate native tile key: '+key);
   const record={...r.definition,key,id:'world-components:'+sheet.id+'.'+r.definition.id,file,width:sheet.tileSize,height:sheet.tileSize,ppu:sheet.tileSize,index:r.index,sourceAtlas:sheet.id,normalization:plan.mode,sourceCell:{column:r.x,row:r.y},sha256:hash(r.bytes)};
   if(r.sourceCutout){record.sourceCellRect=r.sourceCellRect;record.sourceCutout=r.sourceCutout;record.nativePlacement=r.placement;record.alpha=await alphaStats(r.bytes);}
   manifest.assets.push(record);assets.set(key,{...record,bytes:r.bytes});
   const existing=path.join(root,file);if(await exists(existing))assert(hash(await fs.readFile(existing))===record.sha256,'Existing PNG differs; retain it and register a versioned candidate instead: '+file);
  }
 }
 const sourceCount=new Set(plans.map(p=>p.plan.source)).size;
 if(process.argv.includes('--check-only')){console.log('Preflight PASS: '+sourceCount+' preserved masters, '+plans.length+' atlas/crop definitions, '+assets.size+' native cells; no files written.');return;}
 await fs.mkdir(sourceRoot,{recursive:true});await fs.mkdir(outputRoot,{recursive:true});await fs.mkdir(reviewRoot,{recursive:true});
 for(const a of assets.values()){const file=path.join(root,a.file);await preserve(file,a.bytes);await metadata(file);}
 for(const {sheet,plan} of plans){await fs.mkdir(path.join(reviewRoot,'atlases'),{recursive:true});await fs.writeFile(path.join(reviewRoot,'atlases',sheet.id+'-native.png'),plan.normalized);}
 const cards=[];let i=0;
 for(const a of assets.values()){
  const image=await sharp(a.bytes).resize(160,160,{kernel:'nearest'}).png().toBuffer();
  const label=Buffer.from('<svg width="210" height="54"><text x="8" y="20" fill="#eee7ce" font-size="12" font-family="monospace">'+escape(a.key)+'</text><text x="8" y="40" fill="#a5c7b4" font-size="11" font-family="monospace">'+a.width+'px / '+escape(a.cornerRole)+'</text></svg>');
  const card=await sharp({create:{width:210,height:225,channels:4,background:'#25372e'}}).composite([{input:image,left:25,top:5},{input:label,left:0,top:168}]).png().toBuffer();
  cards.push({input:card,left:(i%6)*210,top:Math.floor(i/6)*225});i++;
 }
 await sharp({create:{width:1260,height:Math.ceil(cards.length/6)*225,channels:4,background:'#17251f'}}).composite(cards).png().toFile(path.join(reviewRoot,'contact-sheet.png'));
 const cutouts=[...assets.values()].filter(a=>a.normalization==='per-cell-alpha-cutout-fit');
 if(cutouts.length){
  const checkerCards=[];
  for(let i=0;i<cutouts.length;i++){
   const a=cutouts[i],size=a.width,raw=Buffer.alloc(size*size*4);
   for(let y=0;y<size;y++)for(let x=0;x<size;x++){const p=(y*size+x)*4,color=((Math.floor(x/8)+Math.floor(y/8))&1)?'#a9adb5':'#4a5160';raw[p]=parseInt(color.slice(1,3),16);raw[p+1]=parseInt(color.slice(3,5),16);raw[p+2]=parseInt(color.slice(5,7),16);raw[p+3]=255;}
   const checkerNative=await sharp(raw,{raw:{width:size,height:size,channels:4}}).composite([{input:a.bytes,left:0,top:0}]).png().toBuffer();
   const native=await sharp(checkerNative).resize(192,192,{kernel:'nearest'}).png().toBuffer();
   const label=Buffer.from('<svg width="256" height="40"><text x="8" y="24" fill="#eee7ce" font-size="11" font-family="monospace">'+escape(a.key)+'</text></svg>');
   const card=await sharp({create:{width:256,height:236,channels:4,background:'#17251f'}}).composite([{input:native,left:32,top:0},{input:label,left:0,top:194}]).png().toBuffer();
   checkerCards.push({input:card,left:i%4*256,top:Math.floor(i/4)*236});
  }
  await sharp({create:{width:1024,height:Math.ceil(cutouts.length/4)*236,channels:4,background:'#17251f'}}).composite(checkerCards).png().toFile(path.join(reviewRoot,'cutout-alpha-checker.png'));
 }
 const audits=[],assemblyRecords=[];
 for(const assembly of cfg.assemblies||[]){
  assert(/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(assembly.id),'Invalid assembly ID');
  const size=assembly.tileSize,rows=assembly.cells.length,cols=assembly.cells[0]?.length;
  assert((size===32||size===64)&&rows>0&&cols>0&&assembly.cells.every(r=>r.length===cols),'Invalid assembly grid');
  const cells=[];for(let y=0;y<rows;y++)for(let x=0;x<cols;x++)cells.push(await renderCell(assembly.cells[y][x],assets,size));
  const composites=cells.map((input,index)=>({input,left:index%cols*size,top:Math.floor(index/cols)*size}));
  const native=await sharp({create:{width:cols*size,height:rows*size,channels:4,background:assembly.background||'#244f38'}}).composite(composites).png().toBuffer();
  await fs.mkdir(path.join(reviewRoot,'assemblies'),{recursive:true});
  const file='assemblies/'+assembly.id+'.png';await sharp(native).resize(cols*size*3,rows*size*3,{kernel:'nearest'}).png().toFile(path.join(reviewRoot,file));
  assemblyRecords.push({id:assembly.id,file,cells:assembly.cells,nativeSize:{width:cols*size,height:rows*size},notes:assembly.notes||''});
  for(let y=0;y<rows;y++)for(let x=0;x<cols;x++)for(const direction of ['east','south']){
   const nx=x+(direction==='east'?1:0),ny=y+(direction==='south'?1:0);if(nx>=cols||ny>=rows)continue;
   audits.push({assembly:assembly.id,cell:{x,y},direction,a:assembly.cells[y][x],b:assembly.cells[ny][nx],...await edgeAudit(cells[y*cols+x],cells[ny*cols+nx],direction)});
  }
 }
 manifest.reviewAssemblies=assemblyRecords;
 await fs.writeFile(path.join(reviewRoot,'adjacency-audit.json'),json({status:'diagnostic-only',limits:'Boundary RGB differences are measurements, not a seamlessness verdict. Inspect actual montages for coastline width, flow, terrain continuity and bridge endpoints.',boundaries:audits}));
 await fs.writeFile(path.join(outputRoot,'manifest.json'),json(manifest));await metadata(path.join(outputRoot,'manifest.json'));
 const html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>World components V1 candidates</title><style>body{max-width:1280px;margin:auto;padding:24px;background:#14251d;color:#eee7ce;font:17px system-ui}img{image-rendering:pixelated;max-width:100%}article{margin:24px 0;padding:16px;background:#25372e}a{color:#a2daf4}table{border-collapse:collapse}td,th{border:1px solid #56735e;padding:8px;text-align:left}</style><h1>World component candidates</h1><p>Asset-only delivery. No game integration. Sources are preserved generated masters; terrain cells share whole-atlas normalization, while isolated bridge/mountain objects use declared per-cell cutout fits. Ports are declared terrain semantics. These candidates require visual review and are not certified seamless or WFC-ready.</p><p><a href="../../Assets/Art/Production/WorldComponentsV1/manifest.json">Manifest and source hashes</a> · <a href="adjacency-audit.json">Boundary measurements</a></p><img src="contact-sheet.png" alt="Native component inventory">'+assemblyRecords.map(a=>'<article><h2>'+escape(a.id)+'</h2><p>'+escape(a.notes)+'</p><img src="'+a.file+'" alt="'+escape(a.id)+' native-cell adjacency proof"></article>').join('')+'<h2>Atlas registration</h2>'+manifest.sheets.map(s=>'<article><h3>'+escape(s.id)+'</h3><p>Original '+s.sourceSize.width+'×'+s.sourceSize.height+' → group crop '+s.crop.left+','+s.crop.top+' '+s.crop.width+'×'+s.crop.height+' → '+s.normalizedSize.width+'×'+s.normalizedSize.height+' native atlas. Normalization: '+escape(s.normalization)+'. Per-object source crops and placements are recorded in the manifest.</p><img src="atlases/'+s.id+'-native.png" width="'+s.normalizedSize.width*3+'" alt="'+escape(s.id)+' normalized atlas"></article>').join('')+'</html>';
 const checkerHtml=cutouts.length?'<h2>Cutout alpha and outline review</h2><p>Native isolated objects composited over a checker before 3× nearest-neighbor display. Check the actual alpha outline, baseline and source-fit record; no background paint was added to production PNGs.</p><img src="cutout-alpha-checker.png" alt="Stone bridge and mountain cutouts on a checkerboard">':'';
 await fs.writeFile(path.join(reviewRoot,'index.html'),html.replace('<h2>Atlas registration</h2>',checkerHtml+'<h2>Atlas registration</h2>'));
 console.log('Exported '+assets.size+' candidate native assets from '+sourceCount+' preserved masters ('+plans.length+' atlas/crop definitions); '+assemblyRecords.length+' adjacency assemblies. No game files modified.');
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1});
