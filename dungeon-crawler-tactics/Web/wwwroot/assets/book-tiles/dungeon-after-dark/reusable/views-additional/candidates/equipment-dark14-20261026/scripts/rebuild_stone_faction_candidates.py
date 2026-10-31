from PIL import Image,ImageDraw
import numpy as np,json,os,hashlib,shutil
from scipy import ndimage
ROOT='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'
BASE=ROOT+'/reusable/views-additional/candidates/equipment-dark14-20261026'
D=json.load(open('/workspace/scratch/equipment-dark14-candidate-handoff-20261026.json'))
sha=lambda p:hashlib.sha256(open(p,'rb').read()).hexdigest()
views=['front','right','left','rear']
tasks=[('stone','/workspace/generated_images/exec-2ed4158d-7876-4392-a82e-7794feb7afff.png','stone-corners-batch01-atlas.png',D['objects'][2:4],['front','right','left','rear']),('faction','/workspace/generated_images/exec-72285e6c-93f7-43ab-b43c-9f56e9efa631.png','faction-corners-batch01-atlas.png',D['objects'][4:6],['front','right','left','rear'])]
for name,gen,rawname,obs,order in tasks:
 rawpath=BASE+'/raw/'+rawname;shutil.copy2(gen,rawpath);im=Image.open(rawpath).convert('RGBA');W,H=im.size;cw=W//4;ch=H//2
 prompt_path=BASE+'/prompts/'+name+'-corners-batch01.prompt.json';prompt=json.load(open(prompt_path))['prompt']
 # gather portable references and exact hashes
 refpaths=[BASE+'/references/common-corner-silhouette-guide.png',BASE+'/references/'+name+'-approved-guides.png',BASE+'/references/'+name+'-corner-sources.png']
 refs=[{'path':'references/'+os.path.basename(p),'sha256':sha(p)} for p in refpaths]
 rec={'batch':name+'-corners-batch01','tool':'image_gen.imagegen','tool_request_id':None,'generated_path':gen,'staged_raw_path':'raw/'+rawname,'raw_sha256':sha(rawpath),'raw_dimensions':[W,H],'prompt_path':'../prompts/'+name+'-corners-batch01.prompt.json','prompt_text':prompt,'input_refs':refs,'layout':'4 columns x 2 rows; outer then inner; columns front,right,left,rear','component_policy':'full-atlas alpha threshold >=64/255, 4-connected components; assign by centroid to each logical cell, keep largest component by pixel area, use complete global component bounds even if crossing cell boundary','qa':'Visually reviewed raw atlas. All four cells show broad wall elevations rather than single posts or L elevations. Main world-Z height is consistent within object; source-specific banners/braces remain. Candidate pending Page current-hash review.'}
 # recheck inputs from handoff, no live write
 for o in obs:
  for e in [o['source'],*o['current_six'].values()]:
   p=e['path'] if os.path.isabs(e['path']) else ROOT+'/'+e['path'];assert sha(p)==e['sha256'],('stale',o['object_id'],p)
 alpha=np.asarray(im.getchannel('A'))>=64;lab,n=ndimage.label(alpha);sizes=np.bincount(lab.ravel());sizes[0]=0;centers=ndimage.center_of_mass(alpha,lab,index=np.arange(1,len(sizes)))
 rows=[];components={};bboxdims=[]
 for row,o in enumerate(obs):
  chosen={};
  for col,v in enumerate(order):
   poss=[]
   for k,(cy,cx) in enumerate(centers,1):
    if col*cw<=cx<(col+1)*cw and row*ch<=cy<(row+1)*ch:poss.append((int(sizes[k]),k))
   assert poss,(name,row,col)
   area,k=max(poss);yy,xx=np.where(lab==k);box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));mask=lab==k
   whole=Image.new('RGBA',im.size,(0,0,0,0));whole.paste(im,(0,0));whole.putalpha(Image.fromarray((mask*255).astype('uint8')));crop=whole.crop(box)
   chosen[v]=crop;components[v]={'component_label':int(k),'area_pixels':area,'bbox_global_xyxy':list(box),'nominal_cell_xyxy':[col*cw,row*ch,(col+1)*cw,(row+1)*ch],'crosses_cell':box[0]<col*cw or box[2]>(col+1)*cw or box[1]<row*ch or box[3]>(row+1)*ch}
  # shared scale calibrated isotropically to existing front/rear overall dimensions
  srcboxes=[]
  for v in ('front','rear'):
   bb=Image.open(o['current_six'][v]['path']).convert('RGBA').getchannel('A').getbbox();srcboxes.append((bb[2]-bb[0],bb[3]-bb[1]))
  targetw=float(np.mean([q[0] for q in srcboxes]));targeth=float(np.mean([q[1] for q in srcboxes]))
  raww=float(np.mean([chosen[v].width for v in ('front','rear')]));rawh=float(np.mean([chosen[v].height for v in ('front','rear')]))
  scale=((targetw/raww)*(targeth/rawh))**.5
  candidate_views={}
  for v,crop in chosen.items():
   nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale));crop=crop.resize((nw,nh),Image.Resampling.NEAREST);out=Image.new('RGBA',(256,256),(0,0,0,0));ox=(256-nw)//2;oy=(256-nh)//2;out.alpha_composite(crop,(ox,oy));f=o['object_id']+'.'+v+'.png';p=BASE+'/images/'+f;out.save(p)
   entry={'asset_id':o['object_id']+'.'+v,'object_id':o['object_id'],'view':v,'candidate_path':'images/'+f,'sha256':sha(p),'width':256,'height':256,'anchor_px':[128,128],'provenance':{'method':'generated','source_image':o['source']['path'].replace(ROOT+'/',''),'source_sha256':o['source']['sha256'],'generated_atlas_path':'raw/'+rawname,'generated_atlas_sha256':sha(rawpath),'geometry_guides':refs[:2],'notes':'Hidden surfaces inferred; not recovered source pixels.'},'normalization':{'raw_component':components[v],'shared_isotropic_scale':scale,'target_source_front_rear_extent_mean_px':[targetw,targeth],'resampling':'NEAREST','offset_px':[ox,oy]}}
   rows.append(entry);candidate_views[v]={'asset_id':entry['asset_id'],'path':entry['candidate_path'],'sha256':entry['sha256']}
  def relcurrent(mp):
   return {v:{'path':e['path'].replace(ROOT+'/',''),'sha256':e['sha256']} for v,e in mp.items()}
  # make top/bottom preserved references to current base
  views_full={v:({'path':relcurrent(o['current_six'])[v]['path'],'sha256':relcurrent(o['current_six'])[v]['sha256'],'source':'preserved current base'} if v in ('top','bottom') else candidate_views[v]) for v in ['front','top','right','left','bottom','rear']}
  rowset={'object_id':o['object_id'],'affected_views':views,'preserve_views':['top','bottom'],'source':{'path':o['source']['path'].replace(ROOT+'/',''),'sha256':o['source']['sha256']},'base_current_six':relcurrent(o['current_six']),'candidate_views':candidate_views,'full_candidate_contact_views':views_full,'status':'candidate-only-pending-Page-review','shared_isotropic_scale':scale,'anchor_px':[128,128],'cell_qa':components}
  rows[-1]['row_object_id']=o['object_id']
  # maintain object result
  if 'objects' not in rec:rec['objects']=[]
  rec['objects'].append(rowset)
 rec['assets']=rows
 open(BASE+'/raw/'+name+'-corners-batch01-request.json','w').write(json.dumps(rec,indent=2)+'\n')
 cand={'created_at':'2026-10-26','scope':'book-tiles/dungeon-after-dark','assignment':'candidate-only; Page sole reviewer, Dark sole installer','batch':name+'-corners-batch01','raw_manifest':'raw/'+name+'-corners-batch01-request.json','assets':rows,'objects':rec['objects']}
 open(BASE+'/'+name+'-corners-batch01-candidates.json','w').write(json.dumps(cand,indent=2)+'\n')
 # candidate source+six contact; top/bottom preserve current base views
 contact=Image.new('RGBA',(7*256,2*300),(246,246,246,255));d=ImageDraw.Draw(contact)
 for row,o in enumerate(obs):
  paths=[o['source']['path']]+[ (ROOT+'/'+o['current_six'][v]['path'] if v in ('top','bottom') else BASE+'/'+rec['objects'][row]['candidate_views'][v]['path']) for v in ['front','top','right','left','bottom','rear']]
  labels=['source','front','top','right','left','bottom','rear']
  for col,(p,l) in enumerate(zip(paths,labels)):
   if l in ('top','bottom'): p=o['current_six'][l]['path']
   z=Image.open(p).convert('RGBA');z.thumbnail((244,244));contact.alpha_composite(z,(col*256+(256-z.width)//2,row*300+28+(244-z.height)//2));d.text((col*256+4,row*300+4),l,fill=(0,0,0,255))
 cp=BASE+'/'+name+'-corners-batch01-source-candidate-contact.png';contact.save(cp)
 print(name,'rawsha',sha(rawpath),'contactsha',sha(cp),'manifest',BASE+'/'+name+'-corners-batch01-candidates.json')
 for x in rec['objects']: print(' ',x['object_id'],'scale',x['shared_isotropic_scale'],'component bboxes',[(v,x['cell_qa'][v]['bbox_global_xyxy']) for v in views])
