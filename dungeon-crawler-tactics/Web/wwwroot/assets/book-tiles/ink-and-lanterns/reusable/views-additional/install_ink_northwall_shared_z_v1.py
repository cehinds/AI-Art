#!/usr/bin/env python3
"""Install approved isotropic side-height corrections for six NW walls."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json';IDS=['broadcast-portals-studio-partition-wall-northwest','bubble-airship-riveted-scrap-hull-wall-northwest','bubble-desert-adobe-desert-plaster-wall-northwest','bubble-sea-submarine-metal-hull-wall-northwest','hunting-shrines-village-stone-wall-northwest','hunting-zockau-painted-town-brick-wall-northwest'];VIEWS=('front','top','right','left','bottom','rear')
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
 manifest=json.loads((PACK/'manifest.json').read_text())['assets'];srcs={a['id'].removesuffix('--native'):a for a in manifest};idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};prepared=[]
 for oid in IDS:
  rec=srcs[oid];source_rel=f"{rec['source']['sheet']}/components/{oid}.png";source=PACK/source_rel;assert source.exists()
  for d in ('right','left'):
   rp=HERE/'raw'/f'{oid}.{d}-shared-z-v1-candidate.recipe.json';r=json.loads(rp.read_text());cand=HERE/'raw'/f'{oid}.{d}-shared-z-v1-candidate.png';assert r['object_id']==oid and r['direction']==d and r['status']=='candidate-ready-for-independent-review' and r['candidate_sha256']==sha(cand) and r['canonical_source']==source_rel and r['canonical_source_sha256']==sha(source)
   aid=oid+'.'+d;a=assets[aid];assert a['id']==aid and a['view']==d and a['image']['path'].endswith(f'{oid}.{d}.png');live=PACK/a['image']['path'];mp=PACK/a['metadata_path'];assert mp==PACK/f'reusable/views-additional/{oid}.{d}.json'
   for v,h in r['preinstall_view_hashes'].items():assert sha(HERE/f'{oid}.{v}.png')==h,(oid,v)
   meta=json.loads(mp.read_text());prior=meta.get('provenance',{});prov={**prior,'superseded_provenance':[*prior.get('superseded_provenance',[]),{k:v for k,v in prior.items() if k!='superseded_provenance'}],'method':'derived-isotropic-normalization','source_image':source_rel,'source_sha256':sha(source),'normalization_recipe':'reusable/views-additional/raw/'+rp.name,'normalization_recipe_sha256':sha(rp),'derivation_inputs':[{'path':r['input_png'],'sha256':r['input_sha256']},*r['reference_pngs'].values()],'notes':r['inference_note']}
   prepared.append((oid,d,live,mp,meta,a,prov,cand.read_bytes()))
 for oid,d,live,mp,meta,a,prov,data in prepared:
  atomic(live,data);im=Image.open(live).convert('RGBA');image={'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':sha(live),'rgba_sha256':hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()};meta['image']=image;meta['provenance']=prov;jatomic(mp,meta);a['image']=image;a['provenance']=prov
 for oid in IDS:groups[oid]['complete']=False
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());jatomic(INDEX,idx)
 report=[]
 for oid in IDS:
  rec=srcs[oid];source=PACK/rec['source']['sheet']/'components'/f'{oid}.png';cells=[Image.open(source).convert('RGBA')]+[Image.open(HERE/f'{oid}.{v}.png').convert('RGBA') for v in VIEWS];sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));draw=ImageDraw.Draw(sheet)
  for i,(im,label) in enumerate(zip(cells,['source',*VIEWS])):
   x=i*184;draw.text((x+4,22),label,fill=(15,15,15,255));im.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(im,(x+8+(168-im.width)//2,42+(168-im.height)//2))
  import io
  b=io.BytesIO();sheet.save(b,'PNG',optimize=True);contact=HERE/f'qa-{oid}-shared-z-v1-installed-source-six.png';atomic(contact,b.getvalue());report.append({'object_id':oid,'source_sha256':sha(source),'current_hashes':{v:sha(HERE/f'{oid}.{v}.png') for v in VIEWS},'contact':contact.name,'contact_sha256':sha(contact)})
 jatomic(HERE/'ink-northwall-shared-z-v1-install-report.json',{'schema':'ink-northwall-shared-z-v1-install','status':'installed-pending-current-source-six-review','sets':report});print(json.dumps(report,indent=2))
if __name__=='__main__':main()
