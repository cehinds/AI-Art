"""Install source-guided targeted River/Jungle direction repairs with exact hash guards."""
from pathlib import Path
import json,hashlib,os,struct,copy,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;PACK=OUT.parent.parent
INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
CAND=OUT/'candidates/dark-river-jungle-targeted-v1';MANIFEST=CAND/'candidate-manifest.json'
BACKUP=OUT/'prebuilt/dark-river-jungle-targeted-v1-before';SNAPS=OUT/'prebuilt/replay-dark-river-jungle-targeted-v1'
Q=Path('/workspace/scratch/view-qa-root.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
manifest=json.loads(MANIFEST.read_text()); groups=manifest['sets']
# Add dock end elevations as explicit symmetry aliases from already accepted RIGHT/LEFT profile PNGs.
for dest,donor in [('front','right'),('rear','left')]:
 oid='hunting-river-riverside-dock'; aid=f'{oid}.{dest}'; cand=CAND/f'{aid}.png'
 donor_asset=next(a for a in json.loads(INDEX.read_text())['assets'] if a['id']==f'{oid}.{donor}')
 donor_path=safe(PACK,donor_asset['image']['path']);shutil.copy2(donor_path,cand)
 entry={'object_id':oid,'view':dest,'candidate_path':cand.relative_to(OUT).as_posix(),'candidate_sha256':sha(cand),'raw_path':donor_asset['image']['path'],'raw_sha256':sha(donor_path),'prompt_path':f'prompts/dark-river-jungle-targeted-v1/{oid}.{dest}.txt','prompt_sha256':None,'derived_from_asset_id':f'{oid}.{donor}','derived_from_image_sha256':sha(donor_path),'symmetry_declaration':{'views':[dest,donor],'basis':'dock has two perpendicular orthographic broad-side profiles across its near-square square-layout footprint','reason':'The source deck has opposing side rails and symmetric piers; equivalent accepted same-object broad profile is assigned to the end direction with its axis fixed to the matching world span.'}}
 prompt=OUT/entry['prompt_path'];prompt.parent.mkdir(parents=True,exist_ok=True);prompt.write_text(f"Inferred same-object orthographic profile reuse: {dest} uses the accepted {donor} profile because the square dock footprint and pier/rail geometry are symmetric. Donor PNG SHA-256: {sha(donor_path)}. Canonical source identity retained from the target dock.\n")
 entry['prompt_sha256']=sha(prompt);groups.append(entry)
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};sets={s['object_id']:s for s in idx['view_sets']}
rootqa=json.loads(Q.read_text())['reviewed']; rootkey=lambda oid:f'book-tiles/dungeon-after-dark::{oid}'
recipe=json.loads(RECIPE.read_text());entries=recipe['entries'];lookup={e['asset_id']:i for i,e in enumerate(entries)};assert len(lookup)==len(entries)
prepared=[]
for e in groups:
 oid=e['object_id'];view=e['view'];aid=f'{oid}.{view}';a=assets[aid];old=copy.deepcopy(a)
 dst=safe(PACK,a['image']['path']);mdst=safe(PACK,a['metadata_path']);cand=safe(OUT,e['candidate_path']);base=sha(dst)
 assert base==rootqa[rootkey(oid)]['image_hashes'][view],f'{aid}: live base no longer matches reviewer hash'
 assert sha(cand)==e['candidate_sha256'],f'{aid}: staged candidate changed'
 src_image=a['source']['source_image'];src_path=safe(PACK,src_image);src_sha=sha(src_path);assert src_sha==a['source']['source_sha256']
 im=Image.open(cand).convert('RGBA');asset=copy.deepcopy(a);asset['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)})
 asset.setdefault('provenance_history',[]).append({'candidate_id':'dark-river-jungle-targeted-v1:'+aid,'previous_provenance':old.get('provenance',{}),'previous_image_sha256':base})
 if e.get('derived_from_asset_id'):
  prov={'method':'same-object-symmetry-alias','source_image':src_image,'source_sha256':src_sha,'derived_from_asset_id':e['derived_from_asset_id'],'derived_from_image_sha256':e['derived_from_image_sha256'],'prompt_path':'reusable/views-additional/'+e['prompt_path'],'prompt_sha256':e['prompt_sha256'],'notes':'Same-object accepted view reused by explicit symmetry declaration; canonical source lineage is retained. Inferred projection, not recovered hidden pixels.'}
  asset['symmetry_declaration']=e['symmetry_declaration']
 else:
  prov={'method':'source-guided-isolated-orthographic-view','source_image':src_image,'source_sha256':src_sha,'raw_atlas':e['raw_path'],'raw_atlas_sha256':e['raw_sha256'],'prompt_path':'reusable/views-additional/'+e['prompt_path'],'prompt_sha256':e['prompt_sha256'],'normalization':{'method':'alpha-threshold-crop-uniform-nearest-scale','alpha_threshold':64,'source_crop_px':e['bbox_alpha64'],'uniform_scale':e['uniform_scale'],'output_dimensions':[256,256],'anchor_px':[128,128],'distortion':'none'},'notes':f"{e.get('prompt_path','')} source-guided inferred {view} projection. Unseen geometry is inferred, not recovered hidden pixels."}
 asset['provenance']=prov
 mdata=json.dumps(asset,indent=2)+'\n';msha=hashlib.sha256(mdata.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-dark-river-jungle-targeted-v1/{aid}.json'
 prepared.append({'aid':aid,'dst':dst,'mdst':mdst,'cand':cand,'asset':asset,'mdata':mdata,'msha':msha,'base':base,'candidate_sha':sha(cand),'snap':snap})
# Prepare all snapshots/backups before changing any live output.
BACKUP.mkdir(parents=True,exist_ok=True);SNAPS.mkdir(parents=True,exist_ok=True)
for p in prepared:
 (BACKUP/(p['aid']+'.png')).write_bytes(p['dst'].read_bytes());(BACKUP/(p['aid']+'.json')).write_bytes(p['mdst'].read_bytes());safe(PACK,p['snap']).write_text(p['mdata'])
# Install only after every changed view has passed source, reviewer-hash and candidate guards.
for p in prepared:
 assert sha(p['dst'])==p['base'];assert sha(p['cand'])==p['candidate_sha']
 tmp=p['dst'].with_name(p['dst'].name+'.tmp');tmp.write_bytes(p['cand'].read_bytes());os.replace(tmp,p['dst'])
 tmp=p['mdst'].with_name(p['mdst'].name+'.tmp');tmp.write_text(p['mdata']);os.replace(tmp,p['mdst'])
 assert sha(p['dst'])==p['candidate_sha'] and sha(p['mdst'])==p['msha']
 assets[p['aid']].clear();assets[p['aid']].update(copy.deepcopy(p['asset']))
 re={'asset_id':p['aid'],'image_path':p['asset']['image']['path'],'metadata_path':p['asset']['metadata_path'],'base_sha256':p['base'],'candidate_path':p['cand'].relative_to(OUT).as_posix(),'candidate_sha256':p['candidate_sha'],'final_sha256':p['candidate_sha'],'metadata_snapshot_path':p['snap'],'metadata_sha256':p['msha']}
 if p['aid'] in lookup:entries[lookup[p['aid']]]=re
 else:entries.append(re);lookup[p['aid']]=len(entries)-1
for oid in sorted(set(e['object_id'] for e in groups)):
 sets[oid]['complete']=False;sets[oid]['notes']='Targeted orthographic repairs installed with source lineage; awaiting independent current-hash source-plus-six review.'
tmp=RECIPE.with_suffix('.json.tmp');tmp.write_text(json.dumps(recipe,indent=2)+'\n');os.replace(tmp,RECIPE)
tmp=INDEX.with_suffix('.json.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
print(json.dumps({'candidate_id':'dark-river-jungle-targeted-v1','installed_pngs':len(prepared),'objects':sorted(set(e['object_id'] for e in groups)),'recipe_entries':len(entries),'index_sha256':sha(INDEX)},indent=2))
