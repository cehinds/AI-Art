"""Install the refreshed five facade candidates and four Root-approved last7 leaves."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json';SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
F=OUT/'candidates/equipment-dark-six-cemetery-havana-facades-20261026/candidate-manifest-focused-v5-refreshed-guard.json'
L=OUT/'candidates/equipment-dark-last-seven-fixtures-20261026/candidate-manifest-batch01-v1.json'
BEFORE=OUT/'prebuilt/equipment-facade-last7-v1-before';CID='equipment-dark-facade-last7-root-page-approved-v1'
LAST7={('great-race-transition-fractured-maze-slab','top'),('great-race-transition-fractured-maze-slab','bottom'),('hunting-shrines-hunter-trap-mechanism','top'),('hunting-shrines-hunter-trap-mechanism','bottom')}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,p):
 q=(root/p).resolve();q.relative_to(root.resolve());return q
def rel(p):return Path(p).resolve().relative_to(BOOK.resolve()).as_posix()
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def candidate_rows_focused(d):
 allowed={(x['object_id'],x['view']):x for x in d['install_authorized_directions']}
 for s in d['sets']:
  for v,c in s['candidates'].items():
   k=(s['object_id'],v)
   if k not in allowed:continue
   assert allowed[k]['sha256']==c['sha256']
   yield s,k[0],v,c,s['source'],s['base_current_views']
def candidate_rows_last7(d):
 for s in d['sets']:
  for v,c in s['candidates'].items():
   if (s['object_id'],v) in LAST7:yield s,s['object_id'],v,c,{'path':s['source_path'],'sha256':s['source_sha256']},s['base_current_views']
def main():
 f=json.loads(F.read_text());l=json.loads(L.read_text())
 assert f['installer']=='views_dark_books' and f['reviewer']=='page_inventory'
 assert len(f['install_authorized_directions'])==5 and sha(F)==hashlib.sha256(F.read_bytes()).hexdigest()
 assert sha(L)=='cf3a04e6e572b4f64fa9879cf0b3ed710e5d48d72745e325551ee85f3ca8ab7e'
 # Validate top-level provenance dependencies.
 for d in (f,l):
  for k in ('generation_provenance_path','extractor_path','normalizer_path','supplemental_request_path'):
   val=d.get(k)
   if val and not Path(val).is_absolute():assert safe(BOOK,val).is_file(),(k,val)
  for k in ('generation_provenance_path','normalizer_path','supplemental_request_path'):
   val=d.get(k)
   if val and d.get(k.replace('_path','_sha256')):assert sha(safe(BOOK,val))==d[k.replace('_path','_sha256')],k
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];emap={e['asset_id']:e for e in entries};prepared=[]
 for manpath,man,iterator in ((F,f,candidate_rows_focused),(L,l,candidate_rows_last7)):
  for s,oid,v,c,source,baseviews in iterator(man):
   aid=f'{oid}.{v}';src=safe(BOOK,source['path']);assert sha(src)==source['sha256'],(aid,'source')
   for bv,b in baseviews.items():assert sha(safe(BOOK,b['path']))==b['sha256'],(oid,bv,'base')
   cp=safe(BOOK,c['path']);cs=c['sha256'];assert sha(cp)==cs,(aid,'candidate')
   base=baseviews[v]['sha256'];a=assets[aid];dst=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path']);assert sha(dst)==base,(aid,'target')
   old=json.loads(md.read_text());assert old['image']['sha256']==base
   new=copy.deepcopy(old);im=Image.open(cp).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(cp));new.setdefault('provenance_history',[]).append({'candidate_id':CID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
   evidence={k:c[k] for k in c if k not in ('path','sha256')}
   # Normalize evidence path fields so live metadata contains only pack-root relative paths.
   for key,val in list(evidence.items()):
    if (key.endswith('_path') or key.endswith('_atlas')) and val:
     pp=Path(val)
     evidence[key]=rel(pp) if pp.is_absolute() else (val if safe(BOOK,val).is_file() else rel(safe(OUT,val)))
   prov={'method':c.get('method','accepted-candidate-install'),'source_image':rel(src),'source_sha256':sha(src),'candidate_image':rel(cp),'candidate_image_sha256':cs,'candidate_manifest':rel(manpath),'candidate_manifest_sha256':sha(manpath),'contact_path':rel(safe(BOOK,man['contact_path'])) if man.get('contact_path') and Path(man['contact_path']).is_absolute() else (man.get('contact_path') if man.get('contact_path','').startswith('reusable/') else None),'contact_sha256':man.get('contact_sha256'),'generation_provenance':rel(safe(BOOK,man['generation_provenance_path'])) if man.get('generation_provenance_path') and Path(man['generation_provenance_path']).is_absolute() else man.get('generation_provenance_path'),'generation_provenance_sha256':man.get('generation_provenance_sha256'),'derivation':evidence,'notes':c.get('notes','Root/Page-approved scoped correction; hidden surfaces inferred where appropriate.')}
   for k in ('source_image','candidate_image','candidate_manifest'):
    assert not prov[k].startswith('/') and safe(BOOK,prov[k]).is_file(),(aid,k)
   if prov['contact_path']:assert not prov['contact_path'].startswith('/') and safe(BOOK,prov['contact_path']).is_file()
   gp=prov.get('generation_provenance')
   if gp:assert not gp.startswith('/') and safe(BOOK,gp).is_file()
   for k,val in evidence.items():
    if k.endswith('_path') and val:assert not val.startswith('/') and safe(BOOK,val).is_file(),(aid,k,val)
   new['provenance']=prov;mt=json.dumps(new,indent=2)+'\n';mh=hashlib.sha256(mt.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
   ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':rel(cp).removeprefix('reusable/views-additional/'),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':rel(manpath),'candidate_manifest_sha256':sha(manpath)}
   if aid in emap:assert emap[aid]['final_sha256']==cs and emap[aid]['metadata_sha256']==mh,(aid,'existing recipe')
   prepared.append((aid,oid,dst,md,cp,base,cs,new,mt,mh,snap,ent))
 assert len(prepared)==9 and len({r[0] for r in prepared})==9
 for aid,oid,dst,md,cp,base,cs,new,mt,mh,snap,ent in prepared:
  bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json');sp=safe(BOOK,snap)
  if not bp.exists():atomic(bp,dst.read_bytes())
  else:assert sha(bp)==base
  if not jp.exists():atomic(jp,md.read_bytes())
  else:assert json.loads(jp.read_text())['image']['sha256']==base
  if not sp.exists():atomic(sp,mt.encode())
  else:assert sha(sp)==mh
 for aid,oid,dst,md,cp,base,cs,new,mt,mh,snap,ent in prepared:
  if sha(dst)==base:atomic(dst,cp.read_bytes())
  assert sha(dst)==cs
  if sha(md)!=mh:atomic(md,mt.encode())
  assert sha(md)==mh;assets[aid]=copy.deepcopy(new)
  if aid not in emap:entries.append(ent);emap[aid]=ent
  sets[oid]['complete']=False;sets[oid]['notes']='Root/Page-approved scoped directions installed; awaiting fresh whole-set review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[r[0] for r in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
