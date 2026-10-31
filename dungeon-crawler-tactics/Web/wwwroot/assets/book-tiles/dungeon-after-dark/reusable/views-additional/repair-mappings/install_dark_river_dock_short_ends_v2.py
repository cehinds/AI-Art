"""Install only the independently accepted source-guided dock short-end elevations."""
from pathlib import Path
import json,hashlib,os,copy,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;PACK=OUT.parent.parent;IDX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json';CAND=OUT/'candidates/dark-river-jungle-targeted-v1';BACK=OUT/'prebuilt/dark-river-dock-short-ends-v2-before';SNAP=OUT/'prebuilt/replay-dark-river-dock-short-ends-v2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
idx=json.loads(IDX.read_text());assets={a['id']:a for a in idx['assets']};sets={s['object_id']:s for s in idx['view_sets']};recipe=json.loads(RECIPE.read_text());entries=recipe['entries'];lookup={e['asset_id']:i for i,e in enumerate(entries)};qa=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed'];key='book-tiles/dungeon-after-dark::hunting-river-riverside-dock'
manifest=json.loads((CAND/'candidate-manifest.json').read_text());prepared=[]
for view in ('front','rear'):
 e=next(e for e in manifest['sets'] if e['object_id']=='hunting-river-riverside-dock' and e['view']==view);aid=f'hunting-river-riverside-dock.{view}';a=assets[aid];dst=safe(PACK,a['image']['path']);mdst=safe(PACK,a['metadata_path']);cand=safe(OUT,e['candidate_path']);base=sha(dst);assert base==qa[key]['image_hashes'][view],aid+' reviewer base drift';assert sha(cand)==e['candidate_sha256']
 source=a['source']['source_image'];source_sha=sha(safe(PACK,source));assert source_sha==a['source']['source_sha256'];asset=copy.deepcopy(a);im=Image.open(cand).convert('RGBA');asset['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)});asset.setdefault('provenance_history',[]).append({'candidate_id':'dark-river-dock-short-ends-v2:'+aid,'previous_provenance':asset.get('provenance',{}),'previous_image_sha256':base});asset['provenance']={'method':'source-guided-short-end-orthographic-view','source_image':source,'source_sha256':source_sha,'raw_atlas':e['raw_path'],'raw_atlas_sha256':e['raw_sha256'],'prompt_path':'reusable/views-additional/'+e['prompt_path'],'prompt_sha256':e['prompt_sha256'],'normalization':{'method':'alpha64-bbox-uniform-nearest','source_crop_px':e['bbox_alpha64'],'uniform_scale':e['uniform_scale'],'output_dimensions':[256,256],'anchor_px':[128,128],'distortion':'none'},'notes':'Short-end projection along the dock long axis; two full-height cloth posts, low piers and deck/boat edge. Unseen surfaces are inferred.'};md=json.dumps(asset,indent=2)+'\n';msha=hashlib.sha256(md.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-dark-river-dock-short-ends-v2/{aid}.json';prepared.append((aid,dst,mdst,cand,asset,md,msha,base,snap,e))
BACK.mkdir(parents=True,exist_ok=True);SNAP.mkdir(parents=True,exist_ok=True)
for aid,dst,mdst,cand,asset,md,msha,base,snap,e in prepared:
 (BACK/(aid+'.png')).write_bytes(dst.read_bytes());(BACK/(aid+'.json')).write_bytes(mdst.read_bytes());safe(PACK,snap).write_text(md)
for aid,dst,mdst,cand,asset,md,msha,base,snap,e in prepared:
 assert sha(dst)==base and sha(cand)==e['candidate_sha256'];tmp=dst.with_name(dst.name+'.tmp');tmp.write_bytes(cand.read_bytes());os.replace(tmp,dst);tmp=mdst.with_name(mdst.name+'.tmp');tmp.write_text(md);os.replace(tmp,mdst);assert sha(dst)==e['candidate_sha256'] and sha(mdst)==msha;assets[aid].clear();assets[aid].update(copy.deepcopy(asset));r={'asset_id':aid,'image_path':asset['image']['path'],'metadata_path':asset['metadata_path'],'base_sha256':base,'candidate_path':e['candidate_path'],'candidate_sha256':e['candidate_sha256'],'final_sha256':e['candidate_sha256'],'metadata_snapshot_path':snap,'metadata_sha256':msha};
 if aid in lookup:entries[lookup[aid]]=r
 else:entries.append(r);lookup[aid]=len(entries)-1
sets['hunting-river-riverside-dock']['complete']=False;sets['hunting-river-riverside-dock']['notes']='Short-end FRONT/REAR repaired; awaiting independent current-hash whole-set review.'
t=RECIPE.with_suffix('.json.tmp');t.write_text(json.dumps(recipe,indent=2)+'\n');os.replace(t,RECIPE);t=IDX.with_suffix('.json.tmp');t.write_text(json.dumps(idx,indent=2)+'\n');os.replace(t,IDX);print(json.dumps({'installed':[x[0] for x in prepared],'recipe_entries':len(entries),'index_sha256':sha(IDX)},indent=2))
