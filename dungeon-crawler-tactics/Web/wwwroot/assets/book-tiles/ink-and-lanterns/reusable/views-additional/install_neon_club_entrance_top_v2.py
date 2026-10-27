#!/usr/bin/env python3
import hashlib,json,os,pathlib,struct,tempfile,shutil
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json';LEDGER=pathlib.Path('/workspace/scratch/view-qa-root.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,b):
 fd,t=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 except BaseException:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def aj(p,d):atomic(p,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 d=json.load(open(OUT/'raw/neon-club-entrance-top-v2-candidate.json'));oid=d['object_id'];aid=oid+'.top';live=OUT/f'{aid}.png';cand=PACK/d['candidate_path'];src=PACK/d['source_path'];idx=json.loads(INDEX.read_text());a={x['id']:x for x in idx['assets']};groups={x['object_id']:x for x in idx['view_sets']};r=json.load(open(LEDGER))['reviewed']['book-tiles/ink-and-lanterns::'+oid]
 if sha(live)!=d['expected_current_sha256'] or a[aid]['image']['sha256']!=d['expected_current_sha256'] or r.get('image_hashes',{}).get('top')!=d['expected_current_sha256']:raise RuntimeError('live/root hash mismatch')
 if sha(src)!=d['source_sha256'] or r.get('source_sha256')!=d['source_sha256']:raise RuntimeError('source mismatch')
 if sha(cand)!=d['candidate_sha256']:raise RuntimeError('candidate mismatch')
 with Image.open(cand) as im:
  if im.size!=(256,256):raise RuntimeError('size mismatch')
 snap=OUT/'raw/neon-club-entrance-top-v2-before.png';shutil.copy2(live,snap)
 if sha(snap)!=d['expected_current_sha256']:raise RuntimeError('snapshot mismatch')
 atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');asset=a[aid];sp=PACK/asset['metadata_path'];m=json.loads(sp.read_text());prov=m.setdefault('provenance',{});prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),prov.copy()];prov['derivation']={'method':'source-guided-inferred-overhead-canopy-plan','source_path':d['source_path'],'source_sha256':d['source_sha256'],'request_path':d['request_path'],'raw_atlas_path':d['raw_atlas_path'],'raw_atlas_sha256':d['raw_atlas_sha256'],'candidate_path':d['candidate_path'],'candidate_sha256':d['candidate_sha256'],'contact_path':d['contact_path'],'contact_sha256':d['contact_sha256'],'alpha_bounds_global_xyxy_px':d['alpha_bounds_global_xyxy_px'],'scale':d['normalization']['scale'],'resized_bounds_px':d['normalization']['resized_bounds_px'],'offset_xy_px':d['normalization']['offset_xy_px'],'notes':'Inferred top view: shallow purple canopy footprint, planter crowns, column caps and runner; no full curtain/arch face.'};f=sha(live);rh=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();m['image'].update({'path':asset['image']['path'],'width':256,'height':256,'sha256':f,'rgba_sha256':rh});aj(sp,m);asset['image']=m['image'];asset['provenance']=prov;groups[oid]['complete']=False;idx['assets']=list(a.values());idx['view_sets']=list(groups.values());aj(INDEX,idx);report={'schema_version':1,'asset_id':aid,'before_sha256':d['expected_current_sha256'],'after_sha256':f,'candidate_sha256':d['candidate_sha256'],'source_sha256':d['source_sha256'],'backup_path':snap.relative_to(PACK).as_posix(),'backup_sha256':sha(snap),'review_status':'Root scoped-accepted; fresh full source+six review required.'};aj(OUT/'neon-club-entrance-top-v2-install-report.json',report);print(json.dumps(report))
if __name__=='__main__':main()
