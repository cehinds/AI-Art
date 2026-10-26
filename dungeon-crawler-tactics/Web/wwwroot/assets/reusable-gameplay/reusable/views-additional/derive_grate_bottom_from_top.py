"""Replay the symmetric open-grate underside from a retained top projection."""
from pathlib import Path
import hashlib,json,struct
from PIL import Image
HERE=Path(__file__).resolve().parent
PACK=HERE.parents[1]
OID='room-kit--overlays--grate'
INDEX=HERE/'set-index.json'
source=HERE/'raw'/f'grate-top-before-bottom-fix.png'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
image=Image.open(source).convert('RGBA').transpose(Image.Transpose.ROTATE_180)
index=json.loads(INDEX.read_text());assets={a['id']:a for a in index['assets']};sets={s['object_id']:s for s in index['view_sets']}
aid=f'{OID}.bottom';meta=dict(assets[aid]);out=PACK/meta['image']['path'];image.save(out,optimize=True)
meta['image']={'path':meta['image']['path'],'width':256,'height':256,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'rgba_sha256':hashlib.sha256(struct.pack('>II',256,256)+image.tobytes()).hexdigest()}
meta['anchor_px']=[128,128];meta['metadata_path']=(HERE/f'{aid}.json').relative_to(PACK).as_posix();provenance=dict(meta.get('provenance',{}));provenance.update({'method':'generated','source_image':f'reusable/native/{OID}.png','notes':'Inferred symmetric open-grate underside; derived by rigid 180-degree rotation of the retained open lattice TOP. Slots remain transparent, hidden reverse surfaces inferred.','symmetric_projection_derivation':{'source_view':'top','source_path':f'reusable/views-additional/raw/{source.name}','source_sha256':source_hash,'rotation':'180 degrees','recipe':'reusable/views-additional/derive_grate_bottom_from_top.py'}});meta['provenance']=provenance
(HERE/f'{aid}.json').write_text(json.dumps(meta,indent=2)+'\n');assets[aid]=meta;group=sets[OID];group['complete']=False;group['geometry_qa']={'status':'pending-review','views':['bottom'],'notes':'Open lattice transparency restored in the underside projection; independent source-plus-six review pending.','atlas_self_inspected':True};group['notes']='Targeted grate underside correction awaits independent review.'
index['assets']=list(assets.values());index['view_sets']=list(sets.values());INDEX.write_text(json.dumps(index,indent=2)+'\n');print(meta['image']['sha256'])
