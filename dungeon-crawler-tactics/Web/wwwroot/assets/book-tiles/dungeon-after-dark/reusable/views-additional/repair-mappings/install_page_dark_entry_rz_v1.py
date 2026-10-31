"""Install the Page-approved isotropic side-height calibration with exact guards."""
from pathlib import Path
import copy, hashlib, json, os, struct
from PIL import Image
HERE=Path(__file__).resolve().parent; OUT=HERE.parent; BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'; RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
MANIFEST=OUT/'candidates/page-dark-entry-rz-calibration-v1/candidate-manifest.json'
REVIEW=Path('/workspace/scratch/page-dark-sea-wall-rz-candidate-review.json')
REVIEW_LOCAL=OUT/'qa/page-dark-sea-wall-rz-candidate-review.json'
BEFORE=OUT/'prebuilt/page-dark-entry-rz-v1-before'; CANDID='page-dark-entry-rz-v1'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA'); return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve(); p.relative_to(root.resolve()); return p
def atomic(p,data):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name(p.name+'.tmp'); t.write_bytes(data if isinstance(data,bytes) else data.encode()); os.replace(t,p)
def main():
 manifest=json.loads(MANIFEST.read_text()); review=json.loads(REVIEW.read_text())
 assert review['manifest_sha256']==sha(MANIFEST) and review['source_all_six_base_candidate_hashes_verified']
 rows={(r['object_id'],r['view']):r for r in manifest['candidates']}; accepted={(r['object_id'],r['view']):r['candidate_sha256'] for r in review['decisions'] if r['status']=='candidate-direction-accepted'}
 assert len(accepted)==2 and set(rows)==set(accepted)
 if not REVIEW_LOCAL.exists(): atomic(REVIEW_LOCAL,REVIEW.read_bytes())
 else: assert sha(REVIEW_LOCAL)==sha(REVIEW)
 idx=json.loads(INDEX.read_text()); recipe=json.loads(RECIPE.read_text())
 assets={a['id']:copy.deepcopy(a) for a in idx['assets']}; sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']}; entries=recipe['entries']; existing={e['asset_id']:e for e in entries}
 prepared=[]
 for (oid,v),cs in sorted(accepted.items()):
  e=rows[(oid,v)]; aid=f'{oid}.{v}'; assert e['candidate_sha256']==cs
  source=safe(BOOK,e['source_path']); assert sha(source)==e['source_sha256']
  for view,b in manifest['preserved_views'].items(): assert sha(safe(BOOK,b['path']))==b['sha256'], f'{aid}: {view} base changed'
  assert sha(safe(BOOK,e['base_path']))==e['base_sha256'], f'{aid}: target base changed'
  cand=safe(BOOK,e['candidate_path']); assert sha(cand)==cs
  a=assets[aid]; dest=safe(BOOK,a['image']['path']); md=safe(BOOK,a['metadata_path']); base=e['base_sha256']; cur=sha(dest); assert cur in (base,cs)
  old=json.loads(md.read_text()); assert old['image']['sha256']==base
  new=copy.deepcopy(old); im=Image.open(cand).convert('RGBA'); new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(cand))
  new.setdefault('provenance_history',[]).append({'candidate_id':CANDID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  new['provenance']={'method':'uniform-isotropic-common-elevation-height-calibration','source_image':e['source_path'],'source_sha256':e['source_sha256'],'candidate_manifest':'reusable/views-additional/candidates/page-dark-entry-rz-calibration-v1/candidate-manifest.json','candidate_manifest_sha256':sha(MANIFEST),'candidate_review_record':'reusable/views-additional/qa/page-dark-sea-wall-rz-candidate-review.json','candidate_review_sha256':sha(REVIEW_LOCAL),'normalization':{'uniform_scale':e['uniform_scale'],'input_path':e['input_path'],'input_sha256':e['input_sha256'],'input_alpha_bbox_threshold16':e['input_alpha_bbox_threshold16'],'output_alpha_bbox_threshold16':e['output_alpha_bbox_threshold16'],'baseline_y_exclusive':e['baseline_y_exclusive'],'resampling':'nearest-neighbor','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; uniform isotropic scale'},'notes':'Accepted side elevation calibrated to the canonical FRONT/REAR Z and shared baseline; surfaces remain inferred.'}
  assert not new['provenance']['source_image'].startswith('/') and safe(BOOK,new['provenance']['source_image']).is_file(), f'{aid}: canonical source_image must be pack-relative and resolvable'
  mt=json.dumps(new,indent=2)+'\n'; mh=hashlib.sha256(mt.encode()).hexdigest(); snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  re={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':e['candidate_path'].removeprefix('reusable/views-additional/'),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':'reusable/views-additional/qa/page-dark-sea-wall-rz-candidate-review.json','candidate_manifest_sha256':sha(MANIFEST)}
  if aid in existing: assert existing[aid]['final_sha256']==cs and existing[aid]['metadata_sha256']==mh
  prepared.append((aid,dest,md,cand,base,cs,new,mt,mh,snap,re))
 for aid,dest,md,cand,base,cs,new,mt,mh,snap,re in prepared:
  bp=BEFORE/(aid+'.png'); jp=BEFORE/(aid+'.json')
  if not bp.exists(): atomic(bp,dest.read_bytes())
  else: assert sha(bp)==base
  if not jp.exists(): atomic(jp,md.read_bytes())
  else: assert json.loads(jp.read_text())['image']['sha256']==base
  sp=safe(BOOK,snap)
  if sp.exists(): assert sha(sp)==mh
  else: atomic(sp,mt.encode())
 for aid,dest,md,cand,base,cs,new,mt,mh,snap,re in prepared:
  if sha(dest)==base: atomic(dest,cand.read_bytes())
  assert sha(dest)==cs
  if sha(md)!=mh: atomic(md,mt.encode())
  assert sha(md)==mh; assets[aid]=copy.deepcopy(new)
  if aid not in existing: entries.append(re); existing[aid]=re
 oid=prepared[0][0].rsplit('.',1)[0]; sets[oid]['complete']=False; sets[oid]['notes']='Page-approved R/L uniform common-Z calibration installed; awaiting fresh indexed source-plus-six whole-set review.'
 ni=copy.deepcopy(idx); ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']]; ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n'); atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__': main()
