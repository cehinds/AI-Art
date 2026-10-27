"""Install the seven Root-accepted support6 directions after per-object SHA guards."""
from pathlib import Path
import copy, hashlib, json, os, struct
from PIL import Image
HERE=Path(__file__).resolve().parent
OUT=HERE.parent
BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'
RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
CAND=OUT/'candidates/page-dark-next-six-support6-v1'
MANIFEST=CAND/'candidate-manifest-v2.json'
REPORT=CAND/'manifest-v2-audit.json'
BEFORE=OUT/'prebuilt/page-dark-support6-v2-before'
SNAP=OUT/'prebuilt/replay-sidecars-final-v1'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(p):
 im=Image.open(p).convert('RGBA')
 return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(rel):
 p=(BOOK/rel).resolve();p.relative_to(BOOK.resolve());return p
def atomic(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp')
 tmp.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(tmp,path)

def main():
 m=json.loads(MANIFEST.read_text());assert sha(MANIFEST)==json.loads(REPORT.read_text())['manifest_v2_sha256']
 objects={x['object_id']:x for x in m['objects']}
 accepted=[c for c in m['candidates'] if c['review_status'].startswith('Root visual candidate acceptance')]
 assert len(accepted)==7, len(accepted)
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text())
 assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']}
 entries=recipe['entries']; emap={e['asset_id']:e for e in entries};prepared=[]
 # Validate all seven base sets and candidate bytes before preparing any mutation.
 for c in accepted:
  oid=c['object_id'];view=c['view'];aid=c['asset_id'];o=objects[oid]
  assert oid==c['object_id'] and c['source_path']==o['source_path'] and c['source_sha256']==o['source_sha256']
  src=safe(c['source_path']);assert sha(src)==c['source_sha256'],f'{oid}: source changed'
  for v,b in c['baseline_six'].items(): assert sha(safe(b['path']))==b['sha256'],f'{oid}.{v}: baseline changed'
  candidate=safe(c['candidate_path']);assert sha(candidate)==c['candidate_sha256'],f'{aid}: candidate changed'
  asset=assets[aid];dst=safe(asset['image']['path']);md=safe(asset['metadata_path'])
  base=c['baseline_six'][view]['sha256'];assert sha(dst)==base,f'{aid}: live target changed'
  old=json.loads(md.read_text());assert old['image']['sha256']==base
  new=copy.deepcopy(old);im=Image.open(candidate).convert('RGBA')
  new['image'].update(width=im.width,height=im.height,sha256=c['candidate_sha256'],rgba_sha256=rgba_sha(candidate))
  new.setdefault('provenance_history',[]).append({'candidate_id':f'page-dark-support6-v2:{aid}','previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  prov={'method':'source-guided-orthographic-support-view','source_image':c['source_path'],'source_sha256':c['source_sha256'],
        'candidate_image':c['candidate_path'],'candidate_image_sha256':c['candidate_sha256'],
        'candidate_manifest':'reusable/views-additional/candidates/page-dark-next-six-support6-v1/candidate-manifest-v2.json','candidate_manifest_sha256':sha(MANIFEST),
        'contact_proof':'reusable/views-additional/candidates/page-dark-next-six-support6-v1/source-six-contact-proof-v2.json','contact_sha256':sha(CAND/'source-six-contact-proof-v2.json'),
        'request_id':c.get('request_id'),'raw_response':c.get('raw_path'),'raw_response_sha256':c.get('raw_sha256'),
        'prompt_path':c.get('prompt_path'),'prompt_sha256':c.get('prompt_sha256'),
        'transformation':c.get('transformation'),'normalization':copy.deepcopy(c.get('normalization')),
        'symmetry_inference':c.get('notes'),'notes':'Candidate-only direction accepted by Root. Hidden construction remains inferred.'}
  for k in ('source_image','candidate_image','candidate_manifest','contact_proof','raw_response','prompt_path'):
   if prov.get(k): assert not prov[k].startswith('/'),(aid,k,prov[k]);assert safe(prov[k]).is_file(),(aid,k,prov[k])
  new['provenance']=prov;mb=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(mb).hexdigest()
  snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  entry={'asset_id':aid,'image_path':asset['image']['path'],'candidate_path':c['candidate_path'].replace('reusable/views-additional/','',1),
         'candidate_sha256':c['candidate_sha256'],'base_sha256':base,'final_sha256':c['candidate_sha256'],'metadata_path':asset['metadata_path'],
         'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,
         'candidate_manifest_sha256':sha(MANIFEST)}
  prior=emap.get(aid)
  if prior:
   assert prior['final_sha256']==base,f'{aid}: replay chain current hash mismatch'
   entries[entries.index(prior)]=entry
  else: entries.append(entry)
  emap[aid]=entry
  prepared.append((aid,oid,dst,md,candidate,base,c['candidate_sha256'],new,mb,mh,snap))
 # Persist exact pre-install copies and sidecar snapshots first.
 for aid,oid,dst,md,cand,base,cs,new,mb,mh,snap in prepared:
  bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json')
  if bp.exists(): assert sha(bp)==base
  else: atomic(bp,dst.read_bytes())
  if jp.exists(): assert json.loads(jp.read_text())['image']['sha256']==base
  else: atomic(jp,md.read_bytes())
  sp=safe(snap)
  if sp.exists(): assert sha(sp)==mh,f'{aid}: existing release snapshot differs'
  else: atomic(sp,mb)
 # Install directions, preserve every other image and sidecar.
 for aid,oid,dst,md,cand,base,cs,new,mb,mh,snap in prepared:
  assert sha(dst)==base
  atomic(dst,cand.read_bytes());assert sha(dst)==cs
  atomic(md,mb);assert sha(md)==mh;assets[aid]=copy.deepcopy(new)
 for oid in {r[1] for r in prepared}:
  sets[oid]['complete']=False;sets[oid]['notes']='Scoped support views installed; awaiting current source-plus-six independent whole-set review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries),'index_assets':len(ni['assets']),'view_sets':len(ni['view_sets'])},indent=2))
if __name__=='__main__':main()
