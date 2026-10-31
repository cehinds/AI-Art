#!/usr/bin/env python3
"""Finalize the held curb candidates against the current three-object source-six proof."""
from pathlib import Path
import json,hashlib
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
C=ROOT/'reusable/views-additional/candidates/equipment-dark-six-ground-platforms-20261026'
PROOF=Path('/tmp/page-qa-ground-curb-native-basis-current-20261026-01.png.json')
CONTACT=C/'contacts/source-six-candidate-v7.png'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=json.loads((C/'candidate-manifest-v7.json').read_text())
proof=json.loads(PROOF.read_text()); byproof={o['object_id']:o for o in proof['objects']}
keep={'over-city-city-cobblestone-corner-transition','over-city-city-cobblestone-edge-transition','over-city-venues-civic-stone-tile-corner-transition'}
d=base
d['candidate_id']='equipment-dark-six-ground-platforms-v8'
d['normalizer_path']='reusable/views-additional/candidates/equipment-dark-six-ground-platforms-20261026/raw/finalize_ground_candidates_v8.py'
d['normalizer_sha256']=sha(__file__)
d['current_source_six_proof_path']=str(PROOF); d['current_source_six_proof_sha256']=sha(PROOF)
d['candidate_contact_path']=str(CONTACT); d['candidate_contact_sha256']=sha(CONTACT)
d['sets']=[s for s in d['sets'] if s['object_id'] in keep]
assert len(d['sets'])==3
for s in d['sets']:
 o=byproof[s['object_id']]
 assert sha(o['source']['path'])==o['source']['sha256']==s['source_sha256']
 s['base_current_views']={v:{'path':x['path'],'sha256':x['sha256']} for v,x in o['views'].items()}
 s['base_proof_path']=str(PROOF); s['base_proof_sha256']=sha(PROOF)
 for v,c in s['candidates'].items(): assert sha(c['path'])==c['sha256'],(s['object_id'],v)
# The candidate rows in the contact follow SOURCE + front/top/right/left/bottom/rear.
out=C/'candidate-manifest-v8.json';out.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({'manifest':str(out),'manifest_sha256':sha(out),'contact':str(CONTACT),'contact_sha256':sha(CONTACT),'script_sha256':sha(__file__),'sets':len(d['sets']),'directions':sum(len(s['candidates']) for s in d['sets'])},indent=2))
