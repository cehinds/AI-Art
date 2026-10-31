"""Install Root-accepted tree underside/base composite with current-hash guards."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json';CDIR=OUT/'candidates/page-dark-next-six-support6-v1/held-corrections-v1'
MANIFEST=CDIR/'tree-bottom-base-occlusion-v3-manifest.json';PROOF=CDIR/'tree-bottom-base-occlusion-v3-proof.json';REVIEW=OUT/'qa/root-tree-bottom-base-occlusion-v3-accepted.json';BEFORE=OUT/'prebuilt/tree-bottom-base-occlusion-v3-before';SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 c=json.loads(MANIFEST.read_text());proof=json.loads(PROOF.read_text());assert sha(MANIFEST)==proof['manifest_sha256'];assert c['candidate_sha256']=='2a23d8dac2823339f520f1d39e8a50ac080f989c8dc1f567e7e3da7bc57522ac'
 review={'status':'scoped accepted; live whole-set review required','reviewer':'root','object_id':c['object_id'],'view':c['view'],'candidate_path':c['candidate_path'],'candidate_sha256':c['candidate_sha256'],'contact_path':proof['contact_path'],'contact_sha256':proof['contact_sha256'],'manifest_path':'reusable/views-additional/candidates/page-dark-next-six-support6-v1/held-corrections-v1/tree-bottom-base-occlusion-v3-manifest.json','manifest_sha256':sha(MANIFEST)}
 if REVIEW.exists():assert json.loads(REVIEW.read_text())==review
 else:atomic(REVIEW,json.dumps(review,indent=2)+'\n')
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};oid=c['object_id'];view=c['view'];aid=f'{oid}.{view}'
 src=safe(BOOK,c['source_path']);assert sha(src)==c['source_sha256']
 for v,b in c['baseline_six'].items():assert sha(safe(BOOK,b['path']))==b['sha256'],(oid,v)
 candidate=safe(BOOK,c['candidate_path']);assert sha(candidate)==c['candidate_sha256'];a=assets[aid];dst=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path']);base=c['baseline_six'][view]['sha256'];assert sha(dst)==base
 old=json.loads(md.read_text());assert old['image']['sha256']==base;new=copy.deepcopy(old);im=Image.open(candidate).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=c['candidate_sha256'],rgba_sha256=rgba(candidate))
 new.setdefault('provenance_history',[]).append({'candidate_id':'page-dark-support-tree-bottom-v3:'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
 deriv=c['derivation'];prov={'method':'source-guided-bottom-canopy-with-occluding-stone-base','source_image':c['source_path'],'source_sha256':c['source_sha256'],'candidate_image':c['candidate_path'],'candidate_image_sha256':c['candidate_sha256'],'candidate_manifest':review['manifest_path'],'candidate_manifest_sha256':sha(MANIFEST),'candidate_review_record':'reusable/views-additional/qa/root-tree-bottom-base-occlusion-v3-accepted.json','candidate_review_sha256':sha(REVIEW),'contact_proof':proof['contact_path'],'contact_proof_sha256':sha(PROOF),**deriv,'notes':c['notes']}
 for k in ('source_path','base_candidate_path','canopy_candidate_path'):
  p=prov.get(k)
  if p:assert not p.startswith('/') and safe(BOOK,p).is_file(),(k,p)
 # normalize source key to schema name
 prov['source_sha256']=c['source_sha256'];new['provenance']=prov
 mb=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(mb).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
 ent={'asset_id':aid,'image_path':a['image']['path'],'candidate_path':c['candidate_path'].replace('reusable/views-additional/','',1),'candidate_sha256':c['candidate_sha256'],'base_sha256':base,'final_sha256':c['candidate_sha256'],'metadata_path':a['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'candidate_manifest_sha256':sha(MANIFEST)}
 entries=recipe['entries'];emap={e['asset_id']:e for e in entries};prior=emap.get(aid)
 if prior:
  assert prior['final_sha256']==base;entries[entries.index(prior)]=ent
 else:entries.append(ent)
 bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json')
 if bp.exists():assert sha(bp)==base
 else:atomic(bp,dst.read_bytes())
 if jp.exists():assert json.loads(jp.read_text())['image']['sha256']==base
 else:atomic(jp,md.read_bytes())
 sp=safe(BOOK,snap)
 if sp.exists():assert sha(sp)==mh
 else:atomic(sp,mb)
 atomic(dst,candidate.read_bytes());atomic(md,mb);assets[aid]=copy.deepcopy(json.loads(mb));sets[oid]['complete']=False;sets[oid]['notes']='Tree canopy underside and centered plain base installed; awaiting fresh Root whole-set review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[x['id']]) for x in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[x['object_id']]) for x in idx['view_sets']];assert len({x['id'] for x in ni['assets']})==len(ni['assets']) and len({x['object_id'] for x in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n');print(json.dumps({'installed':aid,'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
