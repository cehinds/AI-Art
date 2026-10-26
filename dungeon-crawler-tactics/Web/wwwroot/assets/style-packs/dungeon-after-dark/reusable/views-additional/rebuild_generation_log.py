"""Build the aggregate provenance log from atomically stored per-batch records."""
from pathlib import Path
import json, os
BASE=Path(__file__).resolve().parent
reqdir=BASE/'generation-requests'
records=[]
for p in sorted(reqdir.glob('*.json')):
    records.append(json.loads(p.read_text()))
out=BASE/'generation-log.json';tmp=out.with_name(out.name+'.tmp')
tmp.write_text(json.dumps({'batches':records},indent=2)+'\n');os.replace(tmp,out)
print(f'indexed {len(records)} generation requests')
