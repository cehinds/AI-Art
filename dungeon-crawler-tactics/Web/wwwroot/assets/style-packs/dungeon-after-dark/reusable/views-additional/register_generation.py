"""Persist generation request details before calling imagegen."""
from pathlib import Path
import argparse, json, os
BASE = Path(__file__).resolve().parent
REQ = BASE / 'generation-requests'
p = argparse.ArgumentParser()
p.add_argument('--batch', required=True)
p.add_argument('--contact', required=True)
p.add_argument('--prompt', required=True)
p.add_argument('--raw', required=True)
a = p.parse_args()
contact = Path(a.contact)
prompt = Path(a.prompt)
if not (BASE / contact).is_file(): raise SystemExit(f'missing contact {contact}')
if not (BASE / prompt).is_file(): raise SystemExit(f'missing prompt {prompt}')
req={'batch_id':a.batch,'status':'pending','source_contact':str(contact),'prompt_path':str(prompt),
     'prompt_text':(BASE/prompt).read_text(),'raw_path':a.raw}
REQ.mkdir(parents=True,exist_ok=True)
out=REQ/f'{a.batch}.json';tmp=out.with_suffix('.json.tmp');tmp.write_text(json.dumps(req,indent=2)+'\n');os.replace(tmp,out)
print(f'registered {a.batch} with source, prompt and destination')
