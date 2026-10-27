#!/usr/bin/env python3
"""Exact replay for final focused curb landmark candidates; v3 accepted bytes are reused."""
from PIL import Image,ImageDraw
import numpy as np
from scipy import ndimage
import json,hashlib,os
PACK='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'; BASE=PACK+'/reusable/views-additional'; CAND=BASE+'/candidates/equipment-dark-six-ground-platforms-20261026'
HAND='/workspace/scratch/equipment-dark-six-ground-platforms-handoff-20261026.json'; HSHA='322d4973ff94801647c5094eda70c11347a20325b66dd0f61c62c4ccff7eb0d9'
REVIEW='/workspace/scratch/page-equipment-ground-platforms-v3-candidate-review.json'; RSHA='21c12d78f1d91b1a46f54b8be849e94cef680c1af63802640c6dd0ea0ed5f3d6'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def cropmain(path,cols,rows,idx):
 im=Image.open(path).convert('RGBA');w,h=im.size;x0=round((idx%cols)*w/cols);x1=round(((idx%cols)+1)*w/cols);y0=round((idx//cols)*h/rows);y1=round(((idx//cols)+1)*h/rows)
 c=im.crop((x0,y0,x1,y1));a=np.asarray(c)[:,:,3];lab,n=ndimage.label(a>=64,structure=np.ones((3,3),dtype=np.uint8));sizes=np.bincount(lab.ravel());sizes[0]=0
 if not sizes.max():raise ValueError('empty generated cell')
 k=int(sizes.argmax());mask=ndimage.binary_dilation(lab==k,structure=np.ones((3,3),dtype=bool));arr=np.asarray(c).copy();arr[:,:,3]=np.where(mask,a,0).astype('uint8');cc=Image.fromarray(arr,'RGBA');bb=cc.getchannel('A').point(lambda x:255 if x>=64 else 0).getbbox();ys,xs=np.where(lab==k)
 comps=[]
 for j in range(1,n+1):
  yy,xx=np.where(lab==j)
  if len(xx):comps.append({'label':j,'alpha64_pixels':int(len(xx)),'bbox_global':[x0+int(xx.min()),y0+int(yy.min()),x0+int(xx.max())+1,y0+int(yy.max())+1]})
 return cc.crop(bb),[x0+bb[0],y0+bb[1],x0+bb[2],y0+bb[3]],[x0,y0,x1,y1],sorted(comps,key=lambda z:z['alpha64_pixels'],reverse=True)
def norm(crop,mw,mh,up=False):
 w,h=crop.size;s=min(mw/w,mh/h) if up else min(mw/w,mh/h,1.0);nw=round(w*s);nh=round(h*s);z=crop.resize((nw,nh),Image.Resampling.NEAREST);xy=((256-nw)//2,(256-nh)//2);o=Image.new('RGBA',(256,256),(0,0,0,0));o.alpha_composite(z,xy);return o,s,[nw,nh],xy
assert sha(HAND)==HSHA and sha(REVIEW)==RSHA
hand=json.load(open(HAND));objs={x['object_id']:x for x in hand['objects']};v3=json.load(open(CAND+'/candidate-manifest-v3.json'));v3sets={x['object_id']:x for x in v3['sets']}
manifest={'candidate_id':'equipment-dark-six-ground-platforms-v5','candidate_only':True,'scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_equipment','reviewer':'page_inventory','installer':'views_dark_books','handoff_path':HAND,'handoff_sha256':HSHA,'prior_review_path':REVIEW,'prior_review_sha256':RSHA,'current_source_six_proof_path':'/tmp/page-qa-ground-v3-and-ramp-installed-20261026-01.png.json','current_source_six_proof_sha256':'d7ff413fdf458ab8b0229a5801a654bfef331c2d2fc8acbb542f6bf493eed895','normalizer_path':'reusable/views-additional/candidates/equipment-dark-six-ground-platforms-20261026/raw/prepare_ground_candidates_v5.py','sets':[]}
updates={
 'over-city-city-cobblestone-corner-transition':('corner-landmark-atlas-v4.png',3,1,['front','right','left'],180,74,{'front':'overcity-corner-request-v4.json','right':'overcity-corner-request-v4.json','left':'overcity-corner-request-v4.json'}),
 'over-city-city-cobblestone-edge-transition':('edge-landmark-atlas-v4.png',3,1,['right','left'],180,74,{'right':'overcity-edge-request-v4.json','left':'overcity-edge-request-v4.json'}),
}
reqs={
 'corner-landmark-atlas-v4.png':'overcity-corner-request-v4.json',
 'edge-landmark-atlas-v4.png':'overcity-edge-request-v4.json',
 'edge-front-atlas-v5.png':'overcity-edge-front-request-v5.json',
 'civic-front-atlas-v4.png':'civic-front-request-v5.json'}
for oid in v3sets:
 e=json.loads(json.dumps(v3sets[oid]));o=objs[oid]
 # Ensure unchanged activation guards are still exact.
 assert sha(o['source']['path'])==o['source']['sha256']
 for v in ('front','top','right','left','bottom','rear'):
  live=sha(o['views'][v]['path']); original=o['views'][v]['sha256']; installed=v3sets[oid]['candidates'].get(v,{}).get('sha256')
  assert live==original or live==installed,(oid,v,'unexpected live hash',live)
  e['base_current_views'][v]['sha256']=live
 if oid in updates:
  rawname,cols,rows,views,mw,mh,reqmap=updates[oid];raw=CAND+'/raw/'+rawname; rsha=sha(raw)
  for i,v in enumerate(views):
   cellidx=(1 if v=='right' else 2) if oid=='over-city-city-cobblestone-edge-transition' else i
   cr,bb,cb,comps=cropmain(raw,cols,rows,cellidx);out,s,sz,xy=norm(cr,mw,mh)
   dest=CAND+'/images/'+oid+'.'+v+'.candidate-v5.png';out.save(dest,optimize=False);req=CAND+'/raw/'+reqmap[v]
   e['candidates'][v]={'path':dest,'sha256':sha(dest),'method':'generated-atlas-main-component','generated_atlas':raw,'generated_atlas_sha256':rsha,'request_path':req,'request_sha256':sha(req),'cell_index':cellidx,'cell_grid':[cols,rows],'cell_order':views,'nominal_cell_global_bbox':cb,'selected_component_alpha64_bbox_global':bb,'components_alpha64_in_cell':comps,'normalization':{'alpha_threshold':64,'selection':'largest 8-connected component, attached antialias fringe by 1px mask dilation','filter':'NEAREST','uniform_scale':s,'resized_dimensions':sz,'canvas':[256,256],'anchor_px':[128,128],'placement_xy':xy}}
  # Edge FRONT is a separate single-view atlas without the full tan curb bank.
  if oid=='over-city-city-cobblestone-edge-transition':
   raw=CAND+'/raw/edge-front-atlas-v5.png';cr,bb,cb,comps=cropmain(raw,1,1,0);out,s,sz,xy=norm(cr,180,55);dest=CAND+'/images/'+oid+'.front.candidate-v5.png';out.save(dest,optimize=False);req=CAND+'/raw/'+reqs['edge-front-atlas-v5.png']
   e['candidates']['front']={'path':dest,'sha256':sha(dest),'method':'generated-single-view-main-component','generated_atlas':raw,'generated_atlas_sha256':sha(raw),'request_path':req,'request_sha256':sha(req),'selected_component_alpha64_bbox_global':bb,'nominal_cell_global_bbox':cb,'components_alpha64_in_cell':comps,'normalization':{'alpha_threshold':64,'selection':'largest 8-connected component with 1px antialias dilation','filter':'NEAREST','uniform_scale':s,'resized_dimensions':sz,'canvas':[256,256],'anchor_px':[128,128],'placement_xy':xy}}
  e['notes']='Only Page-held curb landmark directions replaced; prior accepted candidate bytes retained.'
 elif oid=='over-city-venues-civic-stone-tile-corner-transition':
  raw=CAND+'/raw/civic-front-atlas-v4.png';cr,bb,cb,comps=cropmain(raw,1,1,0);out,s,sz,xy=norm(cr,180,74);dest=CAND+'/images/'+oid+'.front.candidate-v5.png';out.save(dest,optimize=False);req=CAND+'/raw/'+reqs['civic-front-atlas-v4.png']
  e['candidates']['front']={'path':dest,'sha256':sha(dest),'method':'generated-single-view-main-component','generated_atlas':raw,'generated_atlas_sha256':sha(raw),'request_path':req,'request_sha256':sha(req),'selected_component_alpha64_bbox_global':bb,'nominal_cell_global_bbox':cb,'components_alpha64_in_cell':comps,'normalization':{'alpha_threshold':64,'selection':'largest 8-connected component with 1px antialias dilation','filter':'NEAREST','uniform_scale':s,'resized_dimensions':sz,'canvas':[256,256],'anchor_px':[128,128],'placement_xy':xy}}
  e['notes']='Replaces only FRONT with low U-opening projection; other five view candidates from prior accepted base are unchanged.'
 manifest['sets'].append(e)
# Candidate contacts from immutable base six, with candidate directions substituted.
contacts=[]
for e in manifest['sets']:
 oid=e['object_id'];o=objs[oid];ims=[Image.open(o['source']['path']).convert('RGBA')]
 for v in ('front','top','right','left','bottom','rear'):
  p=e['candidates'][v]['path'] if v in e['candidates'] else o['views'][v]['path'];ims.append(Image.open(p).convert('RGBA'))
 contacts.append((oid,ims))
mp=CAND+'/candidate-manifest-v5.json';open(mp,'w').write(json.dumps(manifest,indent=2)+'\n')
tw=170;th=170;lh=24;pad=8;rh=th+lh+pad;sheet=Image.new('RGBA',(pad+7*(tw+pad),pad+len(contacts)*rh),(34,34,40,255));dr=ImageDraw.Draw(sheet)
for ri,(oid,ims) in enumerate(contacts):
 y=pad+ri*rh;dr.text((pad,y),oid,fill='white');ty=y+lh
 for ci,im in enumerate(ims):
  x=pad+ci*(tw+pad);im.thumbnail((tw,th),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+(tw-im.width)//2,ty+(th-im.height)//2));dr.text((x,ty+th),['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR'][ci],fill='white')
cp=CAND+'/contacts/source-six-candidate-v5.png';sheet.save(cp)
rec={'candidate_manifest_path':os.path.relpath(mp,PACK),'candidate_manifest_sha256':sha(mp),'contact_path':cp,'contact_sha256':sha(cp),'candidate_only':True,'install_authorized':False}
rp=CAND+'/contact-receipt-v5.json';open(rp,'w').write(json.dumps(rec,indent=2)+'\n')
print(json.dumps({'manifest':mp,'manifest_sha256':sha(mp),'contact':cp,'contact_sha256':sha(cp),'sets':len(manifest['sets']),'directions':sum(len(x['candidates']) for x in manifest['sets'])},indent=2))
