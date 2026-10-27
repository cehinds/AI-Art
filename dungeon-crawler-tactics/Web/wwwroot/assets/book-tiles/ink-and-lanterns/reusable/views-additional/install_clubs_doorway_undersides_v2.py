#!/usr/bin/env python3
"""Install the two root-approved doorway underside repairs with source/hash guards."""
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
 recipe=json.loads((OUT/'raw/clubs-doorway-undersides-v2-candidates.json').read_text());idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={s['object_id']:s for s in idx['view_sets']};ledger=json.loads(LEDGER.read_text())['reviewed'];plans=[]
 for x in recipe['objects']:
  oid=x['object_id'];d='bottom';aid=f'{oid}.{d}';live=OUT/f'{aid}.png';cand=PACK/x['candidate_path'];src=PACK/x['source_path'];rec=ledger.get('book-tiles/ink-and-lanterns::'+oid)
  if sha(live)!=x['expected_current_sha256'] or assets[aid]['image']['sha256']!=x['expected_current_sha256']:raise RuntimeError('target/index hash changed '+aid)
  if sha(src)!=x['source_sha256']:raise RuntimeError('source hash mismatch '+oid)
  if sha(cand)!=x['candidate_sha256']:raise RuntimeError('candidate hash mismatch '+aid)
  if not rec or rec.get('image_hashes',{}).get(d)!=x['expected_current_sha256'] or rec.get('source_sha256')!=x['source_sha256']:raise RuntimeError('root current review mismatch '+aid)
  with Image.open(cand) as im:
   if im.size!=(256,256):raise RuntimeError('candidate dimension '+aid)
  plans.append((x,aid,live,cand,src))
 snap=OUT/'raw/clubs-doorway-undersides-v2-before-install';backs=[]
 for x,aid,live,cand,src in plans:
  p=snap/x['object_id']/'bottom.png';p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():shutil.copy2(live,p)
  if sha(p)!=x['expected_current_sha256']:raise RuntimeError('snapshot mismatch '+aid)
  backs.append({'asset_id':aid,'path':p.relative_to(PACK).as_posix(),'sha256':sha(p)})
 updated=[]
 for x,aid,live,cand,src in plans:
  atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');a=assets[aid];sp=PACK/a['metadata_path'];meta=json.loads(sp.read_text());prov=meta.setdefault('provenance',{});prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),prov.copy()];prov['derivation']={'method':'source-guided-inferred-bottom-underside','source_path':x['source_path'],'source_sha256':x['source_sha256'],'request_path':x['request_path'],'raw_atlas_path':x['raw_atlas_path'],'raw_atlas_sha256':x['raw_atlas_sha256'],'candidate_path':x['candidate_path'],'candidate_sha256':x['candidate_sha256'],'contact_path':recipe['contact_path'],'contact_sha256':recipe['contact_sha256'],'crop_bounds_global_px':x['component_bounds_global_xyxy_px'],'scale':x['scale'],'resized_bounds_px':x['resized_bounds_px'],'offset_xy_px':x['canvas_offset_xy_px'],'notes':'Inferred underside; no top finials visible. Candidate includes the arch soffit, foot undersides and source-specific runner/planter footprints.'};f=sha(live);rgba=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();meta['image'].update({'path':a['image']['path'],'width':256,'height':256,'sha256':f,'rgba_sha256':rgba});aj(sp,meta);a['image']=meta['image'];a['provenance']=prov;groups[x['object_id']]['complete']=False;updated.append({'asset_id':aid,'before_sha256':x['expected_current_sha256'],'after_sha256':f,'candidate_sha256':x['candidate_sha256'],'source_sha256':x['source_sha256']})
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());aj(INDEX,idx);report={'schema_version':1,'updated':updated,'snapshots':backs,'review_status':'Root scoped-approved candidates installed; fresh source+six callback required.'};aj(OUT/'clubs-doorway-undersides-v2-install-report.json',report);print(json.dumps({'updated':len(updated)}))
if __name__=='__main__':main()
