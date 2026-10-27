#!/usr/bin/env python3
"""Install root-approved staged broad orthographic elevations for Broadcast corners."""
import hashlib,json,os,pathlib,struct,tempfile
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json'
OBJECTS=['broadcast-portals-studio-partition-inner-corner','broadcast-portals-studio-partition-outer-corner']
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
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};plans=[]
 for obj in OBJECTS:
  rp=OUT/'raw'/f'{obj}.broad-elevations-v-candidate.recipe.json';r=json.loads(rp.read_text());assert r['status']=='staged-candidate-pending-current-source-six-review'
  assert sha(PACK/r['atlas_path'])==r['atlas_sha256'];assert sha(PACK/r['source_image'])==r['source_sha256'];assert sha(PACK/r['request_path'])==r['request_sha256']
  for v in r['views']:
   direction=v['direction'];aid=f'{obj}.{direction}';asset=assets[aid];live=PACK/asset['image']['path'];cand=PACK/v['candidate_path'];assert sha(live)==r['pre_install_target_sha256'][direction],f'target changed {aid}';assert sha(cand)==v['sha256'],f'candidate changed {aid}'
   plans.append((obj,rp,r,v,asset,live,cand))
 updated=[]
 for obj,rp,r,v,asset,live,cand in plans:
  direction=v['direction'];atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');fh=sha(live);rgba=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();mp=PACK/asset['metadata_path'];meta=json.loads(mp.read_text());old=meta.get('provenance',{}).copy();sup=[*old.get('superseded_provenance',[]),{k:x for k,x in old.items() if k!='superseded_provenance'}]
  col=v['cell_index'];aw,ah=Image.open(PACK/r['atlas_path']).size;prov={**old,'superseded_provenance':sup,'method':'generated','source_image':r['source_image'],'source_sha256':r['source_sha256'],'source_atlas':r['atlas_path'],'source_atlas_sha256':r['atlas_sha256'],'generation_recipe':r['request_path'],'generation_recipe_sha256':r['request_sha256'],'normalization_adapter':{'method':r['method'],'isotropic_scale':v['scale'],'target_max_dimension_px':208},'crop_bounds_px':{'nominal_cell':{'column':col,'row':0,'bounds':[round(col*aw/4),0,round((col+1)*aw/4),ah]},'alpha_bounds_components_global_px':[v['alpha_bounds_global_px']],'component_labels':v['component_labels'],'resized_bounds_px':v['resized_dimensions_px'],'canvas_offset_px':v['canvas_offset_px'],'shared_scale':v['scale']},'notes':'Inferred orthographic view; not recovered pixels or calibrated 3D. Root-approved broad same-height straight wall-face correction, target material preserved.'}
  meta['provenance']=prov;meta['image'].update({'path':asset['image']['path'],'width':im.width,'height':im.height,'sha256':fh,'rgba_sha256':rgba});atomic_json(mp,meta);asset['image']=meta['image'];asset['provenance']=prov
  updated.append({'asset_id':asset['id'],'sha256':fh,'rgba_sha256':rgba,'candidate_path':v['candidate_path']});v['installed_sha256']=fh
 for obj in OBJECTS:
  groups[obj]['complete']=False;rp=OUT/'raw'/f'{obj}.broad-elevations-v-candidate.recipe.json';r=json.loads(rp.read_text());r['status']='installed-pending-current-source-six-review';atomic_json(rp,r)
  reqp=PACK/r['request_path'];req=json.loads(reqp.read_text());req['status']='installed-pending-current-source-six-review';atomic_json(reqp,req)
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());atomic_json(INDEX,idx)
 report={'schema':'broadcast-partition-corners-broad-elevation-install-v1','updated':updated,'updated_count':len(updated),'objects':OBJECTS,'preserved_directions':['top','bottom'],'atomic_index_update':True};atomic_json(OUT/'broadcast-partition-corners-broad-elevation-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
