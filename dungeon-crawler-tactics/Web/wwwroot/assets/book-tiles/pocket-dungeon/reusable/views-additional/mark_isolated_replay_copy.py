#!/usr/bin/env python3
"""Bind an isolated Pocket copy before its active outputs may be deleted."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys

OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--canonical-pack',required=True,type=Path,help='canonical Pocket book root; must differ from this copy')
ap.add_argument('--confirm-isolated-copy',action='store_true',help='explicitly confirm this target is a disposable copy')
args=ap.parse_args()
canonical=args.canonical_pack.resolve()
if not args.confirm_isolated_copy:raise SystemExit('pass --confirm-isolated-copy only for a disposable isolated copy')
if canonical==PACK.resolve():raise SystemExit('refusing to mark the canonical pack as an isolated copy')
baseline=OUT/'replay-baseline.json'
if not baseline.is_file():raise SystemExit('missing frozen replay-baseline.json')
# Run the strict, non-destructive preflight first; marker creation never permits
# changing or deleting an output that differs from the frozen snapshot.
subprocess.run([sys.executable,str(OUT/'prepare_replay_plan.py')],check=True)
b=json.loads(baseline.read_text());index=PACK/b['set_index_path']
marker={'schema':'pocket-isolated-replay-v1','isolated_pack_root':str(PACK.resolve()),'canonical_pack_root':str(canonical),'baseline_sha256':sha(baseline),'set_index_sha256':b['set_index_sha256'],'active_sets':len(b['sets']),'active_views':sum(len(g['views']) for g in b['sets']),'purpose':'authorize empty-output replay only inside this disposable copy; no canonical fallback is allowed'}
if sha(index)!=marker['set_index_sha256']:raise SystemExit('set-index changed during isolated-copy preflight')
path=OUT/'isolated-replay-marker.json';path.write_text(json.dumps(marker,indent=2)+'\n')
print(json.dumps({'marker':str(path),'baseline_sha256':marker['baseline_sha256'],'set_index_sha256':marker['set_index_sha256'],'isolated_pack_root':marker['isolated_pack_root']},indent=2))
