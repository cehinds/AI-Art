"""Offline rebuild with supersession-aware corrections and exact retained repairs."""
import json
import runpy
from pathlib import Path
from build_batch import process_batch, process_view_columns, process_prebuilt_views, process_view_aliases

OUT=Path(__file__).resolve().parent
specs=json.loads((OUT/'batch-specs.json').read_text())
for spec in specs:
    if (OUT/spec['raw']).exists():
        process_batch(spec)
for spec in json.loads((OUT/'special-batches.json').read_text()):
    if (OUT/spec['raw']).exists():
        process_batch(spec)

# A later per-view correction supersedes an earlier correction for the same asset
# and view. Resolve that once so historical, rejected anisotropic passes do not
# overwrite a newer accepted projection during a full offline rebuild.
corrections=json.loads((OUT/'corrections.json').read_text())
axis_policy_path=OUT/'repair-mappings/reviewed-club-northeast-wall-axis-calibration-v1.json'
axis_policy=json.loads(axis_policy_path.read_text())
axis_policy_keys={(r['object_id'],r['view']) for r in axis_policy.get('rows',[])}
latest={}
for i,c in enumerate(corrections):
    if c.get('full_batch_reextract'):
        continue
    if c.get('symmetric_view_aliases'):
        views=list(c['symmetric_view_aliases'])
    elif c.get('prebuilt_dir'):
        views=list(c['views'])
    elif c.get('view'):
        views=[c['view']] if any((obj.get('id'),c['view']) in axis_policy_keys for obj in c.get('objects',[])) else []
    else:
        views=list(c.get('views',{}))
    for obj in c.get('objects',[]):
        for view in views:
            latest[(obj['id'],view)]=i

for i,c in enumerate(corrections):
    if c.get('symmetric_view_aliases'):
        aliases=c['symmetric_view_aliases']
        for obj in c.get('objects',[]):
            chosen={target:source for target,source in aliases.items() if latest.get((obj['id'],target))==i}
            if chosen:
                process_view_aliases({**c,'objects':[obj],'symmetric_view_aliases':chosen})
        continue
    if c.get('prebuilt_dir'):
        objects=[obj for obj in c.get('objects',[]) if any(latest.get((obj['id'],view))==i for view in c['views'])]
        if objects:
            views=[view for view in c['views'] if any(latest.get((obj['id'],view))==i for obj in objects)]
            process_prebuilt_views({**c,'objects':objects,'views':views})
        continue
    if c.get('full_batch_reextract'):
        if (OUT/c['raw']).exists():
            batch=next((s for s in specs if s['batch_id']==c.get('batch_id')), {})
            process_batch({**batch,**c})
        continue

    views=c.get('views',{})
    if not views and c.get('view') and any((obj.get('id'),c['view']) in axis_policy_keys for obj in c.get('objects',[])):
        views={c['view']:int(c.get('column',0))}
    groups={}
    for obj in c.get('objects',[]):
        active=[]
        for view in views:
            if latest.get((obj['id'],view))!=i:
                continue
            calibration=c.get('cell_calibration',[])
            object_calibration=c.get('object_cell_calibration',{}).get(obj['id'],calibration)
            if len(object_calibration)==2 and abs(float(object_calibration[0])-float(object_calibration[1]))>1e-9:
                continue
            active.append(view)
        if active:
            groups.setdefault(tuple(active),[]).append(obj)
    for active,objects in groups.items():
        batch=next((s for s in specs if s['batch_id']==c.get('batch_id')), {})
        spec={**batch,**c,'objects':objects,'views':{view:views[view] for view in active},'column_count':c.get('column_count',batch.get('column_count',1))}
        if (OUT/spec['raw']).exists():
            process_view_columns(spec,spec['views'])

# These two views require explicit pixel-space remaps after the normalized crop.
for recipe in ('replay_112_rear_profiles.py','replay_121_westwall_rotation.py'):
    runpy.run_path(str(OUT/'repair-mappings'/recipe))

# Apply exact review-backed candidates and canonical JSON snapshots last, after
# all base and per-view generation has finished.
for recipe in ('replay_installed_dark_repairs_v3.py','replay_dark_approved_corrections_v1.py','replay_canonical_json_v3.py'):
    runpy.run_path(str(OUT/'repair-mappings'/recipe))

# Refuse to emit a rebuilt catalog whose canonical source lineage escapes the
# pack root. This catches absolute source paths before the rebuilt index is used.
BOOK=OUT.parent.parent
rebuilt=json.loads((OUT/'set-index.json').read_text())
for asset in rebuilt.get('assets',[]):
    metadata=BOOK/asset['metadata_path']
    doc=json.loads(metadata.read_text())
    provenance=doc.get('provenance',{})
    for path_key,hash_key in (
        ('source_image','source_sha256'),
        ('native_plan_image','native_plan_sha256'),
        ('native_front_image','native_front_sha256'),
    ):
        source_image=provenance.get(path_key)
        if source_image is None:
            continue
        if not isinstance(source_image,str) or source_image.startswith('/'):
            raise ValueError(f"{asset['id']}: provenance.{path_key} must be pack-relative")
        source_path=(BOOK/source_image).resolve()
        source_path.relative_to(BOOK.resolve())
        if not source_path.is_file():
            raise FileNotFoundError(f"{asset['id']}: provenance.{path_key} is missing: {source_image}")
        expected=provenance.get(hash_key)
        if expected:
            import hashlib
            actual=hashlib.sha256(source_path.read_bytes()).hexdigest()
            if actual!=expected:
                raise ValueError(f"{asset['id']}: provenance.{hash_key} does not match {source_image}")
