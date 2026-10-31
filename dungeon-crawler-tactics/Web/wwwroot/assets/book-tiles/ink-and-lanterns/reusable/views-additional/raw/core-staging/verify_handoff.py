from pathlib import Path
import hashlib,json
PACK=Path(__file__).resolve().parents[4]
HANDOFF=Path('/workspace/scratch/inkbook-core-ne-wall-staging-handoff.json')
MERGED=Path('/workspace/scratch/view-review-merged.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
h=json.loads(HANDOFF.read_text()); merged=json.loads(MERGED.read_text()); lib=next(x for x in merged['libraries'] if x['scope']=='book-tiles/ink-and-lanterns'); qsets={x['object_id']:x for x in lib['sets']}
results=[]
for item in h['sets']:
 oid=item['object_id']; source=PACK/item['source']['path']; source_sha=sha(source); ok=source_sha==item['source']['sha256']
 views={}
 for view,rec in item['current_views'].items():
  p=PACK/rec['path']; got=sha(p); views[view]={'path':rec['path'],'expected_sha256':rec['sha256'],'actual_sha256':got,'matches_handoff':got==rec['sha256']};ok &= got==rec['sha256']
 nwid=item['suggested_same_kit_nw_object']; nw=qsets.get(nwid); nwviews={}
 for view,rec in (nw or {}).get('views',{}).items():
  nwpath=PACK/rec['path']; got=sha(nwpath); nwviews[view]={'path':rec['path'],'sha256':got,'handoff_sha256':rec['sha256'],'matches':got==rec['sha256']}
 results.append({'object_id':oid,'source_path':item['source']['path'],'source_sha256':source_sha,'source_matches_handoff':source_sha==item['source']['sha256'],'views':views,'nw_guide_id':nwid,'nw_guide_status':(nw or {}).get('status'),'nw_guide_views':nwviews,'all_ne_hashes_match':bool(ok)})
report={'handoff_path':str(HANDOFF),'scope':h['scope'],'write_root':h['write_root'],'handoff_created_at':h['created_at'],'verification_results':results,'all_ne_hashes_match':all(x['all_ne_hashes_match'] for x in results)}
out=Path(__file__).resolve().parent/'handoff-verification.json';out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'count':len(results),'all_ne_hashes_match':report['all_ne_hashes_match'],'nw_statuses':{x['object_id']:x['nw_guide_status'] for x in results},'report':str(out)},indent=2))
