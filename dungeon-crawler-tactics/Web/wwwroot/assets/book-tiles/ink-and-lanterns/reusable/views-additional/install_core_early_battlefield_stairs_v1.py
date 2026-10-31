#!/usr/bin/env python3
"""Install root-approved Core Early Arenas and Battlefield stair candidates with hash guards."""
import hashlib,json,os,pathlib,struct,tempfile,shutil
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent
PACK=OUT.parents[1]
STAGE=OUT/'raw/core-staging-stairs'
INDEX=OUT/'set-index.json'
LEDGER=pathlib.Path('/workspace/scratch/view-qa-root.json')
NAMES=[
 'installer-handoff--early-arenas-arena-stone-stairs-up.json',
 'installer-handoff--early-arenas-arena-stone-stairs-down.json',
 'installer-handoff--faction-battlefield-churned-battlefield-earth-stairs-up.json',
 'installer-handoff--faction-battlefield-churned-battlefield-earth-stairs-down.json',
]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,b):
 p.parent.mkdir(parents=True,exist_ok=True); fd,t=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f: f.write(b); f.flush(); os.fsync(f.fileno())
  os.replace(t,p)
 except BaseException:
  try: os.unlink(t)
  except FileNotFoundError: pass
  raise
def aj(p,d): atomic(p,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 ix=json.loads(INDEX.read_text()); assets={a['id']:a for a in ix['assets']}
 if len(assets)!=len(ix['assets']): raise RuntimeError('duplicate asset IDs in live index')
 groups={s['object_id']:s for s in ix['view_sets']}
 if len(groups)!=len(ix['view_sets']): raise RuntimeError('duplicate object IDs in live index')
 reviewed=json.loads(LEDGER.read_text())['reviewed']; plans=[]
 for name in NAMES:
  fp=STAGE/name; m=json.loads(fp.read_text()); oid=m['object_id']
  if m.get('status')!='root-approved-candidates-pending-live-install' or m.get('approved_by')!='root': raise RuntimeError('handoff not root approved: '+oid)
  src=PACK/m['source']['path']
  if sha(src)!=m['source']['sha256'] or sha(src)!=m['source_actual_sha256']: raise RuntimeError('canonical source mismatch: '+oid)
  rec=reviewed.get('book-tiles/ink-and-lanterns::'+oid)
  if not rec or rec.get('source_sha256')!=m['source']['sha256']: raise RuntimeError('root ledger source mismatch: '+oid)
  if oid not in groups: raise RuntimeError('missing view set: '+oid)
  if set(m['candidate_views'])|set(m['retained_views'])!=set(m['current_views']): raise RuntimeError('view coverage mismatch: '+oid)
  expected=set(groups[oid]['views'].values())
  if expected!={m['current_views'][v]['asset_id'] for v in m['current_views']}: raise RuntimeError('index view mapping mismatch: '+oid)
  targets=[]
  for d,c in m['current_views'].items():
   aid=c['asset_id']; live=PACK/c['path']
   if sha(live)!=c['sha256'] or assets[aid]['image']['sha256']!=c['sha256'] or rec.get('image_hashes',{}).get(d)!=c['sha256']: raise RuntimeError('live/index/root hash mismatch: '+aid)
   if d in m['retained_views']:
    if m['retained_views'][d]['sha256']!=c['sha256']: raise RuntimeError('retained hash mismatch: '+aid)
   else:
    cv=m['candidate_views'][d]; cand=STAGE/cv['candidate_path']
    if sha(cand)!=cv['candidate_sha256']: raise RuntimeError('candidate hash mismatch: '+aid)
    with Image.open(cand) as im:
     if im.size!=(256,256): raise RuntimeError('candidate must be 256 canvas: '+aid)
    targets.append((d,aid,live,cand,cv))
  plans.append((fp,m,oid,targets))
 # Complete preflight before any write.
 snapshots=STAGE/'before-install-early-battlefield-stairs-v1'; backup=[]
 for fp,m,oid,targets in plans:
  for d,c in m['current_views'].items():
   live=PACK/c['path']; dst=snapshots/oid/(d+'.png'); dst.parent.mkdir(parents=True,exist_ok=True)
   if not dst.exists(): shutil.copy2(live,dst)
   if sha(dst)!=c['sha256']: raise RuntimeError('snapshot mismatch '+oid+'.'+d)
   backup.append({'object_id':oid,'direction':d,'path':dst.relative_to(PACK).as_posix(),'sha256':sha(dst)})
 updated=[]
 for fp,m,oid,targets in plans:
  for d,aid,live,cand,cv in targets:
   atomic(live,cand.read_bytes())
   im=Image.open(live).convert('RGBA'); asset=assets[aid]; side=PACK/asset['metadata_path']; meta=json.loads(side.read_text())
   prov=meta.setdefault('provenance',{}); prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),prov.copy()]
   der=cv['derivation']; prov['derivation']={**der,'handoff_path':fp.relative_to(PACK).as_posix(),'target_source_path':m['source']['path'],'target_source_sha256':m['source']['sha256'],'candidate_path':cand.relative_to(PACK).as_posix(),'candidate_sha256':cv['candidate_sha256'],'notes':der.get('note','Root-approved inferred orthographic stair view; target remains bound to its canonical source.')}
   filehash=sha(live); rgba=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
   meta['image'].update({'path':asset['image']['path'],'width':256,'height':256,'sha256':filehash,'rgba_sha256':rgba})
   aj(side,meta); asset['image']=meta['image']; asset['provenance']=prov; updated.append({'object_id':oid,'asset_id':aid,'direction':d,'before_sha256':m['current_views'][d]['sha256'],'after_sha256':filehash,'candidate_sha256':cv['candidate_sha256'],'source_sha256':m['source']['sha256']})
  groups[oid]['complete']=False
 ix['assets']=list(assets.values()); ix['view_sets']=list(groups.values()); aj(INDEX,ix)
 report={'schema_version':1,'batch':'core-approved-early-battlefield-stairs-v1','updated_count':len(updated),'updated':updated,'snapshots':backup,'preflight':'All root review, source, current live, index, candidate and retained-view hashes checked before writes.','review_status':'Pending fresh whole-set source+six callback.'}
 aj(OUT/'core-approved-early-battlefield-stairs-v1-install-report.json',report)
 print(json.dumps({'sets':len(plans),'updated':len(updated)},indent=2))
if __name__=='__main__': main()
