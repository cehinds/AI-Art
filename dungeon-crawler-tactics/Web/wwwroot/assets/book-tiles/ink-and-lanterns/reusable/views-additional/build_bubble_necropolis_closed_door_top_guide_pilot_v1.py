#!/usr/bin/env python3
"""Normalize one geometry-guided necropolis closed-door TOP pilot."""
import hashlib,json,os,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];OBJ='bubble-necropolis-ancient-tomb-masonry-closed-doorway';REQ=HERE/'raw/bubble-necropolis-closed-door-top-guide-pilot-v1.request.json';ATLAS=HERE/'raw/bubble-necropolis-closed-door-top-guide-pilot-v1-atlas.png';SOURCE=PACK/'bubble-necropolis/components'/f'{OBJ}.png';TARGET=HERE/f'{OBJ}.top.png';W=212
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
 q=json.loads(REQ.read_text());assert q['status']=='generated-atlas-ready-for-normalization';assert sha(ATLAS)==q['generated_atlas_sha256'] and sha(SOURCE)==q['reference_inputs'][1]['sha256'];im=Image.open(ATLAS).convert('RGBA');lab,n=ndimage.label(np.asarray(im)[:,:,3]>=245);cc=[]
 for k in range(1,n+1):
  ys,xs=np.nonzero(lab==k)
  if len(xs)>=50:cc.append((len(xs),k,(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)))
 assert cc;cc.sort(reverse=True);main=cc[0][0];keep=[x for x in cc if x[0]>=main*.02];box=(min(x[2][0] for x in keep),min(x[2][1] for x in keep),max(x[2][2] for x in keep),max(x[2][3] for x in keep));crop=im.crop(box);scale=W/crop.width;size=(W,max(1,round(crop.height*scale)));crop=crop.resize(size,Image.Resampling.NEAREST);off=((256-size[0])//2,(256-size[1])//2);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(crop,off);cand=HERE/'raw'/f'{OBJ}.top-guide-pilot-v1-candidate.png';data=png(canvas);atomic(cand,data);before={v:sha(HERE/f'{OBJ}.{v}.png') for v in ['front','top','right','left','bottom','rear']};recipe={'schema_version':1,'status':'candidate-ready-for-independent-review','object_id':OBJ,'direction':'top','request_path':'reusable/views-additional/raw/'+REQ.name,'request_sha256':sha(REQ),'generated_atlas':'reusable/views-additional/raw/'+ATLAS.name,'generated_atlas_sha256':sha(ATLAS),'canonical_source':'bubble-necropolis/components/'+SOURCE.name,'canonical_source_sha256':sha(SOURCE),'geometry_template':q['reference_inputs'][0]['path'],'geometry_template_sha256':q['reference_inputs'][0]['sha256'],'operation':'full alpha>=245 connected component bounds with all components >=2% largest; isotropic nearest-neighbor scale to 212 px width; centered on transparent 256 canvas','component_labels':[x[1] for x in keep],'component_bounds_xyxy_px':list(box),'scale':scale,'resized_dimensions_px':list(size),'canvas_offset_xy_px':list(off),'candidate_path':'reusable/views-additional/raw/'+cand.name,'candidate_sha256':hashlib.sha256(data).hexdigest(),'preinstall_view_hashes':before,'preserved_directions':['front','right','left','bottom','rear'],'inference_note':'Inferred top principal projection using root-approved doorway geometry donor with canonical Ink source material. Not recovered pixels or calibrated 3D.'};rp=HERE/'raw'/f'{OBJ}.top-guide-pilot-v1-candidate.recipe.json';atomic(rp,(json.dumps(recipe,indent=2)+'\n').encode());cells=[Image.open(SOURCE).convert('RGBA')]+[canvas if v=='top' else Image.open(HERE/f'{OBJ}.{v}.png').convert('RGBA') for v in ['front','top','right','left','bottom','rear']];sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));dr=ImageDraw.Draw(sheet)
 for i,(cell,label) in enumerate(zip(cells,['source','front','top','right','left','bottom','rear'])):
  x=i*184;dr.text((x+4,22),label,fill=(15,15,15,255));cell.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(cell,(x+8+(168-cell.width)//2,42+(168-cell.height)//2))
 contact=HERE/f'qa-{OBJ}-top-guide-pilot-v1-candidate-source-six.png';atomic(contact,png(sheet));print(json.dumps({'candidate':cand.name,'candidate_sha256':recipe['candidate_sha256'],'recipe_sha256':sha(rp),'contact':contact.name,'contact_sha256':sha(contact),'bounds':box,'scale':scale},indent=2))
if __name__=='__main__':main()
