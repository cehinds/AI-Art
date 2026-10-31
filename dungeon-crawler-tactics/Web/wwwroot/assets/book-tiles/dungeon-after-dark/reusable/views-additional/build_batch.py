"""Offline six-view atlas extraction and normalization for one pack-local batch."""
from pathlib import Path
import hashlib, json, os, struct
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
VIEWS = ['front', 'top', 'right', 'left', 'bottom', 'rear']

def process_batch(spec):
    raw = OUT / spec['raw']
    atlas = Image.open(raw).convert('RGBA')
    pixels = np.asarray(atlas)
    height, width = pixels.shape[:2]
    labels, _ = ndimage.label(pixels[:, :, 3] > 32)
    components = []
    for label, sl in enumerate(ndimage.find_objects(labels), 1):
        if sl is None:
            continue
        ys, xs = sl
        area = int(np.count_nonzero(labels[sl] == label))
        if area < 24:
            continue
        components.append({'label':label, 'area':area, 'cx':(xs.start+xs.stop)/2,
                           'cy':(ys.start+ys.stop)/2, 'box':(xs.start,ys.start,xs.stop,ys.stop)})
    atlas_sha = hashlib.sha256(raw.read_bytes()).hexdigest()
    contact_path = ROOT / spec['contact_sheet']
    prompt_path = OUT / spec['prompt_path']
    prompt_rel = 'reusable/views-additional/' + spec['prompt_path'] if not spec['prompt_path'].startswith('reusable/views-additional/') else spec['prompt_path']
    contact_sha = hashlib.sha256(contact_path.read_bytes()).hexdigest() if contact_path.exists() else None
    prompt_sha = hashlib.sha256(prompt_path.read_bytes()).hexdigest() if prompt_path.exists() else None
    index_path = OUT / 'set-index.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else {'assets':[], 'view_sets':[]}
    view_sets={s['object_id']:s for s in index.get('view_sets',[])}
    assets_by_id={a['id']:a for a in index.get('assets',[])}
    approved_ids={s['object_id'] for s in index.get('view_sets',[]) if s.get('complete')} | set(spec.get('preserve_object_ids',[]))
    def approved_outputs_present(object_id):
        refs=view_sets.get(object_id,{}).get('views',{})
        if set(refs)!={'front','top','right','left','bottom','rear'}:
            return False
        for asset_id in refs.values():
            asset=assets_by_id.get(asset_id)
            if not asset:
                return False
            image_path=asset.get('image',{}).get('path')
            if not image_path or not (ROOT/image_path).is_file():
                return False
        return True
    row_count=int(spec.get('row_count',len(spec['objects'])))
    for row, obj in enumerate(spec['objects']):
        # Preserve a reviewed set only while its complete output group is
        # present. Deleted-output replay must regenerate missing approved art
        # from the retained raw atlas; replay-backed scoped repairs run later.
        if (spec.get('preserve_current_approved', True) and obj['id'] in approved_ids
                and approved_outputs_present(obj['id'])):
            continue
        source_row=int(obj.get('source_row',row))
        crops, rects = [], []
        for col in range(6):
            explicit=spec.get('explicit_cell_rectangles')
            if explicit:
                x0,y0,x1,y1=map(int,explicit[source_row][col])
            else:
                x0, x1 = round(col*width/6), round((col+1)*width/6)
                y0, y1 = round(source_row*height/row_count), round((source_row+1)*height/row_count)
            selected = [c for c in components if x0 <= c['cx'] < x1 and y0 <= c['cy'] < y1]
            if not selected:
                # Adjacent views can touch and become one global alpha island. Fall back to this logical cell's own alpha bounds.
                cell_alpha=(pixels[y0:y1,x0:x1,3]>32)
                yy,xx=np.nonzero(cell_alpha)
                if len(xx)==0: raise ValueError(f"{obj['id']}/{VIEWS[col]} has no assigned significant alpha components")
                xlo=x0+int(xx.min()); xhi=x0+int(xx.max())+1; ylo=y0+int(yy.min()); yhi=y0+int(yy.max())+1
                masked=np.zeros_like(pixels); masked[ylo:yhi,xlo:xhi]=pixels[ylo:yhi,xlo:xhi]
                crop=Image.fromarray(masked,'RGBA').crop((xlo,ylo,xhi,yhi))
                crops.append(crop)
                rects.append({'cell':[x0,y0,x1-x0,y1-y0], 'alpha_bounds':[xlo,ylo,xhi-xlo,yhi-ylo], 'component_count':0, 'component_areas':[], 'components_outside_cell':[]})
                continue
            xlo=min(c['box'][0] for c in selected); ylo=min(c['box'][1] for c in selected)
            xhi=max(c['box'][2] for c in selected); yhi=max(c['box'][3] for c in selected)
            mask=np.isin(labels,[c['label'] for c in selected])
            mask=ndimage.binary_dilation(mask,iterations=2) & (pixels[:,:,3]>0)
            masked=np.zeros_like(pixels); masked[mask]=pixels[mask]
            crops.append(Image.fromarray(masked,'RGBA').crop((xlo,ylo,xhi,yhi)))
            rects.append({'cell':[x0,y0,x1-x0,y1-y0], 'alpha_bounds':[xlo,ylo,xhi-xlo,yhi-ylo],
                          'component_count':len(selected), 'component_areas':[c['area'] for c in selected],
                          'components_outside_cell':[c['label'] for c in selected if c['box'][0]<x0 or c['box'][1]<y0 or c['box'][2]>x1 or c['box'][3]>y1]})
        native_top=None
        if spec.get('reuse_source_top') and obj.get('category')=='ground' and 'floor' in obj['id'] and not any(t in obj['id'] for t in ['edge-transition','corner-transition']):
            source_path=ROOT/obj['source_image']
            if not source_path.exists(): raise FileNotFoundError(source_path)
            source_im=Image.open(source_path).convert('RGBA'); source_arr=np.asarray(source_im)
            yy,xx=np.nonzero(source_arr[:,:,3]>32)
            if len(xx)==0: raise ValueError(f"{obj['id']}: native top source has no alpha")
            bounds=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
            crops[1]=source_im.crop(bounds)
            rects[1]={'source_image':obj['source_image'],'source_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),'alpha_bounds':[bounds[0],bounds[1],bounds[2]-bounds[0],bounds[3]-bounds[1]],'method':'existing native top view'}
            native_top={'path':str(source_path.relative_to(ROOT)),'sha256':hashlib.sha256(source_path.read_bytes()).hexdigest()}
        scale=204/max(max(c.size) for c in crops); refs={}
        for col,(view,crop) in enumerate(zip(VIEWS,crops)):
            nw=max(1,round(crop.width*scale)); nh=max(1,round(crop.height*scale))
            crop=crop.resize((nw,nh),Image.Resampling.NEAREST)
            canvas=Image.new('RGBA',(256,256),(0,0,0,0)); ox=(256-nw)//2; oy=(256-nh)//2
            canvas.alpha_composite(crop,(ox,oy))
            asset_id=f"{obj['id']}.{view}"; image_path=OUT/'images'/f'{asset_id}.png'; meta_path=image_path.with_suffix('.json')
            canvas.save(image_path,optimize=True); rgba=canvas.tobytes()
            meta={'id':asset_id,'name':f"{obj['name']} {view.title()}",'kind':obj['kind'],
                  'category':obj.get('category'),'tags':sorted(set(obj.get('tags',[])+['six-view','orthographic',obj['kind'],'generated'])),'image':{
                  'path':str(image_path.relative_to(ROOT)),'width':256,'height':256,
                  'sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),
                  'rgba_sha256':hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest()},
                  'object_id':obj['id'],'source':{'object_id':obj['id'],'category':obj.get('category'),'source_image':obj['source_image'],'source_sha256':obj.get('source_sha256')},'view':view,'provenance':{
                  'method':'existing-source-top' if col==1 and native_top else 'generated','source_image':obj['source_image'],
                  'source_contact_sheet':spec['contact_sheet'],
                  'source_contact_sheet_sha256':contact_sha,
                  'generated_atlas':native_top['path'] if col==1 and native_top else str(raw.relative_to(ROOT)), 'generated_atlas_sha256':native_top['sha256'] if col==1 and native_top else atlas_sha,
                  'prompt_path':prompt_rel, 'prompt_sha256':prompt_sha, 'source_rect':rects[col],
                  'normalization':{'scale':scale,'offset_px':[ox,oy],'resampling':'nearest','frame_size':[256,256]},
                  'rebuild_command':'python3 reusable/views-additional/build_all.py',
                  'notes':'Existing native source top extracted with aspect-preserving nearest-neighbor normalization; source remains unchanged.' if col==1 and native_top else 'Generated orthographic view; surfaces absent from the source view are inferred, not recovered pixels.'},
                  'anchor_px':[128,128]}
            meta['metadata_path']=str(meta_path.relative_to(ROOT))
            meta_path.write_text(json.dumps(meta,indent=2)+'\n')
            index['assets']=[a for a in index['assets'] if a['id']!=asset_id]
            index['assets'].append(meta); refs[view]=asset_id
        index['view_sets']=[s for s in index['view_sets'] if s['object_id']!=obj['id']]
        index['view_sets'].append({'object_id':obj['id'],'views':refs,'complete':False,
            'notes':'Generated six-view set; pending visual QA for source identity, complete alpha-island extraction, transparent background and geometry. Unseen surfaces inferred.'})
    tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)

def process_view_column(spec, view, column=0, column_count=6, index_override=None, write_index=True):
    """Replace one view; optional cell_calibration converts alternate atlas cell units first."""
    raw=OUT/spec['raw']; atlas=Image.open(raw).convert('RGBA'); pixels=np.asarray(atlas); height,width=pixels.shape[:2]
    labels,_=ndimage.label(pixels[:,:,3] > 32); components=[]
    for label,sl in enumerate(ndimage.find_objects(labels),1):
        if sl is None:continue
        ys,xs=sl;area=int(np.count_nonzero(labels[sl]==label))
        if area<24:continue
        components.append({'label':label,'area':area,'cx':(xs.start+xs.stop)/2,'cy':(ys.start+ys.stop)/2,'box':(xs.start,ys.start,xs.stop,ys.stop)})
    index_path=OUT/'set-index.json';index=index_override if index_override is not None else json.loads(index_path.read_text());atlas_sha=hashlib.sha256(raw.read_bytes()).hexdigest()
    contact_path=ROOT/spec['contact_sheet'];prompt_path=OUT/spec['prompt_path']
    prompt_rel='reusable/views-additional/'+spec['prompt_path'] if not spec['prompt_path'].startswith('reusable/views-additional/') else spec['prompt_path']
    contact_sha=hashlib.sha256(contact_path.read_bytes()).hexdigest() if contact_path.exists() else None
    prompt_sha=hashlib.sha256(prompt_path.read_bytes()).hexdigest() if prompt_path.exists() else None
    row_count=int(spec.get('row_count',len(spec['objects'])))
    for row,obj in enumerate(spec['objects']):
        source_row=int(obj.get('source_row',row))
        x0,x1=round(column*width/column_count),round((column+1)*width/column_count)
        y0,y1=round(source_row*height/row_count),round((source_row+1)*height/row_count)
        selected=[c for c in components if x0<=c['cx']<x1 and y0<=c['cy']<y1]
        if not selected:raise ValueError(f"{obj['id']}/{view}: no significant components")
        xlo=min(c['box'][0] for c in selected);ylo=min(c['box'][1] for c in selected);xhi=max(c['box'][2] for c in selected);yhi=max(c['box'][3] for c in selected)
        core=np.isin(labels,[c['label'] for c in selected]);mask=ndimage.binary_dilation(core,iterations=2)&(pixels[:,:,3]>0)
        masked=np.zeros_like(pixels);masked[mask]=pixels[mask];crop=Image.fromarray(masked,'RGBA').crop((xlo,ylo,xhi,yhi))
        aid=f"{obj['id']}.{view}"; asset=next(a for a in index['assets'] if a['id']==aid)
        cal=spec.get('object_cell_calibration',{}).get(obj['id'],spec.get('cell_calibration',[1.0,1.0]))
        if len(cal)!=2:
            raise ValueError(f"{aid}: cell calibration must have two factors")
        sx,sy=map(float,cal)
        norm=asset['provenance']['normalization']
        scale=float(norm['scale'])
        affine_evidence=None
        if abs(sx-sy)>1e-9:
            affine_evidence=_validate_reviewed_axis_calibration(
                aid, view, (sx,sy), raw, atlas_sha, (xlo,ylo,xhi,yhi),
                crop.size, norm, asset, spec)
            crop=crop.resize((max(1,round(crop.width*sx)),max(1,round(crop.height*sy))),Image.Resampling.NEAREST)
        else:
            crop=crop.resize((max(1,round(crop.width*sx)),max(1,round(crop.height*sy))),Image.Resampling.NEAREST)
        nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale))
        if affine_evidence and [nw,nh]!=affine_evidence['target_dimensions_px']:
            raise ValueError(f"{aid}: reviewed affine evidence target dimensions mismatch")
        if max(nw,nh)>204:raise ValueError(f"{aid}: replacement exceeds established shared scale ({nw}x{nh})")
        crop=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));ox=(256-nw)//2;oy=(256-nh)//2;canvas.alpha_composite(crop,(ox,oy))
        ip=OUT/'images'/f'{aid}.png';mp=ip.with_suffix('.json');canvas.save(ip,optimize=True);rgba=canvas.tobytes()
        if affine_evidence:
            output_sha=hashlib.sha256(ip.read_bytes()).hexdigest()
            if output_sha!=affine_evidence['active_output_sha256']:
                raise ValueError(f"{aid}: rebuilt affine output hash differs from reviewed current output")
            rgba_sha=hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest()
            if rgba_sha!=affine_evidence['active_output_rgba_sha256']:
                raise ValueError(f"{aid}: rebuilt affine RGBA hash differs from reviewed current output")
        asset['image']['sha256']=hashlib.sha256(ip.read_bytes()).hexdigest();asset['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest()
        asset['provenance'].update({'generated_atlas':str(raw.relative_to(ROOT)),'generated_atlas_sha256':atlas_sha,'source_cell_calibration':cal,
            'prompt_path':prompt_rel,'source_contact_sheet':spec['contact_sheet'],
            'prompt_sha256':prompt_sha,'source_contact_sheet_sha256':contact_sha,
            'source_rect':{'cell':[x0,y0,x1-x0,y1-y0],'alpha_bounds':[xlo,ylo,xhi-xlo,yhi-ylo],
                           'component_count':len(selected),'component_areas':[c['area'] for c in selected],
                           'components_outside_cell':[c['label'] for c in selected if c['box'][0]<x0 or c['box'][1]<y0 or c['box'][2]>x1 or c['box'][3]>y1]},
            'normalization':{'scale':scale,'offset_px':[ox,oy],'resampling':'nearest','frame_size':[256,256], **({'calibration_evidence':norm['calibration_evidence']} if affine_evidence else {})},
            'notes':f'Generated illustrative {view} orthographic view; unseen surfaces inferred, not recovered pixels or metrically calibrated.'})
        mp.write_text(json.dumps(asset,indent=2)+'\n')
    # Keep the set explicitly incomplete until the underside geometry receives a visual QA pass.
    for obj in spec['objects']:
        ss=next(s for s in index['view_sets'] if s['object_id']==obj['id']);ss['complete']=False
        ss['notes']=f"Replaced {view} view with an isolated-direction atlas crop; other reviewed/generated views retained. Pending geometry QA."
    if write_index:
        tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)
    return index

def _validate_reviewed_axis_calibration(asset_id, view, factors, raw, atlas_sha, crop_bounds, crop_size, norm, asset, spec):
    """Permit unequal input-axis factors only under a precise reviewed proof."""
    evidence=norm.get('calibration_evidence')
    if not isinstance(evidence,dict) or evidence.get('method')!='reviewed-axis-affine-v1':
        raise ValueError(f"{asset_id}: unequal calibration lacks reviewed-axis-affine-v1 evidence")
    if evidence.get('object_id')+'.'+evidence.get('view')!=asset_id or evidence.get('view')!=view:
        raise ValueError(f"{asset_id}: affine evidence identifies a different leaf")
    proof_path=ROOT/evidence.get('recipe_path','')
    if not proof_path.is_file() or hashlib.sha256(proof_path.read_bytes()).hexdigest()!=evidence.get('recipe_sha256'):
        raise ValueError(f"{asset_id}: affine proof missing or hash mismatch")
    proof=json.loads(proof_path.read_text())
    row=next((r for r in proof.get('rows',[]) if r.get('object_id')==evidence['object_id'] and r.get('view')==view),None)
    if row is None or proof.get('method')!='reviewed-axis-affine-v1':
        raise ValueError(f"{asset_id}: affine proof has no unique matching row")
    for key in ('source_path','source_sha256','atlas_path','atlas_sha256',
                'active_output_sha256','active_output_rgba_sha256','crop_bounds_xyxy','resized_dimensions_px',
                'scale_x','scale_y','target_dimensions_px','review_record_path','review_record_sha256','review_status'):
        if evidence.get(key)!=row.get(key):
            raise ValueError(f"{asset_id}: affine evidence {key} does not match proof row")
    for key in ('source_recipe_path','source_recipe_sha256'):
        if evidence.get(key)!=row.get(key):
            raise ValueError(f"{asset_id}: affine evidence {key} does not match proof row")
    if row.get('review_status')!='approved':
        raise ValueError(f"{asset_id}: affine proof review is not approved")
    if tuple(factors)!=(float(row['scale_x']),float(row['scale_y'])):
        raise ValueError(f"{asset_id}: active unequal factors differ from reviewed proof")
    if tuple(crop_bounds)!=tuple(row['crop_bounds_xyxy']) or tuple(crop_size)!=(crop_bounds[2]-crop_bounds[0],crop_bounds[3]-crop_bounds[1]):
        raise ValueError(f"{asset_id}: extracted alpha crop differs from reviewed proof")
    if hashlib.sha256(raw.read_bytes()).hexdigest()!=row['atlas_sha256'] or atlas_sha!=row['atlas_sha256']:
        raise ValueError(f"{asset_id}: affine atlas hash differs from reviewed proof")
    if row.get('source_recipe_path')!='reusable/views-additional/corrections.json':
        raise ValueError(f"{asset_id}: affine recipe path is outside approved correction policy")
    recipe=ROOT/row['source_recipe_path']
    if not recipe.is_file() or hashlib.sha256(recipe.read_bytes()).hexdigest()!=row['source_recipe_sha256']:
        raise ValueError(f"{asset_id}: affine recipe missing or hash mismatch")
    expected_batch=spec.get('batch_id') or 'initial-correction-record'
    if row.get('recipe_batch_id')!=expected_batch:
        raise ValueError(f"{asset_id}: selected correction row differs from affine proof")
    if Path(spec['raw']).as_posix() != Path(row['atlas_path']).relative_to('reusable/views-additional').as_posix():
        raise ValueError(f"{asset_id}: selected correction atlas differs from affine proof")
    configured=spec.get('object_cell_calibration',{}).get(row['object_id'],spec.get('cell_calibration',[1.0,1.0]))
    if [float(x) for x in configured] != [float(row['scale_x']),float(row['scale_y'])]:
        raise ValueError(f"{asset_id}: selected correction calibration differs from affine proof")
    source=ROOT/row['source_path']
    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=row['source_sha256']:
        raise ValueError(f"{asset_id}: affine canonical source missing or hash mismatch")
    review=ROOT/row['review_record_path']
    if not review.is_file() or hashlib.sha256(review.read_bytes()).hexdigest()!=row.get('review_record_sha256'):
        raise ValueError(f"{asset_id}: affine current-review record missing or hash mismatch")
    review_data=json.loads(review.read_text())
    if review_data.get('review_status')!='pass' or review_data.get('object_id')!=row['object_id'] or review_data.get('view_hashes',{}).get(view)!=row['active_output_sha256']:
        raise ValueError(f"{asset_id}: affine proof does not bind current whole-set PASS")
    rx,ry=map(float,row['resized_dimensions_px'])
    if [round((crop_bounds[2]-crop_bounds[0])*float(row['scale_x'])),round((crop_bounds[3]-crop_bounds[1])*float(row['scale_y']))] != [int(rx),int(ry)]:
        raise ValueError(f"{asset_id}: affine axis arithmetic differs from proof")
    if [round(rx*float(row['final_uniform_scale'])),round(ry*float(row['final_uniform_scale']))]!=row['target_dimensions_px']:
        raise ValueError(f"{asset_id}: final uniform scale arithmetic differs from proof")
    if abs(float(norm['scale'])-float(row['final_uniform_scale']))>1e-12:
        raise ValueError(f"{asset_id}: final uniform normalization differs from proof")
    return row

def process_view_columns(spec, view_columns):
    """Apply an entire multi-view repair and atomically publish its index once."""
    index_path=OUT/'set-index.json';index=json.loads(index_path.read_text())
    for view,column in view_columns.items():
        index=process_view_column(spec,view,column,column_count=spec.get('column_count',1),index_override=index,write_index=False)
    tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)
    return index

def process_prebuilt_views(spec):
    """Replay normalized, individually reviewed pilot PNGs and sidecars offline."""
    import shutil
    index_path=OUT/'set-index.json';index=json.loads(index_path.read_text())
    for obj in spec['objects']:
        refs={}
        for view in spec['views']:
            aid=f"{obj['id']}.{view}"
            src=OUT/spec['prebuilt_dir']/f"{aid}.png"
            smeta=src.with_suffix('.json')
            dest=OUT/'images'/f"{aid}.png"
            if not src.exists() or not smeta.exists(): raise FileNotFoundError(src)
            shutil.copyfile(src,dest)
            meta=json.loads(smeta.read_text())
            index['assets']=[a for a in index['assets'] if a['id']!=aid]
            index['assets'].append(meta);refs[view]=aid
        ss=next((s for s in index['view_sets'] if s['object_id']==obj['id']),None)
        if ss is None: raise KeyError(f"missing view set {obj['id']}")
        ss['views']=refs
        expected=spec.get('approved_hashes',{}).get(obj['id'],{})
        actual={v:next(a for a in index['assets'] if a['id']==refs[v])['image']['sha256'] for v in refs}
        approved=bool(expected) and all(actual.get(v)==h for v,h in expected.items()) and set(actual)==set(expected)
        ss['complete']=approved
        ss['notes']='Replayed retained normalized pilot PNGs/sidecars; whole-set root PASS restored only when all six current PNG hashes match the retained approval record.' if approved else 'Replayed retained normalized pilot PNGs and sidecars; pending current-hash geometry approval.'
    tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)
    return index

def process_view_aliases(spec):
    """Copy a physically symmetric view's pixels with explicit provenance and atomic index update."""
    import shutil
    index_path=OUT/'set-index.json';index=json.loads(index_path.read_text())
    aliases=spec['symmetric_view_aliases']
    for obj in spec['objects']:
        for target,source in aliases.items():
            aid=f"{obj['id']}.{target}"; sid=f"{obj['id']}.{source}"
            src=OUT/'images'/f'{sid}.png'; dst=OUT/'images'/f'{aid}.png'
            shutil.copyfile(src,dst)
            source_asset=next(a for a in index['assets'] if a['id']==sid)
            target_asset=next(a for a in index['assets'] if a['id']==aid)
            im=Image.open(dst).convert('RGBA');rgba=im.tobytes()
            prior=target_asset.get('provenance',{})
            hist=target_asset.setdefault('provenance_history',[]);hist.append(prior)
            target_asset['image']['sha256']=hashlib.sha256(dst.read_bytes()).hexdigest()
            target_asset['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',im.width,im.height)+rgba).hexdigest()
            target_asset['provenance']={**source_asset.get('provenance',{}),
                'method':'inferred-symmetric-view-copy',
                'symmetric_alias_of':source,
                'symmetry_reason':spec.get('symmetry_reason','The object has a directionally symmetric physical edge profile; hidden geometry is inferred, not recovered.'),
                'notes':'Pixels copied from a directionally symmetric orthographic side view to preserve identical physical thickness and scale; inferred symmetry, not recovered hidden pixels.'}
            target_meta=OUT/'images'/f'{aid}.json';target_asset['metadata_path']=str(target_meta.relative_to(ROOT))
            target_meta.write_text(json.dumps(target_asset,indent=2)+'\n')
            index['assets']=[a for a in index['assets'] if a['id']!=aid];index['assets'].append(target_asset)
        ss=next(s for s in index['view_sets'] if s['object_id']==obj['id']);ss['complete']=False
        ss['notes']='Symmetric orthographic view copied with explicit inference provenance; pending independent whole-set review.'
    tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)
    return index
