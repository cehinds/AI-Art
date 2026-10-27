#!/usr/bin/env python3
"""Install root-approved Parade inner-corner v3 elevations and underside."""
import hashlib,json,os,pathlib,struct,tempfile
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent; PACK=OUT.parents[1]; INDEX=OUT/'set-index.json'; OBJ='parade-horribles-ceremonial-arena-masonry-inner-corner'
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):return sha_bytes(pathlib.Path(p).read_bytes())
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
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
 recipe_names=[f'raw/{OBJ}-{v}-v3-normalized-to-plan-candidate.recipe.json' for v in ('front','right','left','rear')]+[f'raw/{OBJ}-bottom-v2-plain-L-underside-candidate.recipe.json']
 for rel in recipe_names:
  rp=OUT/rel;r=json.loads(rp.read_text());v=r['view'];aid=f'{OBJ}.{v}';asset=assets[aid];live=OUT/pathlib.Path(asset['image']['path']).name
  if r.get('status')!='staged_candidate_pending_root_visual_review':raise ValueError(f'unexpected status {r.get("status")} for {aid}')
  if sha(live)!=r['target_current_sha256']:raise RuntimeError(f'target hash changed since review: {aid}')
  cand=PACK/r['candidate_path']
  if sha(cand)!=r['candidate_sha256']:raise RuntimeError(f'candidate hash changed since review: {aid}')
  src=PACK/r['source_image']
  if sha(src)!=r['source_sha256']:raise RuntimeError(f'canonical source changed: {aid}')
  atlas_rel=r.get('source_atlas') or r.get('raw_atlas'); atlas_sha=r.get('source_atlas_sha256') or r.get('raw_atlas_sha256')
  atlas=PACK/atlas_rel
  if sha(atlas)!=atlas_sha:raise RuntimeError(f'raw atlas changed: {aid}')
  gen=PACK/r['generation_recipe']
  if sha(gen)!=r['generation_recipe_sha256']:raise RuntimeError(f'request JSON changed: {aid}')
  plans.append((rp,r,asset,live,cand,src))
 updated=[]
 for rp,r,asset,live,cand,src in plans:
  atomic(live,cand.read_bytes()); im=Image.open(live).convert('RGBA');filehash=sha(live);rgba=sha_bytes(struct.pack('>II',*im.size)+im.tobytes())
  meta_path=PACK/asset['metadata_path'];meta=json.loads(meta_path.read_text());prov=meta.setdefault('provenance',{});old=prov.copy();prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),old]
  atlas_rel=r.get('source_atlas') or r.get('raw_atlas'); atlas_sha=r.get('source_atlas_sha256') or r.get('raw_atlas_sha256')
  prov.update({'method':'generated','source_image':r['source_image'],'source_sha256':r['source_sha256'],'source_atlas':atlas_rel,'source_atlas_sha256':atlas_sha,'generation_recipe':r['generation_recipe'],'generation_recipe_sha256':r['generation_recipe_sha256'],'notes':'Inferred orthographic view; not recovered pixels or calibrated 3D. Root-approved source-guided corner correction.'})
  if r['view']=='bottom':
   bbox=r['alpha_bounds_global_px'];prov['crop_bounds_px']={'alpha_bounds_components_global_px':[bbox],'component_labels':[r['component_label']],'resized_bounds_px':r['resized_bounds_px'],'canvas_offset_px':r['canvas_offset_px'],'shared_scale':r['scale']}
  else:
   prov['normalization_adapter']={'method':'isotropic nearest-neighbor normalization to accepted plan width','original_png':r['input_candidate'],'original_png_sha256':r['input_candidate_sha256'],'original_alpha_bounds_px':r['input_alpha_bounds_px'],'ratio':r['isotropic_scale'],'canvas_offset_px':r['output_offset_px']}
  meta['image'].update({'path':asset['image']['path'],'width':im.width,'height':im.height,'sha256':filehash,'rgba_sha256':rgba});atomic_json(meta_path,meta);asset['image']=meta['image'];asset['provenance']=prov
  groups[OBJ]['complete']=False;updated.append({'asset_id':asset['id'],'sha256':filehash,'rgba_sha256':rgba,'recipe':rp.relative_to(PACK).as_posix()});r['status']='installed_pending_current_source_six_whole_set_review';r['installed_image_sha256']=filehash;atomic_json(rp,r)
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());atomic_json(INDEX,idx)
 report={'schema':'ink-parade-inner-corner-v3-install-v1','updated':updated,'updated_count':len(updated),'preserved_views':['top'],'atomic_index_update':True,'source/candidate/target/atlas/request hashes checked before writes':True};atomic_json(OUT/'parade-inner-corner-v3-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
