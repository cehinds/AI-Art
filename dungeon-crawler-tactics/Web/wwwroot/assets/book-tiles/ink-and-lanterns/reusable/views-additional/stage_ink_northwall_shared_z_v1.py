#!/usr/bin/env python3
"""Stage isotropic side-end elevation normalization for six north-wall sets."""
import hashlib,json,os,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];VIEWS=('front','top','right','left','bottom','rear')
IDS=['broadcast-portals-studio-partition-wall-northwest','bubble-airship-riveted-scrap-hull-wall-northwest','bubble-desert-adobe-desert-plaster-wall-northwest','bubble-sea-submarine-metal-hull-wall-northwest','hunting-shrines-village-stone-wall-northwest','hunting-zockau-painted-town-brick-wall-northwest']
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
 manifest=json.loads((PACK/'manifest.json').read_text())['assets'];srcs={a['id'].removesuffix('--native'):a for a in manifest};out=[]
 for oid in IDS:
  rec=srcs[oid];src_rel=f"{rec['source']['sheet']}/components/{oid}.png";src=PACK/src_rel;assert src.exists();imgs={v:Image.open(HERE/f'{oid}.{v}.png').convert('RGBA') for v in VIEWS};before={v:sha(HERE/f'{oid}.{v}.png') for v in VIEWS};ref_heights=[]
  for v in ('front','rear'):
   bb=imgs[v].getchannel('A').getbbox();assert bb;ref_heights.append(bb[3]-bb[1])
  target=round(sum(ref_heights)/len(ref_heights));candidates={}
  for d in ('right','left'):
   im=imgs[d];bb=im.getchannel('A').getbbox();assert bb;crop=im.crop(bb);scale=target/(bb[3]-bb[1]);size=(round(crop.width*scale),target);crop=crop.resize(size,Image.Resampling.NEAREST);off=((256-size[0])//2,(256-size[1])//2);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(crop,off);cand=HERE/'raw'/f'{oid}.{d}-shared-z-v1-candidate.png';data=png(canvas);atomic(cand,data)
   recipe={'schema_version':1,'status':'candidate-ready-for-independent-review','object_id':oid,'direction':d,'canonical_source':src_rel,'canonical_source_sha256':sha(src),'operation':'isotropic nearest-neighbor scale only; crop full alpha bounds, normalize end-elevation world Z to mean FRONT/REAR alpha height, preserve aspect ratio, center on transparent 256 canvas','input_png':'reusable/views-additional/'+f'{oid}.{d}.png','input_sha256':before[d],'reference_pngs':{v:{'path':'reusable/views-additional/'+f'{oid}.{v}.png','sha256':before[v]} for v in ('front','rear')},'reference_heights_px':ref_heights,'target_height_px':target,'input_bounds_xyxy_px':list(bb),'scale':scale,'resized_dimensions_px':list(size),'canvas_offset_xy_px':list(off),'candidate_path':'reusable/views-additional/raw/'+cand.name,'candidate_sha256':hashlib.sha256(data).hexdigest(),'preinstall_view_hashes':before,'preserved_directions':[v for v in VIEWS if v!=d],'inference_note':'North-wall side-end elevations share world Z with front/rear; inferred normalization, not calibrated 3D.'}
   rp=HERE/'raw'/f'{oid}.{d}-shared-z-v1-candidate.recipe.json';atomic(rp,(json.dumps(recipe,indent=2)+'\n').encode());candidates[d]=canvas
  cells=[Image.open(src).convert('RGBA')]+[candidates.get(v,imgs[v]) for v in VIEWS];sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));draw=ImageDraw.Draw(sheet)
  for i,(im,label) in enumerate(zip(cells,['source',*VIEWS])):
   x=i*184;draw.text((x+4,22),label,fill=(15,15,15,255));im.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(im,(x+8+(168-im.width)//2,42+(168-im.height)//2))
  contact=HERE/f'qa-{oid}-shared-z-v1-candidate-source-six.png';atomic(contact,png(sheet));out.append({'object_id':oid,'source_sha256':sha(src),'target_height_px':target,'candidates':{d:{'sha256':sha(HERE/'raw'/f'{oid}.{d}-shared-z-v1-candidate.png'),'recipe_sha256':sha(HERE/'raw'/f'{oid}.{d}-shared-z-v1-candidate.recipe.json')} for d in candidates},'contact':contact.name,'contact_sha256':sha(contact),'preinstall_hashes':before})
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
