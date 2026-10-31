from PIL import Image,ImageDraw
from pathlib import Path
import json,hashlib,numpy as np
from scipy import ndimage
B=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'); C=B/'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026'; R=C/'raw'; O=C/'images'
H=json.load(open('/workspace/scratch/equipment-dark-eight-stairs-successor-handoff-20261026.json'))
TARGET_IDS=['early-arenas-arena-stone-stairs-up','early-arenas-arena-stone-stairs-down','masquerade-white-marble-stairs-up','masquerade-white-marble-stairs-down']
V1=json.load(open(C/'masquerade-early-candidates-v1.json'))
V1PATH={a['asset_id']:C/a['candidate_path'] for a in V1['assets']}
AT=R/'stair-endfaces-atlas-v4.png'; AT_SHA=hashlib.sha256(AT.read_bytes()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bb(im):return im.convert('RGBA').getchannel('A').point(lambda q:255 if q>=64 else 0).getbbox()
# Full-atlas alpha isolation; all 4 complete major components are retained, with extent outside nominal row separator.
im=Image.open(AT).convert('RGBA'); alpha=np.array(im.getchannel('A'))>=64; labels,n=ndimage.label(alpha,structure=np.ones((3,3),bool)); counts=np.bincount(labels.ravel()); slices=ndimage.find_objects(labels)
comps=[]
for i in range(1,n+1):
 if counts[i]>5000:
  s=slices[i-1]; box=(s[1].start,s[0].start,s[1].stop,s[0].stop); comps.append((box,int(counts[i])))
comps.sort(key=lambda x:(x[0][1],x[0][0]))
if len(comps)!=4: raise ValueError(f'Expected four major full-atlas silhouettes, got {comps}')
# Output cells are arranged Early FRONT/REAR in row1, Masquerade FRONT/REAR in row2.
compmap={'early-front':comps[0][0],'early-rear':comps[1][0],'masq-front':comps[2][0],'masq-rear':comps[3][0]}
rec=json.load(open(R/'stair-endfaces-request-v4.json')); prompt=rec['prompt_text']
rec['generated_atlas_sha256']=AT_SHA;rec['geometry_guide_sha256']=sha(R/'stairs-endface-ink-front-guide-v1.png');rec['prompt_sha256']=hashlib.sha256(prompt.encode()).hexdigest();json.dump(rec,open(R/'stair-endfaces-request-v4.json','w'),indent=2)
assets=[];records=[]
for family,ids in [('early',['early-arenas-arena-stone-stairs-up','early-arenas-arena-stone-stairs-down']),('masq',['masquerade-white-marble-stairs-up','masquerade-white-marble-stairs-down'])]:
 for oid in ids:
  obj=next(o for o in H['objects'] if o['object_id']==oid); assert sha(obj['source']['path'])==obj['source']['sha256']
  for v in obj['views']: assert sha(obj['views'][v]['path'])==obj['views'][v]['sha256']
  tw=bb(Image.open(obj['views']['top']['path'])); target_x=tw[2]-tw[0]
  sideheights=[]
  for side in ['right','left']:
   sidepath=V1PATH[oid+'.'+side] if family=='early' else Path(obj['views'][side]['path'])
   q=bb(Image.open(sidepath));sideheights.append(q[3]-q[1])
  target_z=round(sum(sideheights)/len(sideheights))
  for v in ['front','rear']:
   key=('early' if family=='early' else 'masq')+'-'+v; box=comps[0 if family=='early' and v=='front' else 1 if family=='early' else 2 if v=='front' else 3][0]
   part=im.crop(box); rw,rh=part.size
   # One isotropic balance between plan width and full side elevation Z extents.
   scale=((target_x/rw)*(target_z/rh))**0.5
   size=(round(rw*scale),round(rh*scale)); part=part.resize(size,Image.Resampling.NEAREST)
   canvas=Image.new('RGBA',(256,256),(0,0,0,0)); offset=((256-size[0])//2,(256-size[1])//2);canvas.alpha_composite(part,offset)
   out=O/f'{oid}.{v}.v2.png';canvas.save(out)
   asset={'asset_id':oid+'.'+v,'object_id':oid,'view':v,'candidate_path':'images/'+out.name,'sha256':sha(out),'width':256,'height':256,'anchor_px':[128,128],
     'provenance':{'method':'generated','source_image':str(Path(obj['source']['path']).relative_to(B)),'source_sha256':obj['source']['sha256'],'generated_atlas_path':str(AT.relative_to(B)),'generated_atlas_sha256':AT_SHA,'generation_request_path':str((R/'stair-endfaces-request-v4.json').relative_to(B)),'generation_request_sha256':sha(R/'stair-endfaces-request-v4.json'),'prompt_sha256':rec['prompt_sha256'],'geometry_guide':{'path':str((R/'stairs-endface-ink-front-guide-v1.png').relative_to(B)),'sha256':rec['geometry_guide_sha256'],'role':'geometry template only; no guide pixels in output'},'notes':'Inferred end/back support surfaces; same-family UP/DOWN endpoint appearance shared as symmetric geometry; source-specific palette retained.'},
     'normalization':{'alpha_isolation':'largest connected RGBA component in full atlas, alpha>=64','raw_alpha_bbox_global_xyxy':list(box),'raw_component_pixel_count':next(n for b,n in comps if b==box),'raw_size_px':[rw,rh],'target_world_x_px':target_x,'target_world_z_px':target_z,'uniform_scale':scale,'normalized_size_px':list(size),'offset_px':list(offset),'resampling':'NEAREST'}}
   assets.append(asset);records.append({'asset_id':asset['asset_id'],'global_bbox':list(box),'target_xz':[target_x,target_z],'scale':scale,'size':list(size),'sha256':asset['sha256']})
manifest={'created_at':'2026-10-26','scope':'book-tiles/dungeon-after-dark','assignment':'candidate-only; Page sole reviewer; Dark sole installer','batch':'equipment-dark-stairs-endfaces-v2','assets':assets,'normalization_records':records,'source_bindings':{}}
for oid in TARGET_IDS:
 obj=next(o for o in H['objects'] if o['object_id']==oid)
 manifest['source_bindings'][oid]={'source':{'path':str(Path(obj['source']['path']).relative_to(B)),'sha256':obj['source']['sha256']},'base_views':{v:{'path':str(Path(x['path']).relative_to(B)),'sha256':x['sha256']} for v,x in obj['views'].items()},'affected_views':['front','rear']}
mp=C/'masquerade-early-endfaces-v2-candidate.json';json.dump(manifest,open(mp,'w'),indent=2)
# Full contacts show source+current six at row1 and source+candidate six at row2.
for oid in TARGET_IDS:
 obj=next(o for o in H['objects'] if o['object_id']==oid)
 current=[]; candidate=[]
 source=Image.open(obj['source']['path']).convert('RGBA'); source.thumbnail((200,200),Image.Resampling.NEAREST)
 current.append(('SOURCE',source)); candidate.append(('SOURCE',source))
 for v in ['front','top','right','left','bottom','rear']:
  cur=Image.open(obj['views'][v]['path']).convert('RGBA')
  cand=Image.open(O/f'{oid}.{v}.v2.png').convert('RGBA') if v in ['front','rear'] else cur.copy()
  cur.thumbnail((200,200),Image.Resampling.NEAREST);cand.thumbnail((200,200),Image.Resampling.NEAREST)
  current.append((v+' current',cur));candidate.append((v+(' v2' if v in ['front','rear'] else ' kept'),cand))
 contact=Image.new('RGBA',(7*224,2*236),(238,238,238,255));d=ImageDraw.Draw(contact)
 for row,panels in enumerate([current,candidate]):
  for i,(label,im2) in enumerate(panels):
   x=i*224+(224-im2.width)//2;y=row*236+26+(200-im2.height)//2
   contact.alpha_composite(im2,(x,y));d.text((i*224+4,row*236+5),label,fill=(0,0,0,255))
 cp=C/f'{oid}-endfaces-v2-source-current-candidate-contact.png';contact.save(cp)
print(mp,sha(mp),len(assets))
for oid in TARGET_IDS:print(C/f'{oid}-endfaces-v2-source-current-candidate-contact.png')
for x in records: print(x['asset_id'],x['normalized_size_px'] if 'normalized_size_px' in x else x['size'])
