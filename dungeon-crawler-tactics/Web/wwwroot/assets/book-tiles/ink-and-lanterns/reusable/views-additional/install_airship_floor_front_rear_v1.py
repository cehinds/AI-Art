#!/usr/bin/env python3
"""Install the independently approved 3-floor front/rear profile batch."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
from PIL import Image

HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json'
IDS=('bubble-airship-scrap-metal-deck-floor','bubble-airship-wet-scrap-metal-deck-floor','bubble-airship-worn-scrap-metal-deck-floor')
DIRS=('front','rear');REQUEST=HERE/'raw'/'bubble-airship-scrap-metal-deck-floors-front-rear-v1.request.json';ATLAS=HERE/'raw'/'bubble-airship-scrap-metal-deck-floors-front-rear-v1-atlas.png'
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
def jwrite(p,d):atomic(p,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 req=json.loads(REQUEST.read_text());idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']}
 assert sha(ATLAS)==req['generated_atlas_sha256']
 prepared=[]
 for oid in IDS:
  source=PACK/'bubble-airship'/'components'/f'{oid}.png';source_hash=sha(source)
  assert any(r['object_id']==oid and r['sha256']==source_hash for r in req['reference_inputs'])
  for d in DIRS:
   recipe_path=HERE/'raw'/f'{oid}.{d}-v1-candidate.recipe.json';r=json.loads(recipe_path.read_text());aid=f'{oid}.{d}';a=assets[aid];assert a['id']==aid and a['view']==d and a['image']['path'].endswith(f'{oid}.{d}.png');live=PACK/a['image']['path'];mp=PACK/a['metadata_path'];meta=json.loads(mp.read_text());cand=PACK/r['candidate_path']
   assert r['object_id']==oid and r['direction']==d and r['status']=='candidate-ready-for-independent-review'
   assert sha(REQUEST)==r['request_sha256'] and sha(ATLAS)==r['source_atlas_sha256'] and source_hash==r['canonical_source_sha256']
   assert sha(cand)==r['candidate_sha256']
   assert sha(live)==r['preinstall_view_hashes'][d],(aid,'target changed')
   for other,h in r['preinstall_view_hashes'].items():assert sha(HERE/f'{oid}.{other}.png')==h,(oid,other,'preinstall mismatch')
   prior=meta.get('provenance',{});prov={**prior,'superseded_provenance':[*prior.get('superseded_provenance',[]),{k:v for k,v in prior.items() if k!='superseded_provenance'}],'method':'generated','source_image':'bubble-airship/components/'+source.name,'source_sha256':source_hash,'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,'source_atlas_sha256':sha(ATLAS),'generation_recipe':'reusable/views-additional/raw/'+REQUEST.name,'generation_recipe_sha256':sha(REQUEST),'normalization_recipe':'reusable/views-additional/raw/'+recipe_path.name,'normalization_recipe_sha256':sha(recipe_path),'normalization':{k:r[k] for k in ('operation','alpha_threshold','component_label','component_bounds_xyxy_px','scale','resized_dimensions_px','canvas_offset_xy_px')},'notes':'Inferred horizontal floor-edge profile. This is a thin level steel slab elevation, not the broad top pattern; not recovered pixels or calibrated 3D.'}
   prepared.append({'object_id':oid,'direction':d,'live':live,'metadata_path':mp,'metadata':meta,'asset':a,'provenance':prov,'candidate_bytes':cand.read_bytes(),'candidate_sha256':r['candidate_sha256'],'recipe':r})
 # All hashes and inputs are checked before the first live write.
 for item in prepared:
  atomic(item['live'],item['candidate_bytes']);im=Image.open(item['live']).convert('RGBA');fh=sha(item['live']);image={'path':item['asset']['image']['path'],'width':im.width,'height':im.height,'sha256':fh,'rgba_sha256':hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()};item['metadata']['image']=image;item['metadata']['provenance']=item['provenance'];item['asset']['image']=image;item['asset']['provenance']=item['provenance'];item['installed_sha256']=fh;item['rgba_sha256']=image['rgba_sha256']
 for item in prepared:jwrite(item['metadata_path'],item['metadata'])
 for oid in IDS:groups[oid]['complete']=False
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());jwrite(INDEX,idx)
 report={'schema':'airship-floor-front-rear-v1-install-v1','installed':[{'object_id':x['object_id'],'direction':x['direction'],'image_sha256':x['installed_sha256'],'rgba_sha256':x['rgba_sha256'],'candidate_sha256':x['candidate_sha256']} for x in prepared],'preserved_directions':['top','right','left','bottom'],'atomic_index_update':True,'status':'installed-pending-current-source-six-review'};jwrite(HERE/'airship-floor-front-rear-v1-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
