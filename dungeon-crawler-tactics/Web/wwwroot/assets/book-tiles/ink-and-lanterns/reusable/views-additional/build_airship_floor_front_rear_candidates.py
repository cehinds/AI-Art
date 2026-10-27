#!/usr/bin/env python3
"""Extract a 3x2 source-faithful atlas into three front/rear floor candidates."""
import hashlib, json, os, struct, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE=Path(__file__).resolve().parent
PACK=HERE.parents[1]
IDS=('bubble-airship-scrap-metal-deck-floor','bubble-airship-wet-scrap-metal-deck-floor','bubble-airship-worn-scrap-metal-deck-floor')
DIRS=('front','rear')
ATLAS=HERE/'raw'/'bubble-airship-scrap-metal-deck-floors-front-rear-v1-atlas.png'
REQUEST=HERE/'raw'/'bubble-airship-scrap-metal-deck-floors-front-rear-v1.request.json'
TARGET_WIDTH=232
ALPHA_THRESHOLD=245
MIN_COMPONENT=100
EXPECTED_CENTERS={('row1','front'):(330,336),('row1','rear'):(923,336),('row2','front'):(330,670),('row2','rear'):(923,670),('row3','front'):(330,1020),('row3','rear'):(923,1020)}

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
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',im.width,im.height)+im.convert('RGBA').tobytes()).hexdigest()

def main():
 req=json.loads(REQUEST.read_text().removesuffix('\\n'))
 assert req['request_id']=='bubble-airship-scrap-metal-deck-floors-front-rear-v1'
 assert req['status']=='generated-atlas-ready-for-normalization' and sha(ATLAS)==req['generated_atlas_sha256']
 for ref in req['reference_inputs']:
  assert sha(PACK/ref['path'])==ref['sha256'],ref['path']
 for oid in IDS:
  for d,expected in req['preinstall_view_hashes'][oid].items():
   assert sha(HERE/f'{oid}.{d}.png')==expected,(oid,d)
 atlas=Image.open(ATLAS).convert('RGBA');alpha=np.asarray(atlas)[:,:,3];labels,n=ndimage.label(alpha>=ALPHA_THRESHOLD);comps=[]
 for label in range(1,n+1):
  ys,xs=np.nonzero(labels==label)
  if len(xs)>=MIN_COMPONENT:comps.append({'label':label,'area':len(xs),'bounds':[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1],'center':[float(xs.mean()),float(ys.mean())]})
 if len(comps)!=6:raise RuntimeError(f'Expected exactly six significant alpha components, found {len(comps)}')
 assigned={}
 remaining=comps[:]
 for key,pt in EXPECTED_CENTERS.items():
  best=min(remaining,key=lambda c:(c['center'][0]-pt[0])**2+(c['center'][1]-pt[1])**2)
  distance=((best['center'][0]-pt[0])**2+(best['center'][1]-pt[1])**2)**.5
  if distance>220:raise RuntimeError(f'Component assignment too far for {key}: {distance:.1f}')
  assigned[key]=best;remaining.remove(best)
 results={}
 for row,oid in enumerate(IDS,1):
  source=PACK/'bubble-airship'/'components'/f'{oid}.png';source_hash=sha(source)
  current={d:sha(HERE/f'{oid}.{d}.png') for d in ('front','top','right','left','bottom','rear')}
  for direction in DIRS:
   component=assigned[(f'row{row}',direction)];box=component['bounds'];crop=atlas.crop(tuple(box));scale=TARGET_WIDTH/crop.width;size=(TARGET_WIDTH,max(1,round(crop.height*scale)));crop=crop.resize(size,Image.Resampling.NEAREST);offset=((256-size[0])//2,(256-size[1])//2);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(crop,offset);data=png(canvas)
   candidate=HERE/'raw'/f'{oid}.{direction}-v1-candidate.png';atomic(candidate,data)
   recipe={'schema_version':1,'status':'candidate-ready-for-independent-review','object_id':oid,'direction':direction,'request_path':'reusable/views-additional/raw/'+REQUEST.name,'request_sha256':sha(REQUEST),'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,'source_atlas_sha256':sha(ATLAS),'canonical_source':'bubble-airship/components/'+source.name,'canonical_source_sha256':source_hash,'operation':'assign complete global alpha-connected component by row/column centroid; crop full component bounds; isotropic nearest-neighbor scale to 232 px horizontal extent; center on transparent 256x256','alpha_threshold':ALPHA_THRESHOLD,'component_label':component['label'],'component_area_px':component['area'],'component_center_global_px':component['center'],'component_bounds_xyxy_px':box,'crop_dimensions_px':[box[2]-box[0],box[3]-box[1]],'scale':scale,'resized_dimensions_px':list(size),'canvas_offset_xy_px':list(offset),'target_width_px':TARGET_WIDTH,'candidate_path':'reusable/views-additional/raw/'+candidate.name,'candidate_sha256':hashlib.sha256(data).hexdigest(),'candidate_rgba_sha256':rgba_sha(canvas),'preinstall_view_hashes':current,'preserved_directions':['top','right','left','bottom','rear'] if direction=='front' else ['front','top','right','left','bottom'],'inference_note':'Inferred horizontal floor-edge elevation; not recovered pixels or calibrated 3D.'}
   rp=HERE/'raw'/f'{oid}.{direction}-v1-candidate.recipe.json';atomic(rp,(json.dumps(recipe,indent=2)+'\n').encode());results[(oid,direction)]=(candidate,canvas,recipe,rp)
  # One source-plus-six current candidate contact per floor object.
  cells=[Image.open(source).convert('RGBA')]
  for d in ('front','top','right','left','bottom','rear'):
   cells.append(results[(oid,d)][1] if d in DIRS else Image.open(HERE/f'{oid}.{d}.png').convert('RGBA'))
  sheet=Image.new('RGBA',(7*184,216),(112,112,112,255));draw=ImageDraw.Draw(sheet)
  for col,(cell,label) in enumerate(zip(cells,['source','front','top','right','left','bottom','rear'])):
   x=col*184;draw.text((x+4,22),label,fill=(245,245,245,255));cell.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(cell,(x+8+(168-cell.width)//2,42+(168-cell.height)//2))
  contact=HERE/f'qa-{oid}-front-rear-v1-candidate-source-six.png';atomic(contact,png(sheet))
  results[oid]={'contact':contact.name,'contact_sha256':sha(contact),'candidate_hashes':{d:results[(oid,d)][2]['candidate_sha256'] for d in DIRS},'recipe_hashes':{d:sha(results[(oid,d)][3]) for d in DIRS}}
 print(json.dumps({o:results[o] for o in IDS},indent=2))

if __name__=='__main__':main()
