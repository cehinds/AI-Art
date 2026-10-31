#!/usr/bin/env python3
"""Rebuild the road-barrier TOP candidate from the footprint-preserving edit atlas."""
import hashlib, json, os, struct, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE=Path(__file__).resolve().parent
PACK=HERE.parents[1]
OBJ='ghost-havana-ghost-traffic-road-barrier'
ATLAS=HERE/'raw'/f'{OBJ}-top-v6-atlas.png'
REQUEST=HERE/'raw'/f'{OBJ}-top-v6.request.json'
BOTTOM=HERE/f'{OBJ}.bottom.png'
SOURCE=PACK/'ghost-havana'/'components'/f'{OBJ}.png'
CONTACT=HERE/f'qa-{OBJ}-current-source-six-pre-repair.png'
CANDIDATE=HERE/'raw'/f'{OBJ}-top-v6-candidate.png'
RECIPE=HERE/'raw'/f'{OBJ}-top-v6-candidate.recipe.json'
QA=HERE/f'qa-{OBJ}-top-v6-candidate-source-six.png'
VIEWS=('front','top','right','left','bottom','rear')
TARGET_WIDTH=232

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,data):
 fd,tmp=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 except BaseException:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
def png(im):
 import io
 b=io.BytesIO();im.save(b,'PNG',optimize=True);return b.getvalue()

def main():
 req=json.loads(REQUEST.read_text().removesuffix('\\n'))
 assert req['object_id']==OBJ and req['view']=='top' and req['status']=='generated-atlas-ready-for-normalization'
 assert sha(ATLAS)==req['generated_atlas_sha256']
 assert sha(BOTTOM)==req['reference_inputs'][0]['sha256'] and sha(SOURCE)==req['reference_inputs'][1]['sha256']
 im=Image.open(ATLAS).convert('RGBA');a=np.asarray(im)[:,:,3];lab,n=ndimage.label(a>=245);components=[]
 for i in range(1,n+1):
  ys,xs=np.nonzero(lab==i)
  if len(xs)>=50:components.append((len(xs),i,(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)))
 if not components:raise RuntimeError('No substantial opaque image component')
 components.sort(reverse=True);major=components[0][0];keep=[c for c in components if c[0]>=major*.02]
 box=(min(c[2][0] for c in keep),min(c[2][1] for c in keep),max(c[2][2] for c in keep),max(c[2][3] for c in keep))
 crop=im.crop(box);scale=TARGET_WIDTH/crop.width;size=(TARGET_WIDTH,max(1,round(crop.height*scale)));crop=crop.resize(size,Image.Resampling.NEAREST)
 offset=((256-size[0])//2,(256-size[1])//2);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(crop,offset);data=png(canvas);atomic(CANDIDATE,data)
 lives=[HERE/f'{OBJ}.{d}.png' for d in VIEWS];before={d:sha(p) for d,p in zip(VIEWS,lives)}
 rgba=hashlib.sha256(struct.pack('>II',256,256)+canvas.tobytes()).hexdigest()
 recipe={'schema_version':1,'status':'candidate-ready-for-independent-review','object_id':OBJ,'direction':'top','request_path':'reusable/views-additional/raw/'+REQUEST.name,'request_sha256':sha(REQUEST),'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,'source_atlas_sha256':sha(ATLAS),'canonical_source':'ghost-havana/components/'+SOURCE.name,'canonical_source_sha256':sha(SOURCE),'geometry_reference':'reusable/views-additional/'+BOTTOM.name,'geometry_reference_sha256':sha(BOTTOM),'evidence_contact':'reusable/views-additional/'+CONTACT.name,'evidence_contact_sha256':sha(CONTACT),'operation':'keep largest alpha-connected component and any component >=2% of its area at alpha>=245; union full bounds; isotropic nearest-neighbor scale to 232 px full plan width; center on transparent 256x256','alpha_threshold':245,'component_labels':[c[1] for c in keep],'component_bounds_xyxy_px':list(box),'crop_dimensions_px':[box[2]-box[0],box[3]-box[1]],'scale':scale,'resized_dimensions_px':list(size),'canvas_offset_xy_px':list(offset),'target_width_px':TARGET_WIDTH,'candidate_path':'reusable/views-additional/raw/'+CANDIDATE.name,'candidate_sha256':hashlib.sha256(data).hexdigest(),'candidate_rgba_sha256':rgba,'preinstall_view_hashes':before,'preserved_views':['front','right','left','bottom','rear'],'inference_note':'Inferred straight-down plan; not recovered pixels or calibrated 3D.'}
 atomic(RECIPE,(json.dumps(recipe,indent=2)+'\n').encode())
 src=Image.open(SOURCE).convert('RGBA');views=[canvas if d=='top' else Image.open(p).convert('RGBA') for d,p in zip(VIEWS,lives)]
 sheet=Image.new('RGBA',(7*184,216),(112,112,112,255));draw=ImageDraw.Draw(sheet)
 for col,(cell,label) in enumerate(zip([src]+views,['source',*VIEWS])):
  x=col*184;draw.text((x+4,22),label,fill=(245,245,245,255));cell.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(cell,(x+8+(168-cell.width)//2,42+(168-cell.height)//2))
 atomic(QA,png(sheet));print(json.dumps({'candidate':str(CANDIDATE),'candidate_sha256':recipe['candidate_sha256'],'recipe_sha256':sha(RECIPE),'qa_contact':str(QA),'bbox':box,'dimensions':size,'scale':scale},indent=2))

if __name__=='__main__':main()
