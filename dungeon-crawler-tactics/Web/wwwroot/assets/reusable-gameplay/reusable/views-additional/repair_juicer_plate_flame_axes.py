"""Foreshorten the world-X flame in side cameras and mirror the opposite rear face."""
from pathlib import Path
from PIL import Image
import hashlib,json,struct
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json';OID='concepts-boss-juicer-concept-flying-flaming-plate';RAW='reusable/views-additional/raw'
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha(p.read_bytes())
def rgba(im):return sha(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes())
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']}
# Snapshot each incoming direction before writes, retaining exact original files.
original={}
for v in ('front','right','left'):
 aid=f'{OID}.{v}';m=json.loads((PACK/assets[aid]['metadata_path']).read_text());src=PACK/m['image']['path'];data=src.read_bytes();path=PACK/f'{RAW}/juicer-flying-plate-{v}-before-flame-crop.png';path.write_bytes(data);original[v]={'bytes':data,'path':f'{RAW}/juicer-flying-plate-{v}-before-flame-crop.png','sha256':sha(data),'meta':m}
front=Image.open(__import__('io').BytesIO(original['front']['bytes'])).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT)
staged={}
# Rear is the opposite face; mirror the accepted front face so the world-X flame reverses in screen space.
for target,im,src,operation in [('rear',front,'front','horizontal-mirror-opposite-face')]:
 staged[target]=(im,original[src],operation,None)
# For orthographic side cameras the flame axis runs into/out of camera; retain only its compact ring at the rim.
for target,max_x in [('right',126),('left',120)]:
 base=Image.open(__import__('io').BytesIO(original[target]['bytes'])).convert('RGBA');pix=base.load()
 for y in range(base.height):
  for x in range(max_x+1,base.width):
   if pix[x,y][3]:pix[x,y]=(pix[x,y][0],pix[x,y][1],pix[x,y][2],0)
 staged[target]=(base,original[target],'alpha-clip-world-x-tail-to-end-on-profile',max_x)
summary={}
for target,(im,src,operation,max_x) in staged.items():
 aid=f'{OID}.{target}';meta=json.loads((PACK/assets[aid]['metadata_path']).read_text());proj_rel=f'{RAW}/juicer-flying-plate-{target}-final-projection.png';proj=PACK/proj_rel;im.save(proj,optimize=True);out=PACK/meta['image']['path'];out.write_bytes(proj.read_bytes());meta['image']['sha256']=file_sha(out);meta['image']['rgba_sha256']=rgba(im);recipe_rel=f'{RAW}/juicer-flying-plate-{target}-flame-axis.recipe.json';record={'operation':operation,'input_path':src['path'],'input_sha256':src['sha256'],'max_visible_x_px':max_x,'output_projection':proj_rel,'output_projection_sha256':file_sha(proj)};recipe={'object_id':OID,'target_view':target,'derivation':record,'notes':'Source flame tail runs along world X; opposite FRONT/REAR faces reverse screen direction, while RIGHT/LEFT look along the tail axis and show only its foreshortened edge glow.'};(PACK/recipe_rel).write_text(json.dumps(recipe,indent=2)+'\n');p=meta['provenance'];p.update({'method':'generated','source_crop_path':proj_rel,'source_crop_sha256':file_sha(proj),'generation_recipe':recipe_rel,'crop_bounds_px':{'selection_mode':'retained_projection_geometry_cleanup','resized_bounds_px':[256,256],'canvas_offset_px':[0,0],'anchor_px':[128,128]},'projection_remap':record,'notes':'Inferred orthographic projection of an upright spinning fire plate. The world-X flame is reversed on the rear face and foreshortened in side cameras; hidden fire surfaces are not recovered.'});(PACK/assets[aid]['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');assets[aid]=meta;summary[target]={'sha256':meta['image']['sha256'],'rgba_sha256':meta['image']['rgba_sha256'],'bbox':im.getchannel('A').getbbox(),'operation':operation}
for g in idx['view_sets']:
 if g['object_id']==OID:g['complete']=False;g['geometry_qa']={'status':'pending-review','views':['rear','right','left'],'atlas_self_inspected':True,'notes':'Rear world-X flame reversal and foreshortened side flame await independent review; front/top/bottom preserved.'};g['notes']='Targeted rear-face reversal and side flame foreshortening; accepted front/top/bottom and disc geometry retained.'
idx['assets']=[assets[a['id']] for a in idx['assets']];INDEX.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps(summary,indent=2))
