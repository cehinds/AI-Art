"""Use the accepted fixed-tilt lever projection for its unmarked symmetric rear."""
from pathlib import Path
from PIL import Image
import hashlib,json,struct
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json';OID='room-kit--props--lever'
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha(p.read_bytes())
def rgba(im):return sha(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes())
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']}
front_path=PACK/assets[f'{OID}.front']['image']['path'];front_bytes=front_path.read_bytes();front_raw_rel='reusable/views-additional/raw/room-kit-lever-front-mirror-input.png';front_raw=PACK/front_raw_rel;front_raw.write_bytes(front_bytes)
projection=Image.open(front_raw).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT)
proj_rel='reusable/views-additional/raw/room-kit-lever-rear-mirrored-projection.png';proj=PACK/proj_rel;projection.save(proj,optimize=True)
recipe_rel='reusable/views-additional/raw/room-kit-lever-rear-mirror.recipe.json'
recipe={'operation':'horizontal-mirror-of-accepted-opposite-elevation','input_image_id':f'{OID}.front','input_path':front_raw_rel,'input_sha256':file_sha(front_raw),'operation_detail':'PIL Image.Transpose.FLIP_LEFT_RIGHT about the 128px vertical anchor; geometry is symmetric/unmarked','output_projection':proj_rel,'output_projection_sha256':file_sha(proj),'output_id':f'{OID}.rear','notes':'Front and rear share the fixed diagonal lever tilt, mirrored across the vertical axis. Hidden rear surfaces are inferred; this is a geometric derivation, not recovered pixels.'}
(PACK/recipe_rel).write_text(json.dumps(recipe,indent=2)+'\n')
aid=f'{OID}.rear';meta=json.loads((PACK/assets[aid]['metadata_path']).read_text());out=PACK/meta['image']['path'];out.write_bytes(proj.read_bytes());meta['image']['sha256']=file_sha(out);meta['image']['rgba_sha256']=rgba(projection)
p=meta['provenance'];p.update({'method':'generated','source_image':'reusable/sources/room-kit/props/lever.png','generation_recipe':recipe_rel,'source_crop_path':proj_rel,'source_crop_sha256':file_sha(proj),'crop_bounds_px':{'selection_mode':'retained_mirrored_projection','resized_bounds_px':[256,256],'canvas_offset_px':[0,0],'anchor_px':[128,128]},'projection_derivation':{'input_path':front_raw_rel,'input_sha256':file_sha(front_raw),'operation':'horizontal-mirror','notes':'Unmarked lever geometry supports same fixed tilt from the opposite end.'},'notes':'Inferred rear orthographic projection derived by horizontal mirroring of the accepted front view; same diagonal fixed lever tilt, not upright. Hidden rear details are not recovered pixels.'})
(PACK/assets[aid]['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');assets[aid]=meta
for g in idx['view_sets']:
 if g['object_id']==OID:g['complete']=False;g['geometry_qa']={'status':'pending-review','views':['rear'],'atlas_self_inspected':True,'notes':'Rear fixed-tilt projection derived by horizontal reflection of accepted FRONT; awaits independent review.'}
idx['assets']=[assets[a['id']] for a in idx['assets']];INDEX.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps({'rear_sha256':meta['image']['sha256'],'projection_sha256':file_sha(proj),'source_sha256':file_sha(front_raw)},indent=2))
