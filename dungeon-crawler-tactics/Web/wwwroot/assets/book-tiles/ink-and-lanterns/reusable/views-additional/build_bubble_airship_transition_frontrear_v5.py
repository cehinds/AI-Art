#!/usr/bin/env python3
"""Normalize retained front/rear transition profiles and assemble full source contacts."""
import hashlib,json,os,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];IDS=['bubble-airship-scrap-metal-deck-edge-transition','bubble-airship-scrap-metal-deck-corner-transition'];DIRS=['front','rear'];VIEWS=['front','top','right','left','bottom','rear'];ATLAS=HERE/'raw/bubble-airship-scrap-metal-deck-transition-front-rear-v5-atlas.png';REQ=HERE/'raw/bubble-airship-scrap-metal-deck-transition-front-rear-v5.request.json';W=212
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
 q=json.loads(REQ.read_text());assert q['status']=='generated-atlas-ready-for-normalization' and sha(ATLAS)==q['generated_atlas_sha256'];im=Image.open(ATLAS).convert('RGBA');xe=[0,im.width//2,im.width];ye=[0,im.height//2,im.height];labels,n=ndimage.label(np.asarray(im)[:,:,3]>=245);out=[];manifest=json.load(open(PACK/'manifest.json'))['assets'];srcs={a['id'].removesuffix('--native'):a for a in manifest}
 for row,oid in enumerate(IDS):
  src_rec=srcs[oid];src=PACK/src_rec['source']['sheet']/'components'/f'{oid}.png';assert src.exists() and sha(src)==q['reference_inputs'][row]['canonical_source_sha256'];cands={}
  for col,d in enumerate(DIRS):
   x0,y0=xe[col],ye[row];x1,y1=xe[col+1],ye[row+1];cx=(x0+x1)/2;cy=(y0+y1)/2;cs=[]
   for k in range(1,n+1):
    ys,xs=np.nonzero(labels[y0:y1,x0:x1]==k)
    if len(xs)>=60:
     gx=xs+x0;gy=ys+y0;dist=((gx.mean()-cx)/(x1-x0))**2+((gy.mean()-cy)/(y1-y0))**2;cs.append((dist,len(xs),k,(int(gx.min()),int(gy.min()),int(gx.max())+1,int(gy.max())+1)))
   assert cs,(oid,d);cs.sort();main=cs[0];keep=[c for c in cs if c[1]>=main[1]*.02 and c[0]<=main[0]+.08];box=(min(c[3][0] for c in keep),min(c[3][1] for c in keep),max(c[3][2] for c in keep),max(c[3][3] for c in keep));crop=im.crop(box);scale=W/crop.width;size=(W,max(1,round(crop.height*scale)));crop=crop.resize(size,Image.Resampling.NEAREST);off=((256-size[0])//2,(256-size[1])//2);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(crop,off);cand=HERE/'raw'/f'{oid}.{d}-profile-v5-candidate.png';data=png(canvas);atomic(cand,data);before=q['preinstall_view_hashes'][oid]
   rp=HERE/'raw'/f'{oid}.{d}-profile-v5-candidate.recipe.json';recipe={'schema_version':1,'status':'candidate-ready-for-independent-review','object_id':oid,'direction':d,'request_path':'reusable/views-additional/raw/'+REQ.name,'request_sha256':sha(REQ),'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,'source_atlas_sha256':sha(ATLAS),'canonical_source':'bubble-airship/components/'+src.name,'canonical_source_sha256':sha(src),'operation':'assign full alpha>=245 connected components to nearest logical cell center, retain >=2% components near cell; crop union bounds; isotropic nearest-neighbor scale to 212px width; center transparent 256 canvas','alpha_threshold':245,'logical_cell':{'row':row,'column':col,'bounds_xyxy_px':[x0,y0,x1,y1]},'component_labels':[c[2] for c in keep],'component_bounds_xyxy_px':list(box),'scale':scale,'resized_dimensions_px':list(size),'canvas_offset_xy_px':list(off),'candidate_path':'reusable/views-additional/raw/'+cand.name,'candidate_sha256':hashlib.sha256(data).hexdigest(),'preinstall_view_hashes':before,'preserved_directions':[v for v in VIEWS if v!=d],'inference_note':'Horizontal floor-edge elevation with rail at shared Z; inferred, not recovered pixels or calibrated 3D.'};atomic(rp,(json.dumps(recipe,indent=2)+'\n').encode());cands[d]=canvas
  cells=[Image.open(src).convert('RGBA')]+[cands.get(v,Image.open(HERE/f'{oid}.{v}.png').convert('RGBA')) for v in VIEWS];sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));dr=ImageDraw.Draw(sheet)
  for i,(cell,label) in enumerate(zip(cells,['source',*VIEWS])):
   x=i*184;dr.text((x+4,22),label,fill=(15,15,15,255));cell.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(cell,(x+8+(168-cell.width)//2,42+(168-cell.height)//2))
  contact=HERE/f'qa-{oid}-profile-v5-candidate-source-six.png';atomic(contact,png(sheet));out.append({'object_id':oid,'source_sha256':sha(src),'candidate_sha256':{d:sha(HERE/'raw'/f'{oid}.{d}-profile-v5-candidate.png') for d in DIRS},'recipe_sha256':{d:sha(HERE/'raw'/f'{oid}.{d}-profile-v5-candidate.recipe.json') for d in DIRS},'contact':contact.name,'contact_sha256':sha(contact),'preinstall_hashes':q['preinstall_view_hashes'][oid]})
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
