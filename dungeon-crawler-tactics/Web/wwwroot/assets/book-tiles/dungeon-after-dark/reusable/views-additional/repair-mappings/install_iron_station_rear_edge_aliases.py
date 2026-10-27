"""Replace Iron Stations' split profiles with the reviewed clean REAR edge."""
from pathlib import Path
import hashlib,json,os,struct,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;BOOK=ROOT.parent.parent;INDEX=ROOT/'set-index.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(rel):
 p=(BOOK/rel).resolve();p.relative_to(BOOK.resolve());return p
ids=['iron-stations-station-concrete-floor','iron-stations-cracked-station-concrete-floor','iron-stations-wet-station-concrete-floor','iron-stations-worn-station-concrete-floor']
idx=json.loads(INDEX.read_text());A={a['id']:a for a in idx['assets']};S={s['object_id']:s for s in idx['view_sets']};original=json.loads((HERE/'install-floor-profile-aliases-v1.json').read_text());orig={x['asset_id']:x for x in original['installed']}
prepared=[]
for oid in ids:
 ss=S[oid];sid=ss['views']['rear'];sa=A[sid];src=safe(sa['image']['path']);srcsha=sha(src)
 for view in ['front','right','left']:
  aid=ss['views'][view];a=A[aid];dst=safe(a['image']['path']);mdst=safe(a['metadata_path']);expected=orig.get(aid,{}).get('after_sha256');before=sha(dst)
  if expected is not None: assert before==expected,f'{aid}: unexpected current png'
  beforemeta=sha(mdst)
  snap=ROOT/'prebuilt/iron-station-split-profile-snapshots-v1'/f'{aid}.png';snap.parent.mkdir(parents=True,exist_ok=True)
  if not snap.exists():snap.write_bytes(dst.read_bytes())
  assert sha(snap)==before,f'{aid}: retained pre-repair bytes mismatch'
  cand=ROOT/'candidates/iron-station-rear-edge-v1'/f'{aid}.png';cand.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,cand)
  prepared.append((oid,view,aid,sa,src,srcsha,a,dst,mdst,before,beforemeta,snap,cand,sha(cand)))
log=[]
for oid,view,aid,sa,src,srcsha,a,dst,mdst,before,beforemeta,snap,cand,candsha in prepared:
 assert sha(src)==srcsha and sha(cand)==candsha
 tmp=dst.with_name(dst.name+'.tmp');tmp.write_bytes(cand.read_bytes());os.replace(tmp,dst)
 im=Image.open(dst).convert('RGBA');a['image']['sha256']=sha(dst);a['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();a['anchor_px']=[128,128]
 hist=a.setdefault('provenance_history',[]);marker='iron-station-rear-edge-v1:'+aid
 if not any(h.get('candidate_id')==marker for h in hist):hist.append({'candidate_id':marker,'previous_provenance':a.get('provenance',{}),'previous_image_sha256':sha(snap)})
 a['provenance']={'method':'symmetric-floor-edge-view-alias','source_image':sa['source']['source_image'],'source_sha256':sa['source']['source_sha256'],'alias_from_asset_id':sa['id'],'alias_from_view':'rear','alias_png_path':str(src.relative_to(BOOK)),'alias_png_sha256':srcsha,'retained_before_png':'reusable/views-additional/prebuilt/iron-station-split-profile-snapshots-v1/'+aid+'.png','normalization':{'frame_size':list(im.size),'anchor_px':[128,128],'distortion':'none; exact edge-view byte alias'},'notes':'One clean full-width slab edge profile is shared by the symmetric square tile sides; split detached strips are removed.'}
 tmp=mdst.with_name(mdst.name+'.tmp');tmp.write_text(json.dumps(a,indent=2)+'\n');os.replace(tmp,mdst)
 log.append({'asset_id':aid,'before_sha256':before,'source_alias_sha256':srcsha,'installed_sha256':sha(dst)})
for oid in ids:S[oid]['complete']=False;S[oid]['notes']='Clean single-edge profiles installed on all four symmetric sides; awaiting current-hash source-plus-six review.'
tmp=INDEX.with_name(INDEX.name+'.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
(HERE/'install-iron-station-rear-edge-v1.json').write_text(json.dumps({'installed':log},indent=2)+'\n')
print(json.dumps({'installed':len(log),'sets':ids},indent=2))
