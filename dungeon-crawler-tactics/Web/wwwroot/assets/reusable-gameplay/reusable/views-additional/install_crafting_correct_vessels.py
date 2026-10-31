"""Install the open metal vessel and closed storage box using source-faithful views."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json';ATLAS_REL='reusable/views-additional/raw/crafting-correct-vessels-atlas.png';REQ='exec-97df9931-7886-4eae-9605-d2251fc589e3';TH=245
ROWS=[('menu-concepts-safe-room-services--crafting-copper-pot',0),('menu-concepts-safe-room-services--crafting-bench-vise',1)]
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha(p.read_bytes())
def rgba(im):return sha(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes())
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};atlasp=PACK/ATLAS_REL;atlas=Image.open(atlasp).convert('RGBA');a=np.asarray(atlas);labels,_=ndimage.label(a[:,:,3]>=TH,np.ones((3,3),dtype=np.uint8));summary={}
for oid,row in ROWS:
 base=Image.open(PACK/assets[f'{oid}.front']['image']['path']).convert('RGBA').getchannel('A').getbbox();target_z=base[3]-base[1];scale=None
 for col,view in enumerate(('front','top','right','left','bottom','rear')):
  x0=round(col*atlas.width/6);x1=round((col+1)*atlas.width/6);y0=round(row*atlas.height/2);y1=round((row+1)*atlas.height/2);local=labels[y0:y1,x0:x1];counts=np.bincount(local.ravel());counts[0]=0;lab=int(counts.argmax());ys,xs=np.where(local==lab);sx=int(xs[len(xs)//2]+x0);sy=int(ys[len(ys)//2]+y0);glab=int(labels[sy,sx]);ys,xs=np.where(labels==glab);bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];mask=labels[bounds[1]:bounds[3],bounds[0]:bounds[2]]==glab;piece=atlas.crop(tuple(bounds));piece.putalpha(Image.fromarray((mask*255).astype(np.uint8)))
  if scale is None:scale=target_z/piece.height
  size=(max(1,round(piece.width*scale)),max(1,round(piece.height*scale)));piece=piece.resize(size,Image.Resampling.NEAREST);slug=oid.rsplit('--',1)[-1];crop_rel=f'reusable/views-additional/raw/{slug}-{view}-corrected-projection.png';crop=PACK/crop_rel;piece.save(crop,optimize=True);offset=(128-size[0]//2,128-size[1]//2);frame=Image.new('RGBA',(256,256));frame.alpha_composite(piece,offset);aid=f'{oid}.{view}';meta=json.loads((PACK/assets[aid]['metadata_path']).read_text());out=PACK/meta['image']['path'];frame.save(out,optimize=True);rec_rel=f'reusable/views-additional/raw/{slug}-{view}-corrected.recipe.json';
  if oid.endswith('copper-pot'):
   note='Source-faithful inferred orthographic view of an open, straight-sided gray-purple cylindrical metal vessel with pale rim and side handles; TOP is open with dark interior, no lid or rounded kettle belly. Hidden underside details are illustrative.'
  else:
   note='Source-faithful inferred orthographic view of a small closed dark rectangular storage box/cabinet with lid seams and corner hardware; it is not a vise and has no jaws, crank, or threaded rod. Hidden surfaces are illustrative.'
  meta['image']['sha256']=file_sha(out);meta['image']['rgba_sha256']=rgba(frame);p=meta['provenance'];p.update({'method':'generated','source_atlas':ATLAS_REL,'source_atlas_sha256':file_sha(atlasp),'generation_request_id':REQ,'generation_recipe':rec_rel,'source_crop_path':crop_rel,'source_crop_sha256':file_sha(crop),'crop_bounds_px':{'selection_mode':'global_alpha_component','alpha_threshold':TH,'global_component_label':glab,'alpha_bounds_global':bounds,'atlas_cell':{'column':col,'row':row,'columns':6,'rows':2},'common_uniform_scale':scale,'resized_bounds_px':list(size),'canvas_offset_px':list(offset),'anchor_px':[128,128]},'notes':note})
  rec={'operation':'extract-global-alpha-component-common-uniform-scale','request_id':REQ,'input_atlas':ATLAS_REL,'input_sha256':file_sha(atlasp),'alpha_threshold':TH,'cell':{'column':col,'row':row,'columns':6,'rows':2},'global_component_label':glab,'component_bounds_px':bounds,'common_uniform_scale':scale,'target_height_from_existing_front_px':target_z,'resized_bounds_px':list(size),'canvas_offset_px':list(offset),'anchor_px':[128,128],'source_image':p.get('source_image'),'output_crop':crop_rel,'output_id':aid,'notes':note};(PACK/rec_rel).write_text(json.dumps(rec,indent=2)+'\n');(PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');assets[aid]=meta;summary[aid]={'size':size,'bbox':frame.getchannel('A').getbbox(),'sha256':meta['image']['sha256']}
for g in idx['view_sets']:
 for oid,_ in ROWS:
  if g['object_id']==oid:g['complete']=False;g['geometry_qa']={'status':'pending-review','views':['front','top','right','left','bottom','rear'],'atlas_self_inspected':True,'notes':'Open cylindrical vessel / closed storage box source-identity corrections await independent review.'};g['notes']='All six projections refreshed to source appearance; hidden construction remains inferred.'
idx['assets']=[assets[x['id']] for x in idx['assets']];INDEX.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps(summary,indent=2))
