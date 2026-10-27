"""Install Root-approved threshold FRONT/TOP candidates under a complete preflight."""
from pathlib import Path
import hashlib,json,os,shutil,struct,tempfile
from PIL import Image
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json';REC=OUT/'raw/starter-dungeon-safe-room-threshold-candidates-v1.json';CONTACT_SHA='e93c1d84e934f2173a3ef5fd15f46dbb89b56302028a3bfe4217f43bbb164875';OID='starter-dungeon-safe-room-threshold'
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
def jwrite(p,o):atomic(p,(json.dumps(o,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 r=json.loads(REC.read_text());assert sha(PACK/r['contact_path'])==CONTACT_SHA;idx=json.loads(INDEX.read_text());aa={a['id']:a for a in idx['assets']};gg={g['object_id']:g for g in idx['view_sets']};g=gg[OID];plans=[]
 src=PACK/r['source']['path'];assert sha(src)==r['source']['sha256']
 for v,b in r['current_views'].items():
  aid=g['views'][v];a=aa[aid];p=PACK/a['image']['path'];assert a['image']['path']==b['path'] and sha(p)==b['sha256'],f'all-six guard {aid}'
 for v,c in r['candidates'].items():
  aid=g['views'][v];a=aa[aid];live=PACK/a['image']['path'];side=PACK/a['metadata_path'];cand=PACK/c['path'];assert sha(cand)==c['sha256'];assert Image.open(cand).size==(256,256);plans.append((v,c,a,live,side,cand))
 snap=OUT/'raw/safe-room-threshold-v1-before-install';snap.mkdir(parents=True,exist_ok=True);shutil.copy2(INDEX,snap/'set-index.json');before=[]
 for v,c,a,live,side,cand in plans:
  shutil.copy2(live,snap/f'{v}.png');shutil.copy2(side,snap/f'{v}.json');before.append({'view':v,'image_sha256':sha(live),'sidecar_path':a['metadata_path'],'sidecar_sha256':sha(side)})
 jwrite(snap/'snapshot.json',{'schema_version':1,'candidate_receipt_path':REC.relative_to(PACK).as_posix(),'candidate_receipt_sha256':sha(REC),'contact_sha256':CONTACT_SHA,'before':before})
 done=[]
 for v,c,a,live,side,cand in plans:
  atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');fh=sha(live);rh=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();meta=json.loads(side.read_text());prov=meta.setdefault('provenance',{});prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),prov.copy()];prov['source_image']=r['source']['path'];prov['source_sha256']=r['source']['sha256'];prov['repair_candidate']={'candidate_path':c['path'],'candidate_sha256':fh,'receipt_path':REC.relative_to(PACK).as_posix(),'receipt_sha256':sha(REC),'contact_path':r['contact_path'],'contact_sha256':CONTACT_SHA,'request_path':r['request_path'],'raw_atlas':r['raw_atlas'],'recipe':c,'inference':'Inferred principal-axis projection; not recovered hidden pixels or calibrated 3D.','approval':'Root scoped-approved FRONT/TOP candidates on 2026-10-26; fresh whole-set review required.'};meta['image'].update({'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':fh,'rgba_sha256':rh});jwrite(side,meta);a['image']=meta['image'];a['provenance']=prov;done.append({'asset_id':a['id'],'path':a['image']['path'],'sha256':fh,'rgba_sha256':rh})
 g['complete']=False;g.setdefault('geometry_qa',{})['status']='pending-review';idx['assets']=list(aa.values());idx['view_sets']=list(gg.values());jwrite(INDEX,idx)
 report={'schema_version':1,'receipt_path':REC.relative_to(PACK).as_posix(),'receipt_sha256':sha(REC),'contact_sha256':CONTACT_SHA,'installed':done,'snapshot':'reusable/views-additional/raw/safe-room-threshold-v1-before-install/snapshot.json','result':'installed; fresh canonical whole-set review required'};jwrite(OUT/'safe-room-threshold-v1-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
