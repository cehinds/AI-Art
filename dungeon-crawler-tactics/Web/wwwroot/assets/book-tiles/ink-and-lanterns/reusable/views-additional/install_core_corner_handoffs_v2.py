#!/usr/bin/env python3
"""Install a bounded explicitly approved Core corner handoff batch."""
import hashlib,json,os,pathlib,struct,tempfile,shutil
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent;PACK=OUT.parents[1];STAGE=OUT/'raw/core-staging-corners';INDEX=OUT/'set-index.json'
NAMES=['installer-handoff--hunting-zockau-painted-town-brick-inner-corner.json','installer-handoff--hunting-zockau-painted-town-brick-outer-corner.json','installer-handoff--industry-menagerie-soot-stained-brick-inner-corner.json','installer-handoff--over-city-venues-painted-civic-stone-inner-corner.json','installer-handoff--over-city-venues-painted-civic-stone-outer-corner.json']
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
 ix=json.loads(INDEX.read_text());assets={a['id']:a for a in ix['assets']};groups={s['object_id']:s for s in ix['view_sets']};plans=[]
 for name in NAMES:
  fp=STAGE/name;m=json.loads(fp.read_text())
  if m.get('status')!='root-approved-candidates-pending-live-install' or m.get('approved_by')!='root':raise RuntimeError('not approved '+name)
  oid=m['object_id'];src=PACK/m['source']['path']
  if not src.is_file() or sha(src)!=m['source']['sha256']:raise RuntimeError('source mismatch '+oid)
  if oid not in groups:raise KeyError(oid)
  planset=[]
  for d,c in m['current_views'].items():
   aid=c['asset_id'];live=PACK/c['path']
   if not live.is_file() or sha(live)!=c['sha256'] or assets[aid]['image']['sha256']!=c['sha256']:raise RuntimeError('current mismatch '+aid)
   if d in m['candidate_views']:
    cv=m['candidate_views'][d];candidate=STAGE/cv['candidate_path']
    if not candidate.is_file() or sha(candidate)!=cv['candidate_sha256']:raise RuntimeError('candidate mismatch '+aid)
    im=Image.open(candidate)
    if im.size!=(256,256):raise RuntimeError('size mismatch '+aid)
    der=cv['derivation']
    if der.get('guide_path'):
     gp=PACK/der['guide_path']
     if not gp.is_file() or sha(gp)!=der['guide_sha256']:raise RuntimeError('guide mismatch '+aid)
    if der.get('source_path'):
     sp=PACK/der['source_path']
     if not sp.is_file() or sha(sp)!=der['source_sha256']:raise RuntimeError('derivation source mismatch '+aid)
    if der.get('donor_candidate_path'):
     dp=STAGE/der['donor_candidate_path']
     if not dp.is_file() or sha(dp)!=der['donor_sha256']:raise RuntimeError('donor candidate mismatch '+aid)
    planset.append((d,aid,live,candidate,cv,der))
   elif d in m.get('retained_views',{}):
    if m['retained_views'][d]['sha256']!=c['sha256']:raise RuntimeError('retained mismatch '+aid)
   else:raise RuntimeError('direction neither candidate nor retained '+oid+'.'+d)
  if set(m['candidate_views'])|set(m.get('retained_views',{}))!=set(m['current_views']):raise RuntimeError('coverage mismatch '+oid)
  plans.append((fp,m,oid,src,planset))
 snap=STAGE/'before-install-v2';bk=[]
 for fp,m,oid,src,ps in plans:
  for d,c in m['current_views'].items():
   p=snap/oid/f'{d}.png';p.parent.mkdir(parents=True,exist_ok=True);live=PACK/c['path']
   if not p.exists():shutil.copy2(live,p)
   if sha(p)!=c['sha256']:raise RuntimeError('snapshot mismatch '+oid+'.'+d)
   bk.append({'object_id':oid,'direction':d,'path':p.relative_to(PACK).as_posix(),'sha256':sha(p)})
 upd=[]
 for fp,m,oid,src,ps in plans:
  for d,aid,live,candidate,cv,der in ps:
   atomic(live,candidate.read_bytes());im=Image.open(live).convert('RGBA');a=assets[aid];sp=PACK/a['metadata_path'];meta=json.loads(sp.read_text());prov=meta.setdefault('provenance',{});prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),prov.copy()];saved_der=dict(der)
   if saved_der.get('donor_candidate_path'):saved_der['donor_candidate_pack_path']=(STAGE/saved_der['donor_candidate_path']).relative_to(PACK).as_posix()
   prov['derivation']={**saved_der,'candidate_path':(STAGE/cv['candidate_path']).relative_to(PACK).as_posix(),'candidate_sha256':cv['candidate_sha256'],'staging_handoff':fp.relative_to(PACK).as_posix(),'target_source_path':m['source']['path'],'target_source_sha256':m['source']['sha256'],'note':der.get('note','Root-approved inferred orthographic view; canonical target source remains bound.')};f=sha(live);r=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();meta['image'].update({'path':a['image']['path'],'width':256,'height':256,'sha256':f,'rgba_sha256':r});aj(sp,meta);a['image']=meta['image'];a['provenance']=prov;groups[oid]['complete']=False;upd.append({'object_id':oid,'direction':d,'asset_id':aid,'before_sha256':m['current_views'][d]['sha256'],'after_sha256':f,'candidate_sha256':cv['candidate_sha256']})
 ix['assets']=list(assets.values());ix['view_sets']=list(groups.values());aj(INDEX,ix);report={'schema_version':1,'batch':'core-approved-corner-handoffs-v2','handoffs':[p[0].relative_to(PACK).as_posix() for p in plans],'updated_count':len(upd),'updated':upd,'snapshots':bk,'preflight':'All source, candidate, target and guide hashes validated before writes; retained views verified and preserved.','review':'Fresh source+six independent capture still required.'};aj(OUT/'core-approved-corner-handoffs-v2-install-report.json',report);print(json.dumps({'sets':len(plans),'updated':len(upd)}))
if __name__=='__main__':main()
