'use strict';
const {fs,path,hash,assert,root,outputRoot,reviewRoot,normalize,alphaStats}=require('./common.cjs');
async function pngs(directory){const result=[];for(const e of await fs.readdir(directory,{withFileTypes:true})){const file=path.join(directory,e.name);if(e.isDirectory())result.push(...await pngs(file));else if(e.name.endsWith('.png'))result.push(file);}return result;}
async function main(){
 const cfgBytes=await fs.readFile(path.join(__dirname,'kit.json')),cfg=JSON.parse(cfgBytes);
 const manifest=JSON.parse(await fs.readFile(path.join(outputRoot,'manifest.json'),'utf8'));
 assert(manifest.configSha256===hash(cfgBytes),'Export is stale against kit.json');
 if(cfg.generationPrompts)assert(manifest.generationPromptRecord?.file===cfg.generationPrompts&&manifest.generationPromptRecord.sha256===hash(await fs.readFile(path.resolve(root,cfg.generationPrompts))),'Generation prompt provenance record changed');
 assert(cfg.sheets.length>0,'No generated source sheets');let checked=0;
 for(const sheet of cfg.sheets){
  const plan=await normalize(sheet),saved=manifest.sheets.find(s=>s.id===sheet.id);
  assert(saved&&saved.sourceSha256===plan.sourceSha256,'Generated master changed: '+sheet.id);
  assert(JSON.stringify(saved.crop)===JSON.stringify(plan.crop)&&saved.normalizedSha256===hash(plan.normalized),'Atlas group registration changed: '+sheet.id);
  assert(hash(await fs.readFile(path.join(reviewRoot,'atlases',sheet.id+'-native.png')))===saved.normalizedSha256,'Normalized atlas review differs: '+sheet.id);
  for(const r of plan.records){
   const key=sheet.id+'/'+r.definition.id,record=manifest.assets.find(a=>a.key===key);
   assert(record&&record.sha256===hash(r.bytes),'Native cell is not reproducible from shared atlas transform: '+key);
   assert(hash(await fs.readFile(path.join(root,record.file)))===record.sha256,'Production bytes differ: '+key);
   if(r.sourceCutout){
    assert(JSON.stringify(record.sourceCellRect)===JSON.stringify(r.sourceCellRect)&&JSON.stringify(record.sourceCutout)===JSON.stringify(r.sourceCutout)&&JSON.stringify(record.nativePlacement)===JSON.stringify(r.placement),'Cutout registration differs: '+key);
    assert(JSON.stringify(record.alpha)===JSON.stringify(await alphaStats(r.bytes)),'Native alpha/bbox differs: '+key);
    assert(record.alpha.transparent>0&&record.alpha.atLeast128>0,'Cutout needs visible art and transparent canvas: '+key);
   }
   const metadata=await fs.readFile(path.join(root,record.file)+'.meta','utf8');assert(/^guid: [a-f0-9]{32}$/m.test(metadata),'Missing stable metadata GUID: '+key);
   for(const side of ['north','east','south','west'])assert(record.ports?.[side]===r.definition.ports[side],'Port contract differs: '+key+' '+side);
   checked++;
  }
 }
 assert(manifest.assets.length===checked,'Unexpected/unregistered native assets');
 const registered=new Set(manifest.assets.map(a=>path.resolve(root,a.file)));
 for(const file of await pngs(outputRoot))assert(registered.has(file),'Unregistered production PNG retained for review: '+path.relative(root,file));
 const guids=new Set();for(const a of manifest.assets){const m=(await fs.readFile(path.join(root,a.file)+'.meta','utf8')).match(/^guid: ([a-f0-9]{32})$/m)[1];assert(!guids.has(m),'Duplicate GUID');guids.add(m);}
 for(const assembly of manifest.reviewAssemblies||[])await fs.access(path.join(reviewRoot,assembly.file));
 await fs.access(path.join(reviewRoot,'contact-sheet.png'));await fs.access(path.join(reviewRoot,'index.html'));await fs.access(path.join(reviewRoot,'adjacency-audit.json'));
 const sourceCount=new Set(cfg.sheets.map(s=>s.source)).size;
 if(cfg.sheets.some(s=>s.kind==='cutout-atlas'))await fs.access(path.join(reviewRoot,'cutout-alpha-checker.png'));
 console.log('PASS: '+checked+' native assets reproduce from '+sourceCount+' unchanged generated masters ('+cfg.sheets.length+' atlas/crop definitions); hashes, declared atlas/cutout registration, alpha/bboxes, ports, metadata GUIDs and review inventory checked. Visual adjacency and seamlessness remain separate review gates.');
}
main().catch(error=>{console.error(error.stack||error);process.exitCode=1});
