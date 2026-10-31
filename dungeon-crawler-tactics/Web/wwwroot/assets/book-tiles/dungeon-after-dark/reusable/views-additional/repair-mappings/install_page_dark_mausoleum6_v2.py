"""Install Root-accepted mausoleum6 v2 candidates after all per-object source/six guards."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
CDIR=OUT/'candidates/page-dark-next-six-mausoleum-v1';MANIFEST=CDIR/'mausoleum6-candidate-manifest-v2.json';PROOF=CDIR/'mausoleum6-candidate-contact-proof-v2.json'
REVIEW=OUT/'qa/root-dark-mausoleum6-v2-accepted-review.json';BEFORE=OUT/'prebuilt/page-dark-mausoleum6-v2-before';SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 m=json.loads(MANIFEST.read_text());proof=json.loads(PROOF.read_text());assert proof['manifest_sha256']==sha(MANIFEST)
 assert proof['contact_sha256']=='e7d2d4cdf1a5f07665b8e862c4bca014f482990f8dfa963b48e21ea1b4049e0c'
 objects={o['object_id']:o for o in m['objects']};cands=m['candidates'];assert len(cands)==14 and len({c['asset_id'] for c in cands})==14
 # Root explicitly accepted all 14 directions after the six-direction contact correction.
 review={'status':'scoped accepted; live whole-set review required','reviewer':'root','accepted_contact_path':proof['contact_path'],'accepted_contact_sha256':proof['contact_sha256'],'manifest_path':'reusable/views-additional/candidates/page-dark-next-six-mausoleum-v1/mausoleum6-candidate-manifest-v2.json','manifest_sha256':sha(MANIFEST),'accepted_directions':[{'object_id':c['object_id'],'view':c['view'],'candidate_path':c['candidate_path'],'candidate_sha256':c['candidate_sha256']} for c in cands]}
 if REVIEW.exists():assert json.loads(REVIEW.read_text())==review
 else:atomic(REVIEW,json.dumps(review,indent=2)+'\n')
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];emap={e['asset_id']:e for e in entries};prepared=[]
 # Stage guards for every candidate before mutating any output.
 for c in cands:
  oid=c['object_id'];v=c['view'];aid=c['asset_id'];o=objects[oid]
  assert aid==f'{oid}.{v}' and c['source_path']==o['source']['path'] and c['source_sha256']==o['source']['sha256']
  assert sha(safe(BOOK,c['source_path']))==c['source_sha256'],f'{oid}: source changed'
  assert set(c['baseline_six'])==set(o['base_six'])
  for bv,b in c['baseline_six'].items():
   assert b==o['base_six'][bv],f'{oid}.{v}: wrong object baseline row {bv}'
   assert sha(safe(BOOK,b['path']))==b['sha256'],f'{oid}.{bv}: live base changed'
  cand=safe(BOOK,c['candidate_path']);assert sha(cand)==c['candidate_sha256'],f'{aid}: candidate hash mismatch'
  assert c['candidate_path'].startswith('reusable/views-additional/')
  asset=assets[aid];dst=safe(BOOK,asset['image']['path']);md=safe(BOOK,asset['metadata_path']);base=o['base_six'][v]['sha256']
  assert c['baseline_six'][v]['sha256']==base and sha(dst)==base,f'{aid}: live output changed'
  old=json.loads(md.read_text());assert old['image']['sha256']==base
  new=copy.deepcopy(old);im=Image.open(cand).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=c['candidate_sha256'],rgba_sha256=rgba(cand))
  new.setdefault('provenance_history',[]).append({'candidate_id':f'page-dark-mausoleum6-v2:{aid}','previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  prov={'method':'source-guided-orthographic-view-repair','source_image':c['source_path'],'source_sha256':c['source_sha256'],'candidate_image':c['candidate_path'],'candidate_image_sha256':c['candidate_sha256'],
        'candidate_manifest':'reusable/views-additional/candidates/page-dark-next-six-mausoleum-v1/mausoleum6-candidate-manifest-v2.json','candidate_manifest_sha256':sha(MANIFEST),
        'candidate_review_record':'reusable/views-additional/qa/root-dark-mausoleum6-v2-accepted-review.json','candidate_review_sha256':sha(REVIEW),
        'contact_proof':'reusable/views-additional/candidates/page-dark-next-six-mausoleum-v1/mausoleum6-candidate-contact-proof-v2.json','contact_proof_sha256':sha(PROOF),
        'raw_response':c.get('raw_path'),'raw_response_sha256':c.get('raw_sha256'),'prompt_path':c.get('prompt_path'),'prompt_sha256':c.get('prompt_sha256'),
        'request_id':c.get('request_id'),'references':copy.deepcopy(c.get('references')),'derived_from':copy.deepcopy(c.get('derived_from')),
        'normalization':copy.deepcopy(c.get('normalization')),'notes':c.get('notes','')+' Any hidden construction is inferred, not recovered.'}
  for k in ('source_image','candidate_image','candidate_manifest','candidate_review_record','contact_proof','raw_response','prompt_path'):
   if prov.get(k):assert not prov[k].startswith('/') and safe(BOOK,prov[k]).is_file(),(aid,k,prov[k])
  new['provenance']=prov;mb=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(mb).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  ent={'asset_id':aid,'image_path':asset['image']['path'],'candidate_path':c['candidate_path'].replace('reusable/views-additional/','',1),'candidate_sha256':c['candidate_sha256'],'base_sha256':base,'final_sha256':c['candidate_sha256'],'metadata_path':asset['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'candidate_manifest_sha256':sha(MANIFEST)}
  prev=emap.get(aid)
  if prev:
   assert prev['final_sha256']==base,f'{aid}: replay chain current mismatch';entries[entries.index(prev)]=ent
  else:entries.append(ent)
  emap[aid]=ent;prepared.append((aid,oid,dst,md,cand,base,c['candidate_sha256'],mb,mh,snap))
 for aid,oid,dst,md,cand,base,cs,mb,mh,snap in prepared:
  bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json')
  if bp.exists():assert sha(bp)==base
  else:atomic(bp,dst.read_bytes())
  if jp.exists():assert json.loads(jp.read_text())['image']['sha256']==base
  else:atomic(jp,md.read_bytes())
  sp=safe(BOOK,snap)
  if sp.exists():assert sha(sp)==mh
  else:atomic(sp,mb)
 for aid,oid,dst,md,cand,base,cs,mb,mh,snap in prepared:
  assert sha(dst)==base;atomic(dst,cand.read_bytes());assert sha(dst)==cs;atomic(md,mb);assert sha(md)==mh;assets[aid]=copy.deepcopy(json.loads(mb))
 for oid in {x[1] for x in prepared}:
  sets[oid]['complete']=False;sets[oid]['notes']='Mausoleum6 scoped repairs installed; awaiting fresh source-plus-six whole-set review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
