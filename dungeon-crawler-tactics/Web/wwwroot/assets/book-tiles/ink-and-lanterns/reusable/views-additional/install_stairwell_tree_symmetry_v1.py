"""Install Root-approved same-object symmetry aliases with exact current-hash guards."""
from pathlib import Path
import hashlib,json,os,shutil,struct,tempfile
from PIL import Image
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json';RECEIPT=OUT/'raw/stairwell-tree-symmetry-candidates-v1.json';APPROVED_CONTACT='9c5c18b822d060417317e3706cc590788ee6d1a862338cc2dadb5024db77be23'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def atomic(p,b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 except BaseException:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def atomic_json(p,o):atomic(p,(json.dumps(o,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 rec=json.loads(RECEIPT.read_text());assert sha(OUT/rec['contact_path'].split('reusable/views-additional/',1)[1])==APPROVED_CONTACT
 index=json.loads(INDEX.read_text());assets={a['id']:a for a in index['assets']};groups={g['object_id']:g for g in index['view_sets']}
 if len(assets)!=len(index['assets']) or len(groups)!=len(index['view_sets']):raise RuntimeError('duplicate index ids')
 plans=[]
 for row in rec['objects']:
  oid=row['object_id'];group=groups[oid];src=PACK/row['source_path']
  if not src.is_file() or sha(src)!=row['source_sha256']:raise RuntimeError('source changed '+oid)
  for v,guard in row['current_views'].items():
   aid=group['views'][v];a=assets[aid];p=PACK/a['image']['path']
   if a['image']['path']!=guard['path'] or not p.is_file() or sha(p)!=guard['sha256']:raise RuntimeError('current all-six guard failed '+aid)
  for v,c in row['candidates'].items():
   aid=group['views'][v];a=assets[aid];live=PACK/a['image']['path'];side=PACK/a['metadata_path'];cand=PACK/c['path']
   if not cand.is_file() or sha(cand)!=c['sha256']:raise RuntimeError('candidate changed '+oid+'.'+v)
   if not Image.open(cand).size==(256,256):raise RuntimeError('bad candidate canvas '+aid)
   plans.append((oid,v,row,c,a,group,live,side,cand))
 snap=OUT/'raw/stairwell-tree-symmetry-v1-before-install';snap.mkdir(parents=True,exist_ok=True);shutil.copy2(INDEX,snap/'set-index.json');before=[]
 for oid,v,row,c,a,g,live,side,cand in plans:
  d=snap/oid;d.mkdir(exist_ok=True);shutil.copy2(live,d/f'{v}.png');shutil.copy2(side,d/f'{v}.json');before.append({'asset_id':a['id'],'image_sha256':sha(live),'sidecar_path':a['metadata_path'],'sidecar_sha256':sha(side)})
 atomic_json(snap/'snapshot.json',{'schema_version':1,'candidate_receipt_path':RECEIPT.relative_to(PACK).as_posix(),'candidate_receipt_sha256':sha(RECEIPT),'contact_sha256':APPROVED_CONTACT,'before':before})
 installed=[]
 for oid,v,row,c,a,g,live,side,cand in plans:
  atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');fsha=sha(live);rsha=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();meta=json.loads(side.read_text());prov=meta.setdefault('provenance',{});prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),prov.copy()]
  prov['source_image']=row['source_path'];prov['source_sha256']=row['source_sha256'];prov['repair_candidate']={'candidate_path':c['path'],'candidate_sha256':fsha,'contact_path':rec['contact_path'],'contact_sha256':APPROVED_CONTACT,'donor_view':c['donor_view'],'donor_path':c['donor_path'],'donor_sha256':c['donor_sha256'],'transform':c['transform'],'inference':c['rationale'],'approval':'Root scoped-approved symmetry candidates 2026-10-26; fresh whole-set review required.'}
  prov['notes']='Inferred principal projection using declared same-object symmetry, not recovered hidden pixels or calibrated 3D.';meta['image'].update({'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':fsha,'rgba_sha256':rsha});atomic_json(side,meta);a['image']=meta['image'];a['provenance']=prov;g['complete']=False;g.setdefault('geometry_qa',{})['status']='pending-review'
  sym=g.setdefault('symmetry',[]);record={'views':[c['donor_view'],v],'method':'same-object orthogonal rotational projection alias','transform':c['transform'],'candidate_receipt_path':RECEIPT.relative_to(PACK).as_posix(),'candidate_receipt_sha256':sha(RECEIPT)}
  if record not in sym:sym.append(record)
  installed.append({'asset_id':a['id'],'path':a['image']['path'],'sha256':fsha,'rgba_sha256':rsha})
 index['assets']=list(assets.values());index['view_sets']=list(groups.values());atomic_json(INDEX,index)
 report={'schema_version':1,'candidate_receipt_path':RECEIPT.relative_to(PACK).as_posix(),'candidate_receipt_sha256':sha(RECEIPT),'installed':installed,'snapshot':'reusable/views-additional/raw/stairwell-tree-symmetry-v1-before-install/snapshot.json','result':'installed; fresh whole-set review required'};atomic_json(OUT/'stairwell-tree-symmetry-v1-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
