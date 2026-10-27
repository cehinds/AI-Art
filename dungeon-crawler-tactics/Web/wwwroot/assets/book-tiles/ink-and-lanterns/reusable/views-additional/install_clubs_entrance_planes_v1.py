#!/usr/bin/env python3
"""Install only root-approved Club entrance plan candidates with source/hash guards."""
import hashlib,json,os,pathlib,struct,tempfile,shutil
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json';LEDGER=pathlib.Path('/workspace/scratch/view-qa-root.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 except BaseException:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
def atomic_json(path,d):atomic(path,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def install():
 recipe_path=OUT/'raw/clubs-entrance-planes-approved-v1-install.json';recipe=json.loads(recipe_path.read_text())
 if recipe.get('status')!='root-approved-pending-install' or recipe.get('approved_by')!='root':raise RuntimeError('not root-approved')
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={s['object_id']:s for s in idx['view_sets']};ledger=json.loads(LEDGER.read_text())['reviewed'];plans=[]
 for u in recipe['updates']:
  oid,d=u['object_id'],u['direction'];aid=f'{oid}.{d}'; live=OUT/f'{aid}.png';cand=PACK/u['candidate_path'];source=PACK/u['source_path'];rec=ledger.get('book-tiles/ink-and-lanterns::'+oid)
  if aid not in assets or oid not in groups:raise KeyError(aid)
  if not live.is_file() or sha(live)!=u['expected_live_sha256'] or assets[aid]['image']['sha256']!=u['expected_live_sha256']:raise RuntimeError('live/index hash changed '+aid)
  if not source.is_file() or sha(source)!=u['source_sha256']:raise RuntimeError('source hash changed '+oid)
  if not cand.is_file() or sha(cand)!=u['candidate_sha256']:raise RuntimeError('candidate hash changed '+aid)
  if not rec or rec.get('source_sha256') not in (None,u['source_sha256']) or rec.get('image_hashes',{}).get(d)!=u['expected_live_sha256']:raise RuntimeError('root review drift '+aid)
  with Image.open(cand) as im:
   if im.size!=(256,256):raise RuntimeError('bad candidate size '+aid)
  plans.append((u,aid,live,cand,source))
 backups=OUT/'raw/clubs-entrance-planes-v1-before-install';backup_rows=[]
 for u,aid,live,cand,source in plans:
  p=backups/u['object_id']/f'{u["direction"]}.png';p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():shutil.copy2(live,p)
  if sha(p)!=u['expected_live_sha256']:raise RuntimeError('snapshot hash mismatch '+aid)
  backup_rows.append({'asset_id':aid,'path':p.relative_to(PACK).as_posix(),'sha256':sha(p)})
 updated=[]
 for u,aid,live,cand,source in plans:
  atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');asset=assets[aid];side=PACK/asset['metadata_path'];meta=json.loads(side.read_text());prov=meta.setdefault('provenance',{});old=prov.copy();prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),old];prov['derivation']={'method':'source-guided-inferred-orthographic-plan','source_image':u['source_path'],'source_sha256':u['source_sha256'],'request_manifest':u['reference_request'],'candidate_path':u['candidate_path'],'candidate_sha256':u['candidate_sha256'],'contact_path':u['contact_path'],'contact_sha256':u['contact_sha256'],'crop_provenance':u['crop_provenance'],'notes':'Inferred orthographic view; not recovered pixels or calibrated 3D geometry. Only this approved direction changed.'}
  fsha=sha(live);rgba=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();meta['image'].update({'path':asset['image']['path'],'width':256,'height':256,'sha256':fsha,'rgba_sha256':rgba});atomic_json(side,meta);asset['image']=meta['image'];asset['provenance']=prov;groups[u['object_id']]['complete']=False;updated.append({'asset_id':aid,'before_sha256':u['expected_live_sha256'],'after_sha256':fsha,'candidate_sha256':u['candidate_sha256'],'source_sha256':u['source_sha256']})
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());atomic_json(INDEX,idx)
 report={'schema_version':1,'batch':'clubs-entrance-planes-approved-v1','approved_by':'root','updated_count':len(updated),'updated':updated,'snapshots':backup_rows,'preflight':'Source, target, index, candidate and root review hashes checked before writes.','review_status':'Pending fresh authoritative source+six callback.'};atomic_json(OUT/'clubs-entrance-planes-approved-v1-install-report.json',report);print(json.dumps({'updated_count':len(updated),'report':'clubs-entrance-planes-approved-v1-install-report.json'}))
if __name__=='__main__':install()
