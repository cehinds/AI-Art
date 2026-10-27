"""Install source-faithful Adobe corner proportions and full L plans."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
SPEC=json.loads((OUT/'candidates/adobe-corner-plans-v1/candidate.json').read_text());INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json';QUEUE=json.loads(Path('/workspace/scratch/repair-batches-dungeon-after-dark.json').read_text());QROWS={x['object_id']:x for g in QUEUE['groups'].values() for x in g};BACKUP=OUT/'prebuilt/adobe-corner-plans-before-v1';META=OUT/'prebuilt/replay-sidecars-final-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};sets={s['object_id']:s for s in idx['view_sets']};recipe=json.loads(RECIPE.read_text());entries=recipe['entries'];entry_by_id={e['asset_id']:i for i,e in enumerate(entries)}
assert len(entry_by_id)==len(entries),'duplicate replay asset ids'
prepared=[];changed_recipe=[]
for group in SPEC['candidate_sets']:
 oid=group['object_id'];qrow=QROWS[oid];assert oid in sets
 source_image=assets[f'{oid}.front']['source']['source_image'];source_sha=assets[f'{oid}.front']['source']['source_sha256'];assert sha(safe(BOOK,source_image))==source_sha
 for e in group['views']:
  view=e['view'];aid=f'{oid}.{view}';assert aid in assets
  a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);cand=safe(OUT,e['candidate_path']);assert sha(cand)==e['candidate_sha256']
  current=sha(dst);oldmeta=sha(mdst);asset=json.loads(json.dumps(a));base=qrow['current_views'][view]['sha256'];assert (OUT/'prebuilt/corner-elevation-batch-before-v1'/f'{aid}.png').exists() if view in ('front','right') else True
  if view in ('front','right'):
   backup=OUT/'prebuilt/corner-elevation-batch-before-v1'/f'{aid}.png';assert sha(backup)==base
  else: assert current==base,(aid,current,base)
  im=Image.open(cand).convert('RGBA');asset['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)})
  asset.setdefault('provenance_history',[]).append({'candidate_id':'adobe-corner-plans-v1:'+aid,'previous_provenance':asset.get('provenance',{}),'previous_image_sha256':current})
  norm={'scale':e['uniform_scale'],'offset_px':[128-e['normalized_size'][0]//2,128-e['normalized_size'][1]//2],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; isotropic normalization'}
  if e['method']=='exact-horizontal-mirror':
   alias=e['alias_from_asset_id'];src_asset=assets[alias];src_png=safe(BOOK,src_asset['image']['path']);assert sha(src_png)==e['alias_source_sha256']
   prov={'method':'exact-symmetric-view-alias','source_image':source_image,'source_sha256':source_sha,'alias_from_asset_id':alias,'alias_reason':'Opposite broad wall face has the matching wall-span and end-return; horizontal reflection reverses the end-return to the opposite side for the opposite camera.','retained_alias_png':'reusable/views-additional/'+e['candidate_path'],'retained_before_png':'reusable/views-additional/prebuilt/adobe-corner-plans-before-v1/'+aid+'.png','normalization':norm,'notes':'Exact horizontal mirror; no geometric distortion. Native source lineage is retained.'}
  elif e['method']=='exact-source-plan-uniform-normalization':
   prov={'method':'exact-native-top-plan-uniform-normalization','source_image':source_image,'source_sha256':source_sha,'source_contact_sheet':'reusable/views-additional/raw/'+Path(e['source_reference_image']).name,'source_contact_sheet_sha256':e['source_reference_sha256'],'source_rect':e['source_rect'],'normalization':norm,'notes':'TOP is the original native L-shaped map plan, uniformly normalized without alteration of its proportions.'}
  else:
   raw=safe(OUT,Path(e['raw_atlas']).relative_to('reusable/views-additional'));prompt=safe(OUT,Path(e['prompt_path']).relative_to('reusable/views-additional'));assert sha(raw)==e['raw_atlas_sha256'] and sha(prompt)==e['prompt_sha256']
   prov={'method':'source-guided-generated-opaque-underside','source_image':source_image,'source_sha256':source_sha,'raw_atlas':e['raw_atlas'],'raw_atlas_sha256':e['raw_atlas_sha256'],'prompt_path':e['prompt_path'],'prompt_sha256':e['prompt_sha256'],'source_contact_sheet':'reusable/views-additional/raw/'+Path(e['source_reference_image']).name,'source_contact_sheet_sha256':e['source_reference_sha256'],'source_rect':{'component_bbox_threshold32':e['component_bbox_threshold32'],'component_area_threshold32':e['component_area_threshold32'],'crop_rect_with_2px_padding':e['crop_rect_with_2px_padding'],'extraction':'complete alpha-connected L silhouette, threshold32'},'normalization':norm,'notes':'Opaque inferred underside. Full 4x4 bounding L footprint and both one-brick-wide arms retained.'}
  asset['provenance']=prov;mdata=json.dumps(asset,indent=2)+'\n';mdsha=hashlib.sha256(mdata.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json';candrel=e['candidate_path']
  re={'asset_id':aid,'image_path':asset['image']['path'],'candidate_path':candrel,'candidate_sha256':sha(cand),'base_sha256':base,'final_sha256':sha(cand),'metadata_path':asset['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mdsha,'live_before_install_sha256':current,'superseded_installed_sha256':current}
  prepared.append((aid,dst,mdst,cand,asset,mdata,mdsha,oldmeta,current,re))
  if aid in entry_by_id:entries[entry_by_id[aid]]=re
  else:entries.append(re);entry_by_id[aid]=len(entries)-1
BACKUP.mkdir(parents=True,exist_ok=True);META.mkdir(parents=True,exist_ok=True)
for aid,dst,mdst,cand,asset,mdata,mdsha,oldmeta,current,re in prepared:
 (BACKUP/f'{aid}.png').write_bytes(dst.read_bytes());(BACKUP/f'{aid}.json').write_bytes(mdst.read_bytes());(META/f'{aid}.json').write_text(mdata)
for aid,dst,mdst,cand,asset,mdata,mdsha,oldmeta,current,re in prepared:
 assert sha(dst)==current and sha(mdst)==oldmeta
 t=dst.with_suffix('.png.tmp');t.write_bytes(cand.read_bytes());os.replace(t,dst)
 t=mdst.with_suffix('.json.tmp');t.write_text(mdata);os.replace(t,mdst)
 assert sha(dst)==re['final_sha256'] and sha(mdst)==mdsha
 assets[aid].clear();assets[aid].update(asset)
for group in SPEC['candidate_sets']:
 sets[group['object_id']]['complete']=False;sets[group['object_id']]['notes']='Adobe corner footprint/side-span repair installed; awaiting independent current-hash source-plus-six review.'
t=RECIPE.with_suffix('.json.tmp');t.write_text(json.dumps(recipe,indent=2)+'\n');os.replace(t,RECIPE)
t=INDEX.with_suffix('.json.tmp');t.write_text(json.dumps(idx,indent=2)+'\n');os.replace(t,INDEX)
print(json.dumps({'candidate_id':'adobe-corner-plans-v1','installed_pngs':len(prepared),'sets_pending_review':[g['object_id'] for g in SPEC['candidate_sets']],'recipe_entries':len(recipe['entries']),'index_sha256':sha(INDEX)},indent=2))
