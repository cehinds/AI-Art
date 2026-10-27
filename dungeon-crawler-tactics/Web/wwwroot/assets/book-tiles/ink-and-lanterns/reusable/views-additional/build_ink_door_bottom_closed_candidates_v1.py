#!/usr/bin/env python3
"""Normalize closed-door bottom candidates from approved geometry templates."""
import hashlib,json,os,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];IDS=['bubble-necropolis-ancient-tomb-masonry-closed-doorway','starter-dungeon-dark-stone-block-closed-doorway']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,b):
 fd,tmp=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 except BaseException:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
def png(im):
 import io
 b=io.BytesIO();im.save(b,'PNG',optimize=True);return b.getvalue()
def main():
 out=[]
 for oid in IDS:
  rp=HERE/'raw'/f'{oid}.bottom-geometry-guide-v1.request.json';q=json.loads(rp.read_text());assert q['status']=='generated-atlas-ready-for-normalization';atlas=PACK/Path(q['generated_atlas']);assert sha(atlas)==q['generated_atlas_sha256'];source=PACK/q['reference_inputs'][1]['path'];assert sha(source)==q['reference_inputs'][1]['sha256'];im=Image.open(atlas).convert('RGBA');lab,n=ndimage.label(np.asarray(im)[:,:,3]>=245);cc=[]
  for k in range(1,n+1):
   ys,xs=np.nonzero(lab==k)
   if len(xs)>=50:cc.append((len(xs),k,(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)))
  assert cc;cc.sort(reverse=True);keep=[c for c in cc if c[0]>=cc[0][0]*.02];box=(min(c[2][0] for c in keep),min(c[2][1] for c in keep),max(c[2][2] for c in keep),max(c[2][3] for c in keep));crop=im.crop(box);scale=212/crop.width;size=(212,max(1,round(crop.height*scale)));crop=crop.resize(size,Image.Resampling.NEAREST);off=((256-size[0])//2,(256-size[1])//2);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(crop,off);cand=HERE/'raw'/f'{oid}.bottom-geometry-guide-v1-candidate.png';atomic(cand,png(canvas));before={v:sha(HERE/f'{oid}.{v}.png') for v in ['front','top','right','left','bottom','rear']};topguide=(HERE/'raw'/'bubble-necropolis-ancient-tomb-masonry-closed-doorway.top-guide-pilot-v1-candidate.png') if oid=='bubble-necropolis-ancient-tomb-masonry-closed-doorway' else (HERE/f'{oid}.top.png');topguide_sha=sha(topguide);recipe={'schema_version':1,'status':'candidate-ready-for-independent-review','object_id':oid,'direction':'bottom','request_path':'reusable/views-additional/raw/'+rp.name,'request_sha256':sha(rp),'generated_atlas':q['generated_atlas'],'generated_atlas_sha256':sha(atlas),'canonical_source':q['reference_inputs'][1]['path'],'canonical_source_sha256':sha(source),'geometry_template':q['reference_inputs'][0]['path'],'geometry_template_sha256':q['reference_inputs'][0]['sha256'],'operation':'full alpha>=245 component bounds; retain components >=2% of largest; isotropic nearest-neighbor to 212 px width, centered on transparent 256 canvas','alpha_threshold':245,'component_labels':[c[1] for c in keep],'component_bounds_xyxy_px':list(box),'scale':scale,'resized_dimensions_px':list(size),'canvas_offset_xy_px':list(off),'candidate_path':'reusable/views-additional/raw/'+cand.name,'candidate_sha256':sha(cand),'preinstall_view_hashes':before,'related_top_candidate':{'path':'reusable/views-additional/raw/'+topguide.name,'sha256':topguide_sha},'preserved_directions':['front','top','right','left','rear'],'inference_note':'Inferred closed-door underside based on approved geometry template; opaque door-panel underside and lintel span retained; not recovered pixels/calibrated 3D.'};recipepath=HERE/'raw'/f'{oid}.bottom-geometry-guide-v1-candidate.recipe.json';atomic(recipepath,(json.dumps(recipe,indent=2)+'\n').encode());cells=[Image.open(source).convert('RGBA')]+[Image.open(topguide).convert('RGBA') if v=='top' else canvas if v=='bottom' else Image.open(HERE/f'{oid}.{v}.png').convert('RGBA') for v in ['front','top','right','left','bottom','rear']];sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));dr=ImageDraw.Draw(sheet)
  for i,(cell,label) in enumerate(zip(cells,['source','front','top','right','left','bottom','rear'])):
   x=i*184;dr.text((x+4,22),label,fill=(15,15,15,255));cell.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(cell,(x+8+(168-cell.width)//2,42+(168-cell.height)//2))
  contact=HERE/f'qa-{oid}-bottom-geometry-guide-v1-candidate-source-six.png';atomic(contact,png(sheet));out.append({'object_id':oid,'candidate_sha256':recipe['candidate_sha256'],'recipe_sha256':sha(recipepath),'contact':contact.name,'contact_sha256':sha(contact),'source_sha256':sha(source),'bounds':box})
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
