#!/usr/bin/env python3
"""Normalize the isolated overhead edge candidate for the Airship closed door."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage

HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];OBJ='bubble-airship-riveted-scrap-hull-closed-doorway'
REQ=HERE/'raw'/f'{OBJ}-top-v1.request.json';ATLAS=HERE/'raw'/f'{OBJ}-top-v1-atlas.png';SOURCE=PACK/'bubble-airship'/'components'/f'{OBJ}.png';CONTACT=HERE/'qa-bubble-airship-closed-door-source-six-top-repair-v1.png'
CAND=HERE/'raw'/f'{OBJ}-top-v1-candidate.png';RECIPE=HERE/'raw'/f'{OBJ}-top-v1-candidate.recipe.json';QA=HERE/f'qa-{OBJ}-top-v1-candidate-source-six.png';DIRECTIONS=('front','top','right','left','bottom','rear');TARGET_WIDTH=224
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
def rgba_hash(im):return hashlib.sha256(struct.pack('>II',im.width,im.height)+im.convert('RGBA').tobytes()).hexdigest()
def main():
 req=json.loads(REQ.read_text().removesuffix('\\n'));assert req['object_id']==OBJ and req['view']=='top' and req['status']=='generated-atlas-ready-for-normalization'
 assert sha(ATLAS)==req['generated_atlas_sha256'] and sha(SOURCE)==req['reference_inputs'][0]['sha256'] and sha(CONTACT)==req['reference_inputs'][1]['sha256']
 atlas=Image.open(ATLAS).convert('RGBA');a=np.asarray(atlas)[:,:,3];labels,n=ndimage.label(a>=245);components=[]
 for i in range(1,n+1):
  y,x=np.nonzero(labels==i)
  if len(x)>=50:components.append((len(x),i,(int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1)))
 if not components:raise RuntimeError('No substantial opaque component')
 components.sort(reverse=True);area,label,box=components[0];crop=atlas.crop(box);scale=TARGET_WIDTH/crop.width;size=(TARGET_WIDTH,max(1,round(crop.height*scale)));crop=crop.resize(size,Image.Resampling.NEAREST);offset=((256-size[0])//2,(256-size[1])//2);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(crop,offset);data=png(canvas);atomic(CAND,data)
 lives=[HERE/f'{OBJ}.{d}.png' for d in DIRECTIONS];before={d:sha(p) for d,p in zip(DIRECTIONS,lives)}
 recipe={'schema_version':1,'status':'candidate-ready-for-independent-review','object_id':OBJ,'direction':'top','request_path':'reusable/views-additional/raw/'+REQ.name,'request_sha256':sha(REQ),'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,'source_atlas_sha256':sha(ATLAS),'canonical_source':'bubble-airship/components/'+SOURCE.name,'canonical_source_sha256':sha(SOURCE),'contact_reference':'reusable/views-additional/'+CONTACT.name,'contact_reference_sha256':sha(CONTACT),'operation':'largest global alpha-connected component at alpha>=245; crop complete bounds; isotropic nearest-neighbor scale to 224px horizontal span; center on transparent 256x256','alpha_threshold':245,'component_label':label,'component_area_px':area,'component_bounds_xyxy_px':list(box),'crop_dimensions_px':[box[2]-box[0],box[3]-box[1]],'scale':scale,'resized_dimensions_px':list(size),'canvas_offset_xy_px':list(offset),'target_width_px':TARGET_WIDTH,'candidate_path':'reusable/views-additional/raw/'+CAND.name,'candidate_sha256':hashlib.sha256(data).hexdigest(),'candidate_rgba_sha256':rgba_hash(canvas),'preinstall_view_hashes':before,'preserved_directions':['front','right','left','bottom','rear'],'inference_note':'Inferred overhead view of vertical arched door seen edge-on; not recovered pixels or calibrated 3D.'}
 atomic(RECIPE,(json.dumps(recipe,indent=2)+'\n').encode())
 cells=[Image.open(SOURCE).convert('RGBA')]+[canvas if d=='top' else Image.open(p).convert('RGBA') for d,p in zip(DIRECTIONS,lives)];sheet=Image.new('RGBA',(7*184,216),(112,112,112,255));draw=ImageDraw.Draw(sheet)
 for i,(cell,labeltxt) in enumerate(zip(cells,['source',*DIRECTIONS])):
  x=i*184;draw.text((x+4,22),labeltxt,fill=(245,245,245,255));cell.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(cell,(x+8+(168-cell.width)//2,42+(168-cell.height)//2))
 atomic(QA,png(sheet));print(json.dumps({'candidate':str(CAND),'candidate_sha256':recipe['candidate_sha256'],'recipe_sha256':sha(RECIPE),'contact':str(QA),'contact_sha256':sha(QA),'bounds':box,'dimensions':size,'scale':scale},indent=2))
if __name__=='__main__':main()
