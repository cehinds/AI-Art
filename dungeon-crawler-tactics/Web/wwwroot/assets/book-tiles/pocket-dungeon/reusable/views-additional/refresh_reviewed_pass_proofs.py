#!/usr/bin/env python3
"""Refresh pack-local pass proofs from current independent Pocket QA ledgers."""
from pathlib import Path
import hashlib,json
PACK=Path(__file__).resolve().parents[2]
OUT=PACK/'reusable/views-additional'
LEDGERS=[Path('/workspace/scratch/view-qa-report.json'),Path('/workspace/scratch/view-qa-root.json')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def timekey(r):return r.get('reviewed_at') or ''
latest={}
for lp in LEDGERS:
 if not lp.is_file():continue
 d=json.loads(lp.read_text())
 for key,r in d.get('reviewed',{}).items():
  if not key.startswith('book-tiles/pocket-dungeon::'):continue
  oid=key.split('::',1)[1]
  if not all(k in r for k in ('source','source_sha256','view_paths','image_hashes')):continue
  prev=latest.get(oid)
  rec={'status':r.get('status'),'reviewer':r.get('reviewer',lp.name),'reviewed_at':r.get('reviewed_at'),'source':r['source'],'source_sha256':r['source_sha256'],'view_paths':r['view_paths'],'image_hashes':r['image_hashes'],'ledger':str(lp)}
  if prev is None or timekey(rec)>=timekey(prev):latest[oid]=rec
proofs={};decisions={}
for oid,r in latest.items():
 current_source=Path(r['source']).is_file() and sha(r['source'])==r['source_sha256']
 current_views=set(r['view_paths'])=={'front','top','right','left','bottom','rear'}
 if current_views:
  current_views=all(Path(r['view_paths'][v]).is_file() and sha(r['view_paths'][v])==r['image_hashes'].get(v) for v in r['view_paths'])
 status=r['status']
 decisions[oid]={'status':status,'reviewer':r['reviewer'],'reviewed_at':r['reviewed_at'],'ledger':r['ledger'],'source_current':bool(current_source),'views_current':bool(current_views)}
 if status=='pass' and current_source and current_views:
  proofs[oid]={'status':'pass','reviewer':r['reviewer'],'reviewed_at':r['reviewed_at'],'source_path':Path(r['source']).relative_to(PACK).as_posix(),'source_sha256':r['source_sha256'],'image_hashes':r['image_hashes']}
out={'schema_version':1,'provenance':'Latest independent reviewer decisions selected by reviewed_at from the current Pocket QA ledgers; only PASS decisions whose source and all six current PNG hashes match are usable.','ledgers':[str(p) for p in LEDGERS],'proofs':proofs,'latest_decisions':decisions}
p=OUT/'reviewed-pass-proofs.json';p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'latest_decisions':len(decisions),'current_pass_proofs':len(proofs),'output':str(p)},indent=2))
