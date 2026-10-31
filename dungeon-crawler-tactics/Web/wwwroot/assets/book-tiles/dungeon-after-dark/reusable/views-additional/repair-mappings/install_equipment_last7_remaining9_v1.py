"""Install the 9 Root-approved remaining last-seven candidate directions."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json';SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
BASE=OUT/'candidates/equipment-dark-last-seven-fixtures-20261026'
MANIFESTS=[('candidate-manifest-batch02-v1-accepted-v2.json','0795bf34580d4d80bbc805ecfad68b91c9a95a8d077f9fff404281ab536536ab'),('candidate-manifest-batch03-v1-accepted-v2.json','66382d5bbfb1ee55faa0a6a0f00b3f0bacf2ad05b76ebb4ba4fcc38e082979a0'),('candidate-manifest-wall-v2-accepted-v2.json','2cdd67f8a655210224f82ca6c6328c98371ad216b93e4ec704ae2c74ab0c74d5')]
BEFORE=OUT/'prebuilt/equipment-last7-remaining9-before';CID='equipment-last7-root-approved-remaining9-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,p):
 q=(root/p).resolve();q.relative_to(root.resolve());return q
def rel(p):return Path(p).resolve().relative_to(BOOK.resolve()).as_posix()
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 manifests=[]
 for name,expected in MANIFESTS:
  p=BASE/name;assert sha(p)==expected,(name,sha(p));manifests.append((p,json.loads(p.read_text())))
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];emap={e['asset_id']:e for e in entries};prepared=[]
 for mp,man in manifests:
  for s in man['sets']:
   oid=s['object_id'];src=safe(BOOK,s.get('source_path') or s['source']['path']);srcsha=s.get('source_sha256') or s['source']['sha256'];assert sha(src)==srcsha,(oid,'source')
   for v,b in s['base_current_views'].items():assert sha(safe(BOOK,b['path']))==b['sha256'],(oid,v,'base')
   for v,c in s['candidates'].items():
    aid=f'{oid}.{v}';cp=safe(BOOK,c['path']);cs=c['sha256'];assert sha(cp)==cs,(aid,'candidate')
    base=s['base_current_views'][v]['sha256'];a=assets[aid];dst=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path']);assert sha(dst)==base,(aid,'live')
    old=json.loads(md.read_text());assert old['image']['sha256']==base
    new=copy.deepcopy(old);im=Image.open(cp).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(cp));new.setdefault('provenance_history',[]).append({'candidate_id':CID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
    deriv={k:c[k] for k in c if k not in ('path','sha256')}
    for k,val in list(deriv.items()):
     if (k.endswith('_path') or k.endswith('_atlas')) and val:
      p=Path(val);deriv[k]=rel(p) if p.is_absolute() else (val if safe(BOOK,val).is_file() else rel(safe(OUT,val)))
    prov={'method':c.get('method','accepted-candidate-install'),'source_image':rel(src),'source_sha256':sha(src),'candidate_image':rel(cp),'candidate_image_sha256':cs,'candidate_manifest':rel(mp),'candidate_manifest_sha256':sha(mp),'handoff_sha256':man.get('handoff_sha256'),'activation_sha256':man.get('activation_sha256'),'derivation':deriv,'notes':'Root-approved scoped candidate; hidden surfaces are inferred where not shown.'}
    for k in ('source_image','candidate_image','candidate_manifest'):assert not prov[k].startswith('/') and safe(BOOK,prov[k]).is_file(),(aid,k)
    for k,val in deriv.items():
     if (k.endswith('_path') or k.endswith('_atlas')) and val:assert not val.startswith('/') and safe(BOOK,val).is_file(),(aid,k,val)
    new['provenance']=prov;mt=json.dumps(new,indent=2)+'\n';mh=hashlib.sha256(mt.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
    ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':rel(cp).removeprefix('reusable/views-additional/'),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':rel(mp),'candidate_manifest_sha256':sha(mp)}
    if aid in emap:assert emap[aid]['final_sha256']==cs and emap[aid]['metadata_sha256']==mh,(aid,'recipe')
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
  atomic(dst,cp.read_bytes());assert sha(dst)==cs;atomic(md,mt.encode());assert sha(md)==mh;assets[aid]=copy.deepcopy(new)
  if aid not in emap:entries.append(ent);emap[aid]=ent
  sets[oid]['complete']=False;sets[oid]['notes']='Root-approved last-seven scoped directions installed; waiting for fresh source-plus-six review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[r[0] for r in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
