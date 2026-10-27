#!/usr/bin/env python3
"""Extract target atlas components and normalize with per-object shared scale."""
from pathlib import Path
from PIL import Image,ImageDraw
from scipy import ndimage
import numpy as np,json,hashlib
PACK=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
C=PACK/'reusable/views-additional/candidates/equipment-dark-six-cemetery-havana-facades-20261026'
HAND=Path('/workspace/scratch/equipment-dark-six-cemetery-havana-facades-handoff-20261026.json'); PROOF=Path('/tmp/page-qa-equipment-next-six-facades-native-current-20261026-01.png.json')
ATLAS=C/'raw/batch02-atlas.png';REQ=C/'raw/batch02-request.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(HAND)=='ce6fe313909743b156fb8393813248891c76d5d1b0ceaa3663005c45df6451a5'
assert sha(PROOF)=='2c0ca874a6382719f25aee04a40352005f4602d1ed7d28d15d82d182184ee7c1'
assert sha(ATLAS)==json.loads(REQ.read_text())['response']['sha256']
hand=json.loads(HAND.read_text()); proof=json.loads(PROOF.read_text());objs={o['object_id']:o for o in proof['objects']};ids=[x['object_id'] for x in hand['objects'][3:]]
raw=Image.open(ATLAS).convert('RGBA'); alpha=np.asarray(raw.getchannel('A'));labels,n=ndimage.label(alpha>=64,structure=np.ones((3,3),np.uint8)); comps=[]
for i in range(1,n+1):
 y,x=np.where(labels==i)
 if len(x)>=3000: comps.append({'label':i,'area':len(x),'bbox':[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)],'centroid':[float(x.mean()),float(y.mean())]})
assert len(comps)==18,len(comps)
xc={'front':150,'top':438,'right':670,'left':880,'bottom':1115,'rear':1380};yc=[255,565,840]
def choose(row,v):
 ranked=sorted(comps,key=lambda c:(c['centroid'][0]-xc[v])**2+(c['centroid'][1]-yc[row])**2);c=ranked[0];assert abs(c['centroid'][0]-xc[v])<100 and abs(c['centroid'][1]-yc[row])<110,(row,v,c);return c
manifest={'schema_version':1,'candidate_id':'equipment-dark-six-cemetery-havana-facades-batch02-v1','scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_equipment','reviewer':'page_inventory','installer':'views_dark_books','candidate_only':True,'handoff_path':str(HAND),'handoff_sha256':sha(HAND),'source_six_proof_path':str(PROOF),'source_six_proof_sha256':sha(PROOF),'atlas_path':str(ATLAS),'atlas_sha256':sha(ATLAS),'request_path':str(REQ),'request_sha256':sha(REQ),'extractor_path':'reusable/views-additional/candidates/equipment-dark-six-cemetery-havana-facades-20261026/raw/extract_batch02_v1.py','sets':[],'held_directions':[]}
for row,oid in enumerate(ids):
 o=objs[oid];assert sha(o['source']['path'])==o['source']['sha256']
 for v,x in o['views'].items():assert sha(x['path'])==x['sha256']
 fr=choose(row,'front'); raw_fw=fr['bbox'][2]-fr['bbox'][0]; fa=Image.open(o['views']['front']['path']).convert('RGBA').getchannel('A').getbbox(); target_fw=fa[2]-fa[0];scale=target_fw/raw_fw
 s={'object_id':oid,'source':o['source'],'source_sha256':o['source']['sha256'],'base_current_views':{v:{'path':x['path'],'sha256':x['sha256']} for v,x in o['views'].items()},'base_proof_path':str(PROOF),'base_proof_sha256':sha(PROOF),'affected_views':[],'candidates':{},'notes':'Imagegen candidate; identity/materials follow native source; hidden surfaces inferred.'}
 targets=['top','bottom'] if row==0 else ['top']
 for v in targets:
  comp=choose(row,v); mask=labels==comp['label'];dil=ndimage.binary_dilation(mask,structure=np.ones((5,5),bool),iterations=1);yy,xx=np.where(dil);bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];crop=raw.crop(tuple(bbox)); arr=np.array(crop);arr[~dil[bbox[1]:bbox[3],bbox[0]:bbox[2]],3]=0;crop=Image.fromarray(arr,'RGBA');dims=(round(crop.width*scale),round(crop.height*scale));res=crop.resize(dims,Image.Resampling.NEAREST);xy=((256-dims[0])//2,(256-dims[1])//2);out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(res,xy)
  path=C/'images'/f'{oid}.{v}.candidate-batch02-v1.png';out.save(path,optimize=False)
  s['candidates'][v]={'path':str(path),'sha256':sha(path),'method':'imagegen-atlas-component-extraction-uniform-row-scale','raw_component_label':comp['label'],'raw_component_bbox_xyxy':comp['bbox'],'raw_component_centroid':comp['centroid'],'raw_alpha_threshold':64,'mask_dilation_8connected_iterations':1,'mask_dilation_footprint':[5,5],'crop_bbox_xyxy':bbox,'normalization':{'filter':'NEAREST','uniform_scale':scale,'source_row_front_component_width':raw_fw,'target_current_front_alpha_width':target_fw,'resized_dimensions':list(dims),'canvas':[256,256],'anchor_px':[128,128],'placement_xy':list(xy)},'notes':'Generated inferred principal view; exact raw component crop and uniform scaling are recorded.'}
  s['affected_views'].append(v)
  # Self-hold broad or unsupported candidate directions identified on raw screenshot.
  if oid=='ghost-cemetery-temple-of-yemaya-shrine':
   manifest['held_directions'].append({'object_id':oid,'view':v,'status':'candidate-rejected-self-review','reason':'Raw atlas retains a near-square circular/front-panel footprint rather than the shallow source-supported shrine depth; not offered for install.'})
  if oid=='ghost-havana-el-capitolio-entrance-facade' and v=='top':
   manifest['held_directions'].append({'object_id':oid,'view':v,'status':'candidate-rejected-self-review','reason':'Raw overhead candidate is almost square and carries a broad frontal building footprint; source side view requires a shallow-Y plan. Not offered for install.'})
  if oid=='ghost-havana-old-havana-arcade-frontage' and v=='top':
   manifest['held_directions'].append({'object_id':oid,'view':v,'status':'candidate-rejected-self-review','reason':'Raw overhead candidate is too deep relative to accepted side thickness for the shallow facade roof/coping. Not offered for install.'})
 manifest['sets'].append(s)
# Contact = source/current six, with only self-reviewed proposals in the target slots; held rows are marked and current art retained.
W=170;H=170;pad=8;rh=H+34;sheet=Image.new('RGBA',(pad+7*(W+pad),pad+len(ids)*rh),(35,35,40,255));d=ImageDraw.Draw(sheet);labs=['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR']
for r,s in enumerate(manifest['sets']):
 o=objs[s['object_id']];y=pad+r*rh;d.text((pad,y),s['object_id'],fill='white');y+=18
 for c,im in enumerate([Image.open(o['source']['path']).convert('RGBA')]+[Image.open(o['views'][v]['path']).convert('RGBA') for v in ['front','top','right','left','bottom','rear']]):
  v=['front','top','right','left','bottom','rear'][c-1] if c else None
  prop=next((h for h in manifest['held_directions'] if h['object_id']==s['object_id'] and h['view']==v),None) if v else None
  if v and v in s['candidates'] and not prop: im=Image.open(s['candidates'][v]['path']).convert('RGBA')
  x=pad+c*(W+pad);im.thumbnail((W,H),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+(W-im.width)//2,y+(H-im.height)//2));d.text((x,y+H+2),labs[c]+('*' if prop else ''),fill='white')
contact=C/'contacts/batch02-candidate-v1.png';sheet.save(contact);manifest['contact_path']=str(contact);manifest['contact_sha256']=sha(contact);out=C/'candidate-manifest-batch02-v1.json';out.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'manifest':str(out),'manifest_sha256':sha(out),'contact':str(contact),'contact_sha256':sha(contact),'candidate_directions':sum(len(s['affected_views']) for s in manifest['sets']),'accepted_for_review':sum(len(s['candidates']) for s in manifest['sets'])-len(manifest['held_directions']),'held':manifest['held_directions']},indent=2))
