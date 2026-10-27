"""Install the Page-approved Pit Repair Station tire-annulus TOP v2 only."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
HANDOFF=OUT/'raw/core-dark-worktop6-20261026/core-dark-pit-top-v2-installer-handoff.json';REPORT=OUT/'raw/core-dark-worktop6-20261026/core-dark-worktop6-candidate-report-v2.json'
REVIEW=Path('/workspace/scratch/page-core-dark-pit-top-v2-candidate-review.json');REVIEW_LOCAL=OUT/'qa/page-core-dark-pit-top-v2-candidate-review.json';BEFORE=OUT/'prebuilt/core-dark-pit-top-v2-before';PROMPTDIR=OUT/'prompts/core-dark-worktop6-20261026';CANDID='core-dark-pit-top-page-approved-v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 h=json.loads(HANDOFF.read_text());review=json.loads(REVIEW.read_text());report=json.loads(REPORT.read_text());obj=h['objects'][0]
 assert sha(REVIEW)==h['review_proof']['sha256'] and sha(REPORT)==obj['derivation']['report_sha256']
 assert review['source_all_six_base_raw_prompt_candidate_hashes_verified'] and review['decisions'][0]['status']=='candidate-direction-accepted'
 assert review['decisions'][0]['candidate_sha256']==obj['candidate_top']['sha256']
 if not REVIEW_LOCAL.exists():atomic(REVIEW_LOCAL,REVIEW.read_bytes())
 else:assert sha(REVIEW_LOCAL)==sha(REVIEW)
 oid=obj['object_id'];aid=oid+'.top';src=safe(BOOK,obj['canonical_source']['path']);assert sha(src)==obj['canonical_source']['sha256']
 for v,b in obj['current_views'].items():assert sha(safe(BOOK,b['path']))==b['sha256'],f'{v} changed'
 candidate=safe(BOOK,obj['candidate_top']['path']);cs=obj['candidate_top']['sha256'];assert sha(candidate)==cs
 pit=report['pit_v2'];assert pit['object_id']==oid and pit['direction']=='top' and pit['raw_response']['sha256']
 raw=safe(BOOK,pit['raw_response']['path']);assert sha(raw)==pit['raw_response']['sha256']
 request=OUT/'raw/core-dark-worktop6-20261026/race-circuits-pit-repair-station.top.candidate-v2.request.json';assert request.is_file()
 promptpath=PROMPTDIR/(pit['request_id']+'.txt');prompt=pit['prompt'];assert hashlib.sha256(prompt.encode()).hexdigest()==pit['prompt_sha256']
 if promptpath.exists():assert promptpath.read_text()==prompt
 else:atomic(promptpath,prompt)
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];entrymap={e['asset_id']:e for e in entries}
 a=assets[aid];dst=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path']);base=obj['current_views']['top']['sha256'];cur=sha(dst);assert cur in (base,cs);old=json.loads(md.read_text());assert old['image']['sha256']==base
 new=copy.deepcopy(old);im=Image.open(candidate).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(candidate));new.setdefault('provenance_history',[]).append({'candidate_id':CANDID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
 rawrel=Path(pit['raw_response']['path']).resolve().relative_to(BOOK.resolve()).as_posix()
 prov={'method':'source-guided-imagegen-tire-annulus-overhead-correction','source_image':obj['canonical_source']['path'],'source_sha256':obj['canonical_source']['sha256'],'candidate_image':obj['candidate_top']['path'],'candidate_image_sha256':cs,'candidate_handoff':'reusable/views-additional/raw/core-dark-worktop6-20261026/core-dark-pit-top-v2-installer-handoff.json','candidate_handoff_sha256':sha(HANDOFF),'candidate_report':'reusable/views-additional/raw/core-dark-worktop6-20261026/core-dark-worktop6-candidate-report-v2.json','candidate_report_sha256':sha(REPORT),'candidate_review_record':'reusable/views-additional/qa/page-core-dark-pit-top-v2-candidate-review.json','candidate_review_sha256':sha(REVIEW_LOCAL),'raw_response':rawrel,'raw_response_sha256':pit['raw_response']['sha256'],'request_path':'reusable/views-additional/raw/core-dark-worktop6-20261026/race-circuits-pit-repair-station.top.candidate-v2.request.json','request_id':pit['request_id'],'prompt_path':f'reusable/views-additional/prompts/core-dark-worktop6-20261026/{promptpath.name}','prompt_sha256':pit['prompt_sha256'],'normalization':copy.deepcopy(pit['normalization']),'notes':'Page accepted one visible top tire annulus with lower stacked tiers occluded. Source materials and fixed equipment remain; hidden surfaces are inferred.'}
 assert not prov['source_image'].startswith('/') and safe(BOOK,prov['source_image']).is_file()
 for k in ('candidate_image','candidate_handoff','candidate_report','candidate_review_record','raw_response','request_path','prompt_path'):assert not prov[k].startswith('/') and safe(BOOK,prov[k]).is_file(),k
 new['provenance']=prov;mt=json.dumps(new,indent=2)+'\n';mh=hashlib.sha256(mt.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json';ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':'raw/core-dark-worktop6-20261026/race-circuits-pit-repair-station.top.candidate-v2.png','candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':'reusable/views-additional/qa/page-core-dark-pit-top-v2-candidate-review.json','candidate_manifest_sha256':sha(HANDOFF)}
 if aid in entrymap:assert entrymap[aid]['final_sha256']==cs and entrymap[aid]['metadata_sha256']==mh
 bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json')
 if not bp.exists():atomic(bp,dst.read_bytes())
 else:assert sha(bp)==base
 if not jp.exists():atomic(jp,md.read_bytes())
 else:assert json.loads(jp.read_text())['image']['sha256']==base
 sp=safe(BOOK,snap)
 if sp.exists():assert sha(sp)==mh
 else:atomic(sp,mt.encode())
 if sha(dst)==base:atomic(dst,candidate.read_bytes())
 assert sha(dst)==cs
 if sha(md)!=mh:atomic(md,mt.encode())
 assert sha(md)==mh;assets[aid]=copy.deepcopy(new)
 if aid not in entrymap:entries.append(ent);entrymap[aid]=ent
 sets[oid]['complete']=False;sets[oid]['notes']='Page-approved TOP tire-annulus correction installed; waiting for current source-plus-six review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n');print(json.dumps({'installed':aid,'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
