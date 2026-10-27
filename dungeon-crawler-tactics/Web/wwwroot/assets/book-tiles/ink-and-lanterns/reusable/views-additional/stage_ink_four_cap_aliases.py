#!/usr/bin/env python3
"""Stage source-bound same-object endcap symmetry candidates for review."""
import hashlib,json,os,tempfile
from pathlib import Path
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json'
PLANS={
 'hunting-zockau-painted-town-brick-endcap-northeast':{'front':'right','rear':'left'},
 'hunting-zockau-painted-town-brick-endcap-northwest':{'front':'right','rear':'left'},
 'safe-services-cream-service-tile-endcap-northwest':{'right':'front','left':'front','rear':'front'},
}
VIEWS=('front','top','right','left','bottom','rear')
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
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};manifest=json.loads((PACK/'manifest.json').read_text())['assets'];sources={a['id'].removesuffix('--native'):a for a in manifest};out={}
 for oid,mapping in PLANS.items():
  source_rec=sources[oid];source=PACK/f"{source_rec['source']['sheet']}/components/{oid}.png";before={d:sha(HERE/f'{oid}.{d}.png') for d in VIEWS};candidates={}
  for target,donor in mapping.items():
   donor_path=HERE/f'{oid}.{donor}.png';candidate=HERE/'raw'/f'{oid}.{target}-symmetry-v1-candidate.png';data=donor_path.read_bytes();atomic(candidate,data)
   recipe={'schema_version':1,'status':'candidate-ready-for-independent-review','object_id':oid,'direction':target,'operation':'exact same-object symmetry alias; no geometric rescaling or recoloring','canonical_source':f"{source_rec['source']['sheet']}/components/{oid}.png",'canonical_source_sha256':sha(source),'donor_asset_id':f'{oid}.{donor}','donor_path':f'reusable/views-additional/{oid}.{donor}.png','donor_sha256':sha(donor_path),'candidate_path':f'reusable/views-additional/raw/{candidate.name}','candidate_sha256':hashlib.sha256(data).hexdigest(),'preinstall_view_hashes':before,'preserved_directions':[d for d in VIEWS if d!=target],'symmetry_declaration':f'{target} uses the same compact endcap face as {donor}, inferred from the target source’s cube-like symmetric cap; canonical target source remains bound.'}
   rp=HERE/'raw'/f'{oid}.{target}-symmetry-v1.recipe.json';atomic(rp,(json.dumps(recipe,indent=2)+'\n').encode());candidates[target]=Image.open(candidate).convert('RGBA')
  cells=[Image.open(source).convert('RGBA')]
  for d in VIEWS:cells.append(candidates[d] if d in candidates else Image.open(HERE/f'{oid}.{d}.png').convert('RGBA'))
  sheet=Image.new('RGBA',(7*184,216),(112,112,112,255));draw=ImageDraw.Draw(sheet)
  for col,(im,label) in enumerate(zip(cells,['source',*VIEWS])):
   x=col*184;draw.text((x+4,22),label,fill=(245,245,245,255));im.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(im,(x+8+(168-im.width)//2,42+(168-im.height)//2))
  contact=HERE/f'qa-{oid}-symmetry-v1-candidate-source-six.png';atomic(contact,png(sheet))
  out[oid]={'mapping':mapping,'candidate_sha256':{d:sha(HERE/'raw'/f'{oid}.{d}-symmetry-v1-candidate.png') for d in mapping},'recipe_sha256':{d:sha(HERE/'raw'/f'{oid}.{d}-symmetry-v1.recipe.json') for d in mapping},'contact':contact.name,'contact_sha256':sha(contact),'source_sha256':sha(source),'preinstall_hashes':before}
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
