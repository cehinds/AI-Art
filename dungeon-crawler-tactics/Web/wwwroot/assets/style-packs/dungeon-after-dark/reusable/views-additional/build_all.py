"""Rebuild current six-view outputs from retained raw atlases and exact pack-local recipes."""
import json
from pathlib import Path
from build_batch import process_batch, process_view_column, process_arsenal_axis_pair, process_selected_views, process_single_view_image, process_object_local_cells_shared_scale
OUT=Path(__file__).resolve().parent
specs=json.loads((OUT/'batch-specs.json').read_text())
index=json.loads((OUT/'set-index.json').read_text())
asset_map={a['id']:a for a in index['assets']}
VIEWS=['front','top','right','left','bottom','rear']
def views_for(raw, oid):
    suffix=str(raw)
    return {v for v in VIEWS if f'{oid}.{v}' in asset_map and
            str(asset_map[f'{oid}.{v}']['provenance'].get('generated_atlas','')).endswith(suffix)}
def active_for(raw, objects):
    return {obj['id'] for obj in objects if views_for(raw,obj['id'])}
for spec in specs:
    if not (OUT / spec['raw']).is_file():
        continue  # Superseded historical alias; retained split atlas specs cover its objects.
    bid=spec.get('batch_id')
    if spec.get('shared_scale_local_cells'):
        selected={oid:views for oid,views in spec['shared_scale_local_cells'].items()
                  if set(views)&views_for(spec['raw'],oid)}
        if selected:process_object_local_cells_shared_scale(spec,selected)
        continue
    if bid=='dad-arsenal24-top':
        bottom=next(s for s in specs if s.get('batch_id')=='dad-arsenal24-bottom')
        ids=active_for(spec['raw'],spec['objects'])|active_for(bottom['raw'],spec['objects'])
        process_arsenal_axis_pair(spec,bottom,ids)
        continue
    if bid=='dad-arsenal24-bottom':
        continue
    if spec.get('selections'):
        object_ids={o['id'] for o in spec['objects']}
        chosen={oid:{v:True for v in views if v in views_for(spec['raw'],oid)}
                for oid,views in spec['selections'].items() if oid in object_ids}
        chosen={oid:views for oid,views in chosen.items() if views}
        if chosen: process_selected_views(spec,chosen)
        continue
    if spec.get('single_image_view'):
        ids=active_for(spec['raw'],spec['objects'])
        for oid in ids: process_single_view_image(spec,oid)
        continue
    if bid=='dad-actor-01-bottom-correction':
        ids={o['id'] for o in spec['objects'] if 'bottom' in views_for(spec['raw'],o['id'])}
        if ids:process_view_column(spec,'bottom',4,ids)
    elif bid in {'dad-equipment-02-axes','dad-equipment-03-axes'}:
        top_ids={o['id'] for o in spec['objects'] if {'top','bottom'}&views_for(spec['raw'],o['id'])}
        if top_ids:
            process_view_column(spec,'top',1,top_ids);process_view_column(spec,'bottom',4,top_ids)
    elif bid=='dad-rat-top-correction':
        ids=set(spec['object_ids'])&{o['id'] for o in spec['objects'] if 'top' in views_for(spec['raw'],o['id'])}
        if ids:process_view_column(spec,'top',1,ids)
    elif spec.get('single_view'):
        ids={o['id'] for o in spec['objects'] if spec['single_view'] in views_for(spec['raw'],o['id'])}
        if ids:process_view_column(spec,spec['single_view'],spec.get('column',0),ids)
    else:
        per_object={o['id']:views_for(spec['raw'],o['id']) for o in spec['objects']}
        full={oid for oid,views in per_object.items() if len(views)==6}
        partial={oid:{v:True for v in views} for oid,views in per_object.items() if views and len(views)<6}
        if full:process_batch(spec,full)
        if partial:process_selected_views(spec,partial)
