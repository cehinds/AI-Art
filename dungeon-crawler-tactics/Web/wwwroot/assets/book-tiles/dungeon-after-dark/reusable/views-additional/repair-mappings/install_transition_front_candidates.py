"""Install four source-guided transition FRONT profiles with exact guards."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;SPEC=json.loads((OUT/'candidates/transitions-front-v2/candidate.json').read_text());INDEX=OUT/'set-index.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(rel):
 p=(BOOK/rel).resolve();p.relative_to(BOOK.resolve());return p
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};prepared=[]
for e in SPEC['entries']:
 src=safe(e['source_image']);assert sha(src)==e['source_sha256'],f"{e['asset_id']}: source changed"
 atlas=safe(e['raw_atlas']);assert sha(atlas)==e['raw_atlas_sha256']
 prompt=safe(e['prompt_path']);assert sha(prompt)==e['prompt_sha256']
 cand=(OUT/e['candidate_path']).resolve();cand.relative_to(OUT.resolve());assert sha(cand)==e['candidate_sha256']
 a=assets[e['asset_id']];dst=safe(a['image']['path']);mdst=safe(a['metadata_path']);cur=sha(dst) if dst.exists() else None;allowed={None,e['before_sha256'],e['candidate_sha256']}
 if e.get('stale_replay_sha256'):allowed.add(e['stale_replay_sha256'])
 assert cur in allowed,f"{e['asset_id']}: unexpected output hash {cur}"
 meta=sha(mdst) if mdst.exists() else None;expected=hashlib.sha256((json.dumps(a,indent=2)+'\n').encode()).hexdigest()
 allowed_meta={None,e['before_metadata_sha256'],e.get('stale_replay_metadata_sha256'),expected}
 assert meta in allowed_meta,f"{e['asset_id']}: unexpected sidecar {meta}"
 ss=[s for s in idx['view_sets'] if s['object_id']==e['object_id']];assert len(ss)==1
 prepared.append((e,a,dst,mdst,cand,ss[0]))
for e,a,dst,mdst,cand,ss in prepared:
 if not dst.exists() or sha(dst)!=e['candidate_sha256']:
  tmp=dst.with_name(dst.name+'.tmp');tmp.write_bytes(cand.read_bytes());os.replace(tmp,dst)
 im=Image.open(dst).convert('RGBA');a['image']['sha256']=sha(dst);a['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
 hist=a.setdefault('provenance_history',[]);marker='transitions-front-v2:'+e['object_id']
 if not any(h.get('candidate_id')==marker for h in hist):hist.append({'candidate_id':marker,'previous_provenance':a.get('provenance',{}),'previous_image_sha256':e['before_sha256']})
 a['provenance']={'method':'source-guided-orthographic-transition-profile','source_image':e['source_image'],'source_sha256':e['source_sha256'],'source_contact_sheet':'reusable/views-additional/contacts/transition-front-four-source.png','source_contact_sheet_sha256':sha(safe('reusable/views-additional/contacts/transition-front-four-source.png')),'geometry_reference_view':'right','geometry_reference_contact':'reusable/views-additional/contacts/transition-front-four-side-guide.png','geometry_reference_contact_sha256':sha(safe('reusable/views-additional/contacts/transition-front-four-side-guide.png')),'generated_atlas':e['raw_atlas'],'generated_atlas_sha256':e['raw_atlas_sha256'],'prompt_path':e['prompt_path'],'prompt_sha256':e['prompt_sha256'],'source_rect':e['source_rect'],'normalization':{'scale':e['uniform_scale'],'offset_px':[0,0],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; uniform scale matched to existing lateral profile width'},'notes':'Full slab and raised-curb front profile. Illustrative orthographic projection; hidden surfaces remain inferred.'}
 a['anchor_px']=[128,128];mdst.parent.mkdir(parents=True,exist_ok=True);tmp=mdst.with_name(mdst.name+'.tmp');tmp.write_text(json.dumps(a,indent=2)+'\n');os.replace(tmp,mdst);ss['complete']=False;ss['notes']='Front thickness profile corrected; pending current-hash source+six review.'
tmp=INDEX.with_name(INDEX.name+'.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
print(json.dumps({'installed_front_profiles':len(prepared),'object_ids':[e['object_id'] for e,_,_,_,_,_ in prepared]},indent=2))
