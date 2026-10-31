#!/usr/bin/env python3
"""Install root-approved single-view overhead prop candidates with exact hash guards."""
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
 recipe=json.loads((OUT/'raw/overhead-props-v3-candidates.json').read_text());idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={s['object_id']:s for s in idx['view_sets']};ledger=json.loads(LEDGER.read_text())['reviewed'];plans=[]
 for x in recipe['objects']:
  oid=x['object_id'];aid=oid+'.top';live=OUT/f'{aid}.png';cand=PACK/x['candidate_path'];src=PACK/x['source_path'];rec=ledger.get('book-tiles/ink-and-lanterns::'+oid)
  if not rec or rec.get('source_sha256')!=x['source_sha256'] or rec.get('image_hashes',{}).get('top')!=x['expected_current_sha256']:raise RuntimeError('current root ledger mismatch '+aid)
  if sha(live)!=x['expected_current_sha256'] or assets[aid]['image']['sha256']!=x['expected_current_sha256']:raise RuntimeError('live/index mismatch '+aid)
  if sha(src)!=x['source_sha256'] or sha(cand)!=x['candidate_sha256']:raise RuntimeError('source/candidate mismatch '+aid)
  with Image.open(cand) as im:
   if im.size!=(256,256):raise RuntimeError('candidate size '+aid)
  plans.append((x,aid,live,cand,src))
 snap=OUT/'raw/overhead-props-v3-before-install';backs=[]
 for x,aid,live,cand,src in plans:
  p=snap/x['object_id']/'top.png';p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():shutil.copy2(live,p)
  if sha(p)!=x['expected_current_sha256']:raise RuntimeError('snapshot mismatch '+aid)
  backs.append({'asset_id':aid,'path':p.relative_to(PACK).as_posix(),'sha256':sha(p)})
 updated=[]
 for x,aid,live,cand,src in plans:
  atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');a=assets[aid];sp=PACK/a['metadata_path'];m=json.loads(sp.read_text());prov=m.setdefault('provenance',{});prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),prov.copy()];prov['derivation']={'method':'source-guided-inferred-overhead-view','source_path':x['source_path'],'source_sha256':x['source_sha256'],'request_path':x['request_path'],'atlas_path':x['atlas_path'],'atlas_sha256':x['atlas_sha256'],'candidate_path':x['candidate_path'],'candidate_sha256':x['candidate_sha256'],'crop_bounds_global_xyxy_px':x['alpha_bounds_global_xyxy_px'],'normalization':x['normalization'],'contact_path':recipe['contact_path'],'contact_sha256':recipe['contact_sha256'],'notes':'Inferred orthographic top view, not recovered pixels or calibrated 3D. Only TOP was replaced.'};f=sha(live);rh=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();m['image'].update({'path':a['image']['path'],'width':256,'height':256,'sha256':f,'rgba_sha256':rh});aj(sp,m);a['image']=m['image'];a['provenance']=prov;groups[x['object_id']]['complete']=False;updated.append({'asset_id':aid,'before_sha256':x['expected_current_sha256'],'after_sha256':f,'candidate_sha256':x['candidate_sha256'],'source_sha256':x['source_sha256']})
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());aj(INDEX,idx);rep={'schema_version':1,'batch':'overhead-props-v3','updated':updated,'snapshots':backs,'preflight':'Latest Ink root ledger, source, target, index and candidate hashes checked before writes.','review_status':'Fresh source+six callback required.'};aj(OUT/'overhead-props-v3-install-report.json',rep);print(json.dumps({'updated':len(updated)}))
if __name__=='__main__':main()
