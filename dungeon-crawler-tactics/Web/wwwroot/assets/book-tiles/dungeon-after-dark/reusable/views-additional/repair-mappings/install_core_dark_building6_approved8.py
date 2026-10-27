"""Install Page/Root-approved Core building-plan views with exact guards."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
CDIR=OUT/'candidates/core-dark-building6-20261026'
SEVEN=CDIR/'building6-approved-seven-installer-handoff.json'
TEMPLE=CDIR/'building6-temple-top-v3-installer-handoff.json'
REPORT=CDIR/'building6-candidate-report-v2.json'
REQUESTS=CDIR/'requests-imagegen.json'
PAGE_REVIEW=Path('/workspace/scratch/page-core-dark-building6-v2-candidate-review.json')
PAGE_LOCAL=OUT/'qa/page-core-dark-building6-v2-candidate-review.json'
PROMPTDIR=OUT/'prompts/core-dark-building6-20261026'
BEFORE=OUT/'prebuilt/core-dark-building6-approved8-before'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)

def main():
 seven=json.loads(SEVEN.read_text());temple=json.loads(TEMPLE.read_text())
 report=json.loads(REPORT.read_text());review=json.loads(PAGE_REVIEW.read_text())
 assert seven['current_source_and_six_verified_at_handoff']
 assert review['source_all_six_base_raw_prompt_candidate_hashes_verified']
 assert review['report_sha256']==sha(REPORT)
 assert temple['review']['status']=='scoped-accepted'
 reqs=json.loads(REQUESTS.read_text());reqmap={r['request_id']:r for r in reqs}
 reportmap={(r['object_id'],r['view']):r for r in report['candidate_views']}
 reviewmap={(r['object_id'],r['view']):r for r in review['decisions']
            if r['status']=='candidate-direction-accepted'}
 scope=[]
 for d in seven['directions']:
  oid=d['object_id'];v=d['affected_view'];dec=reviewmap[(oid,v)]
  rr=reportmap[(oid,v)];candidate=d['candidate']
  assert candidate['sha256']==dec['candidate_sha256']==rr['candidate']['sha256']
  assert candidate['path']==dec['candidate_path']==rr['candidate']['path']
  derivation={'request_id':rr['request_id'],'prompt_sha256':rr['prompt_sha256'],
    'prompt':rr['prompt'],'raw_response':rr['raw_response'],'normalization':rr['normalization']}
  scope.append({'object_id':oid,'view':v,'source':d['canonical_source'],
    'bases':d['current_views'],'candidate':candidate,'derivation':derivation,
    'review_record':'reusable/views-additional/qa/page-core-dark-building6-v2-candidate-review.json',
    'review_sha':sha(PAGE_REVIEW),'manifest_path':'reusable/views-additional/candidates/core-dark-building6-20261026/building6-approved-seven-installer-handoff.json',
    'manifest_sha':sha(SEVEN)})
 # Root approved the separately reviewed temple v3 exact hash.
 scope.append({'object_id':'over-city-venues-education-temple-entrance','view':'top',
   'source':temple['canonical_source'],'bases':temple['current_views'],
   'candidate':temple['candidate'],'derivation':temple['derivation'],
   'review_record':'reusable/views-additional/candidates/core-dark-building6-20261026/building6-temple-top-v3-installer-handoff.json',
   'review_sha':sha(TEMPLE),'manifest_path':'reusable/views-additional/candidates/core-dark-building6-20261026/building6-temple-top-v3-installer-handoff.json',
   'manifest_sha':sha(TEMPLE)})
 assert len(scope)==8
 if PAGE_LOCAL.exists():assert sha(PAGE_LOCAL)==sha(PAGE_REVIEW)
 else:atomic(PAGE_LOCAL,PAGE_REVIEW.read_bytes())

 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text())
 assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']}
 entries=recipe['entries'];entrymap={e['asset_id']:e for e in entries};prepared=[]
 for row in scope:
  oid=row['object_id'];v=row['view'];aid=f'{oid}.{v}';src=safe(BOOK,row['source']['path'])
  assert sha(src)==row['source']['sha256']
  for bv,b in row['bases'].items():assert sha(safe(BOOK,b['path']))==b['sha256'],f'{oid}.{bv} changed'
  cand=safe(BOOK,row['candidate']['path']);cs=row['candidate']['sha256'];assert sha(cand)==cs
  deriv=row['derivation'];rawinfo=deriv['raw_response'];raw=safe(BOOK,rawinfo['path']);assert sha(raw)==rawinfo['sha256']
  request_id=deriv['request_id']
  if request_id in reqmap:
   rq=reqmap[request_id];prompt=rq['prompt'];requestpath=CDIR/'requests-imagegen.json'
   assert rq['object_id']==oid and rq['view']==v
  else:
   requestpath=CDIR/f"{oid}.{v}.candidate-v3.request.json"
   if requestpath.exists():
    rq=json.loads(requestpath.read_text());prompt=rq['prompt'];assert rq['request_id']==request_id
   else:
    prompt=deriv['prompt'];requestpath=None
  assert hashlib.sha256(prompt.encode()).hexdigest()==deriv['prompt_sha256']
  pfile=PROMPTDIR/f'{request_id}.txt'
  if pfile.exists():assert pfile.read_text()==prompt
  else:atomic(pfile,prompt)
  asset=assets[aid];dst=safe(BOOK,asset['image']['path']);md=safe(BOOK,asset['metadata_path']);base=row['bases'][v]['sha256']
  assert sha(dst) in (base,cs);old=json.loads(md.read_text());assert old['image']['sha256']==base
  new=copy.deepcopy(old);im=Image.open(cand).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba_sha(cand))
  new.setdefault('provenance_history',[]).append({'candidate_id':f'core-dark-building6-approved8:{aid}',
    'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  prov={'method':'source-guided-imagegen-orthographic-building-view','source_image':row['source']['path'],'source_sha256':row['source']['sha256'],
    'candidate_image':row['candidate']['path'],'candidate_image_sha256':cs,'candidate_manifest':row['manifest_path'],'candidate_manifest_sha256':row['manifest_sha'],
    'candidate_review_record':row['review_record'],'candidate_review_sha256':row['review_sha'],
    'raw_response':rawinfo['path'],'raw_response_sha256':rawinfo['sha256'],'request_id':request_id,
    'request_record':('reusable/views-additional/candidates/core-dark-building6-20261026/requests-imagegen.json' if request_id in reqmap else
      (f'reusable/views-additional/candidates/core-dark-building6-20261026/{oid}.{v}.candidate-v3.request.json' if requestpath else row['manifest_path'])),
    'prompt_path':f'reusable/views-additional/prompts/core-dark-building6-20261026/{pfile.name}',
    'prompt_sha256':deriv['prompt_sha256'],'normalization':copy.deepcopy(deriv['normalization']),
    'notes':'Source-specific plane repair. Any hidden details are inferred, not recovered source pixels.'}
  for k in ('source_image','candidate_image','candidate_manifest','candidate_review_record','raw_response','request_record','prompt_path'):
   assert not prov[k].startswith('/') and safe(BOOK,prov[k]).is_file(),(aid,k,prov[k])
  new['provenance']=prov;mb=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(mb).hexdigest()
  snapshot=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  entry={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':row['candidate']['path'].replace('reusable/views-additional/','',1),
    'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snapshot,
    'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':prov['candidate_review_record'],
    'candidate_manifest_sha256':row['manifest_sha']}
  prior=entrymap.get(aid)
  if prior:
   assert prior['final_sha256']==base,f'{aid}: unexpected existing replay final';entries[entries.index(prior)]=entry
  else:entries.append(entry)
  entrymap[aid]=entry
  prepared.append((aid,oid,dst,md,cand,base,cs,new,mb,mh,snapshot))
 for aid,oid,dst,md,cand,base,cs,new,mb,mh,snapshot in prepared:
  bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json')
  if bp.exists():assert sha(bp)==base
  else:atomic(bp,dst.read_bytes())
  if jp.exists():assert json.loads(jp.read_text())['image']['sha256']==base
  else:atomic(jp,md.read_bytes())
  sp=safe(BOOK,snapshot)
  if sp.exists():assert sha(sp)==mh,f'{aid} snapshot differs'
  else:atomic(sp,mb)
 for aid,oid,dst,md,cand,base,cs,new,mb,mh,snapshot in prepared:
  if sha(dst)==base:atomic(dst,cand.read_bytes())
  assert sha(dst)==cs
  if sha(md)!=mh:atomic(md,mb)
  assert sha(md)==mh;assets[aid]=copy.deepcopy(new)
 for oid in {r[1] for r in prepared}:
  sets[oid]['complete']=False;sets[oid]['notes']='Core/Page-approved scoped building views installed; waiting for fresh live source-plus-six review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']]
 ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[r[0] for r in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
