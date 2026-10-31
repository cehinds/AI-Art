#!/usr/bin/env python3
"""Compare an isolated replay against every frozen Pocket PNG, RGBA, sidecar, index, and source hash."""
from pathlib import Path
import argparse,hashlib,json,struct
from PIL import Image
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,default=OUT/'replay-baseline.json');args=ap.parse_args()
b=json.loads(args.baseline.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
errors=[];checked_png=checked_rgba=checked_meta=checked_sources=0
idxp=PACK/b['set_index_path']
if not idxp.is_file() or sha(idxp)!=b['set_index_sha256']:errors.append('set-index mismatch')
for rel,h in b['sources'].items():
 p=PACK/rel;checked_sources+=1
 if not p.is_file() or sha(p)!=h:errors.append(f'source mismatch: {rel}')
for group in b['sets']:
 for view,v in group['views'].items():
  p=PACK/v['image_path'];m=PACK/v['metadata_path'];checked_png+=1;checked_rgba+=1;checked_meta+=1
  if not p.is_file():errors.append(f'missing PNG: {v["image_path"]}');continue
  if sha(p)!=v['image_sha256']:errors.append(f'PNG SHA mismatch: {v["image_path"]}')
  if rgba_sha(p)!=v['rgba_sha256']:errors.append(f'RGBA SHA mismatch: {v["image_path"]}')
  if not m.is_file() or sha(m)!=v['metadata_sha256']:errors.append(f'metadata SHA mismatch: {v["metadata_path"]}')
print(json.dumps({'sets':len(b['sets']),'png_hashes_checked':checked_png,'rgba_hashes_checked':checked_rgba,'metadata_hashes_checked':checked_meta,'source_hashes_checked':checked_sources,'differences':len(errors),'first_differences':errors[:80]},indent=2))
if errors:raise SystemExit(1)
