"""Uniformly calibrate one targeted principal view to sibling world width, updating replay metadata and hashes."""
from pathlib import Path
import hashlib, json, struct, sys
import numpy as np
from PIL import Image
from scipy import ndimage
OUT=Path(__file__).resolve().parent; PACK=OUT.parents[1]; INDEX=OUT/'set-index.json'
index=json.loads(INDEX.read_text()); assets={a['id']:a for a in index['assets']}; sets={s['object_id']:s for s in index['view_sets']}

def alpha_width(path):
    box=Image.open(path).getchannel('A').getbbox()
    return box[2]-box[0] if box else 0

def calibrate(object_id, view, reference_views=('front','top')):
    group=sets[object_id]; aid=group['views'][view]; meta=assets[aid]; sidecar=PACK/meta['metadata_path']; leaf=json.loads(sidecar.read_text()); crop=leaf['provenance']['crop_bounds_px']
    references=[alpha_width(PACK/assets[group['views'][v]]['image']['path']) for v in reference_views]
    target=max(references); dest=PACK/meta['image']['path']; current=alpha_width(dest)
    if not current or not target: raise RuntimeError(f'{object_id}.{view}: missing alpha bounds')
    pre_ratio=max(current/target,target/current)
    factor=target/current
    if abs(factor-1)<1e-6: return {'object_id':object_id,'view':view,'pre_width':current,'target_width':target,'factor':1.0,'post_ratio':pre_ratio}
    crop['projection_scale']=float(crop.get('projection_scale',1.0))*factor
    nw=max(1,round(crop['resized_bounds_px'][0]*factor)); nh=max(1,round(crop['resized_bounds_px'][1]*factor)); crop['resized_bounds_px']=[nw,nh]; crop['canvas_offset_px']=[128-nw//2,128-nh//2]
    crop['scale_calibration']={'target_reference_views':list(reference_views),'target_width_px':target,'previous_alpha_width_px':current,'uniform_factor':factor,'pre_scale_mismatch_ratio':pre_ratio,'post_scale_mismatch_ratio':1.0}
    leaf['provenance']['notes']='inferred orthographic view, not recovered pixels; uniform principal-view scale calibrated to sibling front/top width'
    atlas=Image.open(PACK/leaf['provenance']['source_atlas']).convert('RGBA'); rgba=np.asarray(atlas); threshold=json.loads((PACK/leaf['provenance']['generation_recipe']).read_text()).get('alpha_threshold',245); labels,_=ndimage.label(rgba[:,:,3]>=threshold,np.ones((3,3),dtype=np.uint8)); x0,y0,x1,y1=crop['alpha_bounds_global']; keep=[int(x) for x in crop['component_labels']]; mask=np.isin(labels[y0:y1,x0:x1],keep); piece=atlas.crop((x0,y0,x1,y1)); piece.putalpha(Image.fromarray((mask*255).astype('uint8'))); projection=float(crop['projection_scale']); piece=piece.resize((max(1,round(piece.width*projection)),max(1,round(piece.height*projection))),Image.Resampling.NEAREST); piece=piece.resize((nw,nh),Image.Resampling.NEAREST); frame=Image.new('RGBA',(256,256)); frame.alpha_composite(piece,tuple(crop['canvas_offset_px'])); frame.save(dest,optimize=True)
    leaf['image']['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest(); leaf['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest(); sidecar.write_text(json.dumps(leaf,indent=2)+'\n'); assets[aid]=leaf
    post=alpha_width(dest); mismatch=max(post/target,target/post)
    if mismatch>1.25: raise RuntimeError(f'{object_id}.{view}: calibrated width mismatch remains {mismatch:.3f}x')
    group['complete']=False; group['geometry_qa']={'status':'pending-review','views':[view],'notes':f'Uniform scale calibrated to sibling {"/".join(reference_views).upper()} width; post-scale mismatch {mismatch:.3f}x. Independent review required.','atlas_self_inspected':True}
    return {'object_id':object_id,'view':view,'pre_width':current,'target_width':target,'factor':factor,'post_width':post,'post_ratio':mismatch,'pre_mismatch_ratio':pre_ratio}

args=sys.argv[1:]
if args:
    if len(args)%3: raise SystemExit('usage: calibrate_view_width.py <object_id> <view> <front,top> [<object_id> <view> <front,top> ...]')
    tasks=[(args[i],args[i+1],tuple(args[i+2].split(','))) for i in range(0,len(args),3)]
else:
    tasks=[(f'revamp--characters--carl--{pose}','bottom',('front','top')) for pose in ('windup','attack','hit')]
audit=[calibrate(*task) for task in tasks]
index['assets']=list(assets.values()); index['view_sets']=list(sets.values()); INDEX.write_text(json.dumps(index,indent=2)+'\n'); name='scale-calibration-'+(tasks[0][0].replace('--','-') if len(tasks)==1 else 'batch')+'.json'; (OUT/'raw'/name).write_text(json.dumps(audit,indent=2)+'\n'); print(json.dumps(audit,indent=2))
