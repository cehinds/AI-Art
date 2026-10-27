#!/usr/bin/env python3
"""Install root-approved source-plan and rail-profile candidates with hash guards."""
import hashlib,json,os,pathlib,struct,tempfile,shutil
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent; PACK=OUT.parents[1]; INDEX=OUT/'set-index.json'
ROOT_LEDGER=pathlib.Path('/workspace/scratch/view-qa-root.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,b):
 p.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 except BaseException:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
def atomic_json(p,d):atomic(p,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def install():
 recipe_path=OUT/'raw/iron-tracks-rail-final-install-recipe.json';recipe=json.loads(recipe_path.read_text());
 if recipe.get('status')!='root-approved-pending-install':raise RuntimeError('recipe not root-approved')
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={s['object_id']:s for s in idx['view_sets']};ledger=json.loads(ROOT_LEDGER.read_text())['reviewed'];plans=[]
 for u in recipe['updates']:
  oid,d=u['object_id'],u['direction'];aid=u['asset_id'];live=PACK/u['live_path'];cand=PACK/u['candidate_path'];source=PACK/u['source_path']
  if not live.is_file() or sha(live)!=u['expected_live_sha256']:raise RuntimeError(f'live changed since approval {oid}.{d}')
  if not cand.is_file() or sha(cand)!=u['candidate_sha256']:raise RuntimeError(f'candidate hash mismatch {oid}.{d}')
  if not source.is_file() or sha(source)!=u['source_sha256']:raise RuntimeError(f'source mismatch {oid}')
  if assets[aid]['image']['sha256']!=u['expected_live_sha256']:raise RuntimeError(f'index hash mismatch {aid}')
  rec=ledger.get('book-tiles/ink-and-lanterns::'+oid)
  if not rec:raise RuntimeError('no current root review record '+oid)
  source_live=assets[groups[oid]['views']['front']]['provenance']['source_image']
  if rec.get('source_sha256') and rec['source_sha256']!=u['source_sha256']:raise RuntimeError(f'root source record drift {oid}')
  if rec.get('image_hashes',{}).get(d)!=u['expected_live_sha256']:raise RuntimeError(f'root image record drift {oid}.{d}')
  with Image.open(cand) as im:
   if im.size!=(256,256):raise RuntimeError(f'bad candidate size {aid}: {im.size}')
  plans.append((u,assets[aid],live,cand))
 # Snapshot all affected original bytes before writes.
 snapshot=OUT/'raw/iron-tracks-rail-final-before-install';backups=[]
 for u,a,live,cand in plans:
  p=snapshot/u['object_id']/f"{u['direction']}.png";p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():shutil.copy2(live,p)
  if sha(p)!=u['expected_live_sha256']:raise RuntimeError('snapshot mismatch '+u['asset_id'])
  backups.append({'asset_id':u['asset_id'],'path':p.relative_to(PACK).as_posix(),'sha256':sha(p)})
 updates=[]
 for u,a,live,cand in plans:
  atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');side=PACK/a['metadata_path'];meta=json.loads(side.read_text());prov=meta.setdefault('provenance',{});old=prov.copy();prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),old]
  deriv=dict(u['derivation']);deriv.update({'source_path':u['source_path'],'source_sha256':u['source_sha256'],'recipe_path':recipe_path.relative_to(PACK).as_posix(),'candidate_path':u['candidate_path'],'candidate_sha256':u['candidate_sha256'],'approval_contact':recipe['approval_contact'],'approval_contact_sha256':recipe['approval_contact_sha256']})
  if deriv['method']=='source-art-reused':prov.update({'method':'reused-canonical-source-top','source_image':u['source_path'],'source_sha256':u['source_sha256'],'notes':'Canonical native track-map TOP art reused and isotropically normalized; original source preserved separately.','reused_source_top':deriv})
  else:prov['derivation']=deriv
  fsha=sha(live);rsha=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();meta['image'].update({'path':a['image']['path'],'width':256,'height':256,'sha256':fsha,'rgba_sha256':rsha});atomic_json(side,meta);a['image']=meta['image'];a['provenance']=prov;groups[u['object_id']]['complete']=False
  updates.append({'asset_id':u['asset_id'],'before_sha256':u['expected_live_sha256'],'after_sha256':fsha,'candidate_sha256':u['candidate_sha256'],'source_sha256':u['source_sha256']})
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());atomic_json(INDEX,idx)
 report={'schema_version':1,'batch':'iron-tracks-rail-final-v1','approved_by':'root','updated_count':len(updates),'updated':updates,'backups':backups,'preflight':'Passed candidate, target, index, canonical source and latest root ledger current-hash checks before first write.','review_status':'No review promotion; root must capture fresh current source+six.'};atomic_json(OUT/'iron-tracks-rail-final-v1-install-report.json',report);print(json.dumps({'updated_count':len(updates),'report':'iron-tracks-rail-final-v1-install-report.json'}))
if __name__=='__main__':install()
