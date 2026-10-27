"""Install Page-accepted Personal Space wood stair BOTTOM/REAR directions."""
from pathlib import Path
import copy, hashlib, json, os, struct
from PIL import Image
HERE=Path(__file__).resolve().parent; OUT=HERE.parent; BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'; RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
CANDDIR=OUT/'candidates/equipment-dark-stairs-successor-20261026'
MANIFEST=CANDDIR/'personal-wood-stairs-bottom-rear-v1-candidate.json'
REVIEW=Path('/workspace/scratch/page-equipment-personal-wood-stairs-v1-candidate-review.json')
REVIEW_LOCAL=OUT/'qa/page-equipment-personal-wood-stairs-v1-candidate-review.json'
BEFORE=OUT/'prebuilt/equipment-personal-wood-stairs-v1-before'; CANDID='equipment-personal-wood-stairs-v1'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA'); return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve(); p.relative_to(root.resolve()); return p
def atomic(p,data):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name(p.name+'.tmp'); t.write_bytes(data if isinstance(data,bytes) else data.encode()); os.replace(t,p)
def main():
 manifest=json.loads(MANIFEST.read_text()); review=json.loads(REVIEW.read_text())
 assert review['manifest_sha256']==sha(MANIFEST) and review['source_all_six_base_candidate_hashes_verified']
 accepted={(r['object_id'],r['view']):r['candidate_sha256'] for r in review['decisions'] if r['status']=='candidate-direction-accepted'}
 rows={a['asset_id']:a for a in manifest['assets']}; assert len(accepted)==4 and set(accepted)=={(a['object_id'],a['view']) for a in rows.values()}
 if not REVIEW_LOCAL.exists(): atomic(REVIEW_LOCAL,REVIEW.read_bytes())
 else: assert sha(REVIEW_LOCAL)==sha(REVIEW)
 idx=json.loads(INDEX.read_text()); recipe=json.loads(RECIPE.read_text()); assets={a['id']:copy.deepcopy(a) for a in idx['assets']}; sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']}; entries=recipe['entries']; entrymap={e['asset_id']:e for e in entries}
 prepared=[]
 for aid,record in sorted(rows.items()):
  oid=record['object_id']; view=record['view']; cs=accepted[(oid,view)]; assert cs==record['sha256']
  binding=manifest['source_bindings'][oid]; src=Path(binding['source']['path']); assert sha(src)==binding['source']['sha256']==record['provenance']['source_sha256']
  for bv,b in binding['base_views'].items(): assert sha(b['path'])==b['sha256'], f'{aid}: {bv} base changed'
  cand=safe(CANDDIR,record['candidate_path']); assert sha(cand)==cs
  a=assets[aid]; dest=safe(BOOK,a['image']['path']); md=safe(BOOK,a['metadata_path']); base=binding['base_views'][view]['sha256']; cur=sha(dest); assert cur in (base,cs), f'{aid}: live base changed {cur}'
  old=json.loads(md.read_text()); assert old['image']['sha256']==base
  new=copy.deepcopy(old); im=Image.open(cand).convert('RGBA'); new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(cand))
  new.setdefault('provenance_history',[]).append({'candidate_id':CANDID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  prov=copy.deepcopy(record['provenance']); prov['source_image']=binding['source']['path'].replace(str(BOOK)+'/', ''); prov['source_sha256']=binding['source']['sha256']; prov['candidate_image']='reusable/views-additional/'+str(cand.relative_to(OUT)); prov['candidate_image_sha256']=cs
  prov['candidate_manifest']='reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/personal-wood-stairs-bottom-rear-v1-candidate.json'; prov['candidate_manifest_sha256']=sha(MANIFEST); prov['candidate_review_record']='reusable/views-additional/qa/page-equipment-personal-wood-stairs-v1-candidate-review.json'; prov['candidate_review_sha256']=sha(REVIEW_LOCAL)
  raw=CANDDIR/manifest['raw_manifest']; prov['generated_atlas']=f'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/{manifest["raw_manifest"]}'; prov['generated_atlas_sha256']=sha(raw)
  prov['normalization']=copy.deepcopy(record['normalization']); prov['notes']=record['provenance'].get('notes','')+' Hidden surfaces are inferred, not recovered source pixels.'
  new['provenance']=prov; mt=json.dumps(new,indent=2)+'\n'; mh=hashlib.sha256(mt.encode()).hexdigest(); snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  assert not prov['source_image'].startswith('/') and safe(BOOK,prov['source_image']).is_file(), f'{aid}: canonical source_image must be pack-relative and resolvable'
  re={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':str(cand.relative_to(OUT)),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':'reusable/views-additional/qa/page-equipment-personal-wood-stairs-v1-candidate-review.json','candidate_manifest_sha256':sha(MANIFEST)}
  if aid in entrymap: assert entrymap[aid]['final_sha256']==cs and entrymap[aid]['metadata_sha256']==mh
  prepared.append((aid,oid,dest,md,cand,base,cs,new,mt,mh,snap,re))
 for aid,oid,dest,md,cand,base,cs,new,mt,mh,snap,re in prepared:
  bp=BEFORE/(aid+'.png'); jp=BEFORE/(aid+'.json')
  if not bp.exists(): atomic(bp,dest.read_bytes())
  else: assert sha(bp)==base
  if not jp.exists(): atomic(jp,md.read_bytes())
  else: assert json.loads(jp.read_text())['image']['sha256']==base
  sp=safe(BOOK,snap)
  if sp.exists(): assert sha(sp)==mh
  else: atomic(sp,mt.encode())
 for aid,oid,dest,md,cand,base,cs,new,mt,mh,snap,re in prepared:
  if sha(dest)==base: atomic(dest,cand.read_bytes())
  assert sha(dest)==cs
  if sha(md)!=mh: atomic(md,mt.encode())
  assert sha(md)==mh; assets[aid]=copy.deepcopy(new)
  if aid not in entrymap: entries.append(re); entrymap[aid]=re
 for oid in {p[1] for p in prepared}: sets[oid]['complete']=False; sets[oid]['notes']='Page-accepted wood stair BOTTOM/REAR corrections installed; awaiting current source-plus-six review.'
 ni=copy.deepcopy(idx); ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']]; ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n'); atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[p[0] for p in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__': main()
