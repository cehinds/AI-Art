"""Install six source-guided ground substrate bottoms with snapshot guards."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;BOOK=ROOT.parent.parent;SPEC=json.loads((ROOT/'candidates/varied-ground-undersides-v1/candidate.json').read_text());INDEX=ROOT/'set-index.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(rel):
 p=(BOOK/rel).resolve();p.relative_to(BOOK.resolve());return p
idx=json.loads(INDEX.read_text());A={a['id']:a for a in idx['assets']};S={s['object_id']:s for s in idx['view_sets']};prepared=[]
for e in SPEC['entries']:
 a=A[e['asset_id']];src=safe(e['source_image']);raw=safe(e['raw_atlas']);prompt=safe(e['prompt_path']);contact=safe(e['source_contact_sheet']);cand=(ROOT/e['candidate_path']).resolve();cand.relative_to(ROOT.resolve())
 assert sha(src)==e['source_sha256'] and sha(raw)==e['raw_atlas_sha256'] and sha(prompt)==e['prompt_sha256'] and sha(contact)==e['source_contact_sheet_sha256'] and sha(cand)==e['candidate_sha256']
 dst=safe(a['image']['path']);mdst=safe(a['metadata_path']);snap=ROOT/'prebuilt/varied-ground-underside-before-v1'/f"{a['id']}.png";snap.parent.mkdir(parents=True,exist_ok=True);before=sha(dst);beforemeta=sha(mdst)
 if not snap.exists():snap.write_bytes(dst.read_bytes())
 assert sha(snap)==before
 prepared.append((e,a,dst,mdst,snap,cand,before,beforemeta))
log=[]
for e,a,dst,mdst,snap,cand,before,beforemeta in prepared:
 assert sha(dst)==before and sha(mdst)==beforemeta,f"{a['id']}: changed output"
 tmp=dst.with_name(dst.name+'.tmp');tmp.write_bytes(cand.read_bytes());os.replace(tmp,dst);im=Image.open(dst).convert('RGBA')
 a['image']['sha256']=sha(dst);a['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();a['anchor_px']=[128,128]
 hist=a.setdefault('provenance_history',[]);marker='varied-ground-undersides-v1:'+a['id']
 if not any(h.get('candidate_id')==marker for h in hist):hist.append({'candidate_id':marker,'previous_provenance':a.get('provenance',{}),'previous_image_sha256':before})
 a['provenance']={'method':'source-guided-inferred-opaque-ground-underside','source_image':e['source_image'],'source_sha256':e['source_sha256'],'raw_atlas':e['raw_atlas'],'raw_atlas_sha256':e['raw_atlas_sha256'],'prompt_path':e['prompt_path'],'prompt_sha256':e['prompt_sha256'],'source_contact_sheet':e['source_contact_sheet'],'source_contact_sheet_sha256':e['source_contact_sheet_sha256'],'source_rect':e['source_rect'],'retained_before_png':'reusable/views-additional/prebuilt/varied-ground-underside-before-v1/'+a['id']+'.png','normalization':{'scale':e['uniform_scale'],'offset_px':[0,0],'resampling':'nearest','frame_size':list(im.size),'anchor_px':[128,128],'distortion':'none; isotropic scaling'},'notes':e['notes']}
 tmp=mdst.with_name(mdst.name+'.tmp');tmp.write_text(json.dumps(a,indent=2)+'\n');os.replace(tmp,mdst);log.append({'asset_id':a['id'],'before_sha256':before,'after_sha256':sha(dst)})
for oid in {e['object_id'] for e in SPEC['entries']}:S[oid]['complete']=False;S[oid]['notes']='Inferred substrate underside installed; awaiting current-hash source-plus-six review.'
tmp=INDEX.with_name(INDEX.name+'.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
(HERE/'install-varied-ground-undersides-v1.json').write_text(json.dumps({'installed':log},indent=2)+'\n');print(json.dumps({'installed':len(log),'objects':sorted({e['object_id'] for e in SPEC['entries']})},indent=2))
