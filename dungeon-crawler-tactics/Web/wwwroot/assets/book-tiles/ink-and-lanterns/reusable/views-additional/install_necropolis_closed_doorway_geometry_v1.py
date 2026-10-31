#!/usr/bin/env python3
"""Install root-approved Necropolis doorway planes with source and target hash guards."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json';OID='bubble-necropolis-ancient-tomb-masonry-closed-doorway';VIEWS=('front','top','right','left','bottom','rear')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def atomic(p,b):
 fd,t=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 except BaseException:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def jatomic(p,d):atomic(p,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};assert OID in groups
 source=PACK/'bubble-necropolis/components'/f'{OID}.png';expected_source='f6aea905718aa4990301f87bbb06cf5e6d60624d3a2f3c42592b5fc54474875a';assert sha(source)==expected_source
 specs={
 'right':('raw/'+OID+'.right-geometry-v2-candidate.png','raw/'+OID+'.right-geometry-v2-candidate.recipe.json','b34f0273acd394f1d12567c13a44b1435c5857e9a35eabefbc02cbb9ce26f9b6'),
 'left':('raw/'+OID+'.left-mirrored-approved-right-v1-candidate.png','raw/'+OID+'.left-mirrored-approved-right-v1-candidate.recipe.json','a80746f35cdb3f8365491b5a64a7110ca7f3b2f72dd727954c3adf59252faa2c')}
 plans=[]
 for view,(candrel,recrel,expected_target) in specs.items():
  aid=f'{OID}.{view}';assert aid in assets and assets[aid]['view']==view
  asset=assets[aid];assert asset['id']==aid and asset['image']['path'].endswith(f'{OID}.{view}.png')
  live=PACK/asset['image']['path'];assert sha(live)==expected_target,(view,'target changed')
  candidate=HERE/candrel;recipe_path=HERE/recrel;recipe=json.loads(recipe_path.read_text())
  assert sha(candidate)==recipe['candidate_sha256'] and recipe['status']=='candidate-ready-for-independent-review'
  assert recipe['object_id']==OID and (recipe.get('view') or recipe.get('direction'))==view
  assert recipe['canonical_source_sha256']==expected_source if 'canonical_source_sha256' in recipe else recipe.get('source_sha256')==expected_source
  meta_path=PACK/asset['metadata_path'];meta=json.loads(meta_path.read_text());assert meta['view']==view and meta['object_id']==OID
  plans.append((view,aid,asset,live,candidate,recipe_path,recipe,meta_path,meta))
 # The accepted TOP was already installed by the coordinator; verify its exact candidate and sidecar, then reconcile the stale index descriptor without changing its PNG.
 top_asset=assets[OID+'.top'];top_path=PACK/top_asset['image']['path'];top_meta_path=PACK/top_asset['metadata_path'];top_meta=json.loads(top_meta_path.read_text());top_recipe_path=HERE/'raw'/f'{OID}.top-guide-pilot-v1-candidate.recipe.json';top_recipe=json.loads(top_recipe_path.read_text());assert sha(top_path)==top_recipe['candidate_sha256'] and top_meta['image']['sha256']==sha(top_path);assert top_recipe['canonical_source_sha256']==expected_source
 top_asset['image']=top_meta['image'];top_asset['provenance']=top_meta['provenance']
 # Bottom was separately installed from its accepted candidate; verify it before any remaining writes.
 bottom=assets[OID+'.bottom'];bottom_path=PACK/bottom['image']['path'];assert sha(bottom_path)=='398132d0fde1164627ed90f0969f11c07c9f15a61084bf5a58a25c1456861243'
 for view,aid,asset,live,candidate,recipe_path,recipe,meta_path,meta in plans:
  old=meta.get('provenance',{});prov=dict(old);prov['superseded_provenance']=[*old.get('superseded_provenance',[]),{k:v for k,v in old.items() if k!='superseded_provenance'}]
  if view=='left':
   prov.update({'method':'mirrored-opposite-side-symmetry','source_image':'bubble-necropolis/components/'+source.name,'source_sha256':expected_source,'derivation':{'method':'horizontal-reflection','input_view':'right','input_path':recipe['input_candidate'],'input_sha256':recipe['input_candidate_sha256'],'transform':recipe['transform'],'recipe':'reusable/views-additional/raw/'+recipe_path.name,'recipe_sha256':sha(recipe_path)},'notes':recipe['inference_note']})
  else:
   req=PACK/recipe['request_path']
   atlas=HERE/'raw'/Path(recipe['generated_atlas']).name
   prov.update({'method':'generated-inferred-orthographic','source_image':'bubble-necropolis/components/'+source.name,'source_sha256':expected_source,'source_atlas':'reusable/views-additional/raw/'+atlas.name,'source_atlas_sha256':recipe['generated_atlas_sha256'],'generation_recipe':'reusable/views-additional/raw/'+req.name,'generation_recipe_sha256':sha(req),'normalization_recipe':'reusable/views-additional/raw/'+recipe_path.name,'normalization_recipe_sha256':sha(recipe_path),'notes':recipe.get('inference_note','Inferred principal orthographic view; not recovered pixels or calibrated 3D.')})
  atomic(live,candidate.read_bytes());im=Image.open(live).convert('RGBA');image={'path':asset['image']['path'],'width':im.width,'height':im.height,'sha256':sha(live),'rgba_sha256':rgba_sha(im)};meta['image']=image;meta['provenance']=prov;jatomic(meta_path,meta);asset['image']=image;asset['provenance']=prov
 groups[OID]['complete']=False;idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());jatomic(INDEX,idx)
 # Create authoritative fresh source+current-six contact.
 sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));draw=ImageDraw.Draw(sheet);files=[source]+[HERE/f'{OID}.{v}.png' for v in VIEWS]
 for i,(p,label) in enumerate(zip(files,['source',*VIEWS])):
  im=Image.open(p).convert('RGBA');im.thumbnail((168,168),Image.Resampling.LANCZOS);x=i*184;draw.text((x+4,20),label,fill=(20,20,20,255));sheet.alpha_composite(im,(x+8+(168-im.width)//2,42+(168-im.height)//2))
 contact=HERE/'qa-bubble-necropolis-closed-doorway-geometry-v1-installed-source-six.png';import io;b=io.BytesIO();sheet.save(b,'PNG',optimize=True);atomic(contact,b.getvalue())
 report={'schema':'ink-necropolis-closed-doorway-geometry-v1-install','status':'installed-pending-current-source-six-review','object_id':OID,'source_image':'bubble-necropolis/components/'+source.name,'source_sha256':expected_source,'installed':{v:{'path':assets[OID+'.'+v]['image']['path'],'sha256':assets[OID+'.'+v]['image']['sha256']} for v in ('top','right','left','bottom')},'preserved_directions':['front','rear'],'preserved_hashes':{v:sha(HERE/f'{OID}.{v}.png') for v in ('front','rear')},'contact':contact.name,'contact_sha256':sha(contact)};jatomic(HERE/'necropolis-closed-doorway-geometry-v1-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
