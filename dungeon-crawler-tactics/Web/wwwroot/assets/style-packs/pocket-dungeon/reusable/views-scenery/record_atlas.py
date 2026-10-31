#!/usr/bin/env python3
"""Retain a generated 6x3 atlas and its pack-relative extraction recipe.
Usage: python3 record_atlas.py /path/to/atlas.png object-id object-id object-id
"""
from pathlib import Path
import hashlib,json,sys
from PIL import Image
OUT=Path(__file__).resolve().parent; PACK=OUT.parents[1]; RAW=OUT/'raw'
if len(sys.argv) not in (3,5): raise SystemExit('expected ATLAS and one or three object IDs')
source=Path(sys.argv[1]); ids=sys.argv[2:]
if len(ids) not in (1,3): raise SystemExit('atlas must have one or three object rows')
raw=RAW/source.name; raw.parent.mkdir(exist_ok=True); raw.write_bytes(source.read_bytes())
im=Image.open(raw); d={'file':raw.relative_to(PACK).as_posix(),'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'width':im.width,'height':im.height,'grid':{'columns':6,'rows':len(ids),'order':['front','top','right','left','bottom','rear']},'objects':[{'object_id':oid,'row':row,'source_image':f'components/{oid}.png'} for row,oid in enumerate(ids)],'generation':{'method':'image_gen.imagegen','transparent_background':True,'notes':'Generated orthographic views from attached source component images; hidden surfaces inferred.'}}
meta=raw.with_suffix('.provenance.json'); meta.write_text(json.dumps(d,indent=2)+'\n'); print(meta.relative_to(PACK))
