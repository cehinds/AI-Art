#!/usr/bin/env python3
"""Hash-guarded installer for Page's Root-approved generated 11 Ink views."""
from pathlib import Path
import hashlib, json, os, shutil, struct, tempfile
from PIL import Image
OUT=Path(__file__).resolve().parent
PACK=OUT.parents[1]
PKT=OUT/'candidates/page-ink-six-props-20261026'
MAN=PKT/'generated-candidate-manifest-v1.json'
INDEX=OUT/'set-index.json'
EXPECTED_MANIFEST='98afc5f1b32b9ff8701a39b6c50bdc8754a0f28a753929a96474c6e6e7e54984'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(im): return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def atomic(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 except BaseException:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
def atomic_json(path,value): atomic(path,(json.dumps(value,indent=2,ensure_ascii=False)+'\n').encode())
def install():
 manifest=json.loads(MAN.read_text())
 assert manifest['candidate_only'] is True and manifest['candidate_owner']=='page_inventory' and manifest['reviewer']=='root' and manifest['installer']=='views_ink_books'
 assert sha(MAN)==EXPECTED_MANIFEST, 'manifest changed after review'
 assert sha(PACK/manifest['contact']['path'])==manifest['contact']['sha256'], 'review contact changed'
 assert sha(PACK/manifest['input_guard']['path'])==manifest['input_guard']['sha256'], 'source/current guard manifest changed'
 assert sha(PACK/manifest['script']['path'])==manifest['script']['sha256'], 'candidate builder changed'
 for item in manifest['immutable_inputs']:
  p=PACK/item['path']
  if not p.is_file() or sha(p)!=item['sha256']: raise RuntimeError(f"immutable input changed: {item['path']}")
 index=json.loads(INDEX.read_text())
 assets={a['id']:a for a in index['assets']}; groups={g['object_id']:g for g in index['view_sets']}
 if len(assets)!=len(index['assets']) or len(groups)!=len(index['view_sets']): raise RuntimeError('duplicate index IDs')
 plans=[]; affected={}
 for row in manifest['sets']:
  oid,v=row['object_id'],row['view']; aid=f'{oid}.{v}'
  if oid in affected and affected[oid]!=row['source']['sha256']: raise RuntimeError(f'inconsistent source binding: {oid}')
  affected[oid]=row['source']['sha256']
  if aid not in assets or oid not in groups: raise KeyError(aid)
  source=PACK/row['source']['path'];candidate=PACK/row['candidate']['path'];raw=PACK/row['raw']['path'];prompt=PACK/row['prompt']['path'];response=PACK/row['response']['path'];guide=PACK/row['geometry_guide']['path']
  for p,expected,label in [(source,row['source']['sha256'],'source'),(candidate,row['candidate']['sha256'],'candidate'),(raw,row['raw']['sha256'],'raw atlas'),(prompt,row['prompt']['sha256'],'prompt'),(response,row['response']['sha256'],'response'),(guide,row['geometry_guide']['sha256'],'geometry guide')]:
   if not p.is_file() or sha(p)!=expected: raise RuntimeError(f'{label} mismatch: {p}')
  group=groups[oid]
  for direction,base in row['base_views'].items():
   sid=f'{oid}.{direction}'
   if group['views'].get(direction)!=sid: raise RuntimeError(f'canonical view map changed: {sid}')
   live=PACK/base['path']
   if not live.is_file() or sha(live)!=base['sha256']: raise RuntimeError(f'all-six current guard failed: {sid}')
  asset=assets[aid]
  live=PACK/asset['image']['path'];side=PACK/asset['metadata_path']
  if asset['image']['path']!=row['base_views'][v]['path']: raise RuntimeError(f'index target changed: {aid}')
  if not live.is_file() or sha(live)!=row['base_views'][v]['sha256']: raise RuntimeError(f'target changed: {aid}')
  if not side.is_file(): raise RuntimeError(f'missing sidecar: {side}')
  im=Image.open(candidate).convert('RGBA')
  if im.size!=(256,256): raise RuntimeError(f'bad canvas: {aid} {im.size}')
  plans.append((row,asset,group,live,side,candidate))
 if len(plans)!=11 or len(affected)!=4: raise RuntimeError(f'unexpected packet scope {len(plans)} views / {len(affected)} objects')
 # Preserve exact current bytes/sidecars/index before the first live write.
 snap=OUT/'raw/page-generated11-v1-before-install';snap.mkdir(parents=True,exist_ok=True);shutil.copy2(INDEX,snap/'set-index.json')
 before=[]
 for row,asset,group,live,side,candidate in plans:
  d=snap/row['object_id'];d.mkdir(exist_ok=True);shutil.copy2(live,d/f'{row["view"]}.png');shutil.copy2(side,d/f'{row["view"]}.json')
  before.append({'asset_id':asset['id'],'view_path':asset['image']['path'],'image_sha256':sha(live),'metadata_path':asset['metadata_path'],'metadata_sha256':sha(side)})
 atomic_json(snap/'snapshot.json',{'schema_version':1,'manifest_path':MAN.relative_to(PACK).as_posix(),'manifest_sha256':sha(MAN),'before':before})
 updated=[]
 for row,asset,group,live,side,candidate in plans:
  atomic(live,candidate.read_bytes());im=Image.open(live).convert('RGBA');file_sha=sha(live);canonical=rgba_sha(im)
  meta=json.loads(side.read_text());old=meta.get('provenance',{}).copy();prov=meta.setdefault('provenance',{});prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),old]
  prov['source_image']=row['source']['path'];prov['source_sha256']=row['source']['sha256']
  prov['repair_candidate']={'candidate_path':row['candidate']['path'],'candidate_sha256':file_sha,'manifest_path':MAN.relative_to(PACK).as_posix(),'manifest_sha256':sha(MAN),'contact_path':manifest['contact']['path'],'contact_sha256':manifest['contact']['sha256'],'raw_atlas_path':row['raw']['path'],'raw_atlas_sha256':row['raw']['sha256'],'prompt_path':row['prompt']['path'],'prompt_sha256':row['prompt']['sha256'],'response_path':row['response']['path'],'response_sha256':row['response']['sha256'],'geometry_guide_path':row['geometry_guide']['path'],'geometry_guide_sha256':row['geometry_guide']['sha256'],'recipe':row['recipe'],'inference':row['inference'],'root_approval':'Root accepted Page candidate scope on 2026-10-26; fresh canonical whole-set review after install required.'}
  prov['notes']='Inferred orthographic view, not recovered pixels; source material/count/layout authoritative, not calibrated 3D.'
  meta['image'].update({'path':asset['image']['path'],'width':im.width,'height':im.height,'sha256':file_sha,'rgba_sha256':canonical});atomic_json(side,meta);asset['image']=meta['image'];asset['provenance']=prov;group['complete']=False;group.setdefault('geometry_qa',{})['status']='pending-review'
  updated.append({'asset_id':asset['id'],'view':row['view'],'path':asset['image']['path'],'sha256':file_sha,'rgba_sha256':canonical})
 index['assets']=list(assets.values());index['view_sets']=list(groups.values());atomic_json(INDEX,index)
 report={'schema_version':1,'manifest_path':MAN.relative_to(PACK).as_posix(),'manifest_sha256':sha(MAN),'contact_path':manifest['contact']['path'],'contact_sha256':manifest['contact']['sha256'],'preflight_count':len(plans),'object_count':len(affected),'installed':updated,'snapshot':'reusable/views-additional/raw/page-generated11-v1-before-install/snapshot.json','result':'installed; all four object groups await fresh canonical whole-set review'}
 atomic_json(OUT/'page-generated11-v1-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__': install()
