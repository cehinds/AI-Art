"""Install the eight Page-approved Masquerade/Early stair directions only."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
CANDDIR=OUT/'candidates/equipment-dark-stairs-successor-20261026';MANIFEST=CANDDIR/'masquerade-early-candidates-v1.json'
REVIEW=Path('/workspace/scratch/page-equipment-masquerade-early-v1-candidate-review.json');REVIEW_LOCAL=OUT/'qa/page-equipment-masquerade-early-v1-candidate-review.json'
PROMPTDIR=OUT/'prompts/equipment-masquerade-early-20261026';BEFORE=OUT/'prebuilt/equipment-masquerade-early-v1-before';CANDID='equipment-masquerade-early-page-approved-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 man=json.loads(MANIFEST.read_text());rev=json.loads(REVIEW.read_text());assert rev['manifest_sha256']==sha(MANIFEST) and rev['source_all_six_base_candidate_hashes_verified']
 accepted={(x['object_id'],x['view']):x['candidate_sha256'] for x in rev['decisions'] if x['status']=='candidate-direction-accepted'}; rows={(x['object_id'],x['view']):x for x in man['assets']}
 assert len(accepted)==8 and set(accepted).issubset(set(rows))
 if not REVIEW_LOCAL.exists():atomic(REVIEW_LOCAL,REVIEW.read_bytes())
 else:assert sha(REVIEW_LOCAL)==sha(REVIEW)
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];entrymap={e['asset_id']:e for e in entries};prepared=[]
 for (oid,v),cs in sorted(accepted.items()):
  r=rows[(oid,v)];aid=f'{oid}.{v}';assert r['sha256']==cs;binding=man['source_bindings'][oid];src=Path(binding['source']['path']);assert sha(src)==binding['source']['sha256']==r['provenance']['source_sha256']
  for bv,b in binding['base_views'].items():assert sha(b['path'])==b['sha256'],f'{aid}: {bv} base changed'
  cand=safe(CANDDIR,r['candidate_path']);assert sha(cand)==cs
  a=assets[aid];dst=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path']);base=binding['base_views'][v]['sha256'];cur=sha(dst);assert cur in (base,cs)
  old=json.loads(md.read_text());assert old['image']['sha256']==base
  # Request records carry the exact prompt text; persist it as a portable file.
  requestrel=r['provenance']['generation_request_path'];request=safe(BOOK,requestrel);req=json.loads(request.read_text());prompt=req['prompt_text'];assert hashlib.sha256(prompt.encode()).hexdigest()==r['provenance']['prompt_sha256']
  promptpath=PROMPTDIR/(req['request_id']+'.txt');
  if promptpath.exists():assert promptpath.read_text()==prompt
  else:atomic(promptpath,prompt)
  rawrel=r['provenance']['generated_atlas_path'];raw=safe(BOOK,rawrel);assert sha(raw)==r['provenance']['generated_atlas_sha256']
  new=copy.deepcopy(old);im=Image.open(cand).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(cand));new.setdefault('provenance_history',[]).append({'candidate_id':CANDID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  source_rel=binding['source']['path'].replace(str(BOOK)+'/','');prov={'method':'source-guided-imagegen-stair-view-correction','source_image':source_rel,'source_sha256':binding['source']['sha256'],'candidate_image':'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/'+r['candidate_path'],'candidate_image_sha256':cs,'candidate_manifest':'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/masquerade-early-candidates-v1.json','candidate_manifest_sha256':sha(MANIFEST),'candidate_review_record':'reusable/views-additional/qa/page-equipment-masquerade-early-v1-candidate-review.json','candidate_review_sha256':sha(REVIEW_LOCAL),'raw_atlas':rawrel,'raw_atlas_sha256':sha(raw),'request_path':requestrel,'request_sha256':sha(request),'request_id':req['request_id'],'prompt_path':f'reusable/views-additional/prompts/equipment-masquerade-early-20261026/{promptpath.name}','prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'normalization':copy.deepcopy(r['normalization']),'notes':r['provenance'].get('notes','')+' Hidden construction is inferred, not recovered source pixels.'}
  assert not source_rel.startswith('/') and safe(BOOK,source_rel).is_file(),f'{aid}: canonical source_image must be pack-relative'
  for key in ('candidate_image','candidate_manifest','candidate_review_record','raw_atlas','request_path','prompt_path'):assert not prov[key].startswith('/') and safe(BOOK,prov[key]).is_file(),(aid,key,prov[key])
  new['provenance']=prov;mt=json.dumps(new,indent=2)+'\n';mh=hashlib.sha256(mt.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':str(cand.relative_to(OUT)),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':'reusable/views-additional/qa/page-equipment-masquerade-early-v1-candidate-review.json','candidate_manifest_sha256':sha(MANIFEST)}
  if aid in entrymap:assert entrymap[aid]['final_sha256']==cs and entrymap[aid]['metadata_sha256']==mh
  prepared.append((aid,oid,dst,md,cand,base,cs,new,mt,mh,snap,ent))
 for aid,oid,dst,md,cand,base,cs,new,mt,mh,snap,ent in prepared:
  bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json')
  if not bp.exists():atomic(bp,dst.read_bytes())
  else:assert sha(bp)==base
  if not jp.exists():atomic(jp,md.read_bytes())
  else:assert json.loads(jp.read_text())['image']['sha256']==base
  sp=safe(BOOK,snap)
  if sp.exists():assert sha(sp)==mh
  else:atomic(sp,mt.encode())
 for aid,oid,dst,md,cand,base,cs,new,mt,mh,snap,ent in prepared:
  if sha(dst)==base:atomic(dst,cand.read_bytes())
  assert sha(dst)==cs
  if sha(md)!=mh:atomic(md,mt.encode())
  assert sha(md)==mh;assets[aid]=copy.deepcopy(new)
  if aid not in entrymap:entries.append(ent);entrymap[aid]=ent
 for oid in {x[1] for x in prepared}:sets[oid]['complete']=False;sets[oid]['notes']='Page-approved scoped stair BOTTOM/side corrections installed; front/rear remain held and unchanged.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n');print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
