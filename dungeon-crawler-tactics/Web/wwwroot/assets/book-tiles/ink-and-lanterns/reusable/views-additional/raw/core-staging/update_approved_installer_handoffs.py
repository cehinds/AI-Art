from pathlib import Path
import json,hashlib,os
H=Path(__file__).resolve().parent;PACK=H.parents[3];REPORT=H/'staged-wall-candidates.json';d=json.loads(REPORT.read_text());by={s['object_id']:s for s in d['sets']};sha=lambda b:hashlib.sha256(b).hexdigest()
# Refresh prior handoffs from current staged candidate bytes, including canvas corrections.
for p in H.glob('installer-handoff--*.json'):
 x=json.loads(p.read_text());s=by[x['object_id']]
 for v,c in x.get('candidate_views',{}).items(): c.update(s['candidates'][v])
 x['contact_path']=s['contact_path'];x['contact_sha256']=s['contact_sha256']
 tmp=p.with_suffix('.json.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');os.replace(tmp,p)
# Newly accepted subsets. Preserve all unaffected directions by omitting them from candidate_views.
new=[
 ('surface-entry-urban-brick-wall-northeast',['front','top','bottom','rear'],'Root accepted the calibrated front/rear end elevations and the corrected 256×256 top/bottom candidates; right/left remain unchanged.'),
 ('bubble-glass-sand-coloured-glass-wall-northeast',['front','top','right','left','bottom','rear'],'Root accepted plain target-native front/rear endcourses plus the same-kit remaps for the remaining four directions.'),
 ('bubble-airship-riveted-scrap-hull-wall-northeast',['front','top','right','left','bottom','rear'],'Root accepted the six remapped directions with the porthole-free broad face mirrored from the accepted plain opposite face.'),
 ('bubble-sea-submarine-metal-hull-wall-northeast',['front','top','right','left','bottom','rear'],'Root accepted the six remapped directions with generated plain riveted broad faces replacing unsupported amber portholes.'),
]
for oid,views,decision in new:
 s=by[oid];p=H/f'installer-handoff--{oid}.json';x={'schema_version':1,'object_id':oid,'role':'staging-only-installer-handoff','status':'root-approved-candidate-directions-pending-live-install','write_scope':'book-tiles/ink-and-lanterns/reusable/views-additional/raw/core-staging','installer':'views_ink_books','reviewer':'root','source':s['source'],'source_actual_sha256':s['source_actual_sha256'],'current_views':s['current_views'],'nw_guide_id':s['nw_guide_id'],'nw_guide_status':s['nw_guide_status'],'candidate_views':{v:s['candidates'][v] for v in views},'contact_path':s['contact_path'],'contact_sha256':s['contact_sha256'],'decision':decision+' Directions absent from candidate_views remain unchanged. Recheck canonical NE source and all expected current view hashes before install; keep same-kit guide lineage separate. Staging worker made no live edits.'}
 p.write_text(json.dumps(x,indent=2)+'\n')
# Validate every handoff points at current source/view hashes and staged candidate bytes/canvas.
errors=[];checked=0
for p in H.glob('installer-handoff--*.json'):
 x=json.loads(p.read_text());s=by[x['object_id']]
 if x['source_actual_sha256']!=s['source_actual_sha256']:errors.append((p.name,'source'))
 for v,ref in x['current_views'].items():
  if ref['sha256']!=s['current_views'][v]['sha256']:errors.append((p.name,v,'base-hash'))
 for v,c in x['candidate_views'].items():
  f=H/c['candidate_path'];
  if sha(f.read_bytes())!=c['candidate_sha256']:errors.append((p.name,v,'candidate-hash'))
  from PIL import Image
  if Image.open(f).size!=(256,256):errors.append((p.name,v,'canvas'))
  checked+=1
print(json.dumps({'handoffs':len(list(H.glob('installer-handoff--*.json'))),'candidate_views_checked':checked,'errors':errors,'new':['installer-handoff--'+x[0]+'.json' for x in new]},indent=2))
if errors:raise SystemExit(1)
