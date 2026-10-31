#!/usr/bin/env python3
"""Install the Root-approved Page deterministic five-direction candidate packet."""
from pathlib import Path
import json,hashlib,os,tempfile,struct,shutil
from PIL import Image
OUT=Path(__file__).resolve().parent
PACK=OUT.parents[1]
PKT=OUT/'candidates/page-ink-six-props-20261026'
MAN=PKT/'deterministic-candidate-manifest-v1.json'
INDEX=OUT/'set-index.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 except BaseException:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
def atomic_json(p,o):atomic(p,(json.dumps(o,indent=2,ensure_ascii=False)+'\n').encode())
def install():
 manifest=json.loads(MAN.read_text()); assert manifest['candidate_only'] is True and manifest['candidate_owner']=='page_inventory' and manifest['reviewer']=='root' and manifest['installer']=='views_ink_books'
 assert sha(MAN)=='0f59d1df5c9a08869f5d02cdecfd715775c032d3fa87b1282d6be0424587042d','manifest changed'
 contact=PACK/manifest['contact']['path'];assert sha(contact)==manifest['contact']['sha256']
 input_guard=PACK/manifest['input_guard']['path'];assert sha(input_guard)==manifest['input_guard']['sha256']
 script=PACK/manifest['script']['path'];assert sha(script)==manifest['script']['sha256']
 index=json.loads(INDEX.read_text());assets={a['id']:a for a in index['assets']};groups={g['object_id']:g for g in index['view_sets']}
 if len(assets)!=len(index['assets']) or len(groups)!=len(index['view_sets']):raise RuntimeError('duplicate index IDs')
 plans=[]
 for row in manifest['sets']:
  oid,v=row['object_id'],row['view'];aid=f'{oid}.{v}'
  if aid not in assets or oid not in groups:raise KeyError(aid)
  source=PACK/row['source']['path'];candidate=PACK/row['candidate']['path'];recipe_input=PACK/row['recipe']['input_path']
  if not source.is_file() or sha(source)!=row['source']['sha256']:raise RuntimeError(f'source mismatch {oid}')
  if not candidate.is_file() or sha(candidate)!=row['candidate']['sha256']:raise RuntimeError(f'candidate mismatch {aid}')
  if not recipe_input.is_file() or sha(recipe_input)!=row['recipe']['input_sha256']:raise RuntimeError(f'input mismatch {aid}')
  for sibling,g in row['base_views'].items():
   sid=f'{oid}.{sibling}'
   if groups[oid]['views'].get(sibling)!=sid:raise RuntimeError(f'canonical view mapping changed {sid}')
   live=PACK/g['path']
   if not live.is_file() or sha(live)!=g['sha256']:raise RuntimeError(f'all-six guard failed {sid}')
  asset=assets[aid];live=PACK/asset['image']['path'];side=PACK/asset['metadata_path']
  if sha(live)!=row['base_views'][v]['sha256']:raise RuntimeError(f'target guard failed {aid}')
  im=Image.open(candidate).convert('RGBA')
  if im.size!=(256,256):raise RuntimeError(f'candidate canvas bad {aid}')
  plans.append((row,asset,groups[oid],live,side,candidate,recipe_input))
 # Persist all snapshots after preflight and before first live write.
 snap=OUT/'raw/page-deterministic5-v1-before-install';snap.mkdir(parents=True,exist_ok=True);shutil.copy2(INDEX,snap/'set-index.json')
 before=[]
 for row,asset,group,live,side,candidate,inputp in plans:
  d=snap/row['object_id'];d.mkdir(exist_ok=True);shutil.copy2(live,d/f'{row["view"]}.png');shutil.copy2(side,d/f'{row["view"]}.json');before.append({'asset_id':asset['id'],'view_path':asset['image']['path'],'sha256':sha(live),'metadata_path':asset['metadata_path'],'metadata_sha256':sha(side)})
 atomic_json(snap/'snapshot.json',{'schema_version':1,'manifest_path':MAN.relative_to(PACK).as_posix(),'manifest_sha256':sha(MAN),'before':before})
 updated=[]
 for row,asset,group,live,side,candidate,inputp in plans:
  atomic(live,candidate.read_bytes()); im=Image.open(live).convert('RGBA');fh=sha(live);rh=sha_bytes(struct.pack('>II',*im.size)+im.tobytes());meta=json.loads(side.read_text());old=meta.get('provenance',{}).copy();prov=meta.setdefault('provenance',{});prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),old]
  prov['source_image']=row['source']['path'];prov['source_sha256']=row['source']['sha256'];prov['repair_candidate']={'candidate_path':row['candidate']['path'],'candidate_sha256':fh,'manifest_path':MAN.relative_to(PACK).as_posix(),'manifest_sha256':sha(MAN),'input_path':row['recipe']['input_path'],'input_sha256':row['recipe']['input_sha256'],'transform':{'rigid_rotation_ccw_degrees':row['recipe']['rigid_rotation_ccw_degrees'],'horizontal_reflection':row['recipe']['horizontal_reflection'],'uniform_scale':row['recipe']['uniform_scale'],'alpha_bbox_xyxy':row['recipe']['alpha_bbox_xyxy'],'offset_xy':row['recipe']['offset_xy'],'resampler':row['recipe']['resampler']},'inference':row['inference'],'root_approval':'Root accepted candidate scope on 2026-10-26; fresh canonical whole-set review after install required.'}
  prov['notes']='Inferred orthographic view, not recovered pixels; not calibrated 3D.';meta['image'].update({'path':asset['image']['path'],'width':im.width,'height':im.height,'sha256':fh,'rgba_sha256':rh});atomic_json(side,meta);asset['image']=meta['image'];asset['provenance']=prov;group['complete']=False;group.setdefault('geometry_qa',{})['status']='pending-review';updated.append({'asset_id':asset['id'],'path':asset['image']['path'],'sha256':fh,'rgba_sha256':rh})
 # Declared same-object illustration symmetries from Page's reviewed manifest.
 for sym in manifest.get('required_view_set_symmetry',[]):
  group=groups[sym['object_id']]; existing=group.setdefault('symmetry',[]); record={'views':sym['views'],'method':'declared same-object illustrative symmetry alias','reason':sym['reason'],'manifest_path':MAN.relative_to(PACK).as_posix(),'manifest_sha256':sha(MAN)}
  if record not in existing:existing.append(record)
 index['assets']=list(assets.values());index['view_sets']=list(groups.values());atomic_json(INDEX,index)
 report={'schema_version':1,'manifest_path':MAN.relative_to(PACK).as_posix(),'manifest_sha256':sha(MAN),'contact_path':manifest['contact']['path'],'contact_sha256':manifest['contact']['sha256'],'preflight_count':len(plans),'installed':updated,'snapshot':'reusable/views-additional/raw/page-deterministic5-v1-before-install/snapshot.json','result':'installed; Bed remains pending FRONT repair'};atomic_json(OUT/'page-deterministic5-v1-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':install()
