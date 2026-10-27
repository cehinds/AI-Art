from PIL import Image,ImageDraw
import numpy as np,json,hashlib
from pathlib import Path
from scipy import ndimage
B=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/reusable/views-additional/candidates/equipment-dark-last-seven-fixtures-20261026')
proofpath=Path('/tmp/equipment-last7-held3-after-focused5-install-v2.png.json'); proof=json.load(open(proofpath));current={o['object_id']:o for o in proof['objects']}
base=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'); source_paths={
'over-city-venues-painted-civic-stone-wall-northeast':base/'over-city-venues/components/over-city-venues-painted-civic-stone-wall-northeast.png',
'race-circuits-race-descent-checkpoint':base/'race-circuits/components/race-circuits-race-descent-checkpoint.png',
'safe-services-restaurant-dining-booth':base/'safe-services/components/safe-services-restaurant-dining-booth.png'}
jobs=[
('over-city-venues-painted-civic-stone-wall-northeast','top','civic-top-v5.png',0,1,202,'civic-top-v5.json'),
('race-circuits-race-descent-checkpoint','rear','checkpoint-rear-v4.png',0,1,190,'checkpoint-rear-v4.json'),
('safe-services-restaurant-dining-booth','right','booth-sides-v3.png',0,2,126,'booth-sides-v3.json'),
('safe-services-restaurant-dining-booth','left','booth-sides-v3.png',1,2,126,'booth-sides-v3.json'),
('safe-services-restaurant-dining-booth','bottom','booth-bottom-v4.png',0,1,193,'booth-bottom-v4.json')]
records=[]
for oid,v,rawname,idx,ncols,target,requestname in jobs:
 rp=B/'raw'/rawname;a=np.asarray(Image.open(rp).convert('RGBA'));h,w=a.shape[:2];x0=round(w*idx/ncols);x1=round(w*(idx+1)/ncols);cell=a[:,x0:x1]
 lab,n=ndimage.label(cell[:,:,3]>=64,structure=np.ones((3,3),dtype=np.uint8)); comps=[]
 for k,sl in enumerate(ndimage.find_objects(lab),1):
  if sl is None:continue
  area=int((lab[sl]==k).sum());bb=(sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)
  if area>=20:comps.append((area,k,bb))
 comps.sort(reverse=True);area0,k0,b0=comps[0];keep=[]
 for ar,k,bb in comps:
  bx0,by0,bx1,by1=bb;ax0,ay0,ax1,ay1=b0;gx=max(0,ax0-bx1,bx0-ax1);gy=max(0,ay0-by1,by0-ay1)
  if k==k0 or(gx<=16 and gy<=16):keep.append(k)
 mask=np.isin(lab,keep);ys,xs=np.where(mask);box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];crop=cell[box[1]:box[3],box[0]:box[2]].copy();crop[~mask[box[1]:box[3],box[0]:box[2]]]=0;im=Image.fromarray(crop,'RGBA');scale=target/max(im.size);nw=round(im.width*scale);nh=round(im.height*scale);im=im.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));off=[128-nw//2,128-nh//2];canvas.alpha_composite(im,tuple(off));out=B/'images'/f'{oid}.{v}.focused-v4.png';canvas.save(out)
 req=B/'requests'/requestname
 records.append({'object_id':oid,'view':v,'candidate_path':str(out),'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'raw_path':str(rp),'raw_sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),'request_path':str(req),'request_sha256':hashlib.sha256(req.read_bytes()).hexdigest(),'cell_xyxy':[x0,0,x1,h],'alpha_threshold':64,'connectivity':8,'kept_components':[{'area':ar,'bbox_local_xyxy':list(bb)}for ar,k,bb in comps if k in keep],'crop_local_xyxy':box,'uniform_scale':scale,'resized_wh':[nw,nh],'offset_xy':off,'canvas':[256,256],'anchor_px':[128,128]})
# use canonical source/current-six proof; replace held directions only in contact, preserving installed siblings
for oid in sorted(current):
 o=current[oid];lookup={(r['object_id'],r['view']):r for r in records};tiledata=[]
 # Current proof gives paths/sha. Absolute paths for all views are resolvable from root.
 for label,path in [('SOURCE',source_paths[oid])]+[(v,base/'reusable/views-additional/images'/f'{oid}.{v}.png') for v in ['front','top','right','left','bottom','rear']]:
  key=(oid,label.lower());p=Path(lookup[key]['candidate_path']) if key in lookup else path
  tiledata.append((label,p))
 cw,ch=240,288;board=Image.new('RGB',(cw*7,ch),(236,236,236));d=ImageDraw.Draw(board)
 for i,(lab,p) in enumerate(tiledata):
  d.text((i*cw+5,4),lab.upper()+(' CAND' if (oid,lab.lower()) in lookup else ''),fill=(0,0,0));im=Image.open(p).convert('RGBA');im.thumbnail((cw-14,ch-34),Image.Resampling.NEAREST);bg=Image.new('RGBA',im.size,(255,255,255,255));bg.alpha_composite(im);board.paste(bg.convert('RGB'),(i*cw+(cw-im.width)//2,24+(ch-34-im.height)//2))
 cpath=B/'contacts'/f'{oid}-focused-v4-source-current-six.png';board.save(cpath)
# write recipe/helper and versioned manifest
recipe={'source_six_proof_path':str(proofpath),'source_six_proof_sha256':hashlib.sha256(proofpath.read_bytes()).hexdigest(),'assets':records}
rp=B/'last7-focused-v4-recipe.json';rp.write_text(json.dumps(recipe,indent=2)+'\n')
helper=B/'extract_last7_focused_v4.py';helper.write_text(Path('/tmp/stage_last7_v4.py').read_text());hs=hashlib.sha256(helper.read_bytes()).hexdigest()
# ensure manifest tracks current source/siblings from canonical proof
objects=[]
handoff=json.load(open('/workspace/scratch/equipment-dark-last-seven-fixtures-handoff-20261026.json')); ho={x['object_id']:x for x in handoff['objects']}
for oid in sorted(set(r['object_id']for r in records)):
 o=current[oid];h=ho[oid]; cand={}
 for r in [x for x in records if x['object_id']==oid]:
  v=r['view'];cand[v]={'path':r['candidate_path'],'sha256':r['candidate_sha256'],'method':'generated-atlas-cell-component-isotropic-nearest','raw_path':r['raw_path'],'raw_sha256':r['raw_sha256'],'request_path':r['request_path'],'request_sha256':r['request_sha256'],'normalizer_path':str(helper),'normalizer_sha256':hs}
 objects.append({'object_id':oid,'source':h['source'],'base_current_views':o['views'],'affected_views':list(cand),'candidates':cand,'candidate_contact_path':str(B/'contacts'/f'{oid}-focused-v4-source-current-six.png'),'candidate_contact_sha256':hashlib.sha256((B/'contacts'/f'{oid}-focused-v4-source-current-six.png').read_bytes()).hexdigest()})
manifest={'candidate_id':'equipment-dark-last-seven-held-five-v4','candidate_only':True,'scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_equipment','reviewer':'root','installer':'views_dark_books','handoff_path':'/workspace/scratch/equipment-dark-last-seven-fixtures-handoff-20261026.json','handoff_sha256':hashlib.sha256(Path('/workspace/scratch/equipment-dark-last-seven-fixtures-handoff-20261026.json').read_bytes()).hexdigest(),'activation_path':'/workspace/scratch/page-equipment-last-seven-activation-20261026.json','activation_sha256':hashlib.sha256(Path('/workspace/scratch/page-equipment-last-seven-activation-20261026.json').read_bytes()).hexdigest(),'source_six_proof_path':str(proofpath),'source_six_proof_sha256':hashlib.sha256(proofpath.read_bytes()).hexdigest(),'recipe_path':str(rp),'recipe_sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),'normalizer_path':str(helper),'normalizer_sha256':hs,'sets':objects}
mp=B/'candidate-manifest-last7-held-five-v4.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'manifest':str(mp),'sha':hashlib.sha256(mp.read_bytes()).hexdigest(),'recipe_sha':hashlib.sha256(rp.read_bytes()).hexdigest(),'outputs':[(r['object_id'],r['view'],r['resized_wh'],r['candidate_sha256'])for r in records],'contacts':[(s['object_id'],s['candidate_contact_path'],s['candidate_contact_sha256'])for s in objects]},indent=2))
