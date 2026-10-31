"""Install source-guided submarine endcap candidates with exact guards and replay inputs."""
from pathlib import Path
import hashlib,json,os,struct,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent; OUT=HERE.parent; BOOK=OUT.parent.parent
SPEC=json.loads((OUT/'candidates/submarine-endcaps-v2/candidate.json').read_text())
INDEX=OUT/'set-index.json'; RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
BACKUP=OUT/'prebuilt/submarine-endcaps-before-v2'; META_SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
VIEWS=('front','top','right','left','bottom','rear')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
idx=json.loads(INDEX.read_text()); assets={a['id']:a for a in idx['assets']}; sets={s['object_id']:s for s in idx['view_sets']}
assert len(sets)==len(idx['view_sets']), 'duplicate set ids'
recipe=json.loads(RECIPE.read_text()); entries=recipe['entries']; ids={g['object_id'] for g in SPEC['sets']}
assert all(not any(e['asset_id'].rsplit('.',1)[0]==oid for e in entries) for oid in ids),'existing recipe entry needs explicit supersession'
prepared=[]
for group in SPEC['sets']:
 oid=group['object_id']; assert oid in sets and set(v['view'] for v in group['views'])==set(VIEWS)
 for e in group['views']:
  aid=f"{oid}.{e['view']}"; assert aid in assets
  a=assets[aid]; dst=safe(BOOK,a['image']['path']); mdst=safe(BOOK,a['metadata_path']); cand=safe(OUT,e['candidate_path'])
  assert sha(cand)==e['candidate_sha256']
  base=sha(dst); q=json.loads(Path('/workspace/scratch/repair-batches-dungeon-after-dark.json').read_text()); qrow=next(v for group in q['groups'].values() for v in group if v['object_id']==oid); expected=qrow['current_views'][e['view']]['sha256']
  assert base==expected,(aid,base,expected)
  beforemeta=sha(mdst); oldmeta=json.loads(mdst.read_text()); asset=json.loads(json.dumps(a));
  # Exact source asset lineage remains canonical even though the generated pixels are new.
  source_image=asset['source']['source_image']; source_sha=asset['source']['source_sha256']; source=safe(BOOK,source_image); assert sha(source)==source_sha
  raw=safe(OUT,e['raw_atlas']); prompt=OUT/'prompts'/(f'{oid}-candidate-'+('sixview-v1.txt' if e['view'] in ('front','right','left','rear') else 'topbottom-v3.txt'))
  assert sha(raw)==e['raw_atlas_sha256'] and prompt.exists()
  im=Image.open(cand).convert('RGBA')
  asset['image']['sha256']=sha(cand);asset['image']['rgba_sha256']=rgba_sha(cand);asset['image']['width']=im.width;asset['image']['height']=im.height
  hist=asset.setdefault('provenance_history',[]);hist.append({'candidate_id':'submarine-endcaps-v2:'+aid,'previous_provenance':asset.get('provenance',{}),'previous_image_sha256':base})
  source_crop=f"reusable/views-additional/raw/{oid}-source-crop.png"; style_ref='reusable/views-additional/qa/bubble-airship-endcaps-source-six-current.png'
  prov={'method':'source-guided-orthographic-candidate-install','source_image':source_image,'source_sha256':source_sha,
    'raw_atlas':'reusable/views-additional/'+e['raw_atlas'],'raw_atlas_sha256':e['raw_atlas_sha256'],'prompt_path':'reusable/views-additional/'+str(prompt.relative_to(OUT)),'prompt_sha256':sha(prompt),
    'source_reference_image':source_crop,'source_reference_sha256':sha(safe(BOOK,source_crop)),
    'source_rect':{'component_bbox_threshold32':e['component_bbox_threshold32'],'extraction':'complete connected alpha silhouette, threshold32, horizontal center ordering, 2px crop padding'},
    'normalization':{'scale':e['uniform_scale'],'offset_px':[128-e['normalized_size'][0]//2,128-e['normalized_size'][1]//2],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; uniform isotropic scaling'},
    'notes':'Illustrative orthographic view. The native source is a hybrid map icon; unseen underside surfaces are inferred, not recovered.'}
  if e['view'] in ('front','right','left','rear'):
   prov['style_reference_image']=style_ref;prov['style_reference_sha256']=sha(safe(BOOK,style_ref))
  asset['provenance']=prov
  mdata=json.dumps(asset,indent=2)+'\n'; mdsha=hashlib.sha256(mdata.encode()).hexdigest()
  snap_rel='reusable/views-additional/prebuilt/replay-sidecars-final-v1/'+aid+'.json'
  candidate_rel=e['candidate_path']; recipe_entry={'asset_id':aid,'image_path':asset['image']['path'],'candidate_path':candidate_rel,'candidate_sha256':sha(cand),'base_sha256':base,'final_sha256':sha(cand),'metadata_path':asset['metadata_path'],'metadata_snapshot_path':snap_rel,'metadata_sha256':mdsha,'live_before_install_sha256':base,'superseded_installed_sha256':base}
  prepared.append({'aid':aid,'candidate':cand,'dst':dst,'mdst':mdst,'asset':asset,'metadata':mdata,'mdsha':mdsha,'base':base,'before_meta':beforemeta,'candidate_sha':sha(cand),'recipe_entry':recipe_entry,'oldmeta':oldmeta})
# retain exact previous outputs/sidecars, then prepare durable sidecar replay snapshots
BACKUP.mkdir(parents=True,exist_ok=True); META_SNAP.mkdir(parents=True,exist_ok=True)
for x in prepared:
 (BACKUP/f"{x['aid']}.png").write_bytes(x['dst'].read_bytes()); (BACKUP/f"{x['aid']}.json").write_bytes(x['mdst'].read_bytes())
 (META_SNAP/f"{x['aid']}.json").write_text(x['metadata'])
# Stage and replace every affected PNG and sidecar before publishing the index.
for x in prepared:
 assert sha(x['dst'])==x['base'] and sha(x['mdst'])==x['before_meta'],x['aid']
 tmp=x['dst'].with_suffix('.png.tmp');tmp.write_bytes(x['candidate'].read_bytes());os.replace(tmp,x['dst'])
 mt=x['mdst'].with_suffix('.json.tmp');mt.write_text(x['metadata']);os.replace(mt,x['mdst'])
 assert sha(x['dst'])==x['candidate_sha'] and sha(x['mdst'])==x['mdsha']
 assets[x['aid']].clear();assets[x['aid']].update(x['asset'])
for oid in ids:
 sets[oid]['complete']=False;sets[oid]['notes']='Source-guided endcap projection repair installed; pending independent current-hash source-plus-six review.'
entries.extend(x['recipe_entry'] for x in prepared)
rt=RECIPE.with_suffix('.json.tmp');rt.write_text(json.dumps(recipe,indent=2)+'\n');os.replace(rt,RECIPE)
t=INDEX.with_suffix('.json.tmp');t.write_text(json.dumps(idx,indent=2)+'\n');os.replace(t,INDEX)
print(json.dumps({'candidate_id':'submarine-endcaps-v2','installed_pngs':len(prepared),'sets_pending_review':sorted(ids),'index_sha256':sha(INDEX),'recipe_entries':len(recipe['entries'])},indent=2))
