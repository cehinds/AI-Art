const fs=require('fs'),path=require('path');
const sharp=require(process.env.SHARP_MODULE || 'sharp');
const out=__dirname;
const groups={attack:[0,1,2,3],counterattack:[4,5,6,7],magicAttack:[8,9,10],rangedWeaponAttack:[11,12],sweep:[13,14,15,16],block:[17,18]};
const times={attack:[70,60,60,70],counterattack:[70,60,60,70],magicAttack:[90,80,90],rangedWeaponAttack:[130,130],sweep:[70,60,60,70],block:[130,130]};
const labels=['attack-01','attack-02','attack-03','attack-04','counterattack-01','counterattack-02','counterattack-03','counterattack-04','magic-01','magic-02','magic-03','ranged-01','ranged-02','sweep-01','sweep-02','sweep-03','sweep-04','block-01','block-02','wounded','hit','defeated','preparing','idle'];
const aliases={unknown:'idle',default:'idle',attacking:'attack-03','wind-up':'preparing',defending:'block-01',countering:'counterattack-03',casting:'magic-01',buffing:'magic-01',hurt:'wounded','status-effect':'wounded',prone:'defeated',sleep:'defeated'};
(async()=>{
 const {validateProject}=await import(require('node:url').pathToFileURL(path.join(__dirname,'tooling/core.mjs')).href);
 const inventory=JSON.parse(fs.readFileSync(out+'/inventory.json'));const prompts=JSON.parse(fs.readFileSync(out+'/prompts.json'));
 const old=fs.existsSync(out+'/manifest.json')?JSON.parse(fs.readFileSync(out+'/manifest.json')):{enemies:[]};
 const manifest={schemaVersion:1,sourceCommit:inventory.sourceCommit,facing:'toward viewer, front three-quarter angled slightly screen-left',scope:'art authoring only',canvas:[512,512],sourceFrameResolution:'See each enemy nativeCellSize; 512 canvas exports may be upscaled.',timingBasis:'260 ms per action; source poseAnimator.json defaultPlayMs 260',canonicalCount:inventory.canonicalCount,aliases,enemies:[],notes:['Each pose is independently painted. Projects expose whole-pose artwork layers, not invented anatomical rigs.','Automatic alpha/boundary checks do not constitute anatomy or playback approval.','Left-facing sheets in sheets/ are superseded by user direction and excluded.']};
 for(const e of inventory.roster){
  const id=e.id,file=out+'/front-sheets/'+id+'.png';const record={id,name:e.name,act:e.act,adaptation:prompts.adaptations[id],actions:{},stances:{},status:'missing',review:'not reviewed'};manifest.enemies.push(record);
  if(!fs.existsSync(file))continue;
  const hash=require('crypto').createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  const overrideHashes=Object.fromEntries(labels.filter(p=>fs.existsSync(out+'/overrides/'+id+'/'+p+'.png')).map(p=>[p,require('crypto').createHash('sha256').update(fs.readFileSync(out+'/overrides/'+id+'/'+p+'.png')).digest('hex')]));
  const cached=old.enemies.find(x=>x.id===id&&x.sourceHash===hash&&x.exportVersion===4&&JSON.stringify(x.overrideHashes||{})===JSON.stringify(overrideHashes));if(cached && labels.every(p=>fs.existsSync(out+'/frames/'+id+'/'+p+'.png'))){Object.assign(record,cached);continue;}
  record.sourceHash=hash;record.exportVersion=4;record.overrideHashes=overrideHashes;
  const metadata=await sharp(file).metadata();record.nativeCellSize=[metadata.width/6,metadata.height/4];record.hasAlpha=metadata.hasAlpha;record.status='generated-needs-review';
  const raw=await sharp(file).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  const W=raw.info.width,H=raw.info.height;
  const yProjection=Array(H).fill(0);for(let y=0;y<H;y++)for(let x=0;x<W;x++)if(raw.data[(y*W+x)*4+3]>20)yProjection[y]++;
  function cuts(projection,count){const len=projection.length,step=len/count,result=[0];for(let i=1;i<count;i++){let best=Math.round(i*step),score=Infinity;for(let p=Math.max(result.at(-1)+1,Math.round(i*step-step*.45));p<Math.min(len-1,i*step+step*.45);p++){let sum=0;for(let j=-2;j<=2;j++)sum+=projection[Math.max(0,Math.min(len-1,p+j))];let s=sum*1000+Math.abs(p-i*step);if(s<score){score=s;best=p;}}result.push(best);}result.push(len);return result;}
  const ys=cuts(yProjection,4),rects=[];
  for(let row=0;row<4;row++){const xp=Array(W).fill(0);for(let y=ys[row];y<ys[row+1];y++)for(let x=0;x<W;x++)if(raw.data[(y*W+x)*4+3]>20)xp[x]++;const xs=cuts(xp,6);for(let col=0;col<6;col++)rects.push({left:xs[col],top:ys[row],width:xs[col+1]-xs[col],height:ys[row+1]-ys[row]});}
  const bounds=rects.map(r=>{let x0=W,y0=H,x1=0,y1=0;for(let y=r.top;y<r.top+r.height;y++)for(let x=r.left;x<r.left+r.width;x++)if(raw.data[(y*W+x)*4+3]>8){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}return x1>=x0?{left:x0,top:y0,width:x1-x0+1,height:y1-y0+1}:r;});
  const scale=Math.min(448/Math.max(...bounds.map(r=>r.width)),448/Math.max(...bounds.map(r=>r.height)));record.sourceRects=rects;record.contentBounds=bounds;record.commonExportScale=scale;
  const dir=out+'/frames/'+id;fs.mkdirSync(dir,{recursive:true});fs.mkdirSync(out+'/projects',{recursive:true});fs.mkdirSync(out+'/contacts',{recursive:true});
  const project={schemaVersion:1,id,name:e.name+' frontal combat',canvas:{width:512,height:512,origin:[256,480]},assets:{},poses:{},animations:{},queues:{},revisions:[],notes:'Independent painted whole-pose layers. Anatomy/grip review required. '+record.adaptation};
  const cells=[];const quality=[];
  for(let i=0;i<24;i++){
   const rect=rects[i],bound=bounds[i],cw=Math.max(1,Math.round(bound.width*scale)),ch=Math.max(1,Math.round(bound.height*scale));
   const cut=await sharp(file).extract(bound).resize(cw,ch).png().toBuffer();
   let png=await sharp({create:{width:512,height:512,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite([{input:cut,left:Math.round((512-cw)/2),top:480-ch}]).png().toBuffer();
   const override=out+'/overrides/'+id+'/'+labels[i]+'.png';
   if(fs.existsSync(override)){const ob=await sharp(override).trim({background:'#00000000'}).toBuffer();const om=await sharp(ob).metadata();let oh=ch;if(id==='eclipseCantor')oh=Math.round(bounds[23].height*scale);const ow=Math.round(om.width*oh/om.height);png=await sharp({create:{width:512,height:512,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite([{input:await sharp(ob).resize(ow,oh).png().toBuffer(),left:Math.round((512-ow)/2),top:480-oh}]).png().toBuffer();}
   const pose=labels[i],rel='frames/'+id+'/'+pose+'.png';fs.writeFileSync(out+'/'+rel,png);cells.push(png);
   const {data,info}=await sharp(png).ensureAlpha().raw().toBuffer({resolveWithObject:true});let opaque=0,transparent=0,edge=0;
   for(let y=0;y<512;y++)for(let x=0;x<512;x++){let a=data[(y*512+x)*4+3];if(a===0)transparent++;if(a>20){opaque++;if(x<3||x>508||y<3||y>508)edge++;}}
   let sourceEdge=0;for(let y=rect.top;y<rect.top+rect.height;y++)for(let x=rect.left;x<rect.left+rect.width;x++)if((x===rect.left||x===rect.left+rect.width-1||y===rect.top||y===rect.top+rect.height-1)&&raw.data[(y*W+x)*4+3]>20)sourceEdge++;
   quality.push({pose,transparentPixels:transparent,paintedPixels:opaque,boundaryPixels:edge,sourceBoundaryPixels:sourceEdge,override:fs.existsSync(override),check:!metadata.hasAlpha?'NO_ALPHA':sourceEdge>0&&!fs.existsSync(override)?'CHECK_CLIPPING':'clear-boundary'});
   project.assets[pose]={id:pose,name:pose,width:512,height:512,src:'data:image/png;base64,'+png.toString('base64')};
   project.poses[pose]={id:pose,name:pose,group:'Front-facing enemy',gripMode:'released',reviewed:false,layers:[{id:pose+'-paint',name:'Independent painted pose',assetId:pose,role:'body',x:0,y:0,rotation:0,scale:1,opacity:1,pivot:[256,480],visible:true,locked:false,anchors:[]}],bones:[]};
   record.stances[pose]={poseId:pose,path:rel};
  }
  for(const [action,indices] of Object.entries(groups)){const frames=indices.map((n,k)=>({id:id+'-'+action+'-'+(k+1),poseId:labels[n],duration:times[action][k],event:k===Math.floor(indices.length/2)?'impact':'',path:record.stances[labels[n]].path}));record.actions[action]={frames,totalMs:260,status:'generated-needs-review'};project.animations[action]={id:action,name:action,loop:true,frames:frames.map(({path,...frame})=>frame)};}
  project.animations.stances={id:'stances',name:'Stance review',loop:true,frames:[23,22,17,6,8,19,20,21].map(n=>({id:'stance-'+labels[n],poseId:labels[n],duration:600,event:''}))};
  project.queues.review={id:'review',name:'All action and stance review',loop:true,items:Object.keys(project.animations).map(a=>({id:'queue-'+a,animationId:a,repeats:3,pause:300}))};
  validateProject(project);fs.writeFileSync(out+'/projects/'+id+'.rig.json',JSON.stringify(project));record.project='projects/'+id+'.rig.json';record.alphaChecks=quality;
  const layers=[];for(let i=0;i<24;i++){const x=i%6*192,y=Math.floor(i/6)*218;layers.push({input:await sharp(cells[i]).resize(192,192).png().toBuffer(),left:x,top:y});layers.push({input:Buffer.from('<svg width="192" height="26"><text x="6" y="18" fill="white" font-size="13">'+labels[i]+'</text></svg>'),left:x,top:y+192});}
  await sharp({create:{width:1152,height:872,channels:4,background:'#363d49'}}).composite(layers).png().toFile(out+'/contacts/'+id+'.png');record.contact='contacts/'+id+'.png';
 }
 manifest.counts={generated:manifest.enemies.filter(e=>e.status!=='missing').length,missing:manifest.enemies.filter(e=>e.status==='missing').length,reviewApproved:0};
 fs.writeFileSync(out+'/manifest.json',JSON.stringify(manifest,null,2));console.log(JSON.stringify(manifest.counts));
})();
