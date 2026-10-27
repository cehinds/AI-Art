#!/usr/bin/env python3
"""Normalize focused generated views to target front-view scale and create a guarded candidate-only contact."""
from pathlib import Path
from PIL import Image,ImageDraw
from scipy import ndimage
import numpy as np,json,hashlib
PACK=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark');C=PACK/'reusable/views-additional/candidates/equipment-dark-six-cemetery-havana-facades-20261026'
HAND=Path('/workspace/scratch/equipment-dark-six-cemetery-havana-facades-handoff-20261026.json');PROOF=Path('/tmp/page-qa-equipment-next-six-facades-native-current-20261026-01.png.json');PROV=C/'raw/focused-generation-provenance-v1.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(HAND)=='ce6fe313909743b156fb8393813248891c76d5d1b0ceaa3663005c45df6451a5'
assert sha(PROOF)=='2c0ca874a6382719f25aee04a40352005f4602d1ed7d28d15d82d182184ee7c1'
provenance=json.loads(PROV.read_text()); objs={o['object_id']:o for o in json.loads(PROOF.read_text())['objects']}
raws={
'ghost-cemetery-temple-of-yemaya-shrine':('top',C/'raw/ghost-cemetery-temple-of-yemaya-shrine.top.focused-v1.png'),
'ghost-cemetery-spirit-box-trap':('bottom',C/'raw/ghost-cemetery-spirit-box-trap.bottom.focused-v2.png'),
'ghost-havana-el-capitolio-entrance-facade':('top',C/'raw/ghost-havana-el-capitolio-entrance-facade.top.focused-v2.png'),
'ghost-havana-old-havana-arcade-frontage':('top',C/'raw/ghost-havana-old-havana-arcade-frontage.top.focused-v2.png')}
manifest={'schema_version':1,'candidate_id':'equipment-dark-six-cemetery-havana-facades-focused-v2','scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_equipment','reviewer':'page_inventory','installer':'views_dark_books','candidate_only':True,'handoff_path':str(HAND),'handoff_sha256':sha(HAND),'source_six_proof_path':str(PROOF),'source_six_proof_sha256':sha(PROOF),'generation_provenance_path':str(PROV),'generation_provenance_sha256':sha(PROV),'extractor_path':'reusable/views-additional/candidates/equipment-dark-six-cemetery-havana-facades-20261026/raw/extract_focused_candidates_v2.py','sets':[]}
for oid,(view,rawpath) in raws.items():
 o=objs[oid];assert sha(o['source']['path'])==o['source']['sha256']
 for v,x in o['views'].items():assert sha(x['path'])==x['sha256']
 im=Image.open(rawpath).convert('RGBA');a=np.asarray(im.getchannel('A'));labels,n=ndimage.label(a>=64,structure=np.ones((3,3),np.uint8));parts=[]
 for i in range(1,n+1):
  yy,xx=np.where(labels==i)
  if len(xx)>1000:parts.append((len(xx),i,(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))))
 assert len(parts)==1,(oid,parts)
 area,label,bbox=parts[0];mask=labels==label;dil=ndimage.binary_dilation(mask,structure=np.ones((5,5),bool),iterations=1);yy,xx=np.where(dil);cropbox=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));crop=im.crop(cropbox);arr=np.array(crop);arr[~dil[cropbox[1]:cropbox[3],cropbox[0]:cropbox[2]],3]=0;crop=Image.fromarray(arr,'RGBA')
 fb=Image.open(o['views']['front']['path']).convert('RGBA').getchannel('A').getbbox();target_w=fb[2]-fb[0];scale=target_w/(bbox[2]-bbox[0]);dims=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)));res=crop.resize(dims,Image.Resampling.NEAREST);xy=((256-dims[0])//2,(256-dims[1])//2);out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(res,xy)
 outpath=C/'images'/f'{oid}.{view}.candidate-focused-v2.png';out.save(outpath,optimize=False)
 e={'object_id':oid,'source':o['source'],'source_sha256':o['source']['sha256'],'base_current_views':{v:{'path':x['path'],'sha256':x['sha256']} for v,x in o['views'].items()},'base_proof_path':str(PROOF),'base_proof_sha256':sha(PROOF),'affected_views':[view],'candidates':{view:{'path':str(outpath),'sha256':sha(outpath),'method':'imagegen-single-view-component-extraction-uniform-front-scale','raw_path':str(rawpath),'raw_sha256':sha(rawpath),'raw_alpha_threshold':64,'raw_component_bbox_xyxy':list(bbox),'raw_component_area':area,'mask_dilation_8connected_iterations':1,'mask_dilation_footprint':[5,5],'crop_bbox_xyxy':list(cropbox),'normalization':{'filter':'NEAREST','uniform_scale':scale,'target_current_front_alpha_width':target_w,'raw_component_width':bbox[2]-bbox[0],'resized_dimensions':list(dims),'canvas':[256,256],'anchor_px':[128,128],'placement_xy':list(xy)},'notes':'New view is inferred; geometry comes from same-object source/current accepted elevations and explicit axis occlusion.'}},'notes':'Only the listed requested direction is proposed; all other source/current views remain unchanged.'}
 manifest['sets'].append(e)
# readable source+six contact with fixed 6-view columns
cw=180;ch=180;pad=8;head=26;rh=ch+head+pad;sheet=Image.new('RGBA',(pad+7*(cw+pad),pad+len(manifest['sets'])*rh),(36,36,42,255));draw=ImageDraw.Draw(sheet);labs=['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR']
for r,e in enumerate(manifest['sets']):
 o=objs[e['object_id']];y=pad+r*rh;draw.text((pad,y),e['object_id'],fill='white');y+=head
 ims=[Image.open(o['source']['path']).convert('RGBA')]
 for v in ['front','top','right','left','bottom','rear']:
  im=Image.open(e['candidates'][v]['path']).convert('RGBA') if v in e['candidates'] else Image.open(o['views'][v]['path']).convert('RGBA');ims.append(im)
 for c,im in enumerate(ims):
  x=pad+c*(cw+pad);im.thumbnail((cw,ch),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+(cw-im.width)//2,y+(ch-im.height)//2));draw.text((x,y+ch+2),labs[c],fill='white')
contact=C/'contacts/focused-candidate-v2.png';sheet.save(contact);manifest['contact_path']=str(contact);manifest['contact_sha256']=sha(contact)
mp=C/'candidate-manifest-focused-v2.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'manifest':str(mp),'manifest_sha256':sha(mp),'contact':str(contact),'contact_sha256':sha(contact),'items':[{'id':x['object_id'],'view':x['affected_views'][0],'sha':x['candidates'][x['affected_views'][0]]['sha256'],'dims':x['candidates'][x['affected_views'][0]]['normalization']['resized_dimensions']} for x in manifest['sets']]},indent=2))
