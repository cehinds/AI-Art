#!/usr/bin/env python3
"""Extract full alpha components from the generated atlas, normalize using shared row scale, and make candidate-only proof."""
from pathlib import Path
from PIL import Image, ImageDraw
from scipy import ndimage
import numpy as np, json, hashlib
PACK=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
C=PACK/'reusable/views-additional/candidates/equipment-dark-six-cemetery-havana-facades-20261026'
HAND=Path('/workspace/scratch/equipment-dark-six-cemetery-havana-facades-handoff-20261026.json')
PROOF=Path('/tmp/page-qa-equipment-next-six-facades-native-current-20261026-01.png.json')
ATLAS=C/'raw/batch01-atlas.png'; REQ=C/'raw/batch01-request.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(HAND)=='ce6fe313909743b156fb8393813248891c76d5d1b0ceaa3663005c45df6451a5'
assert sha(PROOF)=='2c0ca874a6382719f25aee04a40352005f4602d1ed7d28d15d82d182184ee7c1'
assert sha(ATLAS)==json.loads(REQ.read_text())['response']['sha256']
hand=json.loads(HAND.read_text()); proof=json.loads(PROOF.read_text()); objects={x['object_id']:x for x in proof['objects']}
ids=[x['object_id'] for x in hand['objects'][:3]]
raw=Image.open(ATLAS).convert('RGBA'); a=np.asarray(raw.getchannel('A')); labels,n=ndimage.label(a>=64,structure=np.ones((3,3),np.uint8))
components=[]
for lab in range(1,n+1):
 yy,xx=np.where(labels==lab); area=len(xx)
 if area>=3000:
  components.append({'label':lab,'area':area,'bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'centroid':[float(xx.mean()),float(yy.mean())]})
assert len(components)==18, (len(components),components)
# Centers are measured from the complete connected objects in the atlas, not nominal grid cells.
centers={'front':195,'top':505,'right':790,'left':1005,'bottom':1273,'rear':1582}
rows=[180,470,715]
def choose(r,v):
 target=(centers[v],rows[r]); ranked=sorted(components,key=lambda c:(c['centroid'][0]-target[0])**2+(c['centroid'][1]-target[1])**2)
 c=ranked[0]; assert abs(c['centroid'][0]-target[0])<100 and abs(c['centroid'][1]-target[1])<100,(r,v,c)
 assert len(ranked)==1 or ranked[1]['label']!=c['label']
 return c
manifest={'schema_version':1,'candidate_id':'equipment-dark-six-cemetery-havana-facades-batch01-v1','scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_equipment','reviewer':'page_inventory','installer':'views_dark_books','candidate_only':True,'handoff_path':str(HAND),'handoff_sha256':sha(HAND),'source_six_proof_path':str(PROOF),'source_six_proof_sha256':sha(PROOF),'atlas_path':str(ATLAS),'atlas_sha256':sha(ATLAS),'request_path':str(REQ),'request_sha256':sha(REQ),'extractor_path':'reusable/views-additional/candidates/equipment-dark-six-cemetery-havana-facades-20261026/raw/extract_batch01_v1.py','sets':[],'held_directions':[]}
for ri,oid in enumerate(ids):
 o=objects[oid]; assert sha(o['source']['path'])==o['source']['sha256']
 for v,x in o['views'].items(): assert sha(x['path'])==x['sha256']
 front=choose(ri,'front'); frontw=front['bbox'][2]-front['bbox'][0]
 fbb=o['views']['front']['path']; fw=Image.open(fbb).convert('RGBA').getchannel('A').getbbox()[2]-Image.open(fbb).convert('RGBA').getchannel('A').getbbox()[0]
 scale=fw/frontw
 entry={'object_id':oid,'source':o['source'],'source_sha256':o['source']['sha256'],'base_current_views':{v:{'path':x['path'],'sha256':x['sha256']} for v,x in o['views'].items()},'base_proof_path':str(PROOF),'base_proof_sha256':sha(PROOF),'affected_views':[],'candidates':{},'notes':'Generated principal-plane views are inferred illustrations; source and accepted current views remain the identity/geometry references.'}
 for view in ('top','bottom'):
  comp=choose(ri,view)
  # Retain low-alpha edge pixels within a two-pixel dilation around its own alpha>=64 component only.
  mask=(labels==comp['label']); dil=ndimage.binary_dilation(mask,structure=np.ones((5,5),bool),iterations=1)
  yy,xx=np.where(dil); bx0,by0,bx1,by1=int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)
  crop=raw.crop((bx0,by0,bx1,by1)); cm=np.asarray(crop.getchannel('A')); dm=dil[by0:by1,bx0:bx1]
  ca=np.array(crop);ca[~dm,3]=0;crop=Image.fromarray(ca,'RGBA')
  dims=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
  resized=crop.resize(dims,Image.Resampling.NEAREST); xy=((256-dims[0])//2,(256-dims[1])//2)
  out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(resized,xy)
  path=C/'images'/f'{oid}.{view}.candidate-batch01-v1.png';out.save(path,optimize=False)
  entry['candidates'][view]={'path':str(path),'sha256':sha(path),'method':'imagegen-atlas-component-extraction-uniform-row-scale','raw_component_label':comp['label'],'raw_component_bbox_xyxy':comp['bbox'],'raw_component_centroid':comp['centroid'],'raw_alpha_threshold':64,'mask_dilation_8connected_iterations':1,'mask_dilation_footprint':[5,5],'crop_bbox_xyxy': [bx0,by0,bx1,by1],'normalization':{'filter':'NEAREST','uniform_scale':scale,'source_row_front_component_width':frontw,'target_current_front_alpha_width':fw,'resized_dimensions':list(dims),'canvas':[256,256],'anchor_px':[128,128],'placement_xy':list(xy)},'notes':'Generated view; hidden surfaces conservatively inferred from source and approved geometry guidance.'}
  if view!='bottom' or oid!='ghost-cemetery-spirit-box-trap':entry['affected_views'].append(view)
  else:manifest['held_directions'].append({'object_id':oid,'view':'bottom','status':'candidate-rejected-self-review','reason':'Generated atlas cell is a broad square full-face plate rather than the narrow axial underside required by the upright panel geometry.'})
 manifest['sets'].append(entry)
# Contact uses current source+six; only staged candidate directions occupy their matching slots.
rowsheet=len(ids);cw=170;ch=170;lh=22;pad=8;rowh=ch+lh+pad
sheet=Image.new('RGBA',(pad+7*(cw+pad),pad+rowsheet*rowh),(35,35,40,255));draw=ImageDraw.Draw(sheet)
for r,entry in enumerate(manifest['sets']):
 o=objects[entry['object_id']]; y=pad+r*rowh;draw.text((pad,y),entry['object_id'],fill='white');y+=lh
 ims=[Image.open(o['source']['path']).convert('RGBA')]
 for v in ('front','top','right','left','bottom','rear'):
  cand=entry['candidates'].get(v)
  ims.append(Image.open(cand['path']).convert('RGBA') if cand and v in entry['affected_views'] else Image.open(o['views'][v]['path']).convert('RGBA'))
 for c,im in enumerate(ims):
  x=pad+c*(cw+pad);im.thumbnail((cw,ch),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+(cw-im.width)//2,y+(ch-im.height)//2));draw.text((x,y+ch+2),['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR'][c],fill='white')
contact=C/'contacts/batch01-candidate-v1.png';sheet.save(contact);manifest['contact_path']=str(contact);manifest['contact_sha256']=sha(contact)
out=C/'candidate-manifest-batch01-v1.json';out.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'manifest':str(out),'manifest_sha256':sha(out),'contact':str(contact),'contact_sha256':sha(contact),'sets':len(ids),'candidate_directions':sum(len(x['affected_views']) for x in manifest['sets']),'held':manifest['held_directions']},indent=2))
