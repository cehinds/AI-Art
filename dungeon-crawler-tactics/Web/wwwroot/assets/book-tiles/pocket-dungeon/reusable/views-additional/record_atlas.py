#!/usr/bin/env python3
"""Retain a generated book atlas and register pack-relative source/provenance.
Usage: python3 record_atlas.py ATLAS KIT BATCH REF_SHEET PROMPT_FILE OBJECT_ID...
"""
from pathlib import Path
import argparse,hashlib,json,shutil
from PIL import Image
OUT=Path(__file__).resolve().parent; BOOK=OUT.parents[1]
p=argparse.ArgumentParser();p.add_argument('atlas');p.add_argument('kit');p.add_argument('batch',type=int);p.add_argument('ref_sheet');p.add_argument('prompt_file');p.add_argument('objects',nargs='+');a=p.parse_args()
if len(a.objects)!=6: raise SystemExit('each atlas must map exactly six object IDs')
src=Path(a.atlas); rawdir=OUT/'raw'/'atlases'; rawdir.mkdir(parents=True,exist_ok=True)
raw=rawdir/f'{a.kit}-batch-{a.batch:02d}.png';shutil.copyfile(src,raw)
im=Image.open(raw)
entry={'kit':a.kit,'batch':a.batch,'raw':raw.relative_to(BOOK).as_posix(),'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'width':im.width,'height':im.height,'grid':{'columns':6,'rows':6,'view_order':['front','top','right','left','bottom','rear']},'objects':[{'object_id':oid,'row':i,'source_image':f'{a.kit}/components/{oid}.png'} for i,oid in enumerate(a.objects)],'reference_sheet':Path(a.ref_sheet).relative_to(BOOK).as_posix(),'prompt_file':Path(a.prompt_file).relative_to(BOOK).as_posix(),'tool':'image_gen.imagegen','transparent_background':True}
records=OUT/'raw'/'generation.json'; data=json.loads(records.read_text()) if records.exists() else []
data=[x for x in data if (x['kit'],x['batch'])!=(a.kit,a.batch)];data.append(entry);data.sort(key=lambda x:(x['kit'],x['batch']));records.write_text(json.dumps(data,indent=2)+'\n')
progress=OUT/'progress.json'
if progress.exists():
 q=json.loads(progress.read_text())
 for b in q['batches']:
  if b['kit']==a.kit and b['batch']==a.batch:
   b.update({'status':'complete','raw_atlas':raw.relative_to(BOOK).as_posix(),'source_sheet':entry['reference_sheet'],'prompt_file':entry['prompt_file']})
 q['complete_batches']=sum(b['status']=='complete' for b in q['batches'])
 q['complete_objects']=sum(len(b['object_ids']) for b in q['batches'] if b['status']=='complete')
 progress.write_text(json.dumps(q,indent=2)+'\n')
print(raw.relative_to(BOOK),entry['sha256'])
