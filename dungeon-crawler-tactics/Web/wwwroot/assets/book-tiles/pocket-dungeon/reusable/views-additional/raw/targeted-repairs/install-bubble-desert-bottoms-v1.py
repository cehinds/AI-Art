#!/usr/bin/env python3
"""Install four material-specific desert underside views under current review hashes."""
import hashlib,importlib.util,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import label,find_objects
OUT=Path(__file__).resolve().parents[2];BOOK=OUT.parents[1];Q=Path('/workspace/scratch/view-qa-root.json')
IDS=['bubble-desert-bactrian-town-ruined-wall','bubble-desert-camel-folk-settlement-well','bubble-desert-narrow-market-stall','bubble-desert-sand-dune-mound'];CY=[214,585,970,1325]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ixp=OUT/'set-index.json';idx=json.loads(ixp.read_text());sets={s['object_id']:s for s in idx['view_sets']};assets={a['id']:a for a in idx['assets']};q=json.loads(Q.read_text())['reviewed'];
 for oid in IDS:
  r=q.get('book-tiles/pocket-dungeon::'+oid)
  if not r or r.get('status')=='pass' or r.get('affected_views')!=['bottom']:raise RuntimeError(f'{oid} no longer unresolved bottom-only target')
  for v,h in r.get('image_hashes',{}).items():
   p=BOOK/assets[sets[oid]['views'][v]]['image']['path']
   if sha(BOOK/p)!=h:raise RuntimeError(f'{oid}.{v}: stale root QA hash')
 atlas=OUT/'raw/atlases/bubble-desert-bottoms-v1.png';atlas_sha=sha(atlas);im=Image.open(atlas).convert('RGBA');lab,n=label(np.asarray(im)[:,:,3]>=64,np.ones((3,3),dtype=np.uint8));boxes=[]
 for i,sl in enumerate(find_objects(lab),1):
  if sl is None:continue
  y,x=sl;area=int((lab[sl]==i).sum())
  if area>=2000:boxes.append((area,(x.start,y.start,x.stop,y.stop),(x.start+x.stop)/2,(y.start+y.stop)/2,i))
 specs=json.loads((OUT/'corrections.json').read_text());ops=[];backup=OUT/'raw/targeted-repairs'/'bubble-desert-bottoms-v1';backup.mkdir(parents=True,exist_ok=True)
 for row,oid in enumerate(IDS):
  opts=[c for c in boxes if abs(c[2]-512)<200 and abs(c[3]-CY[row])<180]
  if not opts:raise RuntimeError(f'No row component for {oid}')
  area,bbox,cx,cy,labid=max(opts,key=lambda x:x[0]);crop=im.crop(bbox); aid=f'{oid}.bottom';target=OUT/f'{aid}.png';before=sha(target)
  top=Image.open(OUT/f'{oid}.top.png').convert('RGBA').getchannel('A').getbbox();tw=top[2]-top[0];scale=tw/crop.width;size=(tw,max(1,round(crop.height*scale)))
  if max(size)>256:raise RuntimeError(f'{oid} bottom would clip {size}')
  frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop.resize(size,Image.Resampling.NEAREST),((256-size[0])//2,248-size[1]));cand=backup/f'{aid}.candidate.png';frame.save(cand,optimize=True);meta=json.loads((OUT/f'{aid}.json').read_text())
  ops.append({'type':'replace-generated-view','object_id':oid,'view':'bottom','before_sha256':before,'after_sha256':sha(cand),'atlas_path':'reusable/views-additional/raw/atlases/bubble-desert-bottoms-v1.png','atlas_sha256':atlas_sha,'crop_bbox':list(bbox),'rotation_degrees':0,'render_size':list(size),'scale':scale,'scale_axis':'width','alpha_threshold':64,'component_policy':'largest opaque component grouped by nearest logical row center; retain complete footprint, exclude detached atlas artifacts','reference_view':'top','reference_sha256':sha(OUT/f'{oid}.top.png'),'prompt_file':'reusable/views-additional/raw/prompts/bubble-desert-bottoms-v1.txt','reason':'Replace an upper-facing roof/rubble surface with the object-specific underside: natural earth and embedded rock backs, a stone well ring and shaft opening, the stall counter/support frame, or the dune mound base. Preserve canonical source identity and calibrate uniformly to the accepted TOP footprint.'})
 specs['operations'].extend(ops);(OUT/'corrections.json').write_text(json.dumps(specs,indent=2)+'\n')
 hp=OUT/'apply_deterministic_view_fixes.py';sp=importlib.util.spec_from_file_location('vf',hp);vf=importlib.util.module_from_spec(sp);sp.loader.exec_module(vf);results=[vf.apply(op,idx,backup) for op in ops];ixp.write_text(json.dumps(idx,indent=2)+'\n');(backup/'result.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
