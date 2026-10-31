"""Install only locally coherent camera and runner axis remaps."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;BOOK=ROOT.parent.parent;SPEC=json.loads((ROOT/'candidates/axis-remaps-v1/candidate.json').read_text());INDEX=ROOT/'set-index.json'
ALLOW={'broadcast-portals-studio-camera','thresholds-red-carpet-runner','ghost-havana-colonial-street-paving-corner-transition'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(rel):
 p=(BOOK/rel).resolve();p.relative_to(BOOK.resolve());return p
idx=json.loads(INDEX.read_text());A={a['id']:a for a in idx['assets']};S={s['object_id']:s for s in idx['view_sets']};prepared=[]
candidate_by_asset={e['asset_id']:e for e in SPEC['entries']}
for e in SPEC['entries']:
 if e['object_id'] not in ALLOW:continue
 a=A[e['asset_id']];cand=(ROOT/e['candidate_path']).resolve();cand.relative_to(ROOT.resolve());assert sha(cand)==e['candidate_sha256']
 src=safe(a['source']['source_image']);assert sha(src)==a['source']['source_sha256']
 if e.get('transform_input_path'):assert sha(safe(e['transform_input_path']))==e['source_sha256']
 if e.get('alias_from_asset_id'):
  if e['alias_from_asset_id'] in candidate_by_asset:
   alias_path=ROOT/candidate_by_asset[e['alias_from_asset_id']]['candidate_path']
  else:
   alias=A[e['alias_from_asset_id']];alias_path=safe(alias['image']['path'])
  assert sha(alias_path)==e['source_sha256']
 dst=safe(a['image']['path']);mdst=safe(a['metadata_path']);snap=ROOT/'prebuilt/axis-remap-before-v1'/f"{e['asset_id']}.png";snap.parent.mkdir(parents=True,exist_ok=True);before=sha(dst);beforemeta=sha(mdst)
 if not snap.exists():snap.write_bytes(dst.read_bytes())
 assert sha(snap)==before or before==e['candidate_sha256'],f"{e['asset_id']}: retained before bytes mismatch"
 prepared.append((e,a,dst,mdst,snap,cand,before,beforemeta))
log=[]
for e,a,dst,mdst,snap,cand,before,beforemeta in prepared:
 assert sha(dst)==before and sha(mdst)==beforemeta
 tmp=dst.with_name(dst.name+'.tmp');tmp.write_bytes(cand.read_bytes());os.replace(tmp,dst);im=Image.open(dst).convert('RGBA')
 a['image']['sha256']=sha(dst);a['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();a['anchor_px']=[128,128]
 hist=a.setdefault('provenance_history',[]);marker='axis-remaps-v1:'+e['asset_id']
 if not any(h.get('candidate_id')==marker for h in hist):hist.append({'candidate_id':marker,'previous_provenance':a.get('provenance',{}),'previous_image_sha256':before})
 prov={'method':e['method'],'source_image':a['source']['source_image'],'source_sha256':a['source']['source_sha256'],'retained_before_png':'reusable/views-additional/prebuilt/axis-remap-before-v1/'+e['asset_id']+'.png','normalization':{'frame_size':list(im.size),'anchor_px':[128,128],'distortion':'none; exact pixel transform or isotropic source normalization'}}
 for k in ('source_rect','uniform_scale','normalized_bbox_size','alias_from_asset_id','alias_from_view','transform_input_path','transform','notes'):
  if k in e:prov[k]=e[k]
 if 'source_sha256' in e:prov['derivation_input_sha256']=e['source_sha256']
 a['provenance']=prov
 tmp=mdst.with_name(mdst.name+'.tmp');tmp.write_text(json.dumps(a,indent=2)+'\n');os.replace(tmp,mdst);log.append({'asset_id':e['asset_id'],'before_sha256':before,'after_sha256':sha(dst)})
for oid in ALLOW:S[oid]['complete']=False;S[oid]['notes']='Orthographic axis correction installed; awaiting current-hash source-plus-six review.'
tmp=INDEX.with_name(INDEX.name+'.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
(HERE/'install-axis-remaps-v1.json').write_text(json.dumps({'installed':log,'pending_candidate_objects':['ghost-havana-colonial-street-paving-corner-transition']},indent=2)+'\n');print(json.dumps({'installed':len(log),'objects':sorted(ALLOW)},indent=2))
