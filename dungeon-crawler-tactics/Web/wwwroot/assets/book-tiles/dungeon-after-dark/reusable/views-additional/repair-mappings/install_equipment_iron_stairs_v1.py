"""Install Page-accepted Iron Trains stair BOTTOM/REAR candidates."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
CANDDIR=OUT/'candidates/equipment-dark-stairs-successor-20261026';MANIFEST=CANDDIR/'iron-bottom-rear-v1-candidate.json'
REVIEW=Path('/workspace/scratch/page-equipment-iron-stairs-v1-candidate-review.json');REVIEW_LOCAL=OUT/'qa/page-equipment-iron-stairs-v1-candidate-review.json'
BEFORE=OUT/'prebuilt/equipment-iron-stairs-v1-before';CANDID='equipment-iron-stairs-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 man=json.loads(MANIFEST.read_text());rev=json.loads(REVIEW.read_text());assert rev['manifest_sha256']==sha(MANIFEST) and rev['source_all_six_base_candidate_hashes_verified']
 accepted={(x['object_id'],x['view']):x['candidate_sha256'] for x in rev['decisions'] if x['status']=='candidate-direction-accepted'};rows={x['asset_id']:x for x in man['assets']};assert len(accepted)==4 and set(accepted)=={(x['object_id'],x['view']) for x in rows.values()}
 if not REVIEW_LOCAL.exists():atomic(REVIEW_LOCAL,REVIEW.read_bytes())
 else:assert sha(REVIEW_LOCAL)==sha(REVIEW)
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];entrymap={e['asset_id']:e for e in entries};prepared=[]
 for aid,r in sorted(rows.items()):
  oid=r['object_id'];v=r['view'];cs=accepted[(oid,v)];assert cs==r['sha256'];binding=man['source_bindings'][oid];src=Path(binding['source']['path']);assert sha(src)==binding['source']['sha256']==r['provenance']['source_sha256']
  for bv,b in binding['base_views'].items():assert sha(b['path'])==b['sha256'],f'{aid}: {bv} changed'
  cand=safe(CANDDIR,r['candidate_path']);assert sha(cand)==cs
  a=assets[aid];dst=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path']);base=binding['base_views'][v]['sha256'];cur=sha(dst);assert cur in (base,cs)
  old=json.loads(md.read_text());assert old['image']['sha256']==base
  new=copy.deepcopy(old);im=Image.open(cand).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(cand));new.setdefault('provenance_history',[]).append({'candidate_id':CANDID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  is_bottom=v=='bottom';promptrel='reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/raw/'+('iron-bottom-request-v2.json' if is_bottom else 'iron-rear-request-v1.json');rawrel='reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/'+r['provenance']['generated_atlas_path'];guide=r['provenance']['geometry_guide']
  prov={'method':'source-guided-isolated-orthographic-stair-correction','source_image':binding['source']['path'].replace(str(BOOK)+'/', ''),'source_sha256':binding['source']['sha256'],'candidate_image':'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/'+r['candidate_path'],'candidate_image_sha256':cs,'candidate_manifest':'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/iron-bottom-rear-v1-candidate.json','candidate_manifest_sha256':sha(MANIFEST),'candidate_review_record':'reusable/views-additional/qa/page-equipment-iron-stairs-v1-candidate-review.json','candidate_review_sha256':sha(REVIEW_LOCAL),'request_path':promptrel,'request_sha256':sha(BOOK/promptrel),'raw_atlas':rawrel,'raw_atlas_sha256':r['provenance']['generated_atlas_sha256'],'geometry_guide':{'path':guide['path'],'sha256':guide['sha256'],'role':guide['role']},'normalization':copy.deepcopy(r['normalization']),'notes':r['provenance'].get('notes','')+' Hidden support construction is inferred; paired underside alias is explicitly target-specific.'}
  assert not prov['source_image'].startswith('/') and safe(BOOK,prov['source_image']).is_file(),f'{aid}: canonical source_image must be pack-relative'
  for key in ('candidate_image','candidate_manifest','candidate_review_record','request_path','raw_atlas'):
   assert not prov[key].startswith('/') and safe(BOOK,prov[key]).is_file(),(aid,key,prov[key])
  new['provenance']=prov;mt=json.dumps(new,indent=2)+'\n';mh=hashlib.sha256(mt.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':str(cand.relative_to(OUT)),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':'reusable/views-additional/qa/page-equipment-iron-stairs-v1-candidate-review.json','candidate_manifest_sha256':sha(MANIFEST)}
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
 for oid in {x[1] for x in prepared}:sets[oid]['complete']=False;sets[oid]['notes']='Page-approved Iron Trains stair BOTTOM/REAR corrections installed; waiting for fresh live source-plus-six review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n');print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
