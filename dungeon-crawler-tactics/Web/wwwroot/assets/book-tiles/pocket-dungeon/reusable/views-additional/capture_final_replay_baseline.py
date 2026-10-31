#!/usr/bin/env python3
"""Capture immutable expected Pocket replay bytes. Run only after the art queue is frozen."""
from pathlib import Path
import argparse,hashlib,json,struct
from PIL import Image
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--confirm-frozen',action='store_true');ap.add_argument('--replace',action='store_true');args=ap.parse_args()
if not args.confirm_frozen:raise SystemExit('refusing baseline capture; pass --confirm-frozen only after art freeze')
path=OUT/'replay-baseline.json'
if path.exists() and not args.replace:raise SystemExit('baseline already exists; use --replace only for a new explicitly frozen snapshot')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());assetmap={a['id']:a for a in idx['assets']};sets=[];sources={}
active_output_paths={idxp.relative_to(PACK).as_posix()}
for group in idx['view_sets']:
 views={}
 for view,aid in group.get('views',{}).items():
  a=assetmap.get(aid)
  if not a:raise SystemExit(f'missing index asset: {aid}')
  png=PACK/a['image']['path'];meta=PACK/a['metadata_path'];md=json.loads(meta.read_text());source_path=md.get('provenance',{}).get('source_image')
  active_output_paths.update((a['image']['path'],a['metadata_path']))
  if not source_path:raise SystemExit(f'missing source provenance: {aid}')
  source=PACK/source_path
  if not png.is_file() or not meta.is_file() or not source.is_file():raise SystemExit(f'missing file for {aid}')
  sources[source_path]=sha(source)
  views[view]={'asset_id':aid,'image_path':a['image']['path'],'image_sha256':sha(png),'rgba_sha256':rgba_sha(png),'metadata_path':a['metadata_path'],'metadata_sha256':sha(meta),'provenance':md.get('provenance',{})}
 if set(views)!={'front','top','right','left','bottom','rear'}:
  # Missing art remains explicit in the snapshot; do not create false six-view completeness.
  pass
 if set(views)!={'front','top','right','left','bottom','rear'}: raise SystemExit(f'{group["object_id"]}: expected all six principal PNGs before freeze')
 sets.append({'object_id':group['object_id'],'views':views,'complete':group.get('complete',False),'geometry_qa':group.get('geometry_qa')})
if len(sets)!=744 or sum(len(s['views']) for s in sets)!=4464: raise SystemExit(f'expected 744 sets/4,464 views, found {len(sets)}/{sum(len(s["views"]) for s in sets)}')
# Capture all authored replay inputs so stale recipes or atlases fail preflight.
inputs={}
transient_names={'replay-baseline.json','replay-plan.json','qa-replay-results.json','replay-run-result.json','isolated-replay-marker.json'}
for p in OUT.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts:continue
 if p.relative_to(PACK).as_posix() in active_output_paths:continue
 if p.name in transient_names:continue
 # These are generated bookkeeping outputs of the atlas splitter, not its inputs.
 if p.parent==OUT/'raw/atlases' and p.name.endswith('.recipe.json'):continue
 inputs[p.relative_to(PACK).as_posix()]=sha(p)
for p in PACK.glob('*/manifest.json'):inputs[p.relative_to(PACK).as_posix()]=sha(p)
for p in PACK.glob('*/components/*.png'):sources[p.relative_to(PACK).as_posix()]=sha(p)
for p in PACK.rglob('components/*.png'):
 if p.is_file():sources[p.relative_to(PACK).as_posix()]=sha(p)
record={'schema_version':1,'scope':'Pocket book full replay expected output bytes','captured_after_freeze':True,'set_index_path':idxp.relative_to(PACK).as_posix(),'set_index_sha256':sha(idxp),'sets':sets,'sources':sources,'replay_inputs':inputs,'counts':{'sets':len(sets),'views':sum(len(s['views']) for s in sets),'png_files':sum(len(s['views']) for s in sets),'sidecars':sum(len(s['views']) for s in sets)}}
path.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'path':str(path),'sets':len(sets),'views':record['counts']['views'],'sources':len(sources),'inputs':len(inputs)},indent=2))
