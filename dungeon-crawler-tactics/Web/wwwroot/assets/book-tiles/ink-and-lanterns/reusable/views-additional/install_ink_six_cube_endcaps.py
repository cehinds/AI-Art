#!/usr/bin/env python3
"""Install six root-approved own-object cube-symmetry cap aliases, with strict hashes."""
import hashlib,json,os,pathlib,struct,tempfile
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json';RECIPE=OUT/'raw/ink-six-cube-endcap-alias-v1.recipe.json'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def atomic(path,data):
 path=pathlib.Path(path);fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 except BaseException:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
def atomic_json(path,value):atomic(path,(json.dumps(value,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};r=json.loads(RECIPE.read_text());assert r['status']=='staged-approved-pending-install';assert len(r['updates'])==12;plans=[]
 for u in r['updates']:
  source=PACK/u['source_image'];don=PACK/u['donor_path'];live=PACK/u['target_path'];cand=PACK/u['candidate_path'];assert sha(source)==u['source_sha256'];assert sha(don)==u['donor_sha256'];assert sha(live)==u['target_preinstall_sha256'];assert sha(cand)==u['candidate_sha256'];assert Image.open(live).size==Image.open(cand).size;plans.append((u,assets[u['target_asset_id']],live,cand))
 for u,a,live,cand in plans:
  atomic(live,cand.read_bytes());fh=sha(live);im=Image.open(live).convert('RGBA');rgba=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();mp=PACK/a['metadata_path'];meta=json.loads(mp.read_text());old=meta.get('provenance',{}).copy();sup=[*old.get('superseded_provenance',[]),{k:v for k,v in old.items() if k!='superseded_provenance'}];src=old.get('source_image',u['source_image']);srcsha=old.get('source_sha256',u['source_sha256']);prov={**old,'superseded_provenance':sup,'source_image':src,'source_sha256':srcsha,'derivation':{'method':'same-object cube-like 90-degree symmetry alias','donor_asset_id':u['donor_asset_id'],'donor_path':u['donor_path'],'donor_sha256':u['donor_sha256'],'transform':'exact PNG copy; no rotation, resampling or recoloring','recipe':'reusable/views-additional/raw/ink-six-cube-endcap-alias-v1.recipe.json','notes':'Same-object square cap symmetry inferred for an unseen principal view; target canonical source lineage retained.'},'notes':'Inferred orthographic view, not recovered pixels or calibrated 3D. Cube symmetry alias documented in derivation.'};meta['provenance']=prov;meta['image'].update({'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':fh,'rgba_sha256':rgba});atomic_json(mp,meta);a['image']=meta['image'];a['provenance']=prov;u['installed_sha256']=fh
 for obj in r['object_ids']:groups[obj]['complete']=False
 r['status']='installed-pending-current-source-six-review';atomic_json(RECIPE,r);rsha=sha(RECIPE)
 for u,a,live,cand in plans:
  mp=PACK/a['metadata_path'];meta=json.loads(mp.read_text());meta['provenance']['derivation']['recipe_sha256']=rsha;atomic_json(mp,meta);a['provenance']=meta['provenance']
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());atomic_json(INDEX,idx)
 report={'schema':'ink-six-cube-endcap-alias-install-v1','object_ids':r['object_ids'],'updated_count':len(plans),'updated':[{'asset_id':u['target_asset_id'],'sha256':u['installed_sha256'],'donor_asset_id':u['donor_asset_id']} for u,*_ in plans],'preserved_directions':['front','top','bottom','rear'],'atomic_index_update':True};atomic_json(OUT/'ink-six-cube-endcap-alias-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
