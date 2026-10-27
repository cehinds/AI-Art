#!/usr/bin/env python3
"""Normalize four retained source-bound RIGHT/LEFT transition candidates."""
import hashlib,json,os,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];OBJ=['bubble-airship-scrap-metal-deck-edge-transition','bubble-airship-scrap-metal-deck-corner-transition'];D=['right','left'];V=['front','top','right','left','bottom','rear'];ATLAS=HERE/'raw/bubble-airship-scrap-metal-deck-transition-side-profiles-v4-atlas.png';REQ=HERE/'raw/bubble-airship-scrap-metal-deck-transition-side-profiles-v4.request.json';W=212
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
 q=json.loads(REQ.read_text());assert q['status']=='generated-atlas-ready-for-normalization' and sha(ATLAS)==q['generated_atlas_sha256'];im=Image.open(ATLAS).convert('RGBA');xedges=[0,im.width//2,im.width];yedges=[0,im.height//2,im.height];labels,n=ndimage.label(np.asarray(im)[:,:,3]>=245);records=[]
 for row,oid in enumerate(OBJ):
  src_rel=q['reference_inputs'][row]['canonical_source'];src=PACK/src_rel;assert src.exists() and sha(src)==q['reference_inputs'][row]['canonical_source_sha256'];before=q['preinstall_view_hashes'][oid];cands={}
  for col,d in enumerate(D):
   x0,y0=xedges[col],yedges[row];x1,y1=xedges[col+1],yedges[row+1];cx=(x0+x1)/2;cy=(y0+y1)/2;cw=x1-x0;ch=y1-y0;cs=[]
   for k in range(1,n+1):
    ys,xs=np.nonzero(labels[y0:y1,x0:x1]==k)
    if len(xs)>=60:
     gx=xs+x0;gy=ys+y0;dist=((gx.mean()-cx)/cw)**2+((gy.mean()-cy)/ch)**2;cs.append((dist,len(xs),k,(int(gx.min()),int(gy.min()),int(gx.max())+1,int(gy.max())+1)))
   assert cs,(oid,d);cs.sort();main=cs[0];keep=[c for c in cs if c[1]>=main[1]*.02 and c[0]<=main[0]+.08];box=(min(c[3][0] for c in keep),min(c[3][1] for c in keep),max(c[3][2] for c in keep),max(c[3][3] for c in keep));crop=im.crop(box);scale=W/crop.width;size=(W,max(1,round(crop.height*scale)));crop=crop.resize(size,Image.Resampling.NEAREST);off=((256-size[0])//2,(256-size[1])//2);out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(crop,off);cand=HERE/'raw'/f'{oid}.{d}-sideprofile-v4-candidate.png';data=png(out);atomic(cand,data)
   rp=HERE/'raw'/f'{oid}.{d}-sideprofile-v4-candidate.recipe.json';recipe={'schema_version':1,'status':'candidate-ready-for-independent-review','object_id':oid,'direction':d,'request_path':'reusable/views-additional/raw/'+REQ.name,'request_sha256':sha(REQ),'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,'source_atlas_sha256':sha(ATLAS),'canonical_source':src_rel,'canonical_source_sha256':sha(src),'operation':'nearest logical-cell center among full alpha>=245 connected components; retain main plus >=2% fragments within cell; full component union bounds; isotropic nearest-neighbor scale to 212px width; centered transparent 256 canvas','alpha_threshold':245,'logical_cell':{'row':row,'column':col,'bounds_xyxy_px':[x0,y0,x1,y1]},'component_labels':[c[2] for c in keep],'component_bounds_xyxy_px':list(box),'scale':scale,'resized_dimensions_px':list(size),'canvas_offset_xy_px':list(off),'candidate_path':'reusable/views-additional/raw/'+cand.name,'candidate_sha256':hashlib.sha256(data).hexdigest(),'preinstall_view_hashes':before,'preserved_directions':[v for v in V if v!=d],'inference_note':'Horizontal side elevation; slab-depth orientation and rail height inferred from canonical source plan, not recovered pixels/calibrated 3D.'};atomic(rp,(json.dumps(recipe,indent=2)+'\n').encode());cands[d]=out
  cells=[Image.open(src).convert('RGBA')]+[cands.get(v,Image.open(HERE/f'{oid}.{v}.png').convert('RGBA')) for v in V];sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));dr=ImageDraw.Draw(sheet)
  for i,(cell,label) in enumerate(zip(cells,['source',*V])):
   x=i*184;dr.text((x+4,22),label,fill=(15,15,15,255));cell.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(cell,(x+8+(168-cell.width)//2,42+(168-cell.height)//2))
  contact=HERE/f'qa-{oid}-sideprofile-v4-candidate-source-six.png';atomic(contact,png(sheet));records.append({'object_id':oid,'source_sha256':sha(src),'candidate_sha256':{d:sha(HERE/'raw'/f'{oid}.{d}-sideprofile-v4-candidate.png') for d in D},'recipe_sha256':{d:sha(HERE/'raw'/f'{oid}.{d}-sideprofile-v4-candidate.recipe.json') for d in D},'contact':contact.name,'contact_sha256':sha(contact),'preinstall_hashes':before})
 print(json.dumps(records,indent=2))
if __name__=='__main__':main()
