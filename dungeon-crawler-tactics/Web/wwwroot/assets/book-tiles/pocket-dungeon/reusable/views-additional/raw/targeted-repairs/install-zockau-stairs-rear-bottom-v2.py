#!/usr/bin/env python3
"""Install current-hash-guarded Zockau stair undersides and closed rear support views."""
import hashlib,importlib.util,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import label,find_objects
OUT=Path(__file__).resolve().parents[2];BOOK=OUT.parents[1];CAPTURE=Path('/tmp/root-pocket-ticket-zockau-current.png.json')
IDS=['hunting-zockau-mid-century-street-pavement-stairs-up','hunting-zockau-mid-century-street-pavement-stairs-down']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bbox_at(atlas, expected, radius=200):
 im=Image.open(atlas).convert('RGBA');lab,n=label(np.asarray(im)[:,:,3]>=245,np.ones((3,3),dtype=np.uint8));cs=[]
 for i,sl in enumerate(find_objects(lab),1):
  if sl is None:continue
  y,x=sl;area=int((lab[sl]==i).sum());box=(x.start,y.start,x.stop,y.stop);cx=(box[0]+box[2])/2;cy=(box[1]+box[3])/2
  if area>2000 and abs(cx-expected[0])<radius and abs(cy-expected[1])<radius:cs.append((area,box))
 if not cs:raise RuntimeError(f'missing object in logical cell {expected}')
 return max(cs,key=lambda x:x[0])[1]
def main():
 ixp=OUT/'set-index.json';idx=json.loads(ixp.read_text());sets={s['object_id']:s for s in idx['view_sets']};assets={a['id']:a for a in idx['assets']};caps=json.loads(CAPTURE.read_text())['records']
 latest=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed']
 for oid in IDS:
  key='book-tiles/pocket-dungeon::'+oid;record=caps[key];q=latest.get(key)
  if not q or q.get('status')=='pass':raise RuntimeError(f'{oid}: independent hold cleared or missing; do not alter')
  for v,h in record['image_hashes'].items():
   p=BOOK/assets[sets[oid]['views'][v]]['image']['path'];
   if sha(BOOK/p)!=h:raise RuntimeError(f'{oid}.{v}: capture hash stale')
 # Crop bboxes are detected from the whole atlas, grouped by expected row/cell centers.
 atlases={v:OUT/f'raw/atlases/zockau-stairs-{v}-v2.png' for v in ('bottom','rear')}; hashes={v:sha(p) for v,p in atlases.items()}; centers={'bottom':[(472,470),(472,1247)],'rear':[(472,469),(472,1248)]}
 specs=json.loads((OUT/'corrections.json').read_text());ops=[];bak=OUT/'raw/targeted-repairs'/'zockau-stairs-rear-bottom-v2';bak.mkdir(parents=True,exist_ok=True)
 for row,oid in enumerate(IDS):
  for view in ('bottom','rear'):
   atlas=atlases[view];box=bbox_at(atlas,centers[view][row]);crop=Image.open(atlas).convert('RGBA').crop(box);refview='top' if view=='bottom' else 'front';refp=OUT/f'{oid}.{refview}.png';ref=Image.open(refp).convert('RGBA').getchannel('A').getbbox();refsha=sha(refp)
   if view=='bottom':
    # Match the source-aligned footprint X width. Keep the artwork's Y aspect.
    width=ref[2]-ref[0];height=round(crop.height*width/crop.width);scale=width/crop.width;axis='width'
   else:
    # Match accepted FRONT physical Z. Uniform scaling preserves the generated panel's proportions.
    height=ref[3]-ref[1];width=round(crop.width*height/crop.height);scale=height/crop.height;axis='height'
   if max(width,height)>256:raise RuntimeError(f'{oid}.{view} would clip {(width,height)}')
   frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop.resize((width,height),Image.Resampling.NEAREST),((256-width)//2,248-height));cand=bak/f'{oid}.{view}.candidate.png';frame.save(cand,optimize=True);target=OUT/f'{oid}.{view}.png'
   op={'type':'replace-generated-view','object_id':oid,'view':view,'before_sha256':sha(target),'after_sha256':sha(cand),'atlas_path':f'raw/atlases/zockau-stairs-{view}-v2.png','atlas_sha256':hashes[view],'crop_bbox':list(box),'rotation_degrees':0,'render_size':[width,height],'scale':scale,'scale_axis':axis,'alpha_threshold':245,'component_policy':'one opaque logical-cell object group; retain full connected alpha bounds, exclude gradient/grid background','reference_view':refview,'reference_sha256':refsha,'prompt_file':f'reusable/views-additional/raw/prompts/zockau-stairs-{view}-v2.txt','reason':('Full-XY underside of the same up/down stair assembly, aligned to the accepted top footprint width and preserving its tan stone rails and charcoal underside; no upper tread faces.' if view=='bottom' else 'Closed reverse support face of the same up/down staircase; uniformly match accepted FRONT physical height, preserve tan side rails and charcoal masonry, and remove all forward-facing treads.')}
   ops.append(op)
 specs['operations'].extend(ops);(OUT/'corrections.json').write_text(json.dumps(specs,indent=2)+'\n');hp=OUT/'apply_deterministic_view_fixes.py';sp=importlib.util.spec_from_file_location('vf',hp);vf=importlib.util.module_from_spec(sp);sp.loader.exec_module(vf);res=[vf.apply(op,idx,bak) for op in ops];ixp.write_text(json.dumps(idx,indent=2)+'\n');(bak/'result.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))
if __name__=='__main__':main()
