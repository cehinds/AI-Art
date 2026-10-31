"""Replay inferred rear profiles for 112 edge/corner transitions."""
from pathlib import Path
import hashlib, json, os, struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
SPEC=json.loads((HERE/'112-rear-profile-mirror.json').read_text());INDEX=OUT/'set-index.json';idx=json.loads(INDEX.read_text())
changed=False
for oid, h in SPEC['objects'].items():
 src=next(a for a in idx['assets'] if a['id']==oid+'.front');dst=next(a for a in idx['assets'] if a['id']==oid+'.rear');srcp=BOOK/src['image']['path'];dstp=BOOK/dst['image']['path']
 if hashlib.sha256(dstp.read_bytes()).hexdigest()==h['after_rear_sha256']:continue
 if hashlib.sha256(srcp.read_bytes()).hexdigest()!=h['source_front_sha256']:raise RuntimeError(f'{oid}: source FRONT changed; refusing replay')
 if hashlib.sha256(dstp.read_bytes()).hexdigest()!=h['prior_rear_sha256']:raise RuntimeError(f'{oid}: unexpected REAR hash; refusing replay')
 im=Image.open(srcp).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);im.save(dstp,optimize=True);rgba=im.tobytes();dst['image']['sha256']=hashlib.sha256(dstp.read_bytes()).hexdigest();dst['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest();dst['provenance'].update({'method':'inferred-opposite-edge-profile-mirror','source_view':'front','source_view_sha256':h['source_front_sha256'],'view_transform':'horizontal mirror in image plane','symmetry_reason':'Rear sees the same full tile curb/bank silhouette from the opposite horizontal direction; back-face material is inferred.'});(BOOK/dst['metadata_path']).write_text(json.dumps(dst,indent=2)+'\n')
 changed=True
if changed:
 for oid in SPEC['objects']:
  s=next(s for s in idx['view_sets'] if s['object_id']==oid);s['complete']=False;s['notes']='Rear profile inferred by mirroring corrected front; pending independent QA.'
t=INDEX.with_suffix('.json.tmp');t.write_text(json.dumps(idx,indent=2)+'\n');os.replace(t,INDEX)
