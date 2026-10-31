#!/usr/bin/env python3
"""Install source-approved Iron Stations tactile edge FRONT candidate."""
import hashlib,json,os,pathlib,struct,tempfile
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json';OBJ='iron-stations-platform-edge-segment';RP=OUT/'raw/iron-stations-platform-edge-segment.front-v3-candidate.recipe.json';REQ=OUT/'raw/iron-stations-platform-edge-segment-front-v3.request.json'
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
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};r=json.loads(RP.read_text());aid=OBJ+'.front';a=assets[aid];live=PACK/a['image']['path'];cand=PACK/r['candidate_path'];source=PACK/'iron-stations/components'/f'{OBJ}.png';assert sha(live)==r['target_preinstall_sha256'];assert sha(cand)==r['candidate_sha256'];assert sha(source)==r['canonical_source_sha256'];assert sha(PACK/r['source_atlas'])==r['source_atlas_sha256'];assert sha(PACK/r['request_path'])==r['request_sha256']
 fd,tmp=tempfile.mkstemp(prefix=live.name+'.',suffix='.tmp',dir=live.parent)
 with os.fdopen(fd,'wb') as f:f.write(cand.read_bytes());f.flush();os.fsync(f.fileno())
 os.replace(tmp,live);im=Image.open(live).convert('RGBA');fh=sha(live);rgba=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();mp=PACK/a['metadata_path'];meta=json.loads(mp.read_text());old=meta.get('provenance',{}).copy();prov={**old,'superseded_provenance':[*old.get('superseded_provenance',[]),{k:v for k,v in old.items() if k!='superseded_provenance'}],'method':'generated','source_image':'iron-stations/components/'+f'{OBJ}.png','source_sha256':sha(source),'source_atlas':r['source_atlas'],'source_atlas_sha256':r['source_atlas_sha256'],'generation_recipe':r['request_path'],'generation_recipe_sha256':r['request_sha256'],'normalization_adapter':{'method':'isotropic nearest-neighbor normalization to retained REAR width','target_width_px':r['rear_reference_width_px'],'scale':r['scale'],'candidate_recipe':'reusable/views-additional/raw/iron-stations-platform-edge-segment.front-v3-candidate.recipe.json'},'crop_bounds_px':{'alpha_bounds_global_px':r['alpha_bounds_global_px'],'component_labels':r['component_labels'],'resized_bounds_px':r['resized_dimensions_px'],'canvas_offset_px':r['canvas_offset_px'],'shared_scale':r['scale']},'notes':'Inferred orthographic view, not recovered pixels or calibrated 3D. Retains a single cream slab edge and thin tactile line over the full-height same-object support frame.'};meta['provenance']=prov;meta['image'].update({'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':fh,'rgba_sha256':rgba});atomic_json(mp,meta);a['image']=meta['image'];a['provenance']=prov;groups[OBJ]['complete']=False;r['installed_sha256']=fh;r['status']='installed-pending-current-source-six-review';atomic_json(RP,r);prov['normalization_adapter']['candidate_recipe_sha256']=sha(RP);meta['provenance']=prov;atomic_json(mp,meta);a['provenance']=prov;idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());atomic_json(INDEX,idx);atomic_json(OUT/'iron-station-edge-front-v3-install-report.json',{'schema':'iron-station-edge-front-v3-install-v1','object_id':OBJ,'direction':'front','image_sha256':fh,'rgba_sha256':rgba,'preserved_directions':['top','right','left','bottom','rear'],'atomic_index_update':True});print(json.dumps({'asset_id':aid,'sha256':fh,'rgba_sha256':rgba},indent=2))
if __name__=='__main__':main()
