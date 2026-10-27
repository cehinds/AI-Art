#!/usr/bin/env python3
"""Replay idempotent swaps and symmetry aliases from corrections.json."""
import hashlib, json, shutil, struct, tempfile
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parent; BOOK=OUT.parents[1]

def file_sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def artifact_path(rel):
    path=Path(rel)
    if path.is_absolute() or '..' in path.parts:raise ValueError(f'unsafe replay artifact path: {rel}')
    root=BOOK if rel.startswith('reusable/views-additional/') else OUT
    resolved=(root/path).resolve();resolved.relative_to(root.resolve());return resolved
def resolve_candidate_donor(op):
    manifest_path=OUT/'raw/replay-retained/donor-snapshots/manifest.json'
    if manifest_path.is_file():
        manifest=json.loads(manifest_path.read_text())
        baseline_path=OUT/'replay-baseline.json';baseline=json.loads(baseline_path.read_text())
        if manifest.get('baseline_sha256')!=file_sha(baseline_path) or manifest.get('set_index_sha256')!=baseline.get('set_index_sha256'):
            raise ValueError('candidate donor snapshot manifest is bound to another frozen baseline')
        row=next((x for x in manifest.get('donors',[]) if x.get('donor_image_path')==op['donor_image_path'] and x.get('object_id')==op['donor_object_id'] and x.get('view')==op['donor_view'] and x.get('sha256')==op['donor_image_sha256']),None)
        if row:
            snapshot=artifact_path(row['snapshot_path'])
            if not snapshot.is_file() or file_sha(snapshot)!=op['donor_image_sha256']:
                raise ValueError('candidate donor snapshot bytes differ from frozen hash')
            return snapshot,row['snapshot_path']
    direct=artifact_path(op['donor_image_path'])
    if not direct.is_file() or file_sha(direct)!=op['donor_image_sha256']:
        raise ValueError('candidate donor source image is missing or differs from frozen hash')
    return direct,op['donor_image_path']
def digest_png(p):
    im=Image.open(p).convert('RGBA')
    return file_sha(p),hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def update_asset(index,oid,view):
    aid=f'{oid}.{view}';meta=json.loads((OUT/f'{aid}.json').read_text());png=OUT/f'{aid}.png';sha,rgba=digest_png(png)
    meta['image'].update({'sha256':sha,'rgba_sha256':rgba});meta['geometry_qa']='pending-review'
    side=OUT/f'{aid}.json';side.write_text(json.dumps(meta,indent=2)+'\n')
    asset=next(x for x in index['assets'] if x['id']==aid);asset.clear();asset.update(meta)
    return sha

def set_pending(index,oid,note):
    s=next(x for x in index['view_sets'] if x['object_id']==oid);s['complete']=False;s['geometry_qa']='pending-review';s['notes']=s.get('notes','')+' '+note

def retained_overlay_covers(op):
    """Allow a stale historical op only when every affected leaf has an exact final output."""
    manifest_path=OUT/'raw/replay-retained/replay-retained-manifest.json'
    baseline_path=OUT/'replay-baseline.json'
    if not manifest_path.is_file() or not baseline_path.is_file():
        return False
    manifest=json.loads(manifest_path.read_text());baseline=json.loads(baseline_path.read_text())
    rows={(g['object_id'],v):row for g in baseline['sets'] for v,row in g['views'].items()}
    snapshots={(x['object_id'],x['view']):x for x in manifest['leaves']}
    oid=op.get('object_id');typ=op.get('type')
    if typ=='swap': views=list(op.get('views',[]))
    elif typ=='alias': views=[op.get('target')]
    elif typ=='source-lineage': views=[op.get('view')]
    else: views=[op.get('view')]
    if not oid or not views or any(not v for v in views):return False
    for view in views:
        row=rows.get((oid,view));snap=snapshots.get((oid,view))
        if not row or not snap:return False
        image_path=BOOK/row['image_path'];metadata_path=BOOK/row['metadata_path']
        image_is_final=image_path.is_file() and file_sha(image_path)==row['image_sha256']
        metadata_is_final=metadata_path.is_file() and file_sha(metadata_path)==row['metadata_sha256']
        if not (snap.get('image_snapshot_path') or image_is_final):return False
        if not (snap.get('metadata_snapshot_path') or metadata_is_final):return False
    return True

def apply(op,index,backup):
    oid=op['object_id'];typ=op['type']
    if op.get('replay_policy')=='skip-incomplete-historical-op-restore-exact-final-output':
        if not retained_overlay_covers(op):
            raise ValueError(f'{oid}.{op.get("view")} incomplete historical operation lacks full retained-output coverage')
        return {'object_id':oid,'view':op.get('view'),'type':typ,'status':'skipped-explicitly-superseded-incomplete-operation','reason':op['supersession_reason'],'retained_output_policy':'all final leaf PNG/sidecar bytes are frozen and hash-bound'}
    if typ=='restore-replay-snapshot':
        view=op['view'];target=OUT/f'{oid}.{view}.png';side=OUT/f'{oid}.{view}.json'
        snapshot=artifact_path(op['snapshot_path']);metadata_snapshot=artifact_path(op['metadata_snapshot_path'])
        if file_sha(snapshot)!=op['snapshot_sha256']:
            raise ValueError(f'{oid}.{view} replay snapshot hash changed')
        if file_sha(metadata_snapshot)!=op['metadata_snapshot_sha256']:
            raise ValueError(f'{oid}.{view} replay metadata snapshot hash changed')
        if file_sha(target) not in (op['before_sha256'],op['snapshot_sha256']):
            raise ValueError(f'{oid}.{view} replay snapshot source differs from retained precondition')
        meta=json.loads(metadata_snapshot.read_text())
        if meta.get('id')!=f'{oid}.{view}' or meta.get('metadata_path')!=op['metadata_path'] or meta.get('image',{}).get('path')!=op['image_path'] or meta.get('image',{}).get('sha256')!=op['snapshot_sha256']:
            raise ValueError(f'{oid}.{view} replay metadata snapshot does not bind the expected asset')
        if file_sha(target)!=op['snapshot_sha256']:
            shutil.copy2(target,backup/f'{oid}.{view}.before-replay-snapshot.png')
            shutil.copyfile(snapshot,target)
        shutil.copyfile(metadata_snapshot,side)
        asset=next(x for x in index['assets'] if x['id']==meta['id']);asset.clear();asset.update(meta)
        return {'object_id':oid,'view':view,'type':typ,'status':'restored-exact-retained-output','sha256':op['snapshot_sha256'],'metadata_sha256':op['metadata_snapshot_sha256']}
    if typ=='source-lineage':
        view=op['view'];aid=f'{oid}.{view}';meta=json.loads((OUT/f'{aid}.json').read_text())
        if file_sha(OUT/f'{aid}.png')!=op['image_sha256']:
            raise ValueError(f'{aid} image hash changed; refusing stale source-lineage recipe')
        source=BOOK/op['source_image']
        if not source.is_file() or file_sha(source)!=op['source_sha256']:
            raise ValueError(f'{aid} canonical source hash changed; refusing stale source-lineage recipe')
        meta.setdefault('provenance',{}).update({'source_image':op['source_image'],'source_sha256':op['source_sha256']})
        if meta['provenance'].get('method')=='inferred-symmetric-view-copy':
            derivation=meta['provenance'].setdefault('derivation_input',{})
            derivation['canonical_target_source_image']=op['source_image']
            derivation['canonical_target_source_sha256']=op['source_sha256']
        (OUT/f'{aid}.json').write_text(json.dumps(meta,indent=2)+'\n')
        asset=next(x for x in index['assets'] if x['id']==aid);asset.clear();asset.update(meta)
        return {'object_id':oid,'view':view,'type':typ,'status':'applied','image_sha256':op['image_sha256']}
    if typ=='mirror-view':
        from PIL import ImageOps
        view,source_view=op['view'],op['source_view'];target=OUT/f'{oid}.{view}.png';source=OUT/f'{oid}.{source_view}.png'
        if file_sha(source)!=op['source_sha256']:raise ValueError(f'{oid}.{source_view} source hash changed; refusing stale mirror recipe')
        if file_sha(target)==op['after_sha256']:return {'object_id':oid,'view':view,'type':typ,'status':'already-applied'}
        if file_sha(target)!=op['before_sha256']:raise ValueError(f'{oid}.{view} mirror target hash changed; refusing stale recipe')
        shutil.copy2(target,backup/f'{oid}.{view}.before-mirror.png');ImageOps.mirror(Image.open(source).convert('RGBA')).save(target,optimize=True)
        if file_sha(target)!=op['after_sha256']:raise ValueError(f'{oid}.{view} mirror output hash does not match recipe')
        meta=json.loads((OUT/f'{oid}.{view}.json').read_text());meta.setdefault('provenance_history',[]).append(meta.get('provenance',{}));canonical=meta.get('provenance',{}).get('source_image');canonical_sha=hashlib.sha256((BOOK/canonical).read_bytes()).hexdigest() if canonical and (BOOK/canonical).is_file() else meta.get('provenance',{}).get('source_sha256')
        sm=json.loads((OUT/f'{oid}.{source_view}.json').read_text());input_source=sm.get('provenance',{}).get('source_image');input_source_sha=hashlib.sha256((BOOK/input_source).read_bytes()).hexdigest() if input_source and (BOOK/input_source).is_file() else None
        meta['provenance']={'method':'inferred-orthographic-mirror','source_image':canonical,'source_sha256':canonical_sha,'notes':op['reason'],'derivation_input':{'asset_id':sm.get('id'),'object_id':oid,'view':source_view,'image_path':sm.get('image',{}).get('path'),'image_sha256':op['source_sha256'],'source_image':input_source,'source_sha256':input_source_sha}}
        meta['geometry_qa']='pending-review';(OUT/f'{oid}.{view}.json').write_text(json.dumps(meta,indent=2)+'\n');update_asset(index,oid,view);set_pending(index,oid,'Mirrored opposite orthographic profile applied; pending independent current-hash review.')
        return {'object_id':oid,'view':view,'type':typ,'status':'applied','sha256':file_sha(target)}
    if typ=='rotate-view':
        view=op['view'];target=OUT/f'{oid}.{view}.png';current=file_sha(target)
        if op.get('after_sha256') and current==op['after_sha256']:return {'object_id':oid,'view':view,'type':typ,'status':'already-applied'}
        if current!=op['before_sha256']:raise ValueError(f'{oid}.{view} rotation source hash changed; refusing stale recipe')
        shutil.copy2(target,backup/f'{oid}.{view}.before-rotation.png');im=Image.open(target).convert('RGBA');degrees=op['degrees']%360
        if degrees==90: im=im.transpose(Image.Transpose.ROTATE_90)
        elif degrees==180: im=im.transpose(Image.Transpose.ROTATE_180)
        elif degrees==270: im=im.transpose(Image.Transpose.ROTATE_270)
        else: raise ValueError('rotate-view only supports right-angle rotations')
        im.save(target,optimize=True)
        if file_sha(target)!=op['after_sha256']:raise ValueError(f'{oid}.{view} rotation output hash does not match recipe')
        meta=json.loads((OUT/f'{oid}.{view}.json').read_text());meta.setdefault('provenance_history',[]).append(meta.get('provenance',{}));meta.setdefault('provenance',{})['axis_correction']={'method':'orthographic-view-plane-rotation','degrees':degrees,'reason':op['reason']};meta['geometry_qa']='pending-review';(OUT/f'{oid}.{view}.json').write_text(json.dumps(meta,indent=2)+'\n');update_asset(index,oid,view);set_pending(index,oid,'Orthographic view-plane rotation applied; pending independent current-hash review.')
        return {'object_id':oid,'view':view,'type':typ,'status':'applied','sha256':file_sha(target)}
    if typ=='swap':
        if op.get('replay_policy')=='skip-superseded-swap-and-restore-exact-final-leaves':
            return {'object_id':oid,'status':'skipped-superseded-by-explicit-final-snapshots','type':typ,'superseded_output_snapshot_views':op.get('superseded_output_snapshot_views',[])}
        a,b=op['views'];pa,pb=OUT/f'{oid}.{a}.png',OUT/f'{oid}.{b}.png';ha,hb=file_sha(pa),file_sha(pb);before=op['before_sha256'];after=op['after_sha256']
        if [ha,hb]==[after[a],after[b]]: return {'object_id':oid,'status':'already-applied','type':typ}
        final=op.get('final_sha256',{})
        if final and [ha,hb]==[final.get(a),final.get(b)]: return {'object_id':oid,'status':'already-applied-with-downstream-cleanup','type':typ}
        if [ha,hb]!=[before[a],before[b]]: raise ValueError(f'{oid} swap source hashes do not match recorded before/after state')
        shutil.copy2(pa,backup/f'{oid}.{a}.before.png');shutil.copy2(pb,backup/f'{oid}.{b}.before.png');tmp=backup/f'{oid}.{a}.tmp';shutil.copy2(pa,tmp);shutil.copy2(pb,pa);shutil.copy2(tmp,pb);tmp.unlink()
        for view,source in ((a,b),(b,a)):
            m=json.loads((OUT/f'{oid}.{view}.json').read_text());m.setdefault('provenance_history',[]).append(m.get('provenance',{}));m['provenance']['axis_correction']={'method':'exact-retained-pixel-swap','pixels_reused_from_view':source,'notes':op['reason']};m['provenance']['notes']=op['reason'];(OUT/f'{oid}.{view}.json').write_text(json.dumps(m,indent=2)+'\n');update_asset(index,oid,view)
        set_pending(index,oid,'Deterministic axis correction applied; pending independent current-hash review.')
        return {'object_id':oid,'type':typ,'status':'applied','after':{v:file_sha(OUT/f'{oid}.{v}.png') for v in (a,b)}}
    if typ=='rotate':
        view=op['view'];target=op['calibrate_to_view'];p=OUT/f'{oid}.{view}.png';source=OUT/f'{oid}.{target}.png';current=file_sha(p);expected=op.get('after_sha256')
        if expected and current==expected:return {'object_id':oid,'view':view,'type':typ,'status':'already-applied'}
        if op.get('final_sha256') and current==op['final_sha256']:return {'object_id':oid,'view':view,'type':typ,'status':'already-applied-with-downstream-fix'}
        if current!=op['before_sha256']:raise ValueError(f'{oid}.{view} rotate source hash does not match recorded before state')
        source_sha=file_sha(source)
        if source_sha!=op['calibrate_to_sha256']:raise ValueError(f'{oid}.{target} calibration source hash changed')
        shutil.copy2(p,backup/f'{oid}.{view}.before.png');im=Image.open(p).convert('RGBA');bbox=im.getchannel('A').getbbox()
        if not bbox:raise ValueError(f'{oid}.{view} is empty')
        crop=im.crop(bbox).rotate(op['degrees_ccw'],expand=True,resample=Image.Resampling.NEAREST)
        ref=Image.open(source).convert('RGBA').getchannel('A').getbbox();rw,rh=ref[2]-ref[0],ref[3]-ref[1];scale=max(rw,rh)/max(crop.size);size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
        if max(size)>256:raise ValueError(f'{oid}.{view} transformed view would clip {size}')
        crop=crop.resize(size,Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop,((256-size[0])//2,248-size[1]));frame.save(p,optimize=True)
        m=json.loads((OUT/f'{oid}.{view}.json').read_text());m.setdefault('provenance_history',[]).append(m.get('provenance',{}));m['provenance']['axis_correction']={'method':'rotate-and-uniformly-calibrate','degrees_ccw':op['degrees_ccw'],'calibrated_to_view':target,'calibrate_to_sha256':source_sha,'scale':scale,'source_bbox':list(bbox),'render_size':list(size),'resampling':'NEAREST','notes':op['reason']};m['provenance']['notes']=op['reason'];(OUT/f'{oid}.{view}.json').write_text(json.dumps(m,indent=2)+'\n');after=update_asset(index,oid,view);op['after_sha256']=after;set_pending(index,oid,'Deterministic rotation and uniform calibration applied; pending independent current-hash review.')
        return {'object_id':oid,'view':view,'type':typ,'status':'applied','sha256':after,'render_size':size}
    if typ=='uniform-scale-to-view':
        view=op['view'];target=op['reference_view'];p=OUT/f'{oid}.{view}.png';refp=OUT/f'{oid}.{target}.png';current=file_sha(p)
        if op.get('after_sha256') and current==op['after_sha256']:return {'object_id':oid,'view':view,'type':typ,'status':'already-applied'}
        if current!=op['before_sha256']:raise ValueError(f'{oid}.{view} scale source hash does not match recorded before/after state')
        shutil.copy2(p,backup/f'{oid}.{view}.before-uniform-scale.png');im=Image.open(p).convert('RGBA');ref=Image.open(refp).convert('RGBA');bbox=im.getchannel('A').getbbox();rb=ref.getchannel('A').getbbox()
        if not bbox or not rb:raise ValueError(f'{oid}.{view} or reference {target} is empty')
        crop=im.crop(bbox);scale=(rb[3]-rb[1])/(bbox[3]-bbox[1]);size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
        if max(size)>256:raise ValueError(f'{oid}.{view} uniformly scaled view would clip {size}')
        crop=crop.resize(size,Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop,((256-size[0])//2,248-size[1]));frame.save(p,optimize=True)
        m=json.loads((OUT/f'{oid}.{view}.json').read_text());m.setdefault('provenance_history',[]).append(m.get('provenance',{}));m['provenance']['axis_correction']={'method':'uniform-scale-to-common-maximum-Z','reference_view':target,'reference_sha256':file_sha(refp),'scale':scale,'source_bbox':list(bbox),'render_size':list(size),'resampling':'NEAREST','notes':op['reason']};m['provenance']['notes']=op['reason'];(OUT/f'{oid}.{view}.json').write_text(json.dumps(m,indent=2)+'\n');after=update_asset(index,oid,view);op['after_sha256']=after;set_pending(index,oid,'Uniform principal-view scale corrected to common maximum Z; pending independent review.');return {'object_id':oid,'view':view,'type':typ,'status':'applied','sha256':after,'scale':scale,'render_size':size}
    if typ=='uniform-scale-to-view-width':
        view=op['view'];target=op['reference_view'];p=OUT/f'{oid}.{view}.png';refp=OUT/f'{oid}.{target}.png';current=file_sha(p)
        if op.get('after_sha256') and current==op['after_sha256']:return {'object_id':oid,'view':view,'type':typ,'status':'already-applied'}
        if current!=op['before_sha256']:raise ValueError(f'{oid}.{view} width-scale source hash does not match recorded before state')
        refsha=file_sha(refp)
        if refsha!=op['reference_sha256']:raise ValueError(f'{oid}.{target} width calibration source hash changed')
        shutil.copy2(p,backup/f'{oid}.{view}.before-uniform-width-scale.png');im=Image.open(p).convert('RGBA');ref=Image.open(refp).convert('RGBA');bbox=im.getchannel('A').getbbox();rb=ref.getchannel('A').getbbox()
        if not bbox or not rb:raise ValueError(f'{oid}.{view} or reference {target} is empty')
        crop=im.crop(bbox);scale=(rb[2]-rb[0])/(bbox[2]-bbox[0]);size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
        if max(size)>256:raise ValueError(f'{oid}.{view} uniformly width-scaled view would clip {size}')
        crop=crop.resize(size,Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop,((256-size[0])//2,248-size[1]));frame.save(p,optimize=True)
        m=json.loads((OUT/f'{oid}.{view}.json').read_text());m.setdefault('provenance_history',[]).append(m.get('provenance',{}));m['provenance']['axis_correction']={'method':'uniform-scale-to-matching-plan-width','reference_view':target,'reference_sha256':refsha,'scale':scale,'source_bbox':list(bbox),'render_size':list(size),'resampling':'NEAREST','notes':op['reason']};m['provenance']['notes']=op['reason'];(OUT/f'{oid}.{view}.json').write_text(json.dumps(m,indent=2)+'\n');after=update_asset(index,oid,view);op['after_sha256']=after;set_pending(index,oid,'Uniform orthographic plan width corrected to the accepted full footprint; pending independent review.');return {'object_id':oid,'view':view,'type':typ,'status':'applied','sha256':after,'scale':scale,'render_size':size}
    if typ=='clear-alpha-pixels':
        import numpy as np
        view=op['view'];p=OUT/f'{oid}.{view}.png';current=file_sha(p)
        if op.get('after_sha256') and current==op['after_sha256']:return {'object_id':oid,'view':view,'type':typ,'status':'already-applied'}
        if current!=op['before_sha256']:raise ValueError(f'{oid}.{view} pixel cleanup source hash does not match recorded before/after state')
        shutil.copy2(p,backup/f'{oid}.{view}.before-pixel-cleanup.png');im=Image.open(p).convert('RGBA');rgba=np.array(im)
        for item in op['pixels']:
            x,y=item['xy'];expected=tuple(item['before_rgba'])
            if tuple(rgba[y,x])!=expected:raise ValueError(f'{oid}.{view} pixel {x},{y} changed; refusing stale cleanup')
            rgba[y,x,3]=0
        Image.fromarray(rgba,'RGBA').save(p,optimize=True)
        if file_sha(p)!=op['after_sha256']:raise ValueError(f'{oid}.{view} pixel cleanup output hash mismatch')
        m=json.loads((OUT/f'{oid}.{view}.json').read_text());m.setdefault('provenance_history',[]).append(m.get('provenance',{}));m['provenance']['cleanup']={'method':typ,'pixels':op['pixels'],'reason':op['reason']};m['provenance']['notes']=op['reason'];(OUT/f'{oid}.{view}.json').write_text(json.dumps(m,indent=2)+'\n');update_asset(index,oid,view);set_pending(index,oid,'Exact isolated guide pixels cleared; pending independent current-hash review.')
        return {'object_id':oid,'view':view,'type':typ,'status':'applied','sha256':file_sha(p)}
    if typ in ('remove-component-bbox','remove-components-bbox'):
        import numpy as np
        from scipy import ndimage
        view=op['view'];p=OUT/f'{oid}.{view}.png';current=file_sha(p);expected=op['after_sha256']
        if current==expected:return {'object_id':oid,'view':view,'type':typ,'status':'already-applied'}
        if current!=op['before_sha256']:raise ValueError(f'{oid}.{view} cleanup source hash does not match recorded before/after state')
        shutil.copy2(p,backup/f'{oid}.{view}.before-cleanup.png');im=Image.open(p).convert('RGBA');rgba=np.array(im)
        for box in op.get('bboxes',[op.get('bbox')]):
            labels,n=ndimage.label(rgba[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8));x0,y0,x1,y1=box;hits=[]
            for i,sl in enumerate(ndimage.find_objects(labels),1):
                if sl is not None:
                    component_box=[sl[1].start,sl[0].start,sl[1].stop,sl[0].stop]
                    if (typ=='remove-components-bbox' and component_box==box) or (typ=='remove-component-bbox' and sl[1].start<=x0 and sl[1].stop>=x1 and sl[0].start<=y0 and sl[0].stop>=y1):hits.append(i)
            if len(hits)!=1:raise ValueError(f'{oid}.{view} expected one alpha component in bbox {box}, found {len(hits)}')
            rgba[:,:,3][labels==hits[0]]=0
        clean=Image.fromarray(rgba,'RGBA');clean.save(p,optimize=True);after=file_sha(p)
        if after!=expected:raise ValueError(f'{oid}.{view} cleanup result hash {after} != expected {expected}')
        m=json.loads((OUT/f'{oid}.{view}.json').read_text());m.setdefault('provenance_history',[]).append(m.get('provenance',{}));m['provenance']['cleanup']={'method':typ,'bbox':op.get('bbox'),'bboxes':op.get('bboxes'),'reason':op['reason']};m['provenance']['notes']=op['reason'];(OUT/f'{oid}.{view}.json').write_text(json.dumps(m,indent=2)+'\n');update_asset(index,oid,view);set_pending(index,oid,'Deterministic detached-component cleanup applied; pending independent current-hash review.')
        return {'object_id':oid,'view':view,'type':typ,'status':'applied','sha256':after}
    if typ=='replace-generated-view':
        view=op['view'];target=OUT/f'{oid}.{view}.png';current=file_sha(target)
        if op.get('after_sha256') and current==op['after_sha256']:return {'object_id':oid,'view':view,'type':typ,'status':'already-applied'}
        if op.get('final_sha256') and current==op['final_sha256']:return {'object_id':oid,'view':view,'type':typ,'status':'already-applied-with-downstream-fix'}
        if not op.get('after_sha256'):
            raise ValueError(f'{oid}.{view} historical replacement has no output hash; final retained output supersedes this incomplete recipe')
        if current!=op['before_sha256']:raise ValueError(f'{oid}.{view} generated replacement source hash changed')
        atlas=artifact_path(op['atlas_path'])
        if file_sha(atlas)!=op['atlas_sha256']:raise ValueError(f'{oid}.{view} atlas hash changed')
        refp=OUT/f"{oid}.{op['reference_view']}.png"
        if file_sha(refp)!=op['reference_sha256']:raise ValueError(f'{oid}.{view} reference view hash changed')
        shutil.copy2(target,backup/f'{oid}.{view}.before-generated-replacement.png')
        crop=Image.open(atlas).convert('RGBA').crop(tuple(op['crop_bbox']))
        if op.get('clip_alpha_below') is not None:
            import numpy as np
            clipped=np.array(crop)
            clipped[:,:,3][clipped[:,:,3]<int(op['clip_alpha_below'])]=0
            crop=Image.fromarray(clipped,'RGBA')
        rotation=op.get('rotation_degrees',0)%360
        if rotation==90: crop=crop.transpose(Image.Transpose.ROTATE_90)
        elif rotation==180: crop=crop.transpose(Image.Transpose.ROTATE_180)
        elif rotation==270: crop=crop.transpose(Image.Transpose.ROTATE_270)
        elif rotation!=0: crop=crop.rotate(rotation,expand=True,resample=Image.Resampling.NEAREST)
        if op.get('trim_after_rotation'):
            rotated_bbox=crop.getchannel('A').getbbox()
            if not rotated_bbox: raise ValueError(f'{oid}.{view} rotated atlas crop is empty')
            crop=crop.crop(rotated_bbox)
        size=tuple(op['render_size']);crop=crop.resize(size,Image.Resampling.NEAREST)
        frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop,((256-size[0])//2,248-size[1]));frame.save(target,optimize=op.get('optimize_png',True))
        if file_sha(target)!=op['after_sha256']:raise ValueError(f'{oid}.{view} generated replacement output hash mismatch')
        meta=json.loads((OUT/f'{oid}.{view}.json').read_text());meta.setdefault('provenance_history',[]).append(meta.get('provenance',{}))
        old=meta.get('provenance',{});source=old.get('source_image');source_path=BOOK/source if source else None
        source_sha=hashlib.sha256(source_path.read_bytes()).hexdigest() if source_path and source_path.is_file() else old.get('source_sha256')
        meta['provenance']={'method':'generated','source_image':source,'source_sha256':source_sha,'generated_atlas':(op['atlas_path'] if op['atlas_path'].startswith('reusable/views-additional/') else 'reusable/views-additional/'+op['atlas_path']),'generated_atlas_sha256':op['atlas_sha256'],'prompt_file':op.get('prompt_file'),'normalization':{'alpha_threshold':op.get('alpha_threshold',245),'component_policy':op.get('component_policy','retain the assigned logical object bounds, preserving meaningful detached parts and excluding foreign neighboring components'),'component_bbox':op['crop_bbox'],'rotation_degrees':rotation,'trim_after_rotation':op.get('trim_after_rotation',False),'reference_view':op['reference_view'],'reference_sha256':op['reference_sha256'],'scale_axis':op.get('scale_axis','height'),'shared_scale':op['scale'],'render_size':op['render_size'],'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]},'notes':op['reason']}
        if op.get('reference_inputs'): meta['provenance']['reference_inputs']=op['reference_inputs']
        if op.get('derived_from_atlas'): meta['provenance']['derivation_input']=op['derived_from_atlas']
        meta['geometry_qa']='pending-review';(OUT/f'{oid}.{view}.json').write_text(json.dumps(meta,indent=2)+'\n');update_asset(index,oid,view);set_pending(index,oid,'Generated orthographic principal view replaced from a retained atlas; pending independent review.')
        return {'object_id':oid,'view':view,'type':typ,'status':'applied','sha256':file_sha(target),'render_size':size}
    if typ=='alias':
        target,source=op['target'],op['source'];source_oid=op.get('source_object_id',oid);tp,sp=OUT/f'{oid}.{target}.png',OUT/f'{source_oid}.{source}.png';ht,hs=file_sha(tp),file_sha(sp)
        if ht==op['after_sha256'] and hs==op['source_sha256']:
            target_meta=json.loads((OUT/f'{oid}.{target}.json').read_text());source_meta=json.loads((OUT/f'{source_oid}.{source}.json').read_text())
            history=target_meta.setdefault('provenance_history',[]);current=target_meta.get('provenance',{})
            base=history[-1] if current.get('method') in ('inferred-symmetric-view-copy','inferred-family-view-donor') and history else current
            source_path=base.get('source_image');source_path_sha=hashlib.sha256((BOOK/source_path).read_bytes()).hexdigest() if source_path and (BOOK/source_path).is_file() else base.get('source_sha256')
            input_source=source_meta.get('provenance',{}).get('source_image');input_source_sha=hashlib.sha256((BOOK/input_source).read_bytes()).hexdigest() if input_source and (BOOK/input_source).is_file() else None
            method=op.get('provenance_method','inferred-symmetric-view-copy')
            lineage={'family_donor_object_id':source_oid,'family_donor_view':source,'derivation_reason':op['reason']} if method=='inferred-family-view-donor' else {'symmetric_alias_of':source,'symmetric_alias_object_id':source_oid,'symmetry_reason':op['reason']}
            target_meta['provenance']={**base,'method':method,'source_image':source_path,'source_sha256':source_path_sha,**lineage,'derivation_input':{'asset_id':source_meta.get('id'),'object_id':source_oid,'view':source,'image_path':source_meta.get('image',{}).get('path'),'image_sha256':hs,'source_image':input_source,'source_sha256':input_source_sha},'notes':('Pixels inferred from a same-family material/geometry donor. Canonical source provenance remains this target object; donor pixels and hashes are recorded separately.' if method=='inferred-family-view-donor' else 'Pixels copied from a directionally symmetric orthographic view. Canonical source provenance remains this target object; derivation input and hashes are recorded separately.')}
            target_meta['metadata_path']=(OUT/f'{oid}.{target}.json').relative_to(BOOK).as_posix();(OUT/f'{oid}.{target}.json').write_text(json.dumps(target_meta,indent=2)+'\n')
            asset=next(x for x in index['assets'] if x['id']==target_meta['id']);asset.clear();asset.update(target_meta)
            return {'object_id':oid,'target':target,'source':source,'type':typ,'status':'already-applied','metadata_reconciled':True}
        if ht!=op['before_sha256'] or hs!=op['source_sha256']:raise ValueError(f'{oid}.{target} alias source hashes do not match recorded before/after state')
        shutil.copy2(tp,backup/f'{oid}.{target}.before.png');shutil.copyfile(sp,tp)
        target_meta=json.loads((OUT/f'{oid}.{target}.json').read_text());source_meta=json.loads((OUT/f'{source_oid}.{source}.json').read_text());target_meta.setdefault('provenance_history',[]).append(target_meta.get('provenance',{}))
        base=target_meta['provenance_history'][-1];source_path=base.get('source_image');source_path_sha=hashlib.sha256((BOOK/source_path).read_bytes()).hexdigest() if source_path and (BOOK/source_path).is_file() else base.get('source_sha256')
        input_source=source_meta.get('provenance',{}).get('source_image');input_source_sha=hashlib.sha256((BOOK/input_source).read_bytes()).hexdigest() if input_source and (BOOK/input_source).is_file() else None
        method=op.get('provenance_method','inferred-symmetric-view-copy')
        lineage={'family_donor_object_id':source_oid,'family_donor_view':source,'derivation_reason':op['reason']} if method=='inferred-family-view-donor' else {'symmetric_alias_of':source,'symmetric_alias_object_id':source_oid,'symmetry_reason':op['reason']}
        target_meta['provenance']={**base,'method':method,'source_image':source_path,'source_sha256':source_path_sha,**lineage,'derivation_input':{'asset_id':source_meta.get('id'),'object_id':source_oid,'view':source,'image_path':source_meta.get('image',{}).get('path'),'image_sha256':hs,'source_image':input_source,'source_sha256':input_source_sha},'notes':('Pixels inferred from a same-family material/geometry donor. Canonical source provenance remains this target object; donor pixels and hashes are recorded separately.' if method=='inferred-family-view-donor' else 'Pixels copied from a directionally symmetric orthographic view. Canonical source provenance remains this target object; derivation input and hashes are recorded separately.')}
        target_meta['metadata_path']=(OUT/f'{oid}.{target}.json').relative_to(BOOK).as_posix();target_meta['geometry_qa']='pending-review';(OUT/f'{oid}.{target}.json').write_text(json.dumps(target_meta,indent=2)+'\n');update_asset(index,oid,target);set_pending(index,oid,'Declared symmetric-view alias applied; pending independent current-hash review.')
        return {'object_id':oid,'target':target,'source':source,'type':typ,'status':'applied','sha256':file_sha(tp)}
    if typ=='restore-reviewed-png':
        view=op['view'];target=OUT/f'{oid}.{view}.png';snapshot=artifact_path(op['snapshot_path'])
        current=file_sha(target);snapshot_sha=file_sha(snapshot)
        if snapshot_sha!=op['snapshot_sha256']:
            raise ValueError(f'{oid}.{view} retained reviewed snapshot hash changed')
        if current==snapshot_sha:
            return {'object_id':oid,'view':view,'type':typ,'status':'already-applied','sha256':current}
        if current!=op['before_sha256']:
            raise ValueError(f'{oid}.{view} retained snapshot base hash changed')
        shutil.copy2(target,backup/f'{oid}.{view}.before-reviewed-snapshot.png');shutil.copyfile(snapshot,target)
        meta=json.loads((OUT/f'{oid}.{view}.json').read_text());meta.setdefault('provenance_history',[]).append(meta.get('provenance',{}))
        source=meta.get('provenance',{}).get('source_image');source_sha=hashlib.sha256((BOOK/source).read_bytes()).hexdigest() if source and (BOOK/source).is_file() else meta.get('provenance',{}).get('source_sha256')
        meta['provenance']={'method':'retained-approved-png-exact-copy','source_image':source,'source_sha256':source_sha,'retained_png':op['snapshot_path'],'retained_png_sha256':snapshot_sha,'reviewer':op['reviewer'],'reviewed_at':op['reviewed_at'],'review_source_sha256':op['review_source_sha256'],'reviewed_image_sha256':snapshot_sha,'notes':op['reason']}
        if op.get('provenance_override'):
            meta['provenance'].update(op['provenance_override'])
        meta['geometry_qa']='cleared';(OUT/f'{oid}.{view}.json').write_text(json.dumps(meta,indent=2)+'\n');update_asset(index,oid,view)
        meta=json.loads((OUT/f'{oid}.{view}.json').read_text());meta['geometry_qa']='cleared';(OUT/f'{oid}.{view}.json').write_text(json.dumps(meta,indent=2)+'\n')
        asset=next(x for x in index['assets'] if x['id']==meta['id']);asset.clear();asset.update(meta)
        return {'object_id':oid,'view':view,'type':typ,'status':'applied','sha256':snapshot_sha}
    if typ=='install-view-candidate':
        view=op['view'];target=OUT/f'{oid}.{view}.png';candidate=artifact_path(op['candidate_path'])
        current=file_sha(target);candidate_sha=file_sha(candidate)
        if candidate_sha!=op['candidate_sha256']:
            raise ValueError(f'{oid}.{view} staged candidate hash changed')
        if current==candidate_sha:
            update_asset(index,oid,view)
            set_pending(index,oid,'Reviewed candidate replayed; pending independent current-hash whole-set review.')
            return {'object_id':oid,'view':view,'type':typ,'status':'already-applied','sha256':candidate_sha}
        if current!=op['before_sha256']:
            raise ValueError(f'{oid}.{view} candidate base hash changed')
        source=BOOK/op['canonical_source_image'];donor,donor_resolved_path=resolve_candidate_donor(op)
        if not source.is_file() or file_sha(source)!=op['canonical_source_sha256']:
            raise ValueError(f'{oid}.{view} canonical source hash changed')
        shutil.copy2(target,backup/f'{oid}.{view}.before-candidate.png');shutil.copyfile(candidate,target)
        meta=json.loads((OUT/f'{oid}.{view}.json').read_text());meta.setdefault('provenance_history',[]).append(meta.get('provenance',{}))
        meta['provenance']=op.get('provenance') or {
            'method':'inferred-family-view-donor','source_image':op['canonical_source_image'],
            'source_sha256':op['canonical_source_sha256'],
            'family_donor_object_id':op['donor_object_id'],'family_donor_view':op['donor_view'],
            'derivation_input':{'image_path':op['donor_image_path'],'resolved_image_path':donor_resolved_path,'image_sha256':op['donor_image_sha256'],
                'source_image':op['donor_source_image'],'source_sha256':op['donor_source_sha256']},
            'transform':op['transform'],'candidate_path':op['candidate_path'],'candidate_sha256':candidate_sha,
            'notes':op['reason']}
        meta['geometry_qa']='pending-review';(OUT/f'{oid}.{view}.json').write_text(json.dumps(meta,indent=2)+'\n')
        update_asset(index,oid,view);set_pending(index,oid,'Same-family orientation remap installed; pending independent current-hash whole-set review.')
        return {'object_id':oid,'view':view,'type':typ,'status':'applied','sha256':candidate_sha}
    raise ValueError(f'unknown correction type {typ}')

def main():
    spec=json.loads((OUT/'corrections.json').read_text());idxp=OUT/'set-index.json';index=json.loads(idxp.read_text());backup=Path(tempfile.mkdtemp(prefix='pocket-view-replay-backup-'));result=[]
    for operation_index,op in enumerate(spec['operations']):
        try:
            result.append(apply(op,index,backup))
        except ValueError as error:
            if not retained_overlay_covers(op):
                raise
            result.append({'operation_index':operation_index,'object_id':op.get('object_id'),'view':op.get('view'),'type':op.get('type'),'status':'skipped-superseded-by-hash-pinned-retained-output','reason':str(error),'retained_output_policy':'all affected final leaves are covered by raw/replay-retained/replay-retained-manifest.json'})
    tmp=idxp.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');tmp.replace(idxp);(OUT/'replay-run-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__': main()
