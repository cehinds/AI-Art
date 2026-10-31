"""Rebuild and deterministically re-key NW wall views from their retained source atlas."""
from pathlib import Path
import hashlib, json, struct
from PIL import Image
import numpy as np
from scipy import ndimage
HERE=Path(__file__).resolve().parent; PACK=HERE.parents[1]; RAW=HERE/'raw'/'dungeon-stone-walls-nw-before-axis-remap'; INDEX=HERE/'set-index.json'; QA=Path('/workspace/scratch/view-qa-report.json')
OBJECT='dungeon-stone--walls-nw'
MAPPING={'front':('right',None),'right':('rear',None),'left':('front',None),'rear':('left',None),'top':('top','clockwise90'),'bottom':('bottom','clockwise90')}
def sha(b): return hashlib.sha256(b).hexdigest()
def png(im):
    import io
    b=io.BytesIO();im.save(b,format='PNG',optimize=True);return b.getvalue()
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={s['object_id']:s for s in idx['view_sets']}
qa=json.loads(QA.read_text()).get('reviewed',{}).get(f'reusable-gameplay::{OBJECT}',{})
history=qa.get('history',[])
expected=next((h.get('image_hashes',{}) for h in history if h.get('status')=='issues' and h.get('image_hashes')), {})
# Rebuild every pre-remap source projection from retained atlas+component metadata,
# rather than reading any current destination view that may already be replaced.
original={}
for view in ('front','top','right','left','bottom','rear'):
    aid=f'{OBJECT}.{view}'; meta=json.loads((PACK/assets[aid]['metadata_path']).read_text()); pr=meta['provenance']; c=pr['crop_bounds_px']; atlas_path=PACK/pr['source_atlas']; atlas=Image.open(atlas_path).convert('RGBA'); arr=np.asarray(atlas)
    if pr.get('source_atlas_sha256') and sha(atlas_path.read_bytes())!=pr['source_atlas_sha256']: raise RuntimeError('source atlas hash mismatch')
    if c.get('selection_mode')=='all_opaque_pixels': local=arr[c['alpha_bounds_global'][1]:c['alpha_bounds_global'][3],c['alpha_bounds_global'][0]:c['alpha_bounds_global'][2],3]>=245
    else:
        labels,_=ndimage.label(arr[:,:,3]>=245,np.ones((3,3),dtype=np.uint8)); x0,y0,x1,y1=c['alpha_bounds_global']; local=np.isin(labels[y0:y1,x0:x1],list(map(int,c['component_labels'])))
    x0,y0,x1,y1=c['alpha_bounds_global']; piece=atlas.crop((x0,y0,x1,y1)); piece.putalpha(Image.fromarray((local*255).astype('uint8')))
    rot=int(c.get('orientation_correction_degrees',0))%360
    if rot: piece=piece.rotate(rot,resample=Image.Resampling.NEAREST,expand=True)
    scale=float(c.get('projection_scale',1.0))
    if scale!=1.0: piece=piece.resize((max(1,round(piece.width*scale)),max(1,round(piece.height*scale))),Image.Resampling.NEAREST)
    w,h=c['resized_bounds_px'];piece=piece.resize((w,h),Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256));frame.alpha_composite(piece,tuple(c['canvas_offset_px']))
    data=png(frame); digest=sha(data)
    if view in expected and digest!=expected[view]: raise RuntimeError(f'{view} source-atlas reconstruction differs from pre-remap reviewed hash')
    RAW.mkdir(parents=True,exist_ok=True);rp=RAW/f'{OBJECT}.{view}.png';rp.write_bytes(data);original[view]=(rp,data)
for dst_view,(src_view,rotation) in MAPPING.items():
    aid=f'{OBJECT}.{dst_view}';meta=json.loads((PACK/assets[aid]['metadata_path']).read_text());rp,sb=original[src_view];im=Image.open(rp).convert('RGBA')
    if rotation=='clockwise90': im=im.transpose(Image.Transpose.ROTATE_270)
    dest=PACK/meta['image']['path'];out=png(im);dest.write_bytes(out);meta['image']['sha256']=sha(out);meta['image']['rgba_sha256']=sha(struct.pack('>II',256,256)+im.tobytes())
    meta['provenance'].pop('source_crop_path',None);meta['provenance'].pop('source_crop_sha256',None)
    meta['provenance']['axis_remap']={'recipe':'reusable/views-additional/repair_dungeon_walls_nw_axes.py','source_asset_id':f'{OBJECT}.{src_view}','source_path':rp.relative_to(PACK).as_posix(),'source_sha256':sha(sb),'rotation':rotation}
    meta['provenance']['notes']='Inferred orthographic long-Y NW wall, remapped from atlas-reconstructed original projections using accepted Gameplay NW convention: front<-right, right<-rear, left<-front, rear<-left; TOP/BOTTOM clockwise 90°. Source stone material and block identity retained; not recovered pixels.'
    (PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');assets[aid]=meta
    original_sha=expected.get(dst_view)
    print(dst_view,'<-',src_view,rotation,'bbox',im.getchannel('A').getbbox(),'sha',meta['image']['sha256'],'source-matched',bool(original_sha))
g=groups[OBJECT];g['complete']=False;g['geometry_qa']={'status':'pending-review','views':list(MAPPING),'notes':'Long-Y axis remap awaits independent canonical source-plus-six review.','atlas_self_inspected':True};g['notes']='NW wall long-Y camera remap; pending independent review.'
(HERE/'raw/dungeon-stone-walls-nw-axis-remap.recipe.json').write_text(json.dumps({'method':'rebuild original six outputs from retained source atlas, then long-X to long-Y axis remap','object_id':OBJECT,'mapping':MAPPING,'source_hashes':{v:sha(data) for v,(path,data) in original.items()}},indent=2)+'\n')
idx['assets']=[assets[a['id']] for a in idx['assets']];idx['view_sets']=[groups[s['object_id']] for s in idx['view_sets']];INDEX.write_text(json.dumps(idx,indent=2)+'\n')
