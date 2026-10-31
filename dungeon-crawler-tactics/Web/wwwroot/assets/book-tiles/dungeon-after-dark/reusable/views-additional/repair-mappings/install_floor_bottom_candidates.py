"""Install eight source-guided underside repairs with exact current-byte guards."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;BOOK=ROOT.parent.parent
SPEC=json.loads((ROOT/'candidates/floor-bottoms-v1/candidate.json').read_text());INDEX=ROOT/'set-index.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(rel):
 p=(BOOK/rel).resolve();p.relative_to(BOOK.resolve());return p
idx=json.loads(INDEX.read_text());A={a['id']:a for a in idx['assets']};S={s['object_id']:s for s in idx['view_sets']}
assert len(S)==len(idx['view_sets']),'duplicate set object_id'
prepared=[]
for e in SPEC['entries']:
 a=A[e['asset_id']];assert e['asset_id']==e['object_id']+'.bottom'
 src=safe(e['source_image']);assert sha(src)==e['source_sha256']
 raw=safe(e['raw_atlas']);assert sha(raw)==e['raw_atlas_sha256']
 prompt=safe(e['prompt_path']);assert sha(prompt)==e['prompt_sha256']
 contact=safe(e['source_contact_sheet']);assert sha(contact)==e['source_contact_sheet_sha256']
 cand=(ROOT/e['candidate_path']).resolve();cand.relative_to(ROOT.resolve());assert sha(cand)==e['candidate_sha256']
 dst=safe(a['image']['path']);mdst=safe(a['metadata_path']);assert dst.exists() and mdst.exists()
 prepared.append((e,a,dst,mdst,cand,sha(dst),sha(mdst)))
snaproot=ROOT/'prebuilt/floor-bottom-snapshots-v1'
for e,a,dst,mdst,cand,before,beforemeta in prepared:
 snap=snaproot/f"{e['asset_id']}.png";snap.parent.mkdir(parents=True,exist_ok=True)
 if not snap.exists():snap.write_bytes(dst.read_bytes())
 assert sha(snap)==before
log=[]
for e,a,dst,mdst,cand,before,beforemeta in prepared:
 assert sha(dst)==before and sha(mdst)==beforemeta,f"{e['asset_id']}: live bytes changed"
 tmp=dst.with_name(dst.name+'.tmp');tmp.write_bytes(cand.read_bytes());os.replace(tmp,dst)
 im=Image.open(dst).convert('RGBA');a['image']['sha256']=sha(dst);a['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();a['anchor_px']=[128,128]
 hist=a.setdefault('provenance_history',[]);marker='floor-bottoms-v1:'+e['asset_id']
 if not any(h.get('candidate_id')==marker for h in hist):hist.append({'candidate_id':marker,'previous_provenance':a.get('provenance',{}),'previous_image_sha256':before})
 a['provenance']={'method':'source-guided-inferred-opaque-floor-underside','source_image':e['source_image'],'source_sha256':e['source_sha256'],'raw_atlas':e['raw_atlas'],'raw_atlas_sha256':e['raw_atlas_sha256'],'prompt_path':e['prompt_path'],'prompt_sha256':e['prompt_sha256'],'source_contact_sheet':e['source_contact_sheet'],'source_contact_sheet_sha256':e['source_contact_sheet_sha256'],'source_rect':e['source_rect'],'retained_before_png':'reusable/views-additional/prebuilt/floor-bottom-snapshots-v1/'+e['asset_id']+'.png','normalization':{'scale':e['uniform_scale'],'offset_px':[0,0],'resampling':'nearest','frame_size':list(im.size),'anchor_px':[128,128],'distortion':'none; uniform isotropic scaling'},'notes':e['notes']}
 tmp=mdst.with_name(mdst.name+'.tmp');tmp.write_text(json.dumps(a,indent=2)+'\n');os.replace(tmp,mdst)
 log.append({'asset_id':e['asset_id'],'before_sha256':before,'after_sha256':sha(dst),'metadata_path':str(mdst.relative_to(BOOK))})
for oid in {e['object_id'] for e in SPEC['entries']}:
 S[oid]['complete']=False;S[oid]['notes']='Inferred opaque underside installed; awaiting current-hash source-plus-six review.'
tmp=INDEX.with_name(INDEX.name+'.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
report={'candidate_id':'floor-bottoms-v1','installed':log,'sets_pending_review':sorted({e['object_id'] for e in SPEC['entries']})}
(HERE/'install-floor-bottom-candidates-v1.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'installed':len(log),'sets_pending_review':report['sets_pending_review']},indent=2))
