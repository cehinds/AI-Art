"""Install source-guided Glass Maze endcap candidates with exact guards/replay."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
SPEC=json.loads((OUT/'candidates/glass-maze-endcaps-v1/candidate.json').read_text());INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
BACKUP=OUT/'prebuilt/glass-maze-endcaps-before-v1';META=OUT/'prebuilt/replay-sidecars-final-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};sets={s['object_id']:s for s in idx['view_sets']};q=json.loads(Path('/workspace/scratch/repair-batches-dungeon-after-dark.json').read_text());recipe=json.loads(RECIPE.read_text());seen={e['asset_id'] for e in recipe['entries']};prepared=[]
for group in SPEC['sets']:
 oid=group['object_id'];assert oid in sets
 assert set(x['view'] for x in group['views'])=={'front','top','right','left','bottom','rear'}
 qrow=next(x for g in q['groups'].values() for x in g if x['object_id']==oid)
 for e in group['views']:
  aid=f"{oid}.{e['view']}";assert aid in assets and aid not in seen
  a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);cand=safe(OUT,e['candidate_path']);assert sha(cand)==e['candidate_sha256']
  base=sha(dst);assert base==qrow['current_views'][e['view']]['sha256'],(aid,base)
  beforemeta=sha(mdst);asset=json.loads(json.dumps(a));source_image=asset['source']['source_image'];source_sha=asset['source']['source_sha256'];assert sha(safe(BOOK,source_image))==source_sha
  raw=safe(OUT,e['raw_atlas']);rawname=Path(e['raw_atlas']).name
  promptname=f"{oid}-candidate-sixview-v2.txt" if rawname.endswith('sixview-v2.png') else f"{oid}-candidate-sixview-v1.txt"
  prompt=OUT/'prompts'/promptname;assert prompt.exists() and sha(raw)==e['raw_atlas_sha256']
  im=Image.open(cand).convert('RGBA');asset['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)})
  asset.setdefault('provenance_history',[]).append({'candidate_id':'glass-maze-endcaps-v1:'+aid,'previous_provenance':asset.get('provenance',{}),'previous_image_sha256':base})
  source_crop=f"reusable/views-additional/raw/{oid}-source-crop.png"
  asset['provenance']={'method':'source-guided-orthographic-candidate-install','source_image':source_image,'source_sha256':source_sha,
   'raw_atlas':'reusable/views-additional/'+e['raw_atlas'],'raw_atlas_sha256':e['raw_atlas_sha256'],
   'prompt_path':'reusable/views-additional/prompts/'+promptname,'prompt_sha256':sha(prompt),
   'source_reference_image':source_crop,'source_reference_sha256':sha(safe(BOOK,source_crop)),
   'source_rect':{'component_bbox_threshold32':e['component_bbox_threshold32'],'component_area_threshold32':e['component_area_threshold32'],'extraction':'complete connected alpha silhouette, threshold32, horizontal center ordering, 2px crop padding'},
   'normalization':{'scale':e['uniform_scale'],'offset_px':[128-e['normalized_size'][0]//2,128-e['normalized_size'][1]//2],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; uniform isotropic scaling'},
   'notes':'Illustrative orthographic views of the native hybrid map icon. Unseen surfaces and underside are inferred, not recovered from source pixels.'}
  mdata=json.dumps(asset,indent=2)+'\n';mdsha=hashlib.sha256(mdata.encode()).hexdigest();snap=f"reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json"
  re={'asset_id':aid,'image_path':asset['image']['path'],'candidate_path':e['candidate_path'],'candidate_sha256':sha(cand),'base_sha256':base,'final_sha256':sha(cand),'metadata_path':asset['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mdsha,'live_before_install_sha256':base,'superseded_installed_sha256':base}
  prepared.append((aid,dst,mdst,cand,asset,mdata,mdsha,beforemeta,base,re))
BACKUP.mkdir(parents=True,exist_ok=True);META.mkdir(parents=True,exist_ok=True)
for aid,dst,mdst,cand,asset,mdata,mdsha,beforemeta,base,re in prepared:
 (BACKUP/f'{aid}.png').write_bytes(dst.read_bytes());(BACKUP/f'{aid}.json').write_bytes(mdst.read_bytes());(META/f'{aid}.json').write_text(mdata)
for aid,dst,mdst,cand,asset,mdata,mdsha,beforemeta,base,re in prepared:
 assert sha(dst)==base and sha(mdst)==beforemeta
 t=dst.with_suffix('.png.tmp');t.write_bytes(cand.read_bytes());os.replace(t,dst)
 t=mdst.with_suffix('.json.tmp');t.write_text(mdata);os.replace(t,mdst)
 assert sha(dst)==re['final_sha256'] and sha(mdst)==mdsha
 assets[aid].clear();assets[aid].update(asset)
for oid in (g['object_id'] for g in SPEC['sets']):sets[oid]['complete']=False;sets[oid]['notes']='Source-guided endcap projections installed; pending independent current-hash source-plus-six review.'
recipe['entries'].extend(x[-1] for x in prepared);t=RECIPE.with_suffix('.json.tmp');t.write_text(json.dumps(recipe,indent=2)+'\n');os.replace(t,RECIPE)
t=INDEX.with_suffix('.json.tmp');t.write_text(json.dumps(idx,indent=2)+'\n');os.replace(t,INDEX)
print(json.dumps({'candidate_id':'glass-maze-endcaps-v1','installed_pngs':len(prepared),'sets_pending_review':[g['object_id'] for g in SPEC['sets']],'recipe_entries':len(recipe['entries']),'index_sha256':sha(INDEX)},indent=2))
