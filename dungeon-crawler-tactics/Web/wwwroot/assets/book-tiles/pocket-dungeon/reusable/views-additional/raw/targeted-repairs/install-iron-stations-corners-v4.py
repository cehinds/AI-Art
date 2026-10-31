#!/usr/bin/env python3
"""Replay the Iron Stations v4 flat-elevation atlas, guarded by captured source/view hashes."""
from pathlib import Path
import argparse, hashlib, json, struct
import numpy as np
from PIL import Image
from scipy import ndimage

PACK = Path(__file__).resolve().parents[4]
VIEW_DIR = PACK / 'reusable/views-additional'
INDEX = VIEW_DIR / 'set-index.json'
ATLAS_REL = Path('reusable/views-additional/raw/atlases/iron-stations-corner-v4-rectangular-faces.png')
OBJECTS = {
 'iron-stations-station-tiled-masonry-outer-corner': 0,
 'iron-stations-station-tiled-masonry-inner-corner': 1,
}
CELL_VIEWS = {'front':0,'right':2,'left':3,'rear':5}
EXPECTED = {
 'iron-stations-station-tiled-masonry-outer-corner': {'front':'0f591ff6ee25601cd92bd208febc548a09315ed04f04928dba7549ffc8a13b66','top':'ca3b8f12574648731ab1cbd363b54a367f896cafde620520302dcda5e660b6ab','right':'a627fb648a139811e11f0b85806f1483cad056e08e19f147ccb230c8e482d54e','left':'bacc821b1b85768c7e9c5ff2076ba4972e0c5ed8e296c760e3b5f2ce6cabcff7','bottom':'1e08412d36e0b5164755d95fd73354640698acd192ac55f25053932e79a9df0e','rear':'e8d83ee710b3029a6824c2669e656355f25626c696c7b575e15408b5dbfa4cbf'},
 'iron-stations-station-tiled-masonry-inner-corner': {'front':'16ac4b7b153a9036439c1d30db33fc5aedf5404577d402870fc8dcb0b90812f9','top':'89a44c30c9a759c6633c4c5f7a5fc3a160c68887fee50b78105c1906c1f585a1','right':'deded697bff88b5b3c02e4e1e0be0e3dabc9484ab4594c2e62ddcc07a8133cd2','left':'d0056f5c9ae33cc344de5d9e9c5387a95d4e0f90d7d64d08c0b059e23890e639','bottom':'f97972dc936b56e9456ff91a3ca4b23b1bf0881345a5c694822aa482af5ab124','rear':'b002253be4048b4b82fb760ab1a0b948bb19a364c8a4955def9a84396e295f5d'}
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im): return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
CURRENT_EXPECTED = {'iron-stations-station-tiled-masonry-outer-corner': {'front': '8df872fee3aca5d7f8050ba2753576eb596fa7e831dc0b9296e248722c7ab7b3', 'top': '3e3bf1899408ecf9ce476efe0f37d4046011ad252bcae01240c9a4be229f864c', 'right': 'fcf5d58d11e6d697c80a2beab2e7307467fda429a650a4ea3cb1d2e7fe07649a', 'left': 'ea7f78d44034eca9712e5e1055881fccf6fd5c80e8201d2961d168cf6aa90892', 'bottom': '4ed1298c3687aafd11fb6ffd0a42f4b6424926a59785728435c1b6b8f19aa2f2', 'rear': '6e0b282768acb2bd0a45979c02c97f03be9eb5f3ccdeb7eec3edc3a2bf048c8a'}, 'iron-stations-station-tiled-masonry-inner-corner': {'front': '622fadc5c18652d1c5953d02688a0216f882307919e294ab79312811061868a6', 'top': '736f963c14480151bb9c5efdd1c351ba87c009bc95d7be58be615b218b589517', 'right': '631e836f5b093ef6ae512bca3a8b4975a94a0fef276f25a79a449fc26ba1487a', 'left': '061a96c0d84b4f73ea2f70b4d6abd2562b09b559c0117726974e6712fdd737b1', 'bottom': 'bbdc69bb87197ef11bf0c94768b4fa5e19dfaf47d3874f5d2c092251171b8b15', 'rear': 'a28f8844a45a3e83cbaf09c695a37365f1aa74d20228521ea1f5752b07a05126'}}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--pack-root',type=Path,default=PACK); a=ap.parse_args(); pack=a.pack_root.resolve(); vd=pack/'reusable/views-additional'; idxpath=vd/'set-index.json'; atlaspath=pack/ATLAS_REL
 atlas=Image.open(atlaspath).convert('RGBA')
 if atlas.size != (2172,724): raise SystemExit(f'unexpected atlas dimensions {atlas.size}')
 index=json.loads(idxpath.read_text())
 # Require exact original hash state for every direction before the first application.
 for obj,expected in EXPECTED.items():
  source=pack/'iron-stations/components'/f'{obj}.png'
  if not source.is_file(): raise SystemExit(f'missing canonical source: {source}')
  if not any(x['object_id']==obj for x in index['view_sets']): raise SystemExit(f'missing view_set {obj}')
  for view,expected_hash in expected.items():
   p=vd/f'{obj}.{view}.png'
   if sha(p)!=expected_hash and sha(p)!=CURRENT_EXPECTED[obj][view]: raise SystemExit(f'current hash guard failed: {obj}.{view}; refusing replay')
  # Capture source hashes into recipe record.
 # Cellwise extraction uses the full nominal cell; main-body component bounds are retained whole.
 cellw,cellh=362,362; pending=[]
 for obj,row in OBJECTS.items():
  components={}
  for view,col in CELL_VIEWS.items():
   cell=atlas.crop((col*cellw,row*cellh,(col+1)*cellw,(row+1)*cellh))
   ar=np.asarray(cell)
   mask=ar[:,:,3] >= 245
   labels,n=ndimage.label(mask,structure=np.ones((3,3),dtype=np.uint8))
   objs=ndimage.find_objects(labels)
   cc=[]
   for i,sl in enumerate(objs,1):
    if sl is None: continue
    area=int((labels[sl]==i).sum())
    if area>=4:
     y0,y1=sl[0].start,sl[0].stop; x0,x1=sl[1].start,sl[1].stop
     cc.append((area,(x0,y0,x1,y1),i))
   if not cc: raise SystemExit(f'empty cell {row},{col} {view}')
   area,bbox,label=max(cc)
   # No isolated remnants or crop clipping may be carried into object output.
   x0,y0,x1,y1=bbox
   if x0<=0 or y0<=0 or x1>=cellw-1 or y1>=cellh-1: raise SystemExit(f'component touches source cell edge: {obj}.{view} {bbox}')
   body=cell.crop((x0,y0,x1,y1))
   # Keep opaque connected body only, remove alpha fringe/foreign islands.
   cm=(labels[y0:y1,x0:x1]==label)
   bodyarr=np.array(body); bodyarr[:,:,3]=np.where(cm,255,0).astype(np.uint8)
   components[view]=(Image.fromarray(bodyarr,'RGBA'),bbox,area)
  # one isotropic shared scale across all four regenerated projections
  scale=min(220/max(im.size) for im,_,_ in components.values())
  for view,(body,bbox,area) in components.items():
   size=(max(1,round(body.width*scale)),max(1,round(body.height*scale)))
   body=body.resize(size,Image.Resampling.NEAREST)
   canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(body,(128-size[0]//2,248-size[1]))
   pending.append((obj,view,canvas,bbox,area,size,scale))
 # Save all views, sidecars, and index with incomplete status.
 atlas_hash=sha(atlaspath)
 promptrel='reusable/views-additional/raw/prompts/iron-stations-corner-v4-rectangular-faces.txt'
 promptfile=pack/promptrel; promptfile.parent.mkdir(parents=True,exist_ok=True)
 request=json.loads((vd/'raw/requests/iron-stations-corner-v4-rectangular-faces.json').read_text())
 promptfile.write_text(request['prompt']+'\n')
 source_hashes={obj:sha(pack/'iron-stations/components'/f'{obj}.png') for obj in OBJECTS}
 for obj,view,im,bbox,area,size,scale in pending:
  dst=vd/f'{obj}.{view}.png'; im.save(dst,optimize=True)
  mp=vd/f'{obj}.{view}.json'; md=json.loads(mp.read_text())
  md['image']={'path':f'reusable/views-additional/{obj}.{view}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba_sha(im)}
  md['geometry_qa']='pending-review'
  md['provenance']['generated_atlas']=str(ATLAS_REL)
  md['provenance']['generated_atlas_sha256']=atlas_hash
  md['provenance']['prompt_file']=promptrel
  md['provenance']['normalization']={'alpha_threshold':245,'minimum_component_area':4,'component_policy':'largest opaque connected body in full nominal atlas cell; full component bounds retained; no cell-edge clipping','cell_xywh':[CELL_VIEWS[view]*cellw,OBJECTS[obj]*cellh,cellw,cellh],'body_bbox_xyxy':list(bbox),'component_area':area,'shared_scale':scale,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]}
  md['provenance']['notes']='Generated axis-aligned orthographic view; four elevations share an isotropic per-object scale. Existing source L footprint retained in TOP/BOTTOM. Inferred surface, not recovered pixels.'
  md['provenance']['source_sha256']=source_hashes[obj]
  md['provenance']['generation_request']='reusable/views-additional/raw/requests/iron-stations-corner-v4-rectangular-faces.json'
  md['provenance']['generation_linkage_note']='External imagegen response path was not bound to this request inside the generation call. The retained pack-local raw atlas and SHA256 are the deterministic replay input; the external generated_images path is not claimed as verified request linkage.'
  mp.write_text(json.dumps(md,indent=2)+'\n')
  for asset in index['assets']:
   if asset.get('id')==md['id']:
    asset.clear(); asset.update(md); break
 for obj in OBJECTS:
  group=next(x for x in index['view_sets'] if x['object_id']==obj)
  group['complete']=False; group['geometry_qa']='pending-review'
  group['notes']='Four elevations regenerated as rectangular full-arm masonry wall faces; TOP/BOTTOM preserved from prior set. Awaiting independent current-source and six-view review.'
 # Remove only detached far atlas-guide components from retained plans, with explicit byte guards.
 clean_original={'iron-stations-station-tiled-masonry-outer-corner':{'top':'ca3b8f12574648731ab1cbd363b54a367f896cafde620520302dcda5e660b6ab','bottom':'1e08412d36e0b5164755d95fd73354640698acd192ac55f25053932e79a9df0e'},'iron-stations-station-tiled-masonry-inner-corner':{'top':'89a44c30c9a759c6633c4c5f7a5fc3a160c68887fee50b78105c1906c1f585a1','bottom':'f97972dc936b56e9456ff91a3ca4b23b1bf0881345a5c694822aa482af5ab124'}}
 clean_final={'iron-stations-station-tiled-masonry-outer-corner':{'top':'c912214f735f368f9780f2698e4501983d92d976d5cf4a5dbb70f11634ce7d52','bottom':'40d30415505405dc3d86dd0eee37db3a6f65d60692498b6745afce58247df08a'},'iron-stations-station-tiled-masonry-inner-corner':{'top':'3af6ea57b55312ae3c524e56d07f318573eed93af0345a9ca9fb4f20ac3b8008','bottom':'8b22b23cd9f29559d626a1e810d88fcb8efcf31bee94d94620ef9bf810e67fe3'}}
 scaled_final={'iron-stations-station-tiled-masonry-outer-corner':{'top':'3e3bf1899408ecf9ce476efe0f37d4046011ad252bcae01240c9a4be229f864c','bottom':'4ed1298c3687aafd11fb6ffd0a42f4b6424926a59785728435c1b6b8f19aa2f2'},'iron-stations-station-tiled-masonry-inner-corner':{'top':'736f963c14480151bb9c5efdd1c351ba87c009bc95d7be58be615b218b589517','bottom':'bbdc69bb87197ef11bf0c94768b4fa5e19dfaf47d3874f5d2c092251171b8b15'}}
 for obj in OBJECTS:
  for view in ('top','bottom'):
   dst=vd/f'{obj}.{view}.png'; before=sha(dst)
   if scaled_final[obj][view] and before==scaled_final[obj][view]: continue
   if before==clean_final[obj][view]:
    pass
   elif before==clean_original[obj][view]:
    # Restore the base-generated image deterministically, then apply the detached-guide cleanup.
    im0=Image.open(dst).convert('RGBA'); ar0=np.array(im0); labels0,n0=ndimage.label(ar0[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8)); found0=[]
    for i0,sl0 in enumerate(ndimage.find_objects(labels0),1):
     if sl0 is None: continue
     area0=int((labels0[sl0]==i0).sum())
     if area0: found0.append((area0,i0,sl0))
    found0.sort(key=lambda z:z[0],reverse=True); main0=found0[0][2]; xx0,xx1=main0[1].start,main0[1].stop; yy0,yy1=main0[0].start,main0[0].stop
    for area0,i0,sl0 in found0[1:]:
     ax0,ax1=sl0[1].start,sl0[1].stop; ay0,ay1=sl0[0].start,sl0[0].stop
     if max(0,xx0-ax1,ax0-xx1)+max(0,yy0-ay1,ay0-yy1)>8: ar0[labels0==i0,3]=0
    Image.fromarray(ar0,'RGBA').save(dst,optimize=True)
   else: raise SystemExit(f'plan cleanup hash guard failed {obj}.{view}: {before}')
   im=Image.open(dst).convert('RGBA'); ar=np.array(im); labels,n=ndimage.label(ar[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8)); found=[]
   for i,sl in enumerate(ndimage.find_objects(labels),1):
    if sl is None: continue
    area=int((labels[sl]==i).sum())
    if area: found.append((area,i,sl))
   found.sort(key=lambda z:z[0],reverse=True); main=found[0][2]; x0,x1=main[1].start,main[1].stop; y0,y1=main[0].start,main[0].stop; removed=[]
   for area,i,sl in found[1:]:
    xx0,xx1=sl[1].start,sl[1].stop; yy0,yy1=sl[0].start,sl[0].stop
    gap=max(0,x0-xx1,xx0-x1)+max(0,y0-yy1,yy0-y1)
    if gap>8: ar[labels==i,3]=0; removed.append({'area':area,'bbox':[xx0,yy0,xx1,yy1],'gap':gap})
   out=Image.fromarray(ar,'RGBA'); out.save(dst,optimize=True); mp=vd/f'{obj}.{view}.json'; md=json.loads(mp.read_text()); md['image']={'path':f'reusable/views-additional/{obj}.{view}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba_sha(out)}; md['geometry_qa']='pending-review'; md['provenance'].setdefault('repair_steps',[]).append({'operation':'remove detached far atlas-guide components','alpha_threshold':245,'minimum_gap_px':8,'removed_components':removed}); mp.write_text(json.dumps(md,indent=2)+'\n')
   for asset in index['assets']:
    if asset.get('id')==md['id']: asset.clear(); asset.update(md); break
   # Uniform nearest-neighbor scaling to accepted 220 px broad-face width; keep aspect and bottom anchor.
   im=Image.open(dst).convert('RGBA'); alpha=np.asarray(im)[:,:,3]; bb=Image.fromarray(np.where(alpha>=245,255,0).astype(np.uint8)).getbbox()
   if not bb: raise SystemExit(f'empty plan {obj}.{view}')
   crop=im.crop(bb); newsize=(220,round(crop.height*220/crop.width)); crop=crop.resize(newsize,Image.Resampling.NEAREST)
   canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(crop,(128-newsize[0]//2,248-newsize[1])); canvas.save(dst,optimize=True)
   md=json.loads(mp.read_text()); md['image']={'path':f'reusable/views-additional/{obj}.{view}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba_sha(canvas)}; md['geometry_qa']='pending-review'; md['provenance'].setdefault('repair_steps',[]).append({'operation':'uniform nearest-neighbor resize plan to accepted broad wall-arm width','target_object_width_px':220,'pre_scale_bbox_xyxy':list(bb),'render_size':list(newsize),'anchor_px':[128,248]}); mp.write_text(json.dumps(md,indent=2)+'\n')
   for asset in index['assets']:
    if asset.get('id')==md['id']: asset.clear(); asset.update(md); break
 # Restore independent approval only if the exact approved source and six output hashes still match.
 approval=json.loads((vd/'raw/targeted-repairs/iron-stations-corner-v4-root-approval.json').read_text())
 for obj in OBJECTS:
  proof=approval.get(obj,{});sourcep=pack/proof.get('source_path','');ok=proof.get('status')=='pass' and sourcep.is_file() and sha(sourcep)==proof.get('source_sha256')
  if ok:
   for view,h in proof.get('image_hashes',{}).items():
    if sha(vd/f'{obj}.{view}.png')!=h:ok=False;break
  status='pass' if ok else 'pending-review'
  for view in ('front','top','right','left','bottom','rear'):
   mp=vd/f'{obj}.{view}.json';md=json.loads(mp.read_text());md['geometry_qa']=status;mp.write_text(json.dumps(md,indent=2)+'\n')
   for asset in index['assets']:
    if asset.get('id')==md['id']:asset.clear();asset.update(md);break
  group=next(x for x in index['view_sets'] if x['object_id']==obj);group['complete']=ok;group['geometry_qa']=status;group['notes']='Root whole-source+six PASS restored from pinned reviewer hash proof.' if ok else 'Awaiting independent source+six review at current hashes.'
 idxpath.write_text(json.dumps(index,indent=2)+'\n')
 print(json.dumps({'atlas_sha256':atlas_hash,'source_hashes':source_hashes,'approval_preserved':{o:next(x for x in index['view_sets'] if x['object_id']==o)['geometry_qa'] for o in OBJECTS},'written':[f'{o}.{v}' for o,v, *_ in pending]},indent=2))
if __name__=='__main__': main()
