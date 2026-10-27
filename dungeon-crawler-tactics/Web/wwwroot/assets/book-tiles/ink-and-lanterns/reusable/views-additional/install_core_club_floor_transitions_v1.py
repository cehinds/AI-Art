#!/usr/bin/env python3
"""Install exact Root-approved Core club carpet transition direction candidates."""
import hashlib,json,os,pathlib,struct,tempfile,shutil
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent;PACK=OUT.parents[1];STAGE=OUT/'raw/core-staging-floor-transitions';INDEX=OUT/'set-index.json'
NAMES=['installer-handoff--clubs-guilds-club-carpet-corner-transition.json','installer-handoff--clubs-guilds-club-carpet-edge-transition.json']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,b):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 except BaseException:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def aj(p,d): atomic(p,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 ix=json.loads(INDEX.read_text());assets={a['id']:a for a in ix['assets']};groups={g['object_id']:g for g in ix['view_sets']}
 if len(assets)!=len(ix['assets']) or len(groups)!=len(ix['view_sets']):raise RuntimeError('duplicate index identifiers')
 plans=[]
 for name in NAMES:
  fp=STAGE/name;m=json.loads(fp.read_text());oid=m['object_id']
  if m.get('status')!='root-approved-candidate-directions-pending-live-install' or m.get('reviewer')!='root':raise RuntimeError('handoff not root approved '+oid)
  source=PACK/m['source']['path']
  if sha(source)!=m['source']['sha256'] or sha(source)!=m['source_actual_sha256']:raise RuntimeError('source hash mismatch '+oid)
  g=groups[oid]
  if set(m['current_views'])!=set(g['views']):raise RuntimeError('current view coverage '+oid)
  if set(g['views'].values())!={m['current_views'][d]['asset_id'] for d in m['current_views']}:raise RuntimeError('index direction map mismatch '+oid)
  plansv=[]
  for d,c in m['current_views'].items():
   a=assets[c['asset_id']];live=PACK/c['path']
   if a['image']['path']!=c['path'] or a['image']['sha256']!=c['sha256'] or sha(live)!=c['sha256']:raise RuntimeError('current live/index mismatch '+oid+'.'+d)
   if d not in m['candidate_views']:continue
   cv=m['candidate_views'][d];cand=STAGE/cv['candidate_path']
   if sha(cand)!=cv['candidate_sha256']:raise RuntimeError('candidate hash mismatch '+oid+'.'+d)
   with Image.open(cand) as im:
    if im.size!=(256,256):raise RuntimeError('candidate canvas mismatch '+oid+'.'+d)
   plansv.append((d,c['asset_id'],live,cand,cv,c))
  plans.append((fp,m,oid,plansv))
 # Snapshot every current view and validate all before the first live write.
 snapshot_root=STAGE/'before-install-clubs-floor-transitions-v1';snapshots=[]
 for fp,m,oid,views in plans:
  for d,c in m['current_views'].items():
   live=PACK/c['path'];p=snapshot_root/oid/(d+'.png');p.parent.mkdir(parents=True,exist_ok=True)
   if not p.exists():shutil.copy2(live,p)
   if sha(p)!=c['sha256']:raise RuntimeError('snapshot mismatch '+oid+'.'+d)
   snapshots.append({'object_id':oid,'direction':d,'path':p.relative_to(PACK).as_posix(),'sha256':sha(p)})
 updated=[]
 for fp,m,oid,views in plans:
  for d,aid,live,cand,cv,c in views:
   atomic(live,cand.read_bytes());a=assets[aid];side=PACK/a['metadata_path'];meta=json.loads(side.read_text());prov=meta.setdefault('provenance',{});prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),prov.copy()];der=cv.get('derivation',{});prov['derivation']={**der,'handoff_path':fp.relative_to(PACK).as_posix(),'candidate_path':cand.relative_to(PACK).as_posix(),'candidate_sha256':cv['candidate_sha256'],'target_source_path':m['source']['path'],'target_source_sha256':m['source']['sha256'],'root_contact_path':m['contact_path'],'root_contact_sha256':m['contact_sha256'],'notes':der.get('note','Root-approved inferred view direction; target remains bound to canonical source.')};im=Image.open(live).convert('RGBA');f=sha(live);rh=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();meta['image'].update({'path':a['image']['path'],'width':256,'height':256,'sha256':f,'rgba_sha256':rh});aj(side,meta);a['image']=meta['image'];a['provenance']=prov;groups[oid]['complete']=False;updated.append({'object_id':oid,'asset_id':aid,'direction':d,'before_sha256':c['sha256'],'after_sha256':f,'candidate_sha256':cv['candidate_sha256'],'source_sha256':m['source']['sha256']})
 ix['assets']=[assets[a['id']] for a in ix['assets']];ix['view_sets']=[groups[g['object_id']] for g in ix['view_sets']];aj(INDEX,ix);report={'schema_version':1,'batch':'core-approved-clubs-floor-transitions-v1','updated_count':len(updated),'updated':updated,'snapshots':snapshots,'preflight':'Root approval, source, all six current live/index and candidate hashes checked before writes.','review_status':'Pending fresh source+six callback.'};aj(OUT/'core-approved-clubs-floor-transitions-v1-install-report.json',report);print(json.dumps({'sets':len(plans),'updated':len(updated)},indent=2))
if __name__=='__main__':main()
