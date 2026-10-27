"""Install Page-accepted Larracos corner directions with source/six/candidate hash guards."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
CDIR=OUT/'candidates/equipment-dark-masonry-rail8-20261026'
MANIFEST=CDIR/'larracos-candidate-manifest-v5.json'
REVIEW=Path('/workspace/scratch/page-equipment-larracos-v5-candidate-review.json')
REVIEW_COPY=OUT/'qa/page-equipment-larracos-v5-candidate-review.json'
BEFORE=OUT/'prebuilt/equipment-larracos-v5-before';SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp');tmp.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(tmp,p)
def main():
 m=json.loads(MANIFEST.read_text());r=json.loads(REVIEW.read_text())
 assert sha(MANIFEST)=='d58491b449ec1bb1180ec85df9986a68bb4e5c47e25dc6fc5cbdd081e12080ca'
 assert r['install_authorized'] is True and r['candidate_manifest']['sha256']==sha(MANIFEST)
 assert len(m['sets'])==12 and r['accepted_directions']==12 and r.get('held_directions')==0
 if REVIEW_COPY.exists():assert sha(REVIEW_COPY)==sha(REVIEW)
 else:atomic(REVIEW_COPY,REVIEW.read_bytes())
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text())
 assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];emap={e['asset_id']:e for e in entries};prepared=[]
 decisions={(x['object_id'],x['view']):x for x in r['decisions'] if x['decision']=='candidate-direction-accepted'}
 for c in m['sets']:
  oid=c['object_id'];v=c['view'];aid=f'{oid}.{v}';assert (oid,v) in decisions
  dec=decisions[(oid,v)]
  for key in ('candidate_path','candidate_sha256','base_path','base_sha256','source_path','source_sha256'):
   assert c[key]==dec[key],(aid,key)
  src=safe(BOOK,c['source_path']);base=safe(BOOK,c['base_path']);candidate=safe(OUT,c['candidate_path'])
  raw=safe(BOOK,c['raw_path']) if c.get('raw_path') else None;prompt=safe(BOOK,c['prompt_path']) if c.get('prompt_path') else None
  assert sha(src)==c['source_sha256'],f'{oid}: source changed'
  assert sha(base)==c['base_sha256'],f'{aid}: base changed'
  assert sha(candidate)==c['candidate_sha256'],f'{aid}: candidate changed'
  if raw: assert sha(raw)==c['raw_sha256'],f'{aid}: raw changed'
  if prompt: assert sha(prompt)==c['prompt_sha256'],f'{aid}: prompt changed'
  asset=assets[aid];dst=safe(BOOK,asset['image']['path']);md=safe(BOOK,asset['metadata_path'])
  assert sha(dst)==c['base_sha256'],f'{aid}: live target changed'
  old=json.loads(md.read_text());assert old['image']['sha256']==c['base_sha256']
  new=copy.deepcopy(old);im=Image.open(candidate).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=c['candidate_sha256'],rgba_sha256=rgba(candidate))
  new.setdefault('provenance_history',[]).append({'candidate_id':f'equipment-dark-larracos-v5:{aid}','previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':c['base_sha256']})
  canpath=f'reusable/views-additional/{c["candidate_path"]}'
  prov={'method':c['provenance_method'],'source_image':c['source_path'],'source_sha256':c['source_sha256'],'candidate_image':canpath,'candidate_image_sha256':c['candidate_sha256'],
        'candidate_manifest':'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/larracos-candidate-manifest-v5.json','candidate_manifest_sha256':sha(MANIFEST),
        'candidate_review_record':'reusable/views-additional/qa/page-equipment-larracos-v5-candidate-review.json','candidate_review_sha256':sha(REVIEW_COPY),
        'raw_response':c.get('raw_path'),'raw_response_sha256':c.get('raw_sha256'),'prompt_path':c.get('prompt_path'),'prompt_sha256':c.get('prompt_sha256'),
        'normalization':{'source_alpha_threshold':c['crop_alpha_threshold'],'source_bbox_xyxy':c['crop_bbox_xyxy'],'uniform_scale':c['uniform_scale'],'resized_dimensions':c['resized_dimensions'],'offset_px':c['offset_px'],'anchor_px':c['anchor_px'],'resampling':'nearest'},
        'notes':c['geometry_note']+' Hidden construction is inferred, not recovered.'}
  for k in ('source_image','candidate_image','candidate_manifest','candidate_review_record','raw_response','prompt_path'):
   if prov[k]: assert not prov[k].startswith('/') and safe(BOOK,prov[k]).is_file(),(aid,k,prov[k])
  new['provenance']=prov;mb=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(mb).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  ent={'asset_id':aid,'image_path':asset['image']['path'],'candidate_path':c['candidate_path'],'candidate_sha256':c['candidate_sha256'],'base_sha256':c['base_sha256'],'final_sha256':c['candidate_sha256'],'metadata_path':asset['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':c['base_sha256'],'superseded_installed_sha256':c['base_sha256'],'candidate_manifest_sha256':sha(MANIFEST)}
  prev=emap.get(aid)
  if prev:
   assert prev['final_sha256']==c['base_sha256'],f'{aid}: replay chain mismatch';entries[entries.index(prev)]=ent
  else:entries.append(ent)
  emap[aid]=ent;prepared.append((aid,oid,dst,md,candidate,c['base_sha256'],c['candidate_sha256'],mb,mh,snap))
 # Snapshot all exact before images/sidecars before mutation.
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
  assert sha(dst)==base;atomic(dst,cand.read_bytes());assert sha(dst)==cs
  atomic(md,mb);assert sha(md)==mh;assets[aid]=copy.deepcopy(json.loads(mb))
 for oid in {x[1] for x in prepared}:
  sets[oid]['complete']=False;sets[oid]['notes']='Larracos scoped corner views installed; awaiting fresh live source-plus-six review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
