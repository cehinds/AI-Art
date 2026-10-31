from PIL import Image,ImageDraw
from pathlib import Path
import json,hashlib,numpy as np
from scipy import ndimage
B=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark');C=B/'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026';R=C/'raw';O=C/'images';H=json.load(open('/workspace/scratch/equipment-dark-eight-stairs-successor-handoff-20261026.json'))
V1=json.load(open(C/'masquerade-early-candidates-v1.json'));V1PATH={a['asset_id']:C/a['candidate_path'] for a in V1['assets']}
TARGET_IDS=['early-arenas-arena-stone-stairs-up','early-arenas-arena-stone-stairs-down','masquerade-white-marble-stairs-up','masquerade-white-marble-stairs-down']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bbox(im):return im.convert('RGBA').getchannel('A').point(lambda q:255 if q>=64 else 0).getbbox()
def big_components(path):
 im=Image.open(path).convert('RGBA'); a=np.array(im.getchannel('A'))>=64;lab,n=ndimage.label(a,structure=np.ones((3,3),bool));counts=np.bincount(lab.ravel());sl=ndimage.find_objects(lab);ls=[]
 for i in range(1,n+1):
  if counts[i]>5000:
   s=sl[i-1];ls.append({'bbox':(s[1].start,s[0].start,s[1].stop,s[0].stop),'count':int(counts[i])})
 ls.sort(key=lambda z:(z['bbox'][1],z['bbox'][0]));
 if len(ls)!=4:raise ValueError(f'{path}: expected four complete objects, found {ls}')
 return im,ls

sets=[('early','early-arenas-endfaces-atlas-v3.png','early-arenas-endfaces-request-v3.json',0,1),('masq','masquerade-endfaces-atlas-v5.png','masquerade-endfaces-request-v5.json',2,3)]
assets=[];records=[]
for family,atlasname,reqname,idxF,idxR in sets:
 raw=R/atlasname;im,cs=big_components(raw);req=json.load(open(R/reqname));atlas_sha=sha(raw)
 for oid in [x for x in TARGET_IDS if x.startswith('early-arenas' if family=='early' else 'masquerade')]:
  obj=next(o for o in H['objects'] if o['object_id']==oid)
  assert sha(obj['source']['path'])==obj['source']['sha256']
  for view,x in obj['views'].items(): assert sha(x['path'])==x['sha256']
  top=bbox(Image.open(obj['views']['top']['path']));tx=top[2]-top[0]
  zh=[]
  for side in ['right','left']:
   p=V1PATH[oid+'.'+side] if family=='early' else Path(obj['views'][side]['path'])
   b=bbox(Image.open(p));zh.append(b[3]-b[1])
  tz=round(sum(zh)/2)
  for view,ci in [('front',idxF),('rear',idxR)]:
   comp=cs[ci];box=comp['bbox'];part=im.crop(box);rw,rh=part.size
   scale=((tx/rw)*(tz/rh))**0.5;sz=(round(rw*scale),round(rh*scale));part=part.resize(sz,Image.Resampling.NEAREST)
   can=Image.new('RGBA',(256,256),(0,0,0,0));off=((256-sz[0])//2,(256-sz[1])//2);can.alpha_composite(part,off)
   out=O/f'{oid}.{view}.v3.png';can.save(out)
   a={'asset_id':oid+'.'+view,'object_id':oid,'view':view,'candidate_path':'images/'+out.name,'sha256':sha(out),'width':256,'height':256,'anchor_px':[128,128],
    'provenance':{'method':'generated','source_image':str(Path(obj['source']['path']).relative_to(B)),'source_sha256':obj['source']['sha256'],'generated_atlas_path':str(raw.relative_to(B)),'generated_atlas_sha256':atlas_sha,'generation_request_path':str((R/reqname).relative_to(B)),'generation_request_sha256':sha(R/reqname),'prompt_sha256':req['prompt_sha256'],'notes':'Full-height, constant-width end support inferred orthographic art. UP/DOWN end faces share the symmetric family image; ascent direction remains in retained approved side elevations.'},
    'normalization':{'alpha_isolation':'4 largest connected components in entire raw atlas, alpha>=64','raw_alpha_bbox_global_xyxy':list(box),'raw_component_pixels':comp['count'],'raw_size_px':[rw,rh],'world_targets_x_z_px':[tx,tz],'uniform_scale':scale,'normalized_size_px':list(sz),'offset_px':list(off),'resampling':'NEAREST'}}
   assets.append(a);records.append({'asset_id':a['asset_id'],'bbox':list(box),'pixels':comp['count'],'target_xz':[tx,tz],'scale':scale,'normalized_size':list(sz),'sha256':a['sha256']})
manifest={'created_at':'2026-10-26','scope':'book-tiles/dungeon-after-dark','assignment':'candidate-only; Page sole reviewer; Dark sole installer','batch':'equipment-dark-stairs-endfaces-v3','assets':assets,'normalization_records':records,'source_bindings':{}}
for oid in TARGET_IDS:
 obj=next(o for o in H['objects'] if o['object_id']==oid);manifest['source_bindings'][oid]={'source':{'path':str(Path(obj['source']['path']).relative_to(B)),'sha256':obj['source']['sha256']},'base_views':{v:{'path':str(Path(x['path']).relative_to(B)),'sha256':x['sha256']} for v,x in obj['views'].items()},'affected_views':['front','rear']}
mp=C/'masquerade-early-endfaces-v3-candidate.json';json.dump(manifest,open(mp,'w'),indent=2)
# Source + current six in first row; complete proposed six in second row.
for oid in TARGET_IDS:
 obj=next(o for o in H['objects'] if o['object_id']==oid); panels=[]
 src=Image.open(obj['source']['path']).convert('RGBA');src.thumbnail((200,200),Image.Resampling.NEAREST);panels.append(('SOURCE',src))
 currow=[];newrow=[]
 for v in ['front','top','right','left','bottom','rear']:
  a=Image.open(obj['views'][v]['path']).convert('RGBA');a.thumbnail((200,200),Image.Resampling.NEAREST);currow.append((v+' current',a))
  p=O/f'{oid}.{v}.v3.png' if v in ('front','rear') else Path(obj['views'][v]['path'])
  a=Image.open(p).convert('RGBA');a.thumbnail((200,200),Image.Resampling.NEAREST);newrow.append((v+(' v3' if v in ('front','rear') else ' kept'),a))
 contact=Image.new('RGBA',(7*224,2*236),(238,238,238,255));d=ImageDraw.Draw(contact)
 for i,(lab,imx) in enumerate([panels[0]]+currow):
  contact.alpha_composite(imx,(i*224+(224-imx.width)//2,26+(200-imx.height)//2));d.text((i*224+4,5),lab,fill=(0,0,0,255))
 for i,(lab,imx) in enumerate([panels[0]]+newrow):
  contact.alpha_composite(imx,(i*224+(224-imx.width)//2,262+26+(200-imx.height)//2));d.text((i*224+4,5+236),lab,fill=(0,0,0,255))
 contact.save(C/f'{oid}-endfaces-v3-source-current-candidate-contact.png')
print('manifest',mp,sha(mp),'assets',len(assets))
for x in records:print(x['asset_id'],x['normalized_size'])
