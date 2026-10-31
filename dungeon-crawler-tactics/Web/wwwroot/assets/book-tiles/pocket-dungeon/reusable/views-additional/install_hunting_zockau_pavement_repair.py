#!/usr/bin/env python3
"""Extract one pixel-art orthographic repair atlas into five Pocket paving sets."""
from pathlib import Path
from PIL import Image
import hashlib, json, struct
import numpy as np
from scipy import ndimage

BASE=Path(__file__).resolve().parent
PACK=BASE.parents[1]
ATLAS=BASE/'raw/atlases/hunting-zockau-pavement-repair-v1.png'
ATLAS_REL='reusable/views-additional/raw/atlases/hunting-zockau-pavement-repair-v1.png'
PROMPT_REL='reusable/views-additional/raw/prompts/hunting-zockau-pavement-repair-v1.txt'
IDS=[
 'hunting-zockau-mid-century-street-pavement-floor',
 'hunting-zockau-worn-mid-century-street-pavement-floor',
 'hunting-zockau-cracked-mid-century-street-pavement-floor',
 'hunting-zockau-wet-mid-century-street-pavement-floor',
 'hunting-zockau-mid-century-street-pavement-edge-transition',
]
VIEWS=['front','right','left','bottom','rear']

def sha(data): return hashlib.sha256(data).hexdigest()
def file_sha(p): return sha(Path(p).read_bytes())
def rgba_sha(im):
 im=im.convert('RGBA'); w,h=im.size
 return sha(struct.pack('>II',w,h)+im.tobytes())
def crop_main(im,box):
 cell=im.crop(box); a=np.asarray(cell.getchannel('A')); labels,n=ndimage.label(a>12,structure=np.ones((3,3),dtype=np.uint8)); objs=ndimage.find_objects(labels); comps=[]
 for label,sl in enumerate(objs,1):
  if sl is None: continue
  area=int((labels[sl]==label).sum())
  if area<50: continue
  y,x=sl; comps.append((area,label,sl))
 if not comps: raise RuntimeError(f'No object component in cell {box}')
 comps.sort(key=lambda x:x[0],reverse=True); area,label,sl=comps[0]
 y,x=sl; bbox=(box[0]+x.start,box[1]+y.start,box[0]+x.stop,box[1]+y.stop)
 return im.crop(bbox),bbox,area,label

def main():
 atlas=Image.open(ATLAS).convert('RGBA'); aw,ah=atlas.size
 if (aw,ah)!=(1536,1024): raise RuntimeError(f'Unexpected atlas size {atlas.size}')
 request=json.loads((BASE/'raw/requests/hunting-zockau-pavement-repair-v1.json').read_text())
 atlas_sha=file_sha(ATLAS)
 if atlas_sha!=request['output_sha256']: raise RuntimeError('Atlas SHA differs from bound request record')
 root_review=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed']
 corrections_path=BASE/'corrections.json'; corrections=json.loads(corrections_path.read_text())
 index_path=BASE/'set-index.json'; index=json.loads(index_path.read_text())
 op_list=[]
 for ri,oid in enumerate(IDS):
  proof=root_review.get('book-tiles/pocket-dungeon::'+oid)
  if not proof or proof.get('status')!='needs-correction': raise RuntimeError(f'{oid} lacks active independent needs-correction proof')
  # Never edit an asset whose source/current views no longer match the review capture.
  source=PACK/'hunting-zockau/components'/f'{oid}.png'
  if proof.get('source_sha256')!=file_sha(source): raise RuntimeError(f'{oid} source SHA no longer matches review')
  current={v:file_sha(BASE/f'{oid}.{v}.png') for v in ['front','top','right','left','bottom','rear']}
  if current!=proof.get('image_hashes'): raise RuntimeError(f'{oid} current bytes differ from independent needs-correction review')
  for ci,view in enumerate(VIEWS):
   x0=round(ci*aw/5); x1=round((ci+1)*aw/5); y0=round(ri*ah/5); y1=round((ri+1)*ah/5)
   crop,bbox,area,label=crop_main(atlas,(x0,y0,x1,y1))
   target=BASE/f'{oid}.{view}.png'; before=file_sha(target)
   if view=='bottom':
    ref=Image.open(BASE/f'{oid}.top.png').convert('RGBA'); refbox=ref.getchannel('A').getbbox()
    target_dim=max(refbox[2]-refbox[0],refbox[3]-refbox[1]); scale=target_dim/max(crop.size)
   else:
    ref=Image.open(BASE/f'{oid}.front.png').convert('RGBA'); refbox=ref.getchannel('A').getbbox()
    target_dim=refbox[3]-refbox[1]; scale=target_dim/crop.height
   size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
   if max(size)>248: raise RuntimeError(f'{oid}.{view} would clip with {size}')
   crop=crop.resize(size,Image.Resampling.NEAREST)
   frame=Image.new('RGBA',(256,256),(0,0,0,0)); frame.alpha_composite(crop,((256-size[0])//2,248-size[1])); frame.save(target,optimize=True)
   after=file_sha(target)
   meta_path=BASE/f'{oid}.{view}.json'; meta=json.loads(meta_path.read_text())
   meta['image']['sha256']=after; meta['image']['rgba_sha256']=rgba_sha(frame)
   oldmeta=meta.get('provenance',{}); meta.setdefault('provenance_history',[]).append(oldmeta)
   meta['provenance']={'method':'generated','source_image':oldmeta.get('source_image'),'source_sha256':file_sha(source),'generated_atlas':ATLAS_REL,'generated_atlas_sha256':atlas_sha,'prompt_file':PROMPT_REL,'normalization':{'alpha_threshold':12,'minimum_component_area':50,'component_policy':'largest single orthographic slab component assigned by logical row and column; exclude detached atlas spill','component_label':int(label),'component_area':int(area),'crop_bbox':list(bbox),'source_crop_size':list(crop.size),'scale':scale,'render_size':list(size),'resampling':'NEAREST','reference_view':'top' if view=='bottom' else 'front','reference_sha256':file_sha(BASE/f'{oid}.top.png' if view=='bottom' else BASE/f'{oid}.front.png'),'canvas':[256,256],'anchor_px':[128,248]},'notes':'Generated source-specific paving slab view. Natural stone/earth substrate follows the corresponding original tile; geometry is inferred orthographic, not recovered pixels.'}
   meta['geometry_qa']='pending-review'; meta_path.write_text(json.dumps(meta,indent=2)+'\n')
   op={'type':'replace-generated-view','object_id':oid,'view':view,'atlas_path':ATLAS_REL,'atlas_sha256':atlas_sha,'prompt_file':PROMPT_REL,'crop_bbox':list(bbox),'alpha_threshold':12,'component_policy':'largest single object component in assigned cell; detached atlas noise discarded','reference_view':'top' if view=='bottom' else 'front','reference_sha256':file_sha(BASE/f'{oid}.top.png' if view=='bottom' else BASE/f'{oid}.front.png'),'scale':scale,'scale_axis':'height' if view!='bottom' else 'max-plan-dimension','render_size':list(size),'before_sha256':before,'after_sha256':after,'reference_inputs':[{'path':'hunting-zockau/components/'+f'{oid}.png','sha256':file_sha(source)},{'path':ATLAS_REL,'sha256':atlas_sha}],'reason':f'Replace the unrelated metal tray with source-matched {view.upper()} stone/earth projection from the five-row atlas; retain the accepted TOP, infer true axis-aligned paving slab geometry and use nearest-neighbor uniform scaling.'}
   op_list.append(op)
   for asset in index['assets']:
    if asset.get('id')==meta['id']:
     asset.clear();asset.update(meta);break
   print(oid,view,'crop',bbox,'render',size,'scale',round(scale,4),'sha',after)
 corrections['operations'].extend(op_list); corrections_path.write_text(json.dumps(corrections,indent=2)+'\n')
 index_path.write_text(json.dumps(index,indent=2)+'\n')
 print('installed',len(op_list),'views')
if __name__=='__main__': main()
