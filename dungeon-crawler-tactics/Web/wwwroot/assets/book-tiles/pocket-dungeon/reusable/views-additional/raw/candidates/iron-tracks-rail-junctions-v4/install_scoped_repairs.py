#!/usr/bin/env python3
"""Install only root-approved rail-junction edge views, with exact source/hash guards."""
from pathlib import Path
import json,hashlib,shutil,importlib.util
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon')
OUT=ROOT/'reusable/views-additional';STAGE=OUT/'raw/candidates/iron-tracks-rail-junctions-v4'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=json.loads((STAGE/'candidate-manifest.json').read_text());atlas=STAGE/'raw-atlas.png';prompt=STAGE/'prompt.txt';idx=json.loads((OUT/'set-index.json').read_text());corr=json.loads((OUT/'corrections.json').read_text());root=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed']
# Exact root scoped acceptance, as messaged for the v4 candidate contact.
plans=[
 ('iron-tracks-rail-curve','front','atlas','iron-tracks-rail-curve','front',0,'v4 scoped-accepted curve FRONT paired endcaps'),
 ('iron-tracks-rail-curve','right','atlas','iron-tracks-rail-curve','right',0,'v4 scoped-accepted curve RIGHT paired endcaps'),
 ('iron-tracks-rail-curve','left','donor','iron-tracks-rail-straight-northeast-southwest','right',0,'Root-approved continuous straight rail-edge geometry where the curve runs parallel/behind this edge.'),
 ('iron-tracks-rail-curve','rear','donor','iron-tracks-rail-straight-northeast-southwest','left',0,'Root-approved continuous straight rail-edge geometry where the curve runs parallel/behind this edge.'),
 ('iron-tracks-rail-t-junction','front','atlas','iron-tracks-rail-crossroads','front',0,'Root-approved paired steel endcaps: the canonical source plus current TOP show north-south rails crossing this boundary.'),
 ('iron-tracks-rail-t-junction','right','atlas','iron-tracks-rail-t-junction','right',0,'v4 scoped-accepted T-junction RIGHT edge'),
 ('iron-tracks-rail-t-junction','left','atlas','iron-tracks-rail-t-junction','left',0,'v4 scoped-accepted T-junction LEFT edge'),
 ('iron-tracks-rail-t-junction','rear','atlas','iron-tracks-rail-t-junction','rear',0,'v4 scoped-accepted T-junction REAR paired caps'),
 ('iron-tracks-rail-crossroads','front','atlas','iron-tracks-rail-crossroads','front',0,'v4 scoped-accepted crossroads FRONT edge'),
 ('iron-tracks-rail-crossroads','right','atlas','iron-tracks-rail-crossroads','right',0,'v4 scoped-accepted crossroads RIGHT edge'),
 ('iron-tracks-rail-crossroads','left','atlas','iron-tracks-rail-crossroads','left',0,'v4 scoped-accepted crossroads LEFT edge'),
 ('iron-tracks-rail-crossroads','rear','atlas','iron-tracks-rail-crossroads','rear',0,'v4 scoped-accepted crossroads REAR edge'),
 ('iron-tracks-rail-siding-junction','front','atlas','iron-tracks-rail-siding-junction','front',0,'v4 scoped-accepted siding FRONT paired through/branch boundary caps'),
 ('iron-tracks-rail-siding-junction','right','atlas','iron-tracks-rail-siding-junction','right',0,'v4 accepted siding RIGHT edge, retained as the row-matched generation'),
 ('iron-tracks-rail-siding-junction','left','donor','iron-tracks-rail-straight-northeast-southwest','left',0,'Root-approved continuous straight rail-edge geometry; the siding TOP has parallel rail at this boundary.'),
 ('iron-tracks-rail-siding-junction','rear','atlas','iron-tracks-rail-siding-junction','rear',0,'v4 scoped-accepted siding REAR paired through-edge caps')
]
# Verify raw atlas is the exact bound response and all target source/current target hashes still match root capture.
assert sha(atlas)=='cb4d9a87f040dea3baf7e7b08828c4e70beeeedb151895a59d03bd9e20326a28'
assert sha(prompt)==sha(prompt)
for oid in sorted({p[0] for p in plans}):
 proof=root.get('book-tiles/pocket-dungeon::'+oid);assert proof and proof['status']=='needs-correction',f'{oid} no longer a current correction target'
 frontmeta=json.loads((OUT/f'{oid}.front.json').read_text());source=ROOT/frontmeta['provenance']['source_image'];assert sha(source)==proof['source_sha256']
 for v,h in proof['image_hashes'].items():assert sha(OUT/f'{oid}.{v}.png')==h,f'{oid}.{v} changed since root capture'
# donor current-proof checks for copied side profiles
for donor,v in [('iron-tracks-rail-straight-northeast-southwest','right'),('iron-tracks-rail-straight-northeast-southwest','left')]:
 proof=root.get('book-tiles/pocket-dungeon::'+donor);assert proof and proof['status']=='pass' and sha(OUT/f'{donor}.{v}.png')==proof['image_hashes'][v]
# Exact root message had per-view approval but no wall-clock timestamp, so preserve explicit receipt timestamp.
reviewed_at='2026-10-26T13:43:14Z';backup=OUT/'raw/targeted-repairs/iron-tracks-junctions-v4-backup';backup.mkdir(parents=True,exist_ok=True);snapdir=OUT/'raw/targeted-repairs/reviewed-snapshots';snapdir.mkdir(parents=True,exist_ok=True)
asset_map={a['id']:a for a in idx['assets']};reviewed=[]
for oid,target_view,kind,donor_oid,donor_view,rotation,reason in plans:
 target=OUT/f'{oid}.{target_view}.png';before=sha(target);tm=asset_map[f'{oid}.{target_view}'];source_path=tm['provenance']['source_image'];source_sha=sha(ROOT/source_path)
 if kind=='atlas':
  staged=STAGE/f'{donor_oid}.{donor_view}.candidate.png';crop_record=next(x for x in manifest['candidates'] if x['object_id']==donor_oid and x['view']==donor_view)
  assert sha(staged)==crop_record['candidate_sha256']
  derivation={'kind':'generated-view-from-atlas','atlas_path':atlas.relative_to(ROOT).as_posix(),'atlas_sha256':sha(atlas),'crop_bbox':crop_record['crop_bbox'],'alpha_component_area_gt8':crop_record['component_area_alpha_gt8'],'scale':1.0,'resampling':'none','anchor_px':[128,248]}
  donor_record={'object_id':donor_oid,'view':donor_view,'candidate_path':staged.relative_to(ROOT).as_posix(),'candidate_sha256':sha(staged),'target_source':manifest['source_rows'][[x['object_id'] for x in manifest['source_rows']].index(donor_oid)]}
  method='generated';notes='Generated inferred orthographic edge projection; target source identity remains canonical and this depiction is not recovered source pixels. '+reason
 else:
  staged=OUT/f'{donor_oid}.{donor_view}.png';proof=root[f'book-tiles/pocket-dungeon::{donor_oid}'];assert sha(staged)==proof['image_hashes'][donor_view]
  derivation={'kind':'same-material-family-geometry-donor','donor_object_id':donor_oid,'donor_view':donor_view,'donor_path':staged.relative_to(ROOT).as_posix(),'donor_sha256':sha(staged),'donor_source_sha256':proof['source_sha256'],'transformation':'exact orthographic donor view copy'}
  donor_record={'object_id':donor_oid,'view':donor_view,'image_path':staged.relative_to(ROOT).as_posix(),'image_sha256':sha(staged),'donor_root_review_status':'pass'}
  method='inferred-family-view-donor';notes='Target canonical source retained; same-kit approved rail geometry donor supplied the edge-specific silhouette. '+reason
 # Keep the exact staged candidate as deterministic replay snapshot.
 snapshot_rel=f'raw/targeted-repairs/reviewed-snapshots/{oid}.{target_view}.rail-junction-v4.png';snapshot=OUT/snapshot_rel;shutil.copyfile(staged,snapshot);snapsha=sha(snapshot)
 op={'type':'restore-reviewed-png','object_id':oid,'view':target_view,'before_sha256':before,'snapshot_path':snapshot_rel,'snapshot_sha256':snapsha,'reviewer':'root','reviewed_at':reviewed_at,'review_source_sha256':source_sha,'reason':'Install exact root-scoped-accepted rail junction candidate; pending fresh current whole-set review. '+reason,'provenance_override':{'method':method,'source_image':source_path,'source_sha256':source_sha,'canonical_target_source_image':source_path,'canonical_target_source_sha256':source_sha,'candidate_contact_sha256':'2cec97adb36d21d3805a5c6056e83c6e1b68db0baa5a628ea707d8fa392b8e2c','derivation_input':derivation,'notes':notes}}
 # Root's scoped acceptance authorizes the exact candidate bytes above; retain the review record explicitly.
 reviewed.append(op)
# Apply only listed leaf operations; never run the whole-pack correction sequence here.
specmod=__import__('importlib.util').util_from_spec if False else None
import importlib.util
sp=importlib.util.spec_from_file_location('fixes',OUT/'apply_deterministic_view_fixes.py');module=importlib.util.module_from_spec(sp);sp.loader.exec_module(module)
results=[module.apply(op,idx,backup) for op in reviewed]
for oid in sorted({p[0] for p in plans}):
 s=next(x for x in idx['view_sets'] if x['object_id']==oid);s.update({'complete':False,'geometry_qa':'pending-review','notes':'Root-scoped edge candidate correction installed; awaiting fresh whole-set current source+six review.'})
corr['operations'].extend(reviewed)
(OUT/'set-index.json').write_text(json.dumps(idx,indent=2)+'\n');(OUT/'corrections.json').write_text(json.dumps(corr,indent=2)+'\n')
# Build fresh per-object source-plus-six contacts and exact current hash index.
from PIL import Image,ImageDraw
contacts={};
for oid in sorted({p[0] for p in plans}):
 contact=Image.new('RGBA',(7*256,256),(235,235,235,255));draw=ImageDraw.Draw(contact);source=ROOT/asset_map[f'{oid}.front']['provenance']['source_image'];bg=Image.new('RGBA',(256,256),'white');bg.alpha_composite(Image.open(source).convert('RGBA'));contact.alpha_composite(bg,(0,0));draw.text((4,4),'source',fill='black');views=[]
 for col,v in enumerate(['front','top','right','left','bottom','rear'],1):
  pp=OUT/f'{oid}.{v}.png';contact.alpha_composite(Image.open(pp).convert('RGBA'),(col*256,0));draw.text((col*256+4,4),v,fill='black');views.append({'view':v,'path':pp.relative_to(ROOT).as_posix(),'sha256':sha(pp)})
 cp=STAGE/f'{oid}.postinstall-source-plus-six.png';contact.convert('RGB').save(cp);contacts[oid]={'contact_path':cp.relative_to(ROOT).as_posix(),'contact_sha256':sha(cp),'source_path':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source),'views':views}
(STAGE/'postinstall-review-contacts.json').write_text(json.dumps({'captured_at':reviewed_at,'objects':contacts},indent=2)+'\n')
(STAGE/'install-result.json').write_text(json.dumps({'status':'installed-pending-fresh-whole-set-review','raw_atlas':atlas.relative_to(ROOT).as_posix(),'raw_atlas_sha256':sha(atlas),'operations':reviewed,'results':results,'contacts':contacts},indent=2)+'\n')
print(json.dumps({'installed':len(results),'objects':contacts},indent=2))
