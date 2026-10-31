"""Install six source-guided corner elevation repairs with guarded replay inputs."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
SPEC=json.loads((OUT/'candidates/corner-elevation-batch-v1/candidate.json').read_text())
REQ=json.loads((OUT/'prompts/corner-family-imagegen-request-result-v1.json').read_text())
REQ_BY_ID={oid:r for r in REQ for oid in r['object_ids']}
INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json';BACKUP=OUT/'prebuilt/corner-elevation-batch-before-v1';META=OUT/'prebuilt/replay-sidecars-final-v1'
QUEUE=json.loads(Path('/workspace/scratch/repair-batches-dungeon-after-dark.json').read_text());QROWS={x['object_id']:x for g in QUEUE['groups'].values() for x in g}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};sets={s['object_id']:s for s in idx['view_sets']};assert len(sets)==len(idx['view_sets'])
recipe=json.loads(RECIPE.read_text());seen={e['asset_id'] for e in recipe['entries']};prepared=[]
for group in SPEC['sets']:
 oid=group['object_id'];assert oid in sets and len(group['views'])==4
 qrow=QROWS[oid];req=REQ_BY_ID[oid]
 for e in group['views']:
  aid=f"{oid}.{e['view']}";assert aid in assets and aid not in seen
  a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);cand=safe(OUT,e['candidate_path']);assert sha(cand)==e['candidate_sha256']
  base=sha(dst);assert base==qrow['current_views'][e['view']]['sha256'],(aid,base)
  beforemeta=sha(mdst);asset=json.loads(json.dumps(a));source_image=asset['source']['source_image'];source_sha=asset['source']['source_sha256'];assert sha(safe(BOOK,source_image))==source_sha
  raw=safe(OUT,e['raw_atlas']);prompt_rel=req['prompt_path'].replace('reusable/views-additional/','');prompt=OUT/prompt_rel;assert sha(raw)==e['raw_atlas_sha256'] and sha(prompt)==req['prompt_sha256']
  refs=[{'path':r.replace('reusable/views-additional/',''),'sha256':h} for r,h in zip(req['reference_paths'],req['reference_sha256'])]
  im=Image.open(cand).convert('RGBA');asset['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)})
  asset.setdefault('provenance_history',[]).append({'candidate_id':'corner-elevation-batch-v1:'+aid,'previous_provenance':asset.get('provenance',{}),'previous_image_sha256':base})
  source_ref=refs[0]['path']
  asset['provenance']={'method':'source-guided-orthographic-corner-elevation-repair','source_image':source_image,'source_sha256':source_sha,
    'raw_atlas':'reusable/views-additional/'+e['raw_atlas'],'raw_atlas_sha256':e['raw_atlas_sha256'],
    'prompt_path':'reusable/views-additional/'+prompt_rel,'prompt_sha256':req['prompt_sha256'],
    'source_reference_image':'reusable/views-additional/'+source_ref,'source_reference_sha256':refs[0]['sha256'],
    'reference_images':[{'path':'reusable/views-additional/'+r['path'],'sha256':r['sha256']} for r in refs],
    'source_rect':{'component_bbox_threshold32':e['component_bbox_threshold32'],'component_area_threshold32':e['component_area_threshold32'],'extraction':'complete connected alpha component, threshold32, row/column ordering, 2px padding'},
    'normalization':{'scale':e['uniform_scale'],'offset_px':[128-e['normalized_size'][0]//2,128-e['normalized_size'][1]//2],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; uniform isotropic scale shared by four views in object row'},
    'notes':'Four straight orthographic elevations of one constant-height L-corner. Native TOP/BOTTOM L plans were retained unchanged. Illustrative projections; hidden surfaces are inferred.'}
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
for group in SPEC['sets']:
 sets[group['object_id']]['complete']=False;sets[group['object_id']]['notes']='Four corner elevations installed; native TOP/BOTTOM L plans retained; awaiting current-hash independent source-plus-six review.'
recipe['entries'].extend(x[-1] for x in prepared);rt=RECIPE.with_suffix('.json.tmp');rt.write_text(json.dumps(recipe,indent=2)+'\n');os.replace(rt,RECIPE)
t=INDEX.with_suffix('.json.tmp');t.write_text(json.dumps(idx,indent=2)+'\n');os.replace(t,INDEX)
print(json.dumps({'candidate_id':'corner-elevation-batch-v1','installed_pngs':len(prepared),'sets_pending_review':[g['object_id'] for g in SPEC['sets']],'recipe_entries':len(recipe['entries']),'index_sha256':sha(INDEX)},indent=2))
