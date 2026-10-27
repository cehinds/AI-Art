#!/usr/bin/env python3
"""Install root-approved horizontal side elevations for Thresholds race podium."""
import hashlib,json,os,pathlib,struct,tempfile
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json';OBJ='thresholds-race-selection-podium';RP=OUT/'raw/thresholds-race-selection-podium.edge-elevations-v1-candidate.recipe.json'
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
def atomic_json(path,x):atomic(path,(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};r=json.loads(RP.read_text());assert r['status']=='staged-candidate-pending-current-source-six-review';assert sha(PACK/r['atlas_path'])==r['atlas_sha256'];assert sha(PACK/r['request_path'])==r['request_sha256'];plans=[]
 for v in r['views']:
  aid=f"{OBJ}.{v['direction']}";a=assets[aid];live=PACK/a['image']['path'];cand=PACK/v['candidate_path'];assert sha(live)==r['pre_install_target_sha256'][v['direction']];assert sha(cand)==v['sha256'];plans.append((v,a,live,cand))
 updated=[]
 for v,a,live,cand in plans:
  atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');fh=sha(live);rgba=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();mp=PACK/a['metadata_path'];meta=json.loads(mp.read_text());old=meta.get('provenance',{}).copy();sup=[*old.get('superseded_provenance',[]),{k:x for k,x in old.items() if k!='superseded_provenance'}];cell=v['cell_index'];aw,ah=Image.open(PACK/r['atlas_path']).size
  prov={**old,'superseded_provenance':sup,'method':'generated','source_image':r['source_image'],'source_sha256':r['source_sha256'],'source_atlas':r['atlas_path'],'source_atlas_sha256':r['atlas_sha256'],'generation_recipe':r['request_path'],'generation_recipe_sha256':r['request_sha256'],'normalization_adapter':{'method':r['method'],'shared_isotropic_scale':v['scale'],'target_max_dimension_px':208},'crop_bounds_px':{'nominal_cell':{'column':cell,'row':0,'bounds':[round(cell*aw/4),0,round((cell+1)*aw/4),ah]},'alpha_bounds_components_global_px':[v['alpha_bounds_global_px']],'component_labels':v['component_labels'],'resized_bounds_px':v['resized_dimensions_px'],'canvas_offset_px':v['canvas_offset_px'],'shared_scale':v['scale']},'notes':'Inferred orthographic view; not recovered pixels or calibrated 3D. Root-approved thin horizontal podium edge elevation; retain two near columns with far columns partly occluded by source geometry.'}
  meta['provenance']=prov;meta['image'].update({'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':fh,'rgba_sha256':rgba});atomic_json(mp,meta);a['image']=meta['image'];a['provenance']=prov;v['installed_sha256']=fh;updated.append({'asset_id':aid,'sha256':fh,'rgba_sha256':rgba})
 groups[OBJ]['complete']=False;r['status']='installed-pending-current-source-six-review';atomic_json(RP,r);idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());atomic_json(INDEX,idx);atomic_json(OUT/'thresholds-race-podium-edge-elevations-install-report.json',{'schema':'thresholds-race-podium-edge-elevations-install-v1','object_id':OBJ,'updated':updated,'preserved_directions':['top','bottom'],'atomic_index_update':True});print(json.dumps(updated,indent=2))
if __name__=='__main__':main()
