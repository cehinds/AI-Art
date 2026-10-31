"""Occlude chest boxes above the opaque display support in the bottom view."""
from pathlib import Path
from PIL import Image
import hashlib,json,struct
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json';OID='concepts-progression-safe-room-loot-chest-stack';VIEW='bottom';RAW='reusable/views-additional/raw';CUT_Y=86
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha(p.read_bytes())
def rgba(im):return sha(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes())
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};aid=f'{OID}.{VIEW}';meta=json.loads((PACK/assets[aid]['metadata_path']).read_text());out=PACK/meta['image']['path'];before=out.read_bytes();source_rel=f'{RAW}/progression-loot-stack-bottom-before-occlusion.png';source=PACK/source_rel;source.write_bytes(before);im=Image.open(source).convert('RGBA');pix=im.load()
for y in range(CUT_Y):
 for x in range(im.width):
  r,g,b,a=pix[x,y]
  if a:pix[x,y]=(r,g,b,0)
projection_rel=f'{RAW}/progression-loot-stack-bottom-occluded-projection.png';projection=PACK/projection_rel;im.save(projection,optimize=True);recipe_rel=f'{RAW}/progression-loot-stack-bottom-occlusion.recipe.json';rec={'operation':'orthographic-occlusion-mask','object_id':OID,'view':VIEW,'input_path':source_rel,'input_sha256':file_sha(source),'mask':'set alpha to zero for y < cut_y; preserve support underside at/under far tabletop edge','cut_y_px':CUT_Y,'output_projection':projection_rel,'output_projection_sha256':file_sha(projection),'notes':'Opaque support tabletop hides all five chest bodies from below; the wooden support underside and legs remain visible.'};(PACK/recipe_rel).write_text(json.dumps(rec,indent=2)+'\n');out.write_bytes(projection.read_bytes());meta['image']['sha256']=file_sha(out);meta['image']['rgba_sha256']=rgba(im);p=meta['provenance'];p.update({'source_crop_path':projection_rel,'source_crop_sha256':file_sha(projection),'generation_recipe':recipe_rel,'crop_bounds_px':{'selection_mode':'occlusion-mask-retained-projection','resized_bounds_px':[256,256],'canvas_offset_px':[0,0],'anchor_px':[128,128]},'projection_remap':rec,'notes':'Inferred bottom projection of the wooden support; opaque tabletop occludes the five chest bodies above. Hidden wood construction is illustrative.'});(PACK/assets[aid]['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');assets[aid]=meta
for g in idx['view_sets']:
 if g['object_id']==OID:g['complete']=False;g['geometry_qa']={'status':'pending-review','views':['bottom'],'atlas_self_inspected':True,'notes':'Upper chest silhouettes removed behind opaque support; awaiting independent review.'};g['notes']='Five-box stack preserved; bottom view corrected for opaque support occlusion.'
idx['assets']=[assets[a['id']] for a in idx['assets']];INDEX.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps({'input_sha256':sha(before),'output_sha256':meta['image']['sha256'],'bbox':im.getchannel('A').getbbox(),'cut_y_px':CUT_Y},indent=2))
