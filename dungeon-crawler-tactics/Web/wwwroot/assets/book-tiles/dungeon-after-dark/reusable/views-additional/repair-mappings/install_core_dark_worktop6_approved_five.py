"""Install the five Page-approved Core worktop TOP candidates with exact guards."""
from pathlib import Path
import copy, hashlib, json, os, struct
from PIL import Image
HERE=Path(__file__).resolve().parent; OUT=HERE.parent; BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'; RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
HANDOFF=OUT/'raw/core-dark-worktop6-20261026/core-dark-worktop6-approved-five-installer-handoff.json'
REPORT=OUT/'raw/core-dark-worktop6-20261026/core-dark-worktop6-candidate-report-v1.json'
REVIEW=Path('/workspace/scratch/page-core-dark-worktop6-v1-candidate-review.json')
REVIEW_LOCAL=OUT/'qa/page-core-dark-worktop6-v1-candidate-review.json'
PROMPTDIR=OUT/'prompts/core-dark-worktop6-20261026'; BEFORE=OUT/'prebuilt/core-dark-worktop6-five-before'; CANDID='core-dark-worktop6-page-approved-five-v1'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA'); return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve(); p.relative_to(root.resolve()); return p
def atomic(p,data):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name(p.name+'.tmp'); t.write_bytes(data if isinstance(data,bytes) else data.encode()); os.replace(t,p)
def main():
 hand=json.loads(HANDOFF.read_text()); report=json.loads(REPORT.read_text()); review=json.loads(REVIEW.read_text())
 assert review['report_sha256']==sha(REPORT) and review['source_all_six_base_raw_prompt_candidate_hashes_verified']
 approved={x['object_id']:x['candidate_sha256'] for x in review['decisions'] if x['view']=='top' and x['status']=='candidate-direction-accepted'}
 assert len(approved)==5
 if not REVIEW_LOCAL.exists(): atomic(REVIEW_LOCAL,REVIEW.read_bytes())
 else: assert sha(REVIEW_LOCAL)==sha(REVIEW)
 report_objects={x['object_id']:x for x in report['objects']}; idx=json.loads(INDEX.read_text()); recipe=json.loads(RECIPE.read_text())
 assets={a['id']:copy.deepcopy(a) for a in idx['assets']}; sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']}; entries=recipe['entries']; entrymap={e['asset_id']:e for e in entries}; prepared=[]
 for o in hand['objects']:
  oid=o['object_id']
  if oid not in approved: continue
  candidate=o['candidate_top']; cs=approved[oid]; aid=f'{oid}.top'; assert candidate['sha256']==cs
  src=safe(BOOK,o['canonical_source']['path']); assert sha(src)==o['canonical_source']['sha256']
  for v,b in o['current_views'].items(): assert sha(safe(BOOK,b['path']))==b['sha256'],f'{aid}: {v} base changed'
  cand=safe(BOOK,candidate['path']); assert sha(cand)==cs
  ro=report_objects[oid]; assert ro['candidate']['sha256']==cs and ro['prompt_sha256']
  raw=safe(BOOK,o['derivation']['raw_response_path']); assert sha(raw)==o['derivation']['raw_response_sha256']==ro['raw_response']['sha256']
  request=OUT/'raw/core-dark-worktop6-20261026'/f'{oid}.top.candidate-v1.request.json'
  assert request.exists()
  PROMPTDIR.mkdir(parents=True,exist_ok=True); promptpath=PROMPTDIR/f'{oid}.top.txt'; prompt=ro['prompt']
  if promptpath.exists(): assert promptpath.read_text()==prompt
  else: atomic(promptpath,prompt)
  assert sha(promptpath)==ro['prompt_sha256']
  a=assets[aid]; dest=safe(BOOK,a['image']['path']); md=safe(BOOK,a['metadata_path']); base=o['current_views']['top']['sha256']; cur=sha(dest); assert cur in (base,cs)
  old=json.loads(md.read_text()); assert old['image']['sha256']==base
  new=copy.deepcopy(old); im=Image.open(cand).convert('RGBA'); new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(cand))
  new.setdefault('provenance_history',[]).append({'candidate_id':CANDID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  prov={'method':'source-guided-imagegen-worktop-top-correction','source_image':o['canonical_source']['path'],'source_sha256':o['canonical_source']['sha256'],'candidate_image':candidate['path'],'candidate_image_sha256':cs,
    'candidate_report':'reusable/views-additional/raw/core-dark-worktop6-20261026/core-dark-worktop6-candidate-report-v1.json','candidate_report_sha256':sha(REPORT),'candidate_review_record':'reusable/views-additional/qa/page-core-dark-worktop6-v1-candidate-review.json','candidate_review_sha256':sha(REVIEW_LOCAL),
    'raw_response':o['derivation']['raw_response_path'],'raw_response_sha256':o['derivation']['raw_response_sha256'],'request_path':f'reusable/views-additional/raw/core-dark-worktop6-20261026/{request.name}','request_id':o['derivation']['request_id'],'prompt_path':f'reusable/views-additional/prompts/core-dark-worktop6-20261026/{promptpath.name}','prompt_sha256':ro['prompt_sha256'],
    'normalization':copy.deepcopy(o['derivation']['normalization']),'notes':'Page-accepted source-guided TOP-only correction. Hidden surfaces remain inferred, not recovered source pixels.'}
  assert not prov['source_image'].startswith('/') and (BOOK/prov['source_image']).is_file()
  for key in ['candidate_image','candidate_report','candidate_review_record','raw_response','request_path','prompt_path']:
   assert not prov[key].startswith('/') and (BOOK/prov[key]).is_file(),(aid,key,prov[key])
  new['provenance']=prov; mt=json.dumps(new,indent=2)+'\n'; mh=hashlib.sha256(mt.encode()).hexdigest(); snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  entry={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':candidate['path'].removeprefix('reusable/views-additional/'),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':'reusable/views-additional/qa/page-core-dark-worktop6-v1-candidate-review.json','candidate_manifest_sha256':sha(HANDOFF)}
  if aid in entrymap: assert entrymap[aid]['final_sha256']==cs and entrymap[aid]['metadata_sha256']==mh
  prepared.append((aid,oid,dest,md,cand,base,cs,new,mt,mh,snap,entry))
 for aid,oid,dest,md,cand,base,cs,new,mt,mh,snap,entry in prepared:
  bp=BEFORE/(aid+'.png'); jp=BEFORE/(aid+'.json')
  if not bp.exists(): atomic(bp,dest.read_bytes())
  else: assert sha(bp)==base
  if not jp.exists(): atomic(jp,md.read_bytes())
  else: assert json.loads(jp.read_text())['image']['sha256']==base
  sp=safe(BOOK,snap)
  if sp.exists(): assert sha(sp)==mh
  else: atomic(sp,mt.encode())
 for aid,oid,dest,md,cand,base,cs,new,mt,mh,snap,entry in prepared:
  if sha(dest)==base: atomic(dest,cand.read_bytes())
  assert sha(dest)==cs
  if sha(md)!=mh: atomic(md,mt.encode())
  assert sha(md)==mh; assets[aid]=copy.deepcopy(new)
  if aid not in entrymap: entries.append(entry); entrymap[aid]=entry
  sets[oid]['complete']=False; sets[oid]['notes']='Page-approved worktop TOP installed; waiting for fresh live source-plus-six review. Pit station remains untouched and held.'
 ni=copy.deepcopy(idx); ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__': main()
