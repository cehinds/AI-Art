#!/usr/bin/env python3
"""Install root-approved Race Circuit stair BOTTOM+REAR candidates, hash guarded."""
import hashlib,json,os,pathlib,struct,tempfile,shutil
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json';LEDGER=pathlib.Path('/workspace/scratch/view-qa-root.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,b):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 except BaseException:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def aj(p,d):atomic(p,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 recipe=json.loads((OUT/'raw/race-circuits-stairs-bottom-rear-v2-install-recipe.json').read_text());idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={s['object_id']:s for s in idx['view_sets']};ledger=json.loads(LEDGER.read_text())['reviewed'];plans=[]
 if recipe.get('approved_by')!='root':raise RuntimeError('not root-approved')
 for u in recipe['updates']:
  oid,d=u['object_id'],u['direction'];aid=f'{oid}.{d}';live=OUT/f'{aid}.png';cand=PACK/u['candidate_path'];src=PACK/u['source_path'];rec=ledger.get('book-tiles/ink-and-lanterns::'+oid)
  if not rec or rec.get('source_sha256')!=u['source_sha256'] or rec.get('image_hashes',{}).get(d)!=u['expected_live_sha256']:raise RuntimeError('latest Ink root ledger mismatch '+aid)
  if sha(live)!=u['expected_live_sha256'] or assets[aid]['image']['sha256']!=u['expected_live_sha256']:raise RuntimeError('live/index mismatch '+aid)
  if sha(cand)!=u['candidate_sha256'] or sha(src)!=u['source_sha256']:raise RuntimeError('candidate/source mismatch '+aid)
  with Image.open(cand) as im:
   if im.size!=(256,256):raise RuntimeError('candidate dimensions '+aid)
  plans.append((u,aid,live,cand,src))
 snap=OUT/'raw/race-circuits-stairs-bottom-rear-v2-before-install';backs=[]
 for u,aid,live,cand,src in plans:
  p=snap/u['object_id']/f"{u['direction']}.png";p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():shutil.copy2(live,p)
  if sha(p)!=u['expected_live_sha256']:raise RuntimeError('snapshot mismatch '+aid)
  backs.append({'asset_id':aid,'path':p.relative_to(PACK).as_posix(),'sha256':sha(p)})
 updates=[]
 for u,aid,live,cand,src in plans:
  atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');a=assets[aid];sp=PACK/a['metadata_path'];m=json.loads(sp.read_text());prov=m.setdefault('provenance',{});prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),prov.copy()];prov['derivation']={'method':u['method'],'source_path':u['source_path'],'source_sha256':u['source_sha256'],'request_path':u['request_path'],'raw_atlas_path':u['atlas_path'],'raw_atlas_sha256':sha(PACK/u['atlas_path']),'candidate_path':u['candidate_path'],'candidate_sha256':u['candidate_sha256'],'notes':'Inferred orthographic projection; not recovered pixels or calibrated 3D. Only this scoped-approved direction changed.'};f=sha(live);rh=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();m['image'].update({'path':a['image']['path'],'width':256,'height':256,'sha256':f,'rgba_sha256':rh});aj(sp,m);a['image']=m['image'];a['provenance']=prov;groups[oid]['complete']=False;updates.append({'asset_id':aid,'before_sha256':u['expected_live_sha256'],'after_sha256':f,'candidate_sha256':u['candidate_sha256'],'source_sha256':u['source_sha256']})
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());aj(INDEX,idx);rep={'schema_version':1,'batch':'race-circuits-stairs-bottom-rear-v2','approved_by':'root','updated':updates,'snapshots':backs,'preflight':'All latest Ink source, root review, candidate, current and index hashes checked before writes.','review_status':'Fresh whole-set source+six callback required.'};aj(OUT/'race-circuits-stairs-bottom-rear-v2-install-report.json',rep);print(json.dumps({'updated':len(updates)}))
if __name__=='__main__':main()
