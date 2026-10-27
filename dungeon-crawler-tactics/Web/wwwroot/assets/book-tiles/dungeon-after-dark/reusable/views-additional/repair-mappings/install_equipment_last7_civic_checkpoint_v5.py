"""Install two Root-approved last-seven leaves under exact current/source/candidate guards."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
MANIFEST=OUT/'candidates/equipment-dark-last-seven-fixtures-20261026/candidate-manifest-last7-civic-checkpoint-accepted-v5.json';MANIFEST_SHA='629d832b9a454bd6a32d26d35fe9f8d8ab9b01248e242777e746484db4f83b1d'
BEFORE=OUT/'prebuilt/equipment-last7-civic-checkpoint-v5-before';CID='equipment-last7-civic-checkpoint-v5-root-accepted'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,p):
 q=(root/p).resolve();q.relative_to(root.resolve());return q
def rel(p):return Path(p).resolve().relative_to(BOOK.resolve()).as_posix()
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def norm(v):
 if isinstance(v,dict):return {k:norm(x) for k,x in v.items()}
 if isinstance(v,list):return [norm(x) for x in v]
 if isinstance(v,str) and v.startswith('/'):
  try:return rel(v)
  except ValueError:return v
 return v
def main():
 assert sha(MANIFEST)==MANIFEST_SHA
 man=json.loads(MANIFEST.read_text());idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text())
 assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];emap={e['asset_id']:e for e in entries};prepared=[]
 assert man['installer']=='views_dark_books'
 for s in man['sets']:
  oid=s['object_id'];src=safe(BOOK,s['source']['path']);assert sha(src)==s['source']['sha256'],(oid,'source')
  for v,b in s['base_current_views'].items():assert sha(safe(BOOK,b['path']))==b['sha256'],(oid,v,'base')
  for v,c in s['candidates'].items():
   aid=f'{oid}.{v}';cand=safe(BOOK,c['path']);cs=c['sha256'];assert sha(cand)==cs,(aid,'candidate')
   base=s['base_current_views'][v]['sha256'];asset=assets[aid];dst=safe(BOOK,asset['image']['path']);md=safe(BOOK,asset['metadata_path']);assert sha(dst)==base,(aid,'live')
   old=json.loads(md.read_text());assert old['image']['sha256']==base
   raw=safe(BOOK,c['raw_path']);req=safe(BOOK,c['request_path']);nrm=safe(BOOK,c['normalizer_path']);assert sha(raw)==c['raw_sha256'] and sha(req)==c['request_sha256'] and sha(nrm)==c['normalizer_sha256']
   rq=json.loads(req.read_text());prompt=rq.get('prompt','');assert prompt
   prompt_path=OUT/'prompts/equipment-dark-last7-v5'/f'{req.stem}.txt';prompt_bytes=(prompt+'\n').encode()
   if prompt_path.exists():assert prompt_path.read_bytes()==prompt_bytes
   new=copy.deepcopy(old);im=Image.open(cand).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(cand))
   new.setdefault('provenance_history',[]).append({'candidate_id':CID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
   deriv={'method':c['method'],'raw_path':rel(raw),'raw_sha256':sha(raw),'request_path':rel(req),'request_sha256':sha(req),'request_id':rq.get('request_id',rq.get('id')),'normalizer_path':rel(nrm),'normalizer_sha256':sha(nrm)}
   prov={'method':'root-approved-focused-candidate-install','source_image':rel(src),'source_sha256':sha(src),'candidate_image':rel(cand),'candidate_image_sha256':cs,'candidate_manifest':rel(MANIFEST),'candidate_manifest_sha256':sha(MANIFEST),'source_six_proof_sha256':man['source_six_proof_sha256'],'derivation':deriv,'prompt_path':rel(prompt_path),'prompt_sha256':hashlib.sha256(prompt_bytes).hexdigest(),'notes':'Scoped accepted direction. Hidden details are inferred, not recovered.'}
   new['provenance']=prov;mb=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(mb).hexdigest();snapshot=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
   ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':rel(cand).replace('reusable/views-additional/','',1),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snapshot,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':rel(MANIFEST),'candidate_manifest_sha256':sha(MANIFEST)}
   if aid in emap:assert emap[aid]['final_sha256']==base;entries[entries.index(emap[aid])]=ent
   else:entries.append(ent)
   emap[aid]=ent;prepared.append((aid,oid,dst,md,cand,base,cs,new,mb,mh,snapshot,prompt_path,prompt_bytes))
 assert len(prepared)==2
 for aid,oid,dst,md,cand,base,cs,new,mb,mh,snapshot,prompt_path,prompt_bytes in prepared:
  bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json');sp=safe(BOOK,snapshot)
  if bp.exists():assert sha(bp)==base
  if jp.exists():assert json.loads(jp.read_text())['image']['sha256']==base
  if sp.exists():assert sha(sp)==mh
 for aid,oid,dst,md,cand,base,cs,new,mb,mh,snapshot,prompt_path,prompt_bytes in prepared:
  if not (BEFORE/(aid+'.png')).exists():atomic(BEFORE/(aid+'.png'),dst.read_bytes())
  if not (BEFORE/(aid+'.json')).exists():atomic(BEFORE/(aid+'.json'),md.read_bytes())
  sp=safe(BOOK,snapshot)
  if not sp.exists():atomic(sp,mb)
  atomic(prompt_path,prompt_bytes)
 for aid,oid,dst,md,cand,base,cs,new,mb,mh,snapshot,prompt_path,prompt_bytes in prepared:
  atomic(dst,cand.read_bytes());assert sha(dst)==cs;atomic(md,mb);assert sha(md)==mh;assets[aid]=copy.deepcopy(new)
 for oid in {r[1] for r in prepared}:sets[oid]['complete']=False;sets[oid]['notes']='Root-approved focused leaves installed; awaiting fresh whole source-plus-six review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
