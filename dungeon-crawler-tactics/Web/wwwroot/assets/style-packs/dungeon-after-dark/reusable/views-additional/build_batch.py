"""Offline six-view atlas extraction and normalization for one pack-local batch."""
from pathlib import Path
import hashlib, json, os, struct
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
VIEWS = ['front', 'top', 'right', 'left', 'bottom', 'rear']

def process_batch(spec, object_ids=None):
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
    index_path = OUT / 'set-index.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else {'assets':[], 'view_sets':[]}
    for row, obj in enumerate(spec['objects']):
        if object_ids is not None and obj['id'] not in object_ids: continue
        crops, rects = [], []
        for col in range(6):
            x0, x1 = round(col*width/6), round((col+1)*width/6)
            y0, y1 = round(row*height/len(spec['objects'])), round((row+1)*height/len(spec['objects']))
            selected=[c for c in components if x0<=c['cx']<x1 and y0<=c['cy']<y1 and x0<=c['box'][0] and y0<=c['box'][1] and c['box'][2]<=x1 and c['box'][3]<=y1]
            if not selected:
                cell_alpha=(pixels[y0:y1,x0:x1,3]>32); yy,xx=np.nonzero(cell_alpha)
                if len(xx)==0:raise ValueError(f"{obj['id']}/{VIEWS[col]} has no significant alpha components")
                xlo=x0+int(xx.min());ylo=y0+int(yy.min());xhi=x0+int(xx.max())+1;yhi=y0+int(yy.max())+1
                crop=Image.fromarray(pixels[y0:y1,x0:x1],'RGBA').crop((int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1))
                outside=[];areas=[];count=0
            else:
                xlo=min(c['box'][0] for c in selected);ylo=min(c['box'][1] for c in selected);xhi=max(c['box'][2] for c in selected);yhi=max(c['box'][3] for c in selected)
                mask=np.isin(labels,[c['label'] for c in selected]);mask=ndimage.binary_dilation(mask,iterations=2)&(pixels[:,:,3]>0)
                masked=np.zeros_like(pixels);masked[mask]=pixels[mask];crop=Image.fromarray(masked,'RGBA').crop((xlo,ylo,xhi,yhi))
                outside=[c['label'] for c in selected if c['box'][0]<x0 or c['box'][1]<y0 or c['box'][2]>x1 or c['box'][3]>y1]
                areas=[c['area'] for c in selected];count=len(selected)
            crops.append(crop)
            edge={'left':int((pixels[y0:y1,x0,3]>32).sum()),'right':int((pixels[y0:y1,x1-1,3]>32).sum()),'top':int((pixels[y0,x0:x1,3]>32).sum()),'bottom':int((pixels[y1-1,x0:x1,3]>32).sum())}
            rects.append({'cell':[x0,y0,x1-x0,y1-y0],'alpha_bounds':[xlo,ylo,xhi-xlo,yhi-ylo],'component_count':count,'component_areas':areas,'components_outside_cell':outside,'edge_alpha_counts':edge})
        scale=204/max(max(c.size) for c in crops); refs={}
        for col,(view,crop) in enumerate(zip(VIEWS,crops)):
            nw=max(1,round(crop.width*scale)); nh=max(1,round(crop.height*scale))
            crop=crop.resize((nw,nh),Image.Resampling.NEAREST)
            canvas=Image.new('RGBA',(256,256),(0,0,0,0)); ox=(256-nw)//2; oy=(256-nh)//2
            canvas.alpha_composite(crop,(ox,oy))
            asset_id=f"{obj['id']}.{view}"; image_path=OUT/'images'/f'{asset_id}.png'; meta_path=image_path.with_suffix('.json')
            canvas.save(image_path,optimize=True); rgba=canvas.tobytes()
            meta={'id':asset_id,'name':f"{obj['name']} {view.title()}",'kind':obj['kind'],
                  'tags':['six-view','orthographic',obj['kind'],'generated'],'image':{
                  'path':str(image_path.relative_to(ROOT)),'width':256,'height':256,
                  'sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),
                  'rgba_sha256':hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest()},
                  'object_id':obj['id'],'view':view,'provenance':{
                  'method':'generated','source_image':obj['source_image'],
                  'source_contact_sheet':spec['contact_sheet'],
                  'generated_atlas':str(raw.relative_to(ROOT)), 'generated_atlas_sha256':atlas_sha,
                  'prompt_path':spec['prompt_path'], 'source_rect':rects[col],
                  'normalization':{'scale':scale,'offset_px':[ox,oy],'resampling':'nearest','frame_size':[256,256]},
                  'rebuild_command':'python3 reusable/views-additional/build_all.py',
                  'notes':'Generated orthographic view; surfaces absent from the source view are inferred, not recovered pixels.'},
                  'anchor_px':[128,128]}
            meta['metadata_path']=str(meta_path.relative_to(ROOT))
            meta_path.write_text(json.dumps(meta,indent=2)+'\n')
            index['assets']=[a for a in index['assets'] if a['id']!=asset_id]
            index['assets'].append(meta); refs[view]=asset_id
        index['view_sets']=[s for s in index['view_sets'] if s['object_id']!=obj['id']]
        index['view_sets'].append({'object_id':obj['id'],'views':refs,'generation_complete':True,'complete':False,
            'geometry_qa':{'status':'pending-review','reviewed_asset_hashes':[]},
            'notes':'Six orthographic views generated; independent geometry QA pending; unseen surfaces inferred.'})
    tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)

def process_arsenal_axis_pair(top_spec,bottom_spec,object_ids=None):
    """Apply two 6×4 end-on atlases and keep one isotropic scale across all six views."""
    specs={'top':top_spec,'bottom':bottom_spec}; atlases={}; arrays={}; hashes={}
    for view,spec in specs.items():
        raw=OUT/spec['raw'];atlases[view]=Image.open(raw).convert('RGBA');arrays[view]=np.asarray(atlases[view]);hashes[view]=hashlib.sha256(raw.read_bytes()).hexdigest()
    index_path=OUT/'set-index.json';index=json.loads(index_path.read_text())
    for i,obj in enumerate(top_spec['objects']):
        if object_ids is not None and obj['id'] not in object_ids: continue
        row,col=divmod(i,6);assetset={v:next(a for a in index['assets'] if a['id']==f"{obj['id']}.{v}") for v in ['front','top','right','left','bottom','rear']}
        original_scale=assetset['front']['provenance']['normalization']['scale'];cells={}
        for view,ar in arrays.items():
            H,W=ar.shape[:2];x0,x1=round(col*W/6),round((col+1)*W/6);y0,y1=round(row*H/4),round((row+1)*H/4)
            cell=ar[y0:y1,x0:x1];alpha=cell[:,:,3]>32;labels,n=ndimage.label(alpha);parts=[]
            for lab,sl in enumerate(ndimage.find_objects(labels),1):
                if sl is None:continue
                ys,xs=sl;area=int(np.count_nonzero(labels[sl]==lab))
                if area<24:continue
                touches=(ys.start<=1 or xs.start<=1 or ys.stop>=cell.shape[0]-1 or xs.stop>=cell.shape[1]-1)
                parts.append((lab,area,touches))
            if not parts:raise ValueError(f"{obj['id']}.{view}: empty atlas cell")
            largest=max(area for _,area,_ in parts)
            chosen=[lab for lab,area,touches in parts if not touches or area>=max(200,largest*.05)]
            if not chosen:chosen=[max(parts,key=lambda x:x[1])[0]]
            mask=np.isin(labels,chosen);yy,xx=np.nonzero(mask);xlo=int(xx.min());ylo=int(yy.min());xhi=int(xx.max())+1;yhi=int(yy.max())+1
            crop=Image.fromarray(np.where(mask[:,:,None],cell,0).astype('uint8'),'RGBA').crop((xlo,ylo,xhi,yhi))
            cells[view]={'crop':crop,'rect':{'cell':[x0,y0,x1-x0,y1-y0],'alpha_bounds':[x0+xlo,y0+ylo,xhi-xlo,yhi-ylo],'component_count':len(chosen),'component_areas':[int(np.count_nonzero(labels==lab)) for lab in chosen],'components_outside_cell':[],'dropped_border_artifacts':[{'area':area} for lab,area,touches in parts if touches and lab not in chosen]}}
        target_scale=min(original_scale,252/max(max(d['crop'].size) for d in cells.values()))
        # Re-normalize every view at this same isotropic scale so end-on projections cannot clip.
        for view,asset in assetset.items():
            factor=target_scale/original_scale
            if view in cells:
                crop=cells[view]['crop'];view_factor=target_scale
            else:
                ip=OUT/'images'/f"{asset['id']}.png";old=Image.open(ip).convert('RGBA');aa=np.asarray(old)[:,:,3];yy,xx=np.nonzero(aa>32)
                if not len(xx):raise ValueError(f"{asset['id']}: empty existing view")
                crop=old.crop((int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1));view_factor=factor
            nw=max(1,round(crop.width*view_factor));nh=max(1,round(crop.height*view_factor))
            if max(nw,nh)>256:raise ValueError(f"{asset['id']} clips at shared scale {nw}×{nh}")
            crop=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));ox=(256-nw)//2;oy=(256-nh)//2;canvas.alpha_composite(crop,(ox,oy))
            ip=OUT/'images'/f"{asset['id']}.png";mp=ip.with_suffix('.json');canvas.save(ip,optimize=True);rgba=canvas.tobytes()
            asset['image']['sha256']=hashlib.sha256(ip.read_bytes()).hexdigest();asset['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest()
            norm={'scale':target_scale,'offset_px':[ox,oy],'resampling':'nearest','frame_size':[256,256]}
            asset['provenance']['normalization']=norm
            if view in cells:
                spec=specs[view];raw=OUT/spec['raw'];asset['provenance'].update({'method':'generated','generated_atlas':str(raw.relative_to(ROOT)),'generated_atlas_sha256':hashes[view],'source_contact_sheet':spec['contact_sheet'],'prompt_path':spec['prompt_path'],'source_rect':cells[view]['rect'],'source_cell_calibration':[1.0,1.0],'notes':'Generated end-on orthographic projection including all visible head/guard and end-cap components; inferred surfaces, not recovered pixels.'})
            mp.write_text(json.dumps(asset,indent=2)+'\n')
        ss=next(s for s in index['view_sets'] if s['object_id']==obj['id']);ss['generation_complete']=True;ss['complete']=False;ss['geometry_qa']={'status':'pending-review','reviewed_asset_hashes':[]};ss['notes']='End-on top/bottom projections installed at a common isotropic six-view scale; independent geometry QA pending.'
    tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)

def process_view_column(spec, view, column=0, object_ids=None):
    """Replace one view; optional cell_calibration converts alternate atlas cell units first."""
    raw=OUT/spec['raw']; atlas=Image.open(raw).convert('RGBA'); pixels=np.asarray(atlas); height,width=pixels.shape[:2]
    labels,_=ndimage.label(pixels[:,:,3] > 32); components=[]
    for label,sl in enumerate(ndimage.find_objects(labels),1):
        if sl is None:continue
        ys,xs=sl;area=int(np.count_nonzero(labels[sl]==label))
        if area<24:continue
        components.append({'label':label,'area':area,'cx':(xs.start+xs.stop)/2,'cy':(ys.start+ys.stop)/2,'box':(xs.start,ys.start,xs.stop,ys.stop)})
    index_path=OUT/'set-index.json';index=json.loads(index_path.read_text());atlas_sha=hashlib.sha256(raw.read_bytes()).hexdigest()
    for row,obj in enumerate(spec['objects']):
        if object_ids is not None and obj['id'] not in object_ids: continue
        x0,x1=round(column*width/6),round((column+1)*width/6)
        y0,y1=round(row*height/len(spec['objects'])),round((row+1)*height/len(spec['objects']))
        cell=pixels[y0:y1,x0:x1];cell_alpha=cell[:,:,3]>32;ll,nl=ndimage.label(cell_alpha)
        chosen=[]
        local_parts=[]
        for lab,sl in enumerate(ndimage.find_objects(ll),1):
            if sl is None:continue
            ys,xs=sl;area=int(np.count_nonzero(ll[sl]==lab))
            if area<24:continue
            local_parts.append((lab,area,ys,xs))
        if obj['id'] in spec.get('keep_largest_component_only',[]):
            if local_parts: chosen=[max(local_parts,key=lambda part:part[1])[0]]
        else:
            for lab,area,ys,xs in local_parts:
                touches=(ys.start<=1 or xs.start<=1 or ys.stop>=cell.shape[0]-1 or xs.stop>=cell.shape[1]-1)
                if touches:continue
                chosen.append(lab)
        if not chosen:
            chosen=[lab for lab,sl in enumerate(ndimage.find_objects(ll),1) if sl is not None and int(np.count_nonzero(ll[sl]==lab))>=24]
        if not chosen:raise ValueError(f"{obj['id']}/{view}: no significant local components")
        mask=np.isin(ll,chosen); yy,xx=np.nonzero(mask)
        xlo=x0+int(xx.min());ylo=y0+int(yy.min());xhi=x0+int(xx.max())+1;yhi=y0+int(yy.max())+1
        if spec.get('batch_id')=='dad-rat-top-correction':
            # Preserve antialiased pixels inside the manually reviewed rat component bounds.
            crop=Image.fromarray(cell,'RGBA').crop((int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1))
        else:
            crop=Image.fromarray(np.where(mask[:,:,None],cell,0).astype('uint8'),'RGBA').crop((int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1))
        nlocal=len(chosen);areas=[int(np.count_nonzero(ll==lab)) for lab in chosen]
        aid=f"{obj['id']}.{view}"; asset=next(a for a in index['assets'] if a['id']==aid)
        cal=spec.get('cell_calibration',[1.0,1.0]); crop=crop.resize((max(1,round(crop.width*cal[0])),max(1,round(crop.height*cal[1]))),Image.Resampling.NEAREST)
        scale=asset['provenance']['normalization']['scale'];nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale))
        if max(nw,nh)>256:raise ValueError(f"{aid}: replacement clips 256px canvas at established shared scale ({nw}x{nh})")
        crop=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));ox=(256-nw)//2;oy=(256-nh)//2;canvas.alpha_composite(crop,(ox,oy))
        ip=OUT/'images'/f'{aid}.png';mp=ip.with_suffix('.json');canvas.save(ip,optimize=True);rgba=canvas.tobytes()
        asset['image']['sha256']=hashlib.sha256(ip.read_bytes()).hexdigest();asset['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest()
        asset['provenance'].update({'generated_atlas':str(raw.relative_to(ROOT)),'generated_atlas_sha256':atlas_sha,'source_cell_calibration':spec.get('cell_calibration',[1.0,1.0]),
            'prompt_path':spec['prompt_path'],'source_contact_sheet':spec['contact_sheet'],
            'source_rect':{'cell':[x0,y0,x1-x0,y1-y0],'alpha_bounds':[xlo,ylo,xhi-xlo,yhi-ylo],
                           **({'manual_cell_review':'restricted to row 5 column 2 to exclude merged row-6 rat scout top-view island'} if spec.get('batch_id')=='dad-rat-top-correction' else {}),
                           'component_count':nlocal,'component_areas':areas,'components_outside_cell':[],
                           'edge_alpha_counts':{'left':int(cell_alpha[:,0].sum()),'right':int(cell_alpha[:,-1].sum()),'top':int(cell_alpha[0,:].sum()),'bottom':int(cell_alpha[-1,:].sum())}},
            'normalization':{'scale':scale,'offset_px':[ox,oy],'resampling':'nearest','frame_size':[256,256]},
            'notes':('Rat top cell extracted locally to separate a merged neighboring row; antialiasing retained.' if spec.get('batch_id')=='dad-rat-top-correction' else 'Generated illustrative underside orthographic view; minor foreshortening and unseen surfaces inferred, not recovered pixels or metrically calibrated.')})
        if spec.get('batch_id')=='dad-rat-top-correction':
            asset['provenance'].pop('source_cell_calibration',None)
            rect=asset['provenance']['source_rect'];manual=rect.pop('manual_cell_review');rect.pop('edge_alpha_counts',None);rect['manual_cell_review']=manual
            asset['provenance']['notes']='Generated orthographic view; surfaces absent from the source view are inferred, not recovered pixels.'
        mp.write_text(json.dumps(asset,indent=2)+'\n')
    # Keep the set explicitly incomplete until the underside geometry receives a visual QA pass.
    for obj in spec['objects']:
        if object_ids is not None and obj['id'] not in object_ids: continue
        ss=next(s for s in index['view_sets'] if s['object_id']==obj['id']);ss['generation_complete']=True;ss['complete']=False
        ss['geometry_qa']={'status':'pending-review','reviewed_asset_hashes':[]}
        ss['notes']=f'Five original views retained; corrected {view} view installed, awaiting independent geometry QA.'
    tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)

def process_single_view_image(spec, object_id):
    """Install one standalone generated view without fabricating an atlas grid."""
    raw=OUT/spec['raw'];im=Image.open(raw).convert('RGBA');pixels=np.asarray(im);alpha=pixels[:,:,3]>32
    labels,n=ndimage.label(alpha);parts=[]
    for lab,sl in enumerate(ndimage.find_objects(labels),1):
        if sl is None:continue
        area=int(np.count_nonzero(labels[sl]==lab))
        if area<24:continue
        ys,xs=sl;parts.append({'label':lab,'area':area,'box':(xs.start,ys.start,xs.stop,ys.stop)})
    if not parts:raise ValueError(f"{object_id}: standalone view has no significant alpha component")
    largest=max(p['area'] for p in parts)
    if spec.get('keep_largest_component_only'):
        chosen=[max(parts,key=lambda p:p['area'])]
    else:
        chosen=[p for p in parts if p['area']>=max(24,largest*0.005)]
    x0=min(p['box'][0] for p in chosen);y0=min(p['box'][1] for p in chosen);x1=max(p['box'][2] for p in chosen);y1=max(p['box'][3] for p in chosen)
    crop=im.crop((x0,y0,x1,y1));cal=spec.get('cell_calibration',[1.0,1.0])
    if isinstance(cal,(float,int)):cal=[float(cal),float(cal)]
    if abs(float(cal[0])-float(cal[1]))>1e-9:raise ValueError('standalone view calibration must be isotropic')
    crop=crop.resize((max(1,round(crop.width*cal[0])),max(1,round(crop.height*cal[1]))),Image.Resampling.NEAREST)
    index_path=OUT/'set-index.json';index=json.loads(index_path.read_text());asset=next(a for a in index['assets'] if a['id']==f"{object_id}.{spec['single_image_view']}")
    scale=asset['provenance']['normalization']['scale'];nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale))
    if max(nw,nh)>256:raise ValueError(f"{asset['id']}: standalone replacement clips ({nw}x{nh})")
    crop=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));ox=(256-nw)//2;oy=(256-nh)//2;canvas.alpha_composite(crop,(ox,oy))
    ip=OUT/'images'/f"{asset['id']}.png";mp=ip.with_suffix('.json');canvas.save(ip,optimize=True);rgba=canvas.tobytes();atlas_sha=hashlib.sha256(raw.read_bytes()).hexdigest()
    asset['image']['sha256']=hashlib.sha256(ip.read_bytes()).hexdigest();asset['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest()
    asset['provenance'].update({'generated_atlas':str(raw.relative_to(ROOT)),'generated_atlas_sha256':atlas_sha,
      'source_contact_sheet':spec['contact_sheet'],'prompt_path':spec['prompt_path'],
      **({'geometry_guide':spec['geometry_guide'],'geometry_guide_sha256':spec['geometry_guide_sha256']} if spec.get('geometry_guide') else {}),
      **({'additional_geometry_guides':spec['additional_geometry_guides']} if spec.get('additional_geometry_guides') else {}),
      **({'preprocessed_from':spec['preprocessed_from'],'preprocessed_from_sha256':spec['preprocessed_from_sha256'],'preprocessing':spec['preprocessing']} if spec.get('preprocessed_from') else {}),
      'source_cell_calibration':[float(cal[0]),float(cal[1])],
      'source_rect':{'cell':[0,0,im.width,im.height],'alpha_bounds':[x0,y0,x1-x0,y1-y0],
                     'component_count':len(chosen),'component_areas':[p['area'] for p in chosen],
                     'components_outside_cell':[]},
      'normalization':{'scale':scale,'offset_px':[ox,oy],'resampling':'nearest','frame_size':[256,256]},
      'notes':'Generated standalone orthographic view; hidden surfaces are inferred, not recovered pixels.'})
    mp.write_text(json.dumps(asset,indent=2)+'\n')
    s=next(x for x in index['view_sets'] if x['object_id']==object_id);old=s.get('geometry_qa',{});hist=old.get('history',[])
    if old.get('reviewed_image_hashes'):hist.append({'status':old.get('status'),'reviewed_image_hashes':old['reviewed_image_hashes'],'notes':old.get('notes',[])})
    changed=set(old.get('changed_views',[]));changed.add(spec['single_image_view'])
    s['geometry_qa']={'status':'pending-correction','reviewer':old.get('reviewer','root'),'changed_views':sorted(changed),
      'notes':['Standalone generated view installed; current-hash geometry re-review required.'],'history':hist};s['complete']=False
    s['notes']='Standalone orthographic correction installed; awaiting independent current-hash review.'
    tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)

def process_object_local_cells_shared_scale(spec, selections):
    """Extract one intended object from each local cell, remove adjacent-cell spill, and normalize selected views together."""
    raw=OUT/spec['raw'];atlas=Image.open(raw).convert('RGBA');pixels=np.asarray(atlas);height,width=pixels.shape[:2]
    index_path=OUT/'set-index.json';index=json.loads(index_path.read_text());asset_map={a['id']:a for a in index['assets']}
    atlas_sha=hashlib.sha256(raw.read_bytes()).hexdigest();rows={o['id']:i for i,o in enumerate(spec['objects'])}
    for oid,views in selections.items():
        if oid not in rows:raise ValueError(f'{oid}: not present in local-cell recipe')
        row=rows[oid];crops={};rects={}
        for col,view in enumerate(VIEWS):
            x0,x1=round(col*width/6),round((col+1)*width/6);y0,y1=round(row*height/len(spec['objects'])),round((row+1)*height/len(spec['objects']))
            cell=pixels[y0:y1,x0:x1];alpha=cell[:,:,3]>32;labels,n=ndimage.label(alpha);parts=[]
            for lab,sl in enumerate(ndimage.find_objects(labels),1):
                if sl is None:continue
                ys,xs=sl;area=int(np.count_nonzero(labels[sl]==lab))
                if area<24:continue
                touches=(ys.start<=1 or xs.start<=1 or ys.stop>=cell.shape[0]-1 or xs.stop>=cell.shape[1]-1)
                parts.append({'label':lab,'area':area,'box':(xs.start,ys.start,xs.stop,ys.stop),'touches':touches})
            if not parts:raise ValueError(f'{oid}.{view}: local source cell has no significant alpha')
            largest=max(parts,key=lambda p:p['area'])
            # Keep detached pieces inside the cell only when they are substantial and not border spill.
            chosen=[p for p in parts if not p['touches'] and p['area']>=largest['area']*0.01]
            if not chosen:chosen=[largest]
            mask=np.isin(labels,[p['label'] for p in chosen]);yy,xx=np.nonzero(mask)
            lx0,ly0,lx1,ly1=int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1
            crop=Image.fromarray(np.where(mask[:,:,None],cell,0).astype('uint8'),'RGBA').crop((lx0,ly0,lx1,ly1))
            crops[view]=crop
            rects[view]={'cell':[x0,y0,x1-x0,y1-y0],'alpha_bounds':[x0+lx0,y0+ly0,lx1-lx0,ly1-ly0],
                'component_count':len(chosen),'component_areas':[p['area'] for p in chosen],'components_outside_cell':[],
                'edge_alpha_counts':{'left':int(alpha[:,0].sum()),'right':int(alpha[:,-1].sum()),'top':int(alpha[0,:].sum()),'bottom':int(alpha[-1,:].sum())}}
        cal=spec.get('cell_calibration',{}).get(oid,[1.0,1.0]) if isinstance(spec.get('cell_calibration'),dict) else spec.get('cell_calibration',[1.0,1.0])
        if isinstance(cal,(float,int)):cal=[float(cal),float(cal)]
        if abs(float(cal[0])-float(cal[1]))>1e-9:raise ValueError(f'{oid}: anisotropic local-cell calibration is forbidden')
        for view in VIEWS:
            crop=crops[view];crops[view]=crop.resize((max(1,round(crop.width*cal[0])),max(1,round(crop.height*cal[1]))),Image.Resampling.NEAREST)
        scale=204/max(max(c.width,c.height) for c in crops.values())
        for view in views:
            crop=crops[view];nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale))
            if max(nw,nh)>256:raise ValueError(f'{oid}.{view}: local-cell output clips at shared scale ({nw}x{nh})')
            canvas=Image.new('RGBA',(256,256),(0,0,0,0));ox=(256-nw)//2;oy=(256-nh)//2
            crop=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas.alpha_composite(crop,(ox,oy))
            aid=f'{oid}.{view}';asset=asset_map[aid];ip=OUT/'images'/f'{aid}.png';mp=ip.with_suffix('.json')
            canvas.save(ip,optimize=True);rgba=canvas.tobytes();asset['image']['sha256']=hashlib.sha256(ip.read_bytes()).hexdigest()
            asset['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest()
            asset['provenance'].update({'method':'generated','generated_atlas':str(raw.relative_to(ROOT)),'generated_atlas_sha256':atlas_sha,
                'source_contact_sheet':spec['contact_sheet'],'prompt_path':spec['prompt_path'],'source_rect':rects[view],
                'normalization':{'scale':scale,'offset_px':[ox,oy],'resampling':'nearest','frame_size':[256,256]},
                'source_cell_calibration':[float(cal[0]),float(cal[1]),'isotropic'],'rebuild_command':'python3 reusable/views-additional/build_all.py',
                'notes':'Locally isolated original generated view; neighboring alpha spill excluded, then all six views normalized with one shared isotropic scale.'})
            mp.write_text(json.dumps(asset,indent=2)+'\n')
        s=next(x for x in index['view_sets'] if x['object_id']==oid);old=s.get('geometry_qa',{});history=old.get('history',[])
        if old.get('reviewed_image_hashes'):history.append({'status':old.get('status'),'reviewed_image_hashes':old['reviewed_image_hashes'],'notes':old.get('notes',[])})
        s['complete']=False;s['geometry_qa']={'status':'pending-correction','reviewer':old.get('reviewer','independent-visual-review'),'changed_views':list(views),'history':history,
            'notes':['Locally isolated generated cells and normalized with one shared scale; current-hash visual QA pending.']}
        s['notes']='Neighboring atlas spill removed and locally isolated views normalized to one shared scale; pending independent QA.'
    tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)

def process_selected_views(spec, selections):
    """Replace selected (object_id, view) cells from a full-view correction atlas, retaining all other views."""
    raw=OUT/spec['raw']; atlas=Image.open(raw).convert('RGBA'); pixels=np.asarray(atlas); height,width=pixels.shape[:2]
    labels,_=ndimage.label(pixels[:,:,3]>32); atlas_sha=hashlib.sha256(raw.read_bytes()).hexdigest()
    components=[]
    for label,sl in enumerate(ndimage.find_objects(labels),1):
        if sl is None: continue
        ys,xs=sl; area=int(np.count_nonzero(labels[sl]==label))
        if area<24: continue
        components.append({'label':label,'area':area,'cx':(xs.start+xs.stop)/2,'cy':(ys.start+ys.stop)/2,
                           'box':(xs.start,ys.start,xs.stop,ys.stop)})
    index_path=OUT/'set-index.json'; index=json.loads(index_path.read_text()); asset_map={a['id']:a for a in index['assets']}
    columns={v:i for i,v in enumerate(VIEWS)}
    selected_ids=set()
    for row,obj in enumerate(spec['objects']):
        targets=selections.get(obj['id'],{})
        if not targets: continue
        selected_ids.add(obj['id'])
        for view in targets:
            col=columns[view]; x0,x1=round(col*width/6),round((col+1)*width/6)
            y0,y1=round(row*height/len(spec['objects'])),round((row+1)*height/len(spec['objects']))
            selected=[c for c in components if x0<=c['cx']<x1 and y0<=c['cy']<y1 and x0<=c['box'][0] and y0<=c['box'][1] and c['box'][2]<=x1 and c['box'][3]<=y1]
            if not selected:
                cell=pixels[y0:y1,x0:x1]; alpha=cell[:,:,3]>32; local,_=ndimage.label(alpha)
                selected_local=[]
                for lab,sl in enumerate(ndimage.find_objects(local),1):
                    if sl is None: continue
                    ys,xs=sl; area=int(np.count_nonzero(local[sl]==lab))
                    if area<24: continue
                    selected_local.append({'label':lab,'area':area,'box':(xs.start,ys.start,xs.stop,ys.stop),'cx':(xs.start+xs.stop)/2,'cy':(ys.start+ys.stop)/2})
                if not selected_local: raise ValueError(f"{obj['id']}.{view}: correction atlas cell is empty")
                # Last-resort local fallback; never silently produce an empty/cropped result.
                yy,xx=np.nonzero(np.isin(local,[c['label'] for c in selected_local])); lx0=int(xx.min());ly0=int(yy.min());lx1=int(xx.max())+1;ly1=int(yy.max())+1
                crop=Image.fromarray(np.where(np.isin(local,[c['label'] for c in selected_local])[:,:,None],cell,0).astype('uint8'),'RGBA').crop((lx0,ly0,lx1,ly1))
                rect={'cell':[x0,y0,x1-x0,y1-y0],'alpha_bounds':[x0+lx0,y0+ly0,lx1-lx0,ly1-ly0],
                      'component_count':len(selected_local),'component_areas':[c['area'] for c in selected_local],'components_outside_cell':[],
                      'edge_alpha_counts':{'left':int(alpha[:,0].sum()),'right':int(alpha[:,-1].sum()),'top':int(alpha[0,:].sum()),'bottom':int(alpha[-1,:].sum())}}
            else:
                chosen=[c['label'] for c in selected]
                bx0=min(c['box'][0] for c in selected);by0=min(c['box'][1] for c in selected);bx1=max(c['box'][2] for c in selected);by1=max(c['box'][3] for c in selected)
                mask=np.isin(labels,chosen)&(pixels[:,:,3]>0);crop=Image.fromarray(np.where(mask[:,:,None],pixels,0).astype('uint8'),'RGBA').crop((bx0,by0,bx1,by1))
                outside=[c['label'] for c in selected if c['box'][0]<x0 or c['box'][1]<y0 or c['box'][2]>x1 or c['box'][3]>y1]
                cell_alpha=pixels[y0:y1,x0:x1,3]>32
                rect={'cell':[x0,y0,x1-x0,y1-y0],'alpha_bounds':[bx0,by0,bx1-bx0,by1-by0],
                      'component_count':len(selected),'component_areas':[c['area'] for c in selected],'components_outside_cell':outside,
                      'edge_alpha_counts':{'left':int(cell_alpha[:,0].sum()),'right':int(cell_alpha[:,-1].sum()),'top':int(cell_alpha[0,:].sum()),'bottom':int(cell_alpha[-1,:].sum())}}
            asset_id=f"{obj['id']}.{view}"; asset=asset_map[asset_id]; scale=asset['provenance']['normalization']['scale']
            cal=spec.get('cell_calibration',[1.0,1.0])
            # Some generated atlases draw individual orthographic cells at different
            # raw resolutions. Permit a per-object/per-view *isotropic* calibration
            # so plans and elevations share one world footprint without squeezing an
            # axis. Values are absolute atlas-unit factors, recorded in the recipe.
            view_cal=spec.get('view_calibration',{}).get(obj['id'],{}).get(view,cal)
            if isinstance(view_cal,(float,int)): view_cal=[float(view_cal),float(view_cal)]
            if abs(float(view_cal[0])-float(view_cal[1]))>1e-9:
                raise ValueError(f"{obj['id']}.{view}: anisotropic cell calibration is forbidden")
            crop=crop.resize((max(1,round(crop.width*view_cal[0])),max(1,round(crop.height*view_cal[1]))),Image.Resampling.NEAREST)
            rotation=int(spec.get('view_rotation_cw',{}).get(obj['id'],{}).get(view,0))%360
            if rotation:
                if rotation not in (90,180,270):raise ValueError(f"{obj['id']}.{view}: rotation must be a quarter turn")
                crop=crop.rotate(-rotation,expand=True,resample=Image.Resampling.NEAREST)
            nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale))
            if max(nw,nh)>256: raise ValueError(f"{asset_id}: correction clips at established shared scale ({nw}x{nh})")
            crop=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));ox=(256-nw)//2;oy=(256-nh)//2;canvas.alpha_composite(crop,(ox,oy))
            ip=OUT/'images'/f'{asset_id}.png';mp=ip.with_suffix('.json');canvas.save(ip,optimize=True);rgba=canvas.tobytes()
            asset['image']['sha256']=hashlib.sha256(ip.read_bytes()).hexdigest();asset['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest()
            asset['provenance'].update({'method':'generated','generated_atlas':str(raw.relative_to(ROOT)),'generated_atlas_sha256':atlas_sha,
              'source_contact_sheet':spec['contact_sheet'],'prompt_path':spec['prompt_path'],
              **({'geometry_guide':spec['geometry_guide'],'geometry_guide_sha256':spec['geometry_guide_sha256']} if spec.get('geometry_guide') else {}),
      **({'additional_geometry_guides':spec['additional_geometry_guides']} if spec.get('additional_geometry_guides') else {}),
      **({'preprocessed_from':spec['preprocessed_from'],'preprocessed_from_sha256':spec['preprocessed_from_sha256'],'preprocessing':spec['preprocessing']} if spec.get('preprocessed_from') else {}),
              'source_rect':rect,
              'normalization':{'scale':scale,'offset_px':[ox,oy],'resampling':'nearest','frame_size':[256,256],
                               **({'rotation_cw_degrees':rotation} if rotation else {})},
              'source_cell_calibration':[float(view_cal[0]),float(view_cal[1])],
              'notes':f"Generated corrective {view} projection at the established six-view scale; isotropic cell calibration applied; inferred surfaces, not recovered pixels."})
            mp.write_text(json.dumps(asset,indent=2)+'\n')
    for oid in selected_ids:
        s=next(x for x in index['view_sets'] if x['object_id']==oid); prior=s.get('geometry_qa',{}); hist=prior.get('history',[])
        if prior.get('reviewed_image_hashes'): hist.append({'status':prior.get('status'),'reviewed_image_hashes':prior['reviewed_image_hashes'],'notes':prior.get('notes',[])})
        s['geometry_qa']={'status':'pending-correction','reviewer':prior.get('reviewer','independent-visual-review'),'history':hist,
          'changed_views':sorted(selections[oid].keys()),'notes':['Corrective view assets installed; independent current-hash re-review required.']}
        s['complete']=False;s['notes']='Corrected view(s) installed; pending independent geometry re-review.'
    tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)
