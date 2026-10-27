#!/usr/bin/env python3
"""Install only root-approved source-bound cap symmetry candidates."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json';VIEWS=('front','top','right','left','bottom','rear')
MAPS={'hunting-zockau-painted-town-brick-endcap-northeast':{'front':'right','rear':'left'},'hunting-zockau-painted-town-brick-endcap-northwest':{'front':'right','rear':'left'},'safe-services-cream-service-tile-endcap-northwest':{'right':'front','left':'front','rear':'front'}}
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
def jatomic(p,x):atomic(p,(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};prepared=[]
 for oid,mapping in MAPS.items():
  source_rec=next(x for x in json.loads((PACK/'manifest.json').read_text())['assets'] if x['id'].removesuffix('--native')==oid);source_rel=f"{source_rec['source']['sheet']}/components/{oid}.png";source=PACK/source_rel;before={v:sha(HERE/f'{oid}.{v}.png') for v in VIEWS}
  for target,donor in mapping.items():
   aid=oid+'.'+target;asset=assets[aid];assert asset['id']==aid and asset['view']==target and asset['image']['path'].endswith(f'{oid}.{target}.png');live=PACK/asset['image']['path'];meta_path=PACK/asset['metadata_path'];assert meta_path==PACK/f'reusable/views-additional/{oid}.{target}.json'
   cand=HERE/'raw'/f'{oid}.{target}-symmetry-v1-candidate.png';recipe_path=HERE/'raw'/f'{oid}.{target}-symmetry-v1.recipe.json';r=json.loads(recipe_path.read_text());assert r['status']=='candidate-ready-for-independent-review' and r['object_id']==oid and r['direction']==target
   assert r['canonical_source']==source_rel and r['canonical_source_sha256']==sha(source) and r['candidate_sha256']==sha(cand)
   for d,h in before.items():assert sha(HERE/f'{oid}.{d}.png')==h,(oid,d)
   meta=json.loads(meta_path.read_text());prior=meta.get('provenance',{});prov={**prior,'superseded_provenance':[*prior.get('superseded_provenance',[]),{k:v for k,v in prior.items() if k!='superseded_provenance'}],'method':'derived-symmetry','source_image':source_rel,'source_sha256':sha(source),'normalization_recipe':'reusable/views-additional/raw/'+recipe_path.name,'normalization_recipe_sha256':sha(recipe_path),'derivation_inputs':[{'path':r['donor_path'],'sha256':r['donor_sha256'],'role':'same-object symmetry donor'}],'notes':r['symmetry_declaration']}
   prepared.append((oid,target,live,meta_path,meta,asset,prov,cand.read_bytes(),before))
 for oid,d,live,mp,meta,a,prov,data,before in prepared:
  atomic(live,data);im=Image.open(live).convert('RGBA');img={'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':sha(live),'rgba_sha256':hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()};meta['image']=img;meta['provenance']=prov;jatomic(mp,meta);a['image']=img;a['provenance']=prov
 for oid in MAPS:groups[oid]['complete']=False
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());jatomic(INDEX,idx)
 reports=[]
 for oid,mapping in MAPS.items():
  src_rec=next(x for x in json.loads((PACK/'manifest.json').read_text())['assets'] if x['id'].removesuffix('--native')==oid);src=PACK/f"{src_rec['source']['sheet']}/components/{oid}.png";cells=[Image.open(src).convert('RGBA')]+[Image.open(HERE/f'{oid}.{v}.png').convert('RGBA') for v in VIEWS];sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));draw=ImageDraw.Draw(sheet)
  for i,(im,label) in enumerate(zip(cells,['source',*VIEWS])):
   x=i*184;draw.text((x+4,22),label,fill=(15,15,15,255));im.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(im,(x+8+(168-im.width)//2,42+(168-im.height)//2))
  import io
  b=io.BytesIO();sheet.save(b,'PNG',optimize=True);contact=HERE/f'qa-{oid}-symmetry-v1-installed-source-six.png';atomic(contact,b.getvalue());reports.append({'object_id':oid,'changed_directions':list(mapping),'current_hashes':{v:sha(HERE/f'{oid}.{v}.png') for v in VIEWS},'source_sha256':sha(src),'contact':contact.name,'contact_sha256':sha(contact),'status':'installed-pending-current-source-six-review'})
 jatomic(HERE/'ink-four-cap-symmetry-v1-install-report.json',{'schema':'ink-four-cap-symmetry-v1-install-report','sets':reports});print(json.dumps(reports,indent=2))
if __name__=='__main__':main()
