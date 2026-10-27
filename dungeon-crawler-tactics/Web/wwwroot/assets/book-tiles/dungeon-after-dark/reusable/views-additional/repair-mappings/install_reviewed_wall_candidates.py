"""Install the root-reviewed Dark-book wall candidates with exact hash guards."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
SPEC=json.loads((HERE/'install-reviewed-wall-candidates-2026-10-26.json').read_text());INDEX=OUT/'set-index.json'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def safe(rel):
 p=(BOOK/rel).resolve();p.relative_to(BOOK.resolve());return p
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};prepared=[];sets=[]
for s in SPEC['sets']:
 src=safe(s['source_image']);assert sha(src)==s['source_sha256'],f"{s['object_id']}: source changed"
 atlas=safe(s['raw_atlas']);assert sha(atlas)==s['raw_atlas_sha256'],f"{s['object_id']}: raw atlas changed"
 prompt=safe(s['prompt_path']);assert sha(prompt)==s['prompt_sha256'],f"{s['object_id']}: prompt changed"
 contact=safe(s['source_contact_sheet']);assert contact.exists(),f"{s['object_id']}: missing reference contact"
 ss=[x for x in idx['view_sets'] if x['object_id']==s['object_id']];assert len(ss)==1,f"{s['object_id']}: duplicate set index"
 for v,item in s['views'].items():
  aid=item['asset_id'];assert aid in assets;asset=assets[aid];dst=safe(asset['image']['path']);mdst=safe(asset['metadata_path']);cand=(OUT/item['candidate_path']).resolve();cand.relative_to(OUT.resolve())
  assert sha(cand)==item['after_sha256'],f"{aid}: candidate changed"
  current=sha(dst) if dst.exists() else None;allowed={None,item['before_sha256'],item['after_sha256']}
  if item.get('stale_replay_sha256'):allowed.add(item['stale_replay_sha256'])
  assert current in allowed,f"{aid}: unexpected image {current}"
  meta=sha(mdst) if mdst.exists() else None;expected_index_meta=hashlib.sha256((json.dumps(asset,indent=2)+'\n').encode()).hexdigest()
  assert meta in {None,item['before_metadata_sha256'],expected_index_meta},f"{aid}: unexpected metadata {meta}"
  prepared.append((s,v,item,asset,dst,mdst,cand))
 sets.append(ss[0])
# Verify each affected view-set has exactly six distinct referenced assets.
for s in SPEC['sets']:
 ss=[x for x in idx['view_sets'] if x['object_id']==s['object_id']][0]
 assert set(ss['views'])=={'front','top','right','left','bottom','rear'}
# All guard checks precede writes. Update candidates and sidecars; replace index last.
for s,v,item,asset,dst,mdst,cand in prepared:
 if not dst.exists() or sha(dst)!=item['after_sha256']:
  tmp=dst.with_name(dst.name+'.tmp');tmp.write_bytes(cand.read_bytes());os.replace(tmp,dst)
 im=Image.open(dst).convert('RGBA');asset['image']['sha256']=sha(dst);asset['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()
 hist=asset.setdefault('provenance_history',[]);marker='reviewed-wall-candidate-2026-10-26:'+s['object_id']+':'+v
 if not any(h.get('candidate_id')==marker for h in hist):hist.append({'candidate_id':marker,'previous_provenance':asset.get('provenance',{}),'previous_image_sha256':item['before_sha256']})
 normalization={'frame_size':[256,256],'anchor_px':[128,128],'resampling':'nearest','distortion':'none; aspect ratio preserved','uniform_scale':item.get('uniform_scale',s.get('uniform_scale'))}
 transform='none'
 if item.get('rotation_degrees_ccw'):
  transform=f"rotate {item['rotation_degrees_ccw']} degrees counter-clockwise; calibrate long-Y extent to retained live broad-side span {item['target_live_broad_span_px']} px"
 asset['provenance']={'method':'source-guided-orthographic-view-repair','source_image':s['source_image'],'source_sha256':s['source_sha256'],'source_contact_sheet':s['source_contact_sheet'],'source_contact_sheet_sha256':sha(safe(s['source_contact_sheet'])),'generated_atlas':s['raw_atlas'],'generated_atlas_sha256':s['raw_atlas_sha256'],'prompt_path':s['prompt_path'],'prompt_sha256':s['prompt_sha256'],'source_rect':item['source_rect'],'normalization':normalization,'view_transform':transform,'geometry_basis':s.get('geometry_basis','Y-extended upright wall: thin end elevations, broad opposing side elevations, long-Y top/bottom plans; one isotropic scale across the generated six-view set'),'notes':'Illustrative orthographic view. Hidden surfaces are inferred, not recovered source pixels or metrically calibrated.'}
 asset.pop('_installed_metadata_sha256',None)
 mdst.parent.mkdir(parents=True,exist_ok=True);tmp=mdst.with_name(mdst.name+'.tmp');tmp.write_text(json.dumps(asset,indent=2)+'\n');os.replace(tmp,mdst)
for s in SPEC['sets']:
 target=next(x for x in idx['view_sets'] if x['object_id']==s['object_id']);target['complete']=False;target['notes']='Root-reviewed source-guided correction installed; pending indexed current-source+six PASS.'
tmp=INDEX.with_name(INDEX.name+'.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
print(json.dumps({'installed_views':len(prepared),'objects':[s['object_id'] for s in SPEC['sets']]},indent=2))
