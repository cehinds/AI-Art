#!/usr/bin/env python3
"""Install the two root-approved Core Club stair candidates with complete hash guards."""
import hashlib,json,os,pathlib,struct,tempfile,shutil
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent;PACK=OUT.parents[1];STAGE=OUT/'raw/core-staging-stairs';INDEX=OUT/'set-index.json';LEDGER=pathlib.Path('/workspace/scratch/view-qa-root.json')
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
 files=[STAGE/'installer-handoff--clubs-guilds-club-carpet-stairs-up.json',STAGE/'installer-handoff--clubs-guilds-club-carpet-stairs-down.json'];ix=json.loads(INDEX.read_text());assets={a['id']:a for a in ix['assets']};groups={s['object_id']:s for s in ix['view_sets']};ledger=json.loads(LEDGER.read_text())['reviewed'];plans=[]
 for fp in files:
  m=json.loads(fp.read_text());oid=m['object_id']
  if m.get('status')!='root-approved-candidates-pending-live-install' or m.get('approved_by')!='root':raise RuntimeError('not approved '+oid)
  src=PACK/m['source']['path']
  if sha(src)!=m['source']['sha256'] or sha(src)!=m['source_actual_sha256']:raise RuntimeError('source mismatch '+oid)
  rec=ledger.get('book-tiles/ink-and-lanterns::'+oid)
  if not rec or rec.get('source_sha256')!=m['source']['sha256']:raise RuntimeError('root source mismatch '+oid)
  targets=[]
  if set(m['candidate_views'])|set(m['retained_views'])!=set(m['current_views']):raise RuntimeError('direction coverage '+oid)
  for d,c in m['current_views'].items():
   aid=c['asset_id'];live=PACK/c['path']
   if sha(live)!=c['sha256'] or assets[aid]['image']['sha256']!=c['sha256'] or rec.get('image_hashes',{}).get(d)!=c['sha256']:raise RuntimeError('current/root hash mismatch '+aid)
   if d in m['retained_views']:
    if m['retained_views'][d]['sha256']!=c['sha256']:raise RuntimeError('retained hash mismatch '+aid)
   else:
    cv=m['candidate_views'][d];cand=STAGE/cv['candidate_path']
    if sha(cand)!=cv['candidate_sha256']:raise RuntimeError('candidate mismatch '+aid)
    with Image.open(cand) as im:
     if im.size!=(256,256):raise RuntimeError('candidate size '+aid)
    targets.append((d,aid,live,cand,cv))
  plans.append((fp,m,oid,targets))
 snap=STAGE/'before-install-club-v1';backs=[]
 for fp,m,oid,targets in plans:
  for d,c in m['current_views'].items():
   p=snap/oid/f'{d}.png';p.parent.mkdir(parents=True,exist_ok=True);live=PACK/c['path']
   if not p.exists():shutil.copy2(live,p)
   if sha(p)!=c['sha256']:raise RuntimeError('snapshot mismatch '+oid+'.'+d)
   backs.append({'object_id':oid,'direction':d,'path':p.relative_to(PACK).as_posix(),'sha256':sha(p)})
 upd=[]
 for fp,m,oid,targets in plans:
  for d,aid,live,cand,cv in targets:
   atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');asset=assets[aid];sp=PACK/asset['metadata_path'];meta=json.loads(sp.read_text());prov=meta.setdefault('provenance',{});prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),prov.copy()];der=cv['derivation'];prov['derivation']={**der,'handoff_path':fp.relative_to(PACK).as_posix(),'target_source_path':m['source']['path'],'target_source_sha256':m['source']['sha256'],'candidate_path':(STAGE/cv['candidate_path']).relative_to(PACK).as_posix(),'candidate_sha256':cv['candidate_sha256'],'notes':der.get('note','Root-approved inferred orthographic stair view; target remains bound to canonical source.')};f=sha(live);rh=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();meta['image'].update({'path':asset['image']['path'],'width':256,'height':256,'sha256':f,'rgba_sha256':rh});aj(sp,meta);asset['image']=meta['image'];asset['provenance']=prov;groups[oid]['complete']=False;upd.append({'asset_id':aid,'direction':d,'before_sha256':m['current_views'][d]['sha256'],'after_sha256':f,'candidate_sha256':cv['candidate_sha256'],'source_sha256':m['source']['sha256']})
 ix['assets']=list(assets.values());ix['view_sets']=list(groups.values());aj(INDEX,ix);rep={'schema_version':1,'batch':'core-approved-club-stairs-v1','updated_count':len(upd),'updated':upd,'snapshots':backs,'preflight':'All root review, source, current, candidate, index and retained view hashes checked before writes.','review_status':'Pending fresh whole-set source+six callback.'};aj(OUT/'core-approved-club-stairs-v1-install-report.json',rep);print(json.dumps({'sets':len(plans),'updated':len(upd)}))
if __name__=='__main__':main()
