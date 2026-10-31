#!/usr/bin/env python3
"""Normalize retained source-bound Airship transition profiles into staged candidates."""
import hashlib,json,os,tempfile,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];ATLAS=HERE/'raw/bubble-airship-scrap-metal-deck-transitions-front-rear-v1-atlas.png';REQ=HERE/'raw/bubble-airship-scrap-metal-deck-transitions-front-rear-v1.request.json'
OBJECTS=['bubble-airship-scrap-metal-deck-edge-transition','bubble-airship-scrap-metal-deck-corner-transition'];DIRECTIONS=['front','rear'];VIEWS=['front','top','right','left','bottom','rear'];W=212

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
 q=json.loads(REQ.read_text());assert q['status']=='generated-atlas-ready-for-normalization' and sha(ATLAS)==q['generated_atlas_sha256']
 atlas=Image.open(ATLAS).convert('RGBA');xedges=[0,atlas.width//2,atlas.width];yedges=[0,atlas.height//2,atlas.height];alpha=np.asarray(atlas)[:,:,3];lab,n=ndimage.label(alpha>=245);records={};contacts=[]
 for row,oid in enumerate(OBJECTS):
  src_rel=q['reference_inputs'][row]['path'];src=PACK/src_rel;assert src.exists() and sha(src)==q['reference_inputs'][row]['sha256']
  before={v:sha(HERE/f'{oid}.{v}.png') for v in VIEWS}; candidates={}
  for col,d in enumerate(DIRECTIONS):
   x0,y0=xedges[col],yedges[row];x1,y1=xedges[col+1],yedges[row+1];cw,ch=x1-x0,y1-y0;cx=(x0+x1)/2;cy=(y0+y1)/2;comps=[]
   for k in range(1,n+1):
    cyi,cxi=np.nonzero(lab[y0:y1,x0:x1]==k)
    if len(cxi)>=50:
     gx=cxi+x0;gy=cyi+y0;dist=((gx.mean()-cx)/cw)**2+((gy.mean()-cy)/ch)**2;comps.append((dist,len(cxi),k,(int(gx.min()),int(gy.min()),int(gx.max())+1,int(gy.max())+1)))
   assert comps,(oid,d,'no components in cell')
   comps.sort();main=comps[0];keep=[z for z in comps if z[1]>=main[1]*.02 and z[0]<=main[0]+.08]
   bx=(min(z[3][0] for z in keep),min(z[3][1] for z in keep),max(z[3][2] for z in keep),max(z[3][3] for z in keep));crop=atlas.crop(bx);s=W/crop.width;size=(W,max(1,round(crop.height*s)));crop=crop.resize(size,Image.Resampling.NEAREST);off=((256-size[0])//2,(256-size[1])//2);out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(crop,off);candidate=HERE/'raw'/f'{oid}.{d}-profile-v1-candidate.png';data=png(out);atomic(candidate,data)
   recipe={'schema_version':1,'status':'candidate-ready-for-independent-review','object_id':oid,'direction':d,'request_path':'reusable/views-additional/raw/'+REQ.name,'request_sha256':sha(REQ),'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,'source_atlas_sha256':sha(ATLAS),'canonical_source':src_rel,'canonical_source_sha256':sha(src),'operation':'select full alpha>=245 connected-component bounds assigned to the nearest logical-cell center; retain secondary components >=2% of largest when within cell; isotropic nearest-neighbor resize to 212 px width; center on transparent 256 canvas','alpha_threshold':245,'logical_cell':{'row':row,'column':col,'bounds_xyxy_px':[x0,y0,x1,y1]},'component_labels':[z[2] for z in keep],'component_bounds_xyxy_px':list(bx),'crop_dimensions_px':[bx[2]-bx[0],bx[3]-bx[1]],'scale':s,'resized_dimensions_px':list(size),'canvas_offset_xy_px':list(off),'candidate_path':'reusable/views-additional/raw/'+candidate.name,'candidate_sha256':hashlib.sha256(data).hexdigest(),'preinstall_view_hashes':before,'preserved_directions':[v for v in VIEWS if v!=d],'inference_note':'Inferred principal horizontal floor-edge elevation; preserve one-sided/L boundary state from canonical source. Not recovered pixels or calibrated 3D.'}
   rp=HERE/'raw'/f'{oid}.{d}-profile-v1-candidate.recipe.json';atomic(rp,(json.dumps(recipe,indent=2)+'\n').encode());candidates[d]=out
  cells=[Image.open(src).convert('RGBA')]+[candidates.get(v,Image.open(HERE/f'{oid}.{v}.png').convert('RGBA')) for v in VIEWS];sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));draw=ImageDraw.Draw(sheet)
  for i,(im,label) in enumerate(zip(cells,['source',*VIEWS])):
   x=i*184;draw.text((x+4,22),label,fill=(15,15,15,255));im.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(im,(x+8+(168-im.width)//2,42+(168-im.height)//2))
  contact=HERE/f'qa-{oid}-front-rear-profile-v1-candidate-source-six.png';atomic(contact,png(sheet));records[oid]={'candidate_sha256':{d:sha(HERE/'raw'/f'{oid}.{d}-profile-v1-candidate.png') for d in DIRECTIONS},'recipe_sha256':{d:sha(HERE/'raw'/f'{oid}.{d}-profile-v1-candidate.recipe.json') for d in DIRECTIONS},'source_sha256':sha(src),'contact':contact.name,'contact_sha256':sha(contact),'preinstall_hashes':before}
 print(json.dumps(records,indent=2))
if __name__=='__main__':main()
