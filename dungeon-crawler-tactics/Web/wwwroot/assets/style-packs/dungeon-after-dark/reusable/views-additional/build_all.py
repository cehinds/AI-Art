"""Rebuild current six-view outputs from retained raw atlases and exact pack-local recipes."""
import json, hashlib, os, struct
from pathlib import Path
from PIL import Image
from build_batch import process_batch, process_view_column, process_arsenal_axis_pair, process_selected_views, process_single_view_image, process_object_local_cells_shared_scale
OUT=Path(__file__).resolve().parent
specs=json.loads((OUT/'batch-specs.json').read_text())
index=json.loads((OUT/'set-index.json').read_text())
initial_index=json.loads(json.dumps(index))
PACK=OUT.parent.parent
asset_map={a['id']:a for a in index['assets']}
VIEWS=['front','top','right','left','bottom','rear']
SPILL_POLICIES={'global-centroid-alpha-components-spill-mask-v1',
                'global-centroid-alpha-components-spill-mask-dilation2-v1'}
def views_for(raw, oid):
    suffix=str(raw)
    return {v for v in VIEWS if f'{oid}.{v}' in asset_map and
            str(asset_map[f'{oid}.{v}']['provenance'].get('generated_atlas','')).endswith(suffix)}
def active_for(raw, objects):
    return {obj['id'] for obj in objects if views_for(raw,obj['id'])}
def process_partial_views(spec, selections):
    """Replay views by their recorded extraction recipe, preserving base/patch ordering."""
    if spec.get('partial_component_policy'):
        process_selected_views(spec,selections)
        return
    spill={};ordinary={}
    for oid,views in selections.items():
        for view in views:
            asset=asset_map.get(f'{oid}.{view}',{})
            policy=asset.get('provenance',{}).get('normalization',{}).get('component_selection')
            target=spill if policy in SPILL_POLICIES else ordinary
            target.setdefault(oid,{})[view]=views[view]
    if spill:
        for policy in sorted({asset_map[f'{oid}.{view}']['provenance']['normalization']['component_selection']
                              for oid,views in spill.items() for view in views}):
            selection={oid:{view:value for view,value in views.items()
                            if asset_map[f'{oid}.{view}']['provenance']['normalization']['component_selection']==policy}
                       for oid,views in spill.items()}
            selection={oid:views for oid,views in selection.items() if views}
            process_selected_views({**spec,'partial_component_policy':policy},selection)
    if ordinary:process_selected_views(spec,ordinary)
for spec in specs:
    if not (OUT / spec['raw']).is_file():
        continue  # Superseded historical alias; retained split atlas specs cover its objects.
    bid=spec.get('batch_id')
    if spec.get('shared_scale_local_cells'):
        selected={oid:views for oid,views in spec['shared_scale_local_cells'].items()
                  if set(views)&views_for(spec['raw'],oid)}
        if selected:process_object_local_cells_shared_scale(spec,selected)
        continue
    if spec.get('method')=='process_object_local_cells_shared_scale':
        selected={oid:views for oid,views in spec.get('selections',{}).items()
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
        if chosen: process_partial_views(spec,chosen)
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
        if partial:process_partial_views(spec,partial)


def restore_verified_retained_snapshots():
    """Replay exact legacy outputs from distinct, hash-verified pack-local snapshots."""
    manifest_path=OUT/'raw'/'retained-approved-output-snapshots-v1.json'
    if not manifest_path.is_file(): return
    manifest_bytes=manifest_path.read_bytes()
    manifest_sha=hashlib.sha256(manifest_bytes).hexdigest()
    manifest=json.loads(manifest_bytes)
    if manifest.get('schema_version')!=1 or manifest.get('method')!='verified-retained-snapshot-v1':
        raise ValueError('Unsupported retained approved-output snapshot manifest')
    initial_assets={a['id']:a for a in initial_index['assets']}
    current_index_path=OUT/'set-index.json'
    current=json.loads(current_index_path.read_text())
    current_assets={a['id']:a for a in current['assets']}
    for row in manifest.get('records',[]):
        if row.get('schema_version')!=1 or row.get('method')!='verified-retained-snapshot-v1':
            raise ValueError('Malformed retained snapshot row')
        aid=f"{row['object_id']}.{row['view']}"
        expected=initial_assets.get(aid)
        if not expected: raise ValueError(f'{aid}: retained snapshot is not an indexed output')
        ev=expected.get('provenance',{}).get('normalization',{}).get('retained_snapshot_evidence',{})
        if (ev.get('manifest_sha256')!=manifest_sha or ev.get('manifest_path')!='reusable/views-additional/raw/retained-approved-output-snapshots-v1.json'
                or ev.get('object_id')!=row['object_id'] or ev.get('view')!=row['view']):
            raise ValueError(f'{aid}: retained snapshot evidence disagrees with manifest')
        output_rel=expected['image']['path']
        if row.get('active_output_path')!=output_rel or row.get('active_output_sha256')!=expected['image']['sha256']:
            raise ValueError(f'{aid}: retained snapshot output binding mismatch')
        snapshot_rel=row.get('snapshot_path','')
        if not snapshot_rel or snapshot_rel==output_rel:
            raise ValueError(f'{aid}: snapshot input must be distinct from output')
        snapshot_path=PACK/snapshot_rel
        if not snapshot_path.is_file(): raise FileNotFoundError(snapshot_path)
        data=snapshot_path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=row.get('snapshot_sha256') or row.get('snapshot_sha256')!=row.get('active_output_sha256'):
            raise ValueError(f'{aid}: retained snapshot file hash mismatch')
        with Image.open(snapshot_path) as im:
            rgba=im.convert('RGBA')
            rgba_sha=hashlib.sha256(struct.pack('>II',*rgba.size)+rgba.tobytes()).hexdigest()
            if list(rgba.size)!=row.get('dimensions_px') or rgba_sha!=row.get('snapshot_rgba_sha256') or rgba_sha!=row.get('active_output_rgba_sha256'):
                raise ValueError(f'{aid}: retained snapshot RGBA binding mismatch')
        out=PACK/output_rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
        restored=json.loads(json.dumps(expected))
        cur=current_assets.get(aid)
        if cur is None: raise ValueError(f'{aid}: output missing from rebuilt catalog')
        current['assets']=[restored if a['id']==aid else a for a in current['assets']]
        metadata_path=PACK/restored.get('metadata_path',str(Path(output_rel).with_suffix('.json')))
        metadata_path.parent.mkdir(parents=True,exist_ok=True);metadata_path.write_text(json.dumps(restored,indent=2)+'\n')
    tmp=current_index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(current,indent=2)+'\n');os.replace(tmp,current_index_path)

restore_verified_retained_snapshots()
