"""Re-key existing disc-face and edge projections into a coherent upright disc basis."""
from pathlib import Path
import hashlib,json,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json';OID='concepts-boss-juicer-concept-flying-flaming-plate';RAW='reusable/views-additional/raw';mapping={'front':'top','top':'front','right':'right','left':'left','bottom':'rear','rear':'bottom'}
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha(p.read_bytes())
def rgba(im):return sha(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes())
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};snapshots={}
# Snapshot and hash all six originals before touching any live view path.
for view in ('front','top','right','left','bottom','rear'):
 aid=f'{OID}.{view}';meta=json.loads((PACK/assets[aid]['metadata_path']).read_text());src=PACK/meta['image']['path'];data=src.read_bytes();snap_rel=f'{RAW}/juicer-flying-plate-original-{view}.png';snap=PACK/snap_rel;snap.write_bytes(data);snapshots[view]={'bytes':data,'sha256':sha(data),'snapshot_path':snap_rel,'metadata':meta}
# Stage transformed bytes in memory, with a retained 256px source projection for replay.
staged={}
for target,source in mapping.items():
 item=snapshots[source];im=Image.open(__import__('io').BytesIO(item['bytes'])).convert('RGBA');aid=f'{OID}.{target}';meta=json.loads((PACK/assets[aid]['metadata_path']).read_text());projection_rel=f'{RAW}/juicer-flying-plate-{target}-axis-projection.png';projection=PACK/projection_rel
 # Separate raw projection copy is never the live destination; it is the deterministic replay source.
 projection.write_bytes(item['bytes']);record={'target':target,'source':source,'source_path':item['snapshot_path'],'source_sha256':item['sha256'],'projection_path':projection_rel,'projection_sha256':file_sha(projection)}
 rec_rel=f'{RAW}/juicer-flying-plate-{target}-axis-remap.recipe.json';rec={'operation':'rekey-existing-orthographic-projection','object_id':OID,'mapping':record,'mapping_all_views':mapping,'all_original_view_hashes':{v:s['sha256'] for v,s in snapshots.items()},'notes':'The upright disc has its broad plane on FRONT/REAR and edge-on profiles on TOP/BOTTOM; views are re-keyed from the same fixed pose. This is a deterministic projection remap, not new recovered pixels.'};(PACK/rec_rel).write_text(json.dumps(rec,indent=2)+'\n')
 meta['image']['sha256']=file_sha(projection);meta['image']['rgba_sha256']=rgba(im);p=meta['provenance'];p.update({'method':'generated','source_image':p.get('source_image'),'generation_recipe':rec_rel,'source_crop_path':projection_rel,'source_crop_sha256':file_sha(projection),'crop_bounds_px':{'selection_mode':'retained_projection_remap','resized_bounds_px':[256,256],'canvas_offset_px':[0,0],'anchor_px':[128,128]},'projection_remap':record,'notes':'Inferred orthographic projection of the same upright rolling fire plate. Re-keyed from an existing generated view to establish the fixed vertical-disc basis; hidden surfaces are illustrative, not recovered.'});staged[target]=(meta,projection.read_bytes(),rec_rel)
# Atomically install each staged PNG and matching metadata/index entries.
for target,(meta,data,rec_rel) in staged.items():
 out=PACK/meta['image']['path'];tmp=out.with_suffix(out.suffix+'.tmp');tmp.write_bytes(data);tmp.replace(out);(PACK/assets[f'{OID}.{target}']['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');assets[f'{OID}.{target}']=meta
for g in idx['view_sets']:
 if g['object_id']==OID:g['complete']=False;g['geometry_qa']={'status':'pending-review','views':['front','top','bottom','rear'],'atlas_self_inspected':True,'notes':'Disc-face/edge projections were re-keyed into the upright source basis; independent review required.'};g['notes']='Targeted axis remap of front/top/bottom/rear; right/left retained.'
idx['assets']=[assets[a['id']] for a in idx['assets']];INDEX.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps({'object_id':OID,'mapping':mapping,'original_hashes':{v:s['sha256'] for v,s in snapshots.items()},'new_hashes':{v:staged[v][0]['image']['sha256'] for v in staged}},indent=2))
