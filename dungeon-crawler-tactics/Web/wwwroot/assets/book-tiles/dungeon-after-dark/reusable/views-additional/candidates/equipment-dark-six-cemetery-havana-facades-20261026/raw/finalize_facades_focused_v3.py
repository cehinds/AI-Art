#!/usr/bin/env python3
"""Merge focused, current-hash-guarded facade candidates into a review contact."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
C=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/reusable/views-additional/candidates/equipment-dark-six-cemetery-havana-facades-20261026')
HAND=Path('/workspace/scratch/equipment-dark-six-cemetery-havana-facades-handoff-20261026.json');PROOF=Path('/tmp/page-qa-equipment-next-six-facades-native-current-20261026-01.png.json');PROV=C/'raw/focused-generation-provenance-v1.json';YREQ=C/'raw/yemaya-bottom-focused-v3-request.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(HAND)=='ce6fe313909743b156fb8393813248891c76d5d1b0ceaa3663005c45df6451a5'
assert sha(PROOF)=='2c0ca874a6382719f25aee04a40352005f4602d1ed7d28d15d82d182184ee7c1'
proof=json.loads(PROOF.read_text());objs={o['object_id']:o for o in proof['objects']};d=json.loads((C/'candidate-manifest-focused-v2.json').read_text());d['candidate_id']='equipment-dark-six-cemetery-havana-facades-focused-v3';d['source_six_proof_path']=str(PROOF);d['source_six_proof_sha256']=sha(PROOF);d['generation_provenance_path']=str(PROV);d['generation_provenance_sha256']=sha(PROV);d['normalizer_path']='reusable/views-additional/candidates/equipment-dark-six-cemetery-havana-facades-20261026/raw/finalize_facades_focused_v3.py';d['normalizer_sha256']=sha(__file__)
# Refresh every set against the current proof and reject any source/view drift.
for e in d['sets']:
 o=objs[e['object_id']];assert sha(o['source']['path'])==o['source']['sha256']==e['source_sha256']
 e['base_current_views']={v:{'path':a['path'],'sha256':a['sha256']} for v,a in o['views'].items()};e['base_proof_path']=str(PROOF);e['base_proof_sha256']=sha(PROOF)
 for v,a in o['views'].items():assert sha(a['path'])==a['sha256']
 for v,a in e['candidates'].items():assert sha(a['path'])==a['sha256']
# Add Yemaya bottom candidate to its existing TOP-only row.
e=next(x for x in d['sets'] if x['object_id']=='ghost-cemetery-temple-of-yemaya-shrine');o=objs[e['object_id']]
raw=C/'raw/ghost-cemetery-temple-of-yemaya-shrine.bottom.focused-v3.png';assert sha(raw)==json.loads(YREQ.read_text())['response']['raw_sha256']
# Crop/bounds and common scale used by extractor.
from PIL import Image
from scipy import ndimage
import numpy as np
im=Image.open(raw).convert('RGBA');lab,n=ndimage.label(np.asarray(im.getchannel('A'))>=64,structure=np.ones((3,3),np.uint8));parts=[]
for i in range(1,n+1):
 y,x=np.where(lab==i)
 if len(x)>1000:parts.append((len(x),i,(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1))))
assert len(parts)==1;area,label,bbox=parts[0];mask=lab==label;dil=ndimage.binary_dilation(mask,structure=np.ones((5,5),bool),iterations=1);y,x=np.where(dil);cropbox=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1));front=Image.open(o['views']['front']['path']).convert('RGBA').getchannel('A').getbbox();tw=front[2]-front[0];scale=tw/(bbox[2]-bbox[0]);crop=im.crop(cropbox);arr=np.array(crop);arr[~dil[cropbox[1]:cropbox[3],cropbox[0]:cropbox[2]],3]=0;crop=Image.fromarray(arr,'RGBA');dims=(round(crop.width*scale),round(crop.height*scale));xy=((256-dims[0])//2,(256-dims[1])//2);out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(crop.resize(dims,Image.Resampling.NEAREST),xy);path=C/'images/ghost-cemetery-temple-of-yemaya-shrine.bottom.candidate-focused-v3.png';out.save(path,optimize=False)
e['candidates']['bottom']={'path':str(path),'sha256':sha(path),'method':'imagegen-single-view-component-extraction-uniform-front-scale','raw_path':str(raw),'raw_sha256':sha(raw),'raw_alpha_threshold':64,'raw_component_bbox_xyxy':list(bbox),'raw_component_area':area,'mask_dilation_8connected_iterations':1,'mask_dilation_footprint':[5,5],'crop_bbox_xyxy':list(cropbox),'normalization':{'filter':'NEAREST','uniform_scale':scale,'target_current_front_alpha_width':tw,'raw_component_width':bbox[2]-bbox[0],'resized_dimensions':list(dims),'canvas':[256,256],'anchor_px':[128,128],'placement_xy':list(xy)},'notes':'Below-view illustration inferred from accepted target TOP outline and source; only underside stone/basin support visible.'}
e['affected_views']=sorted(set(e['affected_views']+['bottom']),key=['front','top','right','left','bottom','rear'].index)
# Rebuild current source+six contact for the four objects.
W=180;H=180;pad=8;header=28;rh=H+header+pad;sheet=Image.new('RGBA',(pad+7*(W+pad),pad+len(d['sets'])*rh),(36,36,42,255));draw=ImageDraw.Draw(sheet);labs=['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR']
for r,e in enumerate(d['sets']):
 o=objs[e['object_id']];y=pad+r*rh;draw.text((pad,y),e['object_id'],fill='white');y+=header
 ims=[Image.open(o['source']['path']).convert('RGBA')]
 for v in ['front','top','right','left','bottom','rear']:
  im=Image.open(e['candidates'][v]['path']).convert('RGBA') if v in e['candidates'] else Image.open(o['views'][v]['path']).convert('RGBA');ims.append(im)
 for c,im in enumerate(ims):
  x=pad+c*(W+pad);im.thumbnail((W,H),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+(W-im.width)//2,y+(H-im.height)//2));draw.text((x,y+H+2),labs[c],fill='white')
contact=C/'contacts/focused-candidate-v3.png';sheet.save(contact);d['contact_path']=str(contact);d['contact_sha256']=sha(contact);mp=C/'candidate-manifest-focused-v3.json';mp.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'manifest':str(mp),'manifest_sha256':sha(mp),'contact':str(contact),'contact_sha256':sha(contact),'candidate_directions':sum(len(x['affected_views']) for x in d['sets'])},indent=2))
