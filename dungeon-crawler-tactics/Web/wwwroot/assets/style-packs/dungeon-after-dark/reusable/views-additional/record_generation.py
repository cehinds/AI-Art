"""Record a generated atlas mapping and preserve the raw output for offline rebuilds."""
from pathlib import Path
import argparse, hashlib, json, os, shutil
BASE = Path(__file__).resolve().parent
REQ = BASE / 'generation-requests'
LOG = BASE / 'generation-log.json'
p = argparse.ArgumentParser()
p.add_argument('--batch', required=True)
p.add_argument('--generated', required=True)
a = p.parse_args()
req_path = REQ / f'{a.batch}.json'
if not req_path.exists():
    raise SystemExit(f'missing persisted request: {req_path}')
req = json.loads(req_path.read_text())
src = Path(a.generated).resolve()
if not src.is_file():
    raise SystemExit(f'generated file missing: {src}')
dest = BASE / req['raw_path']
dest.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(src, dest)
req.update({'status':'generated','generated_file':str(src),'raw_path':str(dest.relative_to(BASE)),
            'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size})
tmp = req_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(req,indent=2)+'\n');os.replace(tmp,req_path)
print(f"recorded {a.batch}: {req['raw_path']} sha256={req['sha256']}")
