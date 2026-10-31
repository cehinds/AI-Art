"""Install only the corrected compact TOP/BOTTOM plans for Glass Maze NE."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent; OUT=HERE.parent; BOOK=OUT.parent.parent
SPEC=json.loads((OUT/'candidates/glass-ne-plans-v3/candidate.json').read_text())
INDEX=OUT/'set-index.json'; RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
BACKUP=OUT/'prebuilt/glass-ne-plans-before-v3'; META=OUT/'prebuilt/replay-sidecars-final-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};sets={s['object_id']:s for s in idx['view_sets']};recipe=json.loads(RECIPE.read_text());entries=recipe['entries'];lookup={e['asset_id']:i for i,e in enumerate(entries)}
assert len(lookup)==len(entries),'duplicate replay asset IDs'
oid=SPEC['object_id']; assert oid in sets
source_image=assets[f'{oid}.front']['source']['source_image'];source_sha=assets[f'{oid}.front']['source']['source_sha256'];assert sha(safe(BOOK,source_image))==source_sha
prepared=[]
for e in SPEC['views']:
 v=e['view'];assert v in ('top','bottom');aid=f'{oid}.{v}';a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);cand=safe(OUT,e['candidate_path'])
 assert sha(cand)==e['candidate_sha256'];base=sha(dst);oldmeta=sha(mdst);asset=json.loads(json.dumps(a))
 raw=safe(OUT,Path(e['raw_atlas']).relative_to('reusable/views-additional'));prompt=safe(OUT,Path(e['prompt_path']).relative_to('reusable/views-additional'))
 assert sha(raw)==e['raw_atlas_sha256'] and sha(prompt)==e['prompt_sha256']
 im=Image.open(cand).convert('RGBA');asset['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)})
 asset.setdefault('provenance_history',[]).append({'candidate_id':'glass-ne-plans-v3:'+aid,'previous_provenance':asset.get('provenance',{}),'previous_image_sha256':base})
 norm={'scale':e['uniform_scale'],'offset_px':[128-e['normalized_size'][0]//2,128-e['normalized_size'][1]//2],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; isotropic scaling'}
 asset['provenance']={'method':'source-guided-compact-endcap-plan','source_image':source_image,'source_sha256':source_sha,'raw_atlas':e['raw_atlas'],'raw_atlas_sha256':e['raw_atlas_sha256'],'prompt_path':e['prompt_path'],'prompt_sha256':e['prompt_sha256'],'reference_paths':e['reference_paths'],'reference_sha256':e['reference_sha256'],'component_bbox_threshold32':e['component_bbox_threshold32'],'component_area_threshold32':e['component_area_threshold32'],'crop_rect_with_2px_padding':e['crop_rect_with_2px_padding'],'normalization':norm,'notes':'Illustrative compact endcap plan, isotropically normalized to agree with the accepted front width and side depth. Unseen underside is inferred, not recovered from source pixels.' if v=='bottom' else 'Illustrative compact overhead endcap footprint, isotropically normalized to agree with the accepted front width and side depth.'}
 mdata=json.dumps(asset,indent=2)+'\n';mdsha=hashlib.sha256(mdata.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
 re={'asset_id':aid,'image_path':asset['image']['path'],'candidate_path':e['candidate_path'],'candidate_sha256':sha(cand),'base_sha256':base,'final_sha256':sha(cand),'metadata_path':asset['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mdsha,'live_before_install_sha256':base,'superseded_installed_sha256':base}
 prepared.append((aid,dst,mdst,cand,asset,mdata,mdsha,oldmeta,base,re))
BACKUP.mkdir(parents=True,exist_ok=True);META.mkdir(parents=True,exist_ok=True)
for aid,dst,mdst,cand,asset,mdata,mdsha,oldmeta,base,re in prepared:
 (BACKUP/f'{aid}.png').write_bytes(dst.read_bytes());(BACKUP/f'{aid}.json').write_bytes(mdst.read_bytes());(META/f'{aid}.json').write_text(mdata)
for aid,dst,mdst,cand,asset,mdata,mdsha,oldmeta,base,re in prepared:
 assert sha(dst)==base and sha(mdst)==oldmeta
 t=dst.with_suffix('.png.tmp');t.write_bytes(cand.read_bytes());os.replace(t,dst)
 t=mdst.with_suffix('.json.tmp');t.write_text(mdata);os.replace(t,mdst)
 assert sha(dst)==re['final_sha256'] and sha(mdst)==mdsha
 assets[aid].clear();assets[aid].update(asset)
 if aid in lookup:entries[lookup[aid]]=re
 else:entries.append(re);lookup[aid]=len(entries)-1
sets[oid]['complete']=False;sets[oid]['notes']='Compact TOP/BOTTOM plans installed; accepted four elevations preserved. Pending independent current-hash source-plus-six review.'
t=RECIPE.with_suffix('.json.tmp');t.write_text(json.dumps(recipe,indent=2)+'\n');os.replace(t,RECIPE)
t=INDEX.with_suffix('.json.tmp');t.write_text(json.dumps(idx,indent=2)+'\n');os.replace(t,INDEX)
print(json.dumps({'candidate_id':'glass-ne-plans-v3','installed_views':[x[0] for x in prepared],'recipe_entries':len(entries),'index_sha256':sha(INDEX),'png_sha256':{x[0]:sha(x[1]) for x in prepared}},indent=2))
