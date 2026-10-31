#!/usr/bin/env python3
"""Install root-approved, same-family NW->NE view mapping with hash guards."""
import hashlib,json,shutil,sys,datetime
from pathlib import Path
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon')
OUT=ROOT/'reusable/views-additional'; STAGE=OUT/'raw/candidates/broadcast-studio-partition-ne-v1'
MAN=json.loads((STAGE/'candidate-manifest.json').read_text())
ROOT_LEDGER=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())
OID=MAN['object_id']; DONOR=MAN['donor_object_id']
assert hashlib.sha256((STAGE/'candidate-source-plus-six.png').read_bytes()).hexdigest()==MAN['contact_sha256']
source=ROOT/MAN['canonical_source']; donor_source=ROOT/MAN['donor_source']
assert hashlib.sha256(source.read_bytes()).hexdigest()==MAN['canonical_source_sha256']
assert hashlib.sha256(donor_source.read_bytes()).hexdigest()==MAN['donor_source_sha256']
proof=ROOT_LEDGER['reviewed'].get(f'book-tiles/pocket-dungeon::{DONOR}')
assert proof and proof.get('status')=='pass', 'Donor lacks current independent PASS'
assert proof.get('source_sha256') in (None,MAN['donor_source_sha256'])
for v in ['front','top','right','left','bottom','rear']:
 assert proof['image_hashes'][v]==hashlib.sha256((OUT/f'{DONOR}.{v}.png').read_bytes()).hexdigest(),f'donor {v} bytes differ from current PASS'
idx=json.loads((OUT/'set-index.json').read_text());spec=json.loads((OUT/'corrections.json').read_text())
backup=OUT/'raw/targeted-repairs/broadcast-ne-install-backup';backup.mkdir(parents=True,exist_ok=True)
snap=OUT/'raw/targeted-repairs/reviewed-snapshots';snap.mkdir(parents=True,exist_ok=True)
reviewed_at='2026-10-26T13:36:20Z'
review={'object_id':OID,'reviewer':'root','reviewed_at':reviewed_at,'status':'candidate-approved-all-six','contact':MAN['contact'],'contact_sha256':MAN['contact_sha256'],'target_source_sha256':MAN['canonical_source_sha256'],'donor_object_id':DONOR,'donor_source_sha256':MAN['donor_source_sha256'],'view_map':MAN['views'],'approval_scope':'Exact staged source-plus-six contact; all six target views accepted for installation.'}
(STAGE/'candidate-review.json').write_text(json.dumps(review,indent=2)+'\n')
import importlib.util
specmod=importlib.util.spec_from_file_location('deterministic',OUT/'apply_deterministic_view_fixes.py');mod=importlib.util.module_from_spec(specmod);specmod.loader.exec_module(mod)
ops=[];records=[]
for rec in MAN['views']:
 v=rec['target_view'];target=OUT/f'{OID}.{v}.png';current=hashlib.sha256(target.read_bytes()).hexdigest()
 assert current==rec['target_sha256_before'],f'target {v} changed since staging'
 donor_path=OUT/f"{DONOR}.{rec['donor_view']}.png"
 assert hashlib.sha256(donor_path.read_bytes()).hexdigest()==rec['donor_sha256'],f'donor {v} changed since staging'
 snapshot_path=f'raw/targeted-repairs/reviewed-snapshots/{OID}.{v}.root-approved.png';snapshot=OUT/snapshot_path
 shutil.copyfile(ROOT/rec['candidate_path'],snapshot)
 snapsha=hashlib.sha256(snapshot.read_bytes()).hexdigest()
 op={'type':'restore-reviewed-png','object_id':OID,'view':v,'before_sha256':current,'snapshot_path':snapshot_path,'snapshot_sha256':snapsha,'reviewer':'root','reviewed_at':reviewed_at,'review_source_sha256':MAN['canonical_source_sha256'],'reason':'Install exact root-approved target-source-plus-six view derived from the current whole-set-PASS same-family NW donor. Target NE source identity remains canonical; donor relationship and rigid direction mapping are recorded in provenance_override.','provenance_override':{'method':'inferred-family-view-donor','source_image':MAN['canonical_source'],'source_sha256':MAN['canonical_source_sha256'],'family_donor_object_id':DONOR,'family_donor_view':rec['donor_view'],'donor_source_image':MAN['donor_source'],'donor_source_sha256':MAN['donor_source_sha256'],'donor_image_sha256':rec['donor_sha256'],'mapping_transform':{'rotation_degrees_ccw':rec['rotation_degrees_ccw'],'operation':'donor view remapped to corresponding world-axis view; TOP/BOTTOM cropped, rotated 90 degrees, uniformly re-anchored'},'candidate_contact_sha256':MAN['contact_sha256'],'notes':'Same-kit source-bounded geometry donor; target canonical source remains authoritative.'}}
 ops.append(op)
res=[mod.apply(op,idx,backup) for op in ops]
s=next(x for x in idx['view_sets'] if x['object_id']==OID);s['complete']=False;s['geometry_qa']='pending-review';s['notes']='Root-approved exact target-source-plus-six NW→NE role mapping installed; awaiting fresh current-source hash review.'
spec['operations'].extend(ops)
(OUT/'set-index.json').write_text(json.dumps(idx,indent=2)+'\n');(OUT/'corrections.json').write_text(json.dumps(spec,indent=2)+'\n')
(STAGE/'install-result.json').write_text(json.dumps({'object_id':OID,'status':'installed-pending-fresh-review','review':review,'operations':ops,'results':res},indent=2)+'\n')
print(json.dumps({'object_id':OID,'results':res},indent=2))
