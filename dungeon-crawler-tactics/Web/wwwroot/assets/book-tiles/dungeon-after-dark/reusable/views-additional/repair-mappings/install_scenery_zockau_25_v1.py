"""Guarded install of the Root-approved 19 + 6 Zockau plan/cap leaves."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;BASE=OUT/'candidates/scenery-dark-next-six-zockau-v1'
INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
P1=BASE/'accepted-subset-install-packet-v2.json';M1=BASE/'accepted-subset-manifest-v2.json'
P2=BASE/'final-six-install-packet-v3-after-approved19.json';M2=BASE/'remaining-six-manifest-v2.json'
BEFORE=OUT/'prebuilt/scenery-zockau-25-before';SNAP=OUT/'prebuilt/replay-sidecars-final-v1';CID='scenery-zockau-root-approved-25-v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,p):
 q=(root/p).resolve();q.relative_to(root.resolve());return q
def rel(p):return Path(p).resolve().relative_to(BOOK.resolve()).as_posix()
def packpath(p):
 p=Path(p)
 if p.is_absolute():return rel(p)
 q=BOOK/p
 if q.is_file():return p.as_posix()
 return rel(safe(OUT,p.as_posix()))
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def verify_guard(g):
 oid=g['object_id'];src=g['source'];assert sha(safe(BOOK,src['path']))==src['sha256'],(oid,'source')
 for v,b in g['views'].items():assert sha(safe(BOOK,b['path']))==b['sha256'],(oid,v)
def prep_direction(d,manpath,packetpath,assets):
 oid=d['object_id'];v=d['view'];aid=f'{oid}.{v}';src=safe(BOOK,d['source_path']);assert sha(src)==d['source_sha256'],(aid,'source')
 cp=safe(OUT,d['candidate_path']);cs=d['candidate_sha256'];assert sha(cp)==cs,(aid,'candidate')
 a=assets[aid];dst=safe(BOOK,a['image']['path']);base=d['base_sha256'];assert sha(dst)==base,(aid,'base')
 if d.get('base_path'): assert a['image']['path']==d['base_path']
 md=safe(BOOK,a['metadata_path']);old=json.loads(md.read_text());assert old['image']['sha256']==base
 new=copy.deepcopy(old);im=Image.open(cp).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(cp));new.setdefault('provenance_history',[]).append({'candidate_id':CID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
 fields={k:d[k] for k in ('raw_path','raw_sha256','request_path','request_sha256','crop_bbox_alpha64','cell_bbox','raw_component','component_mask','uniform_scale','resized_dimensions','canvas','placement_xy','filter','method','derived_from_candidate_path','derived_from_candidate_sha256','recipe_path','recipe_sha256','notes') if k in d}
 for k in ('raw_path','request_path','derived_from_candidate_path','recipe_path'):
  if fields.get(k): fields[k]=packpath(fields[k])
 prov={'method':'source-guided-component-extraction-or-rigid-plan-rotation','source_image':rel(src),'source_sha256':sha(src),'candidate_image':rel(cp),'candidate_image_sha256':cs,'candidate_manifest':rel(manpath),'candidate_manifest_sha256':sha(manpath),'install_packet':rel(packetpath),'install_packet_sha256':sha(packetpath),'derived_from':fields,'notes':'Root-approved plan/cap correction. Hidden construction remains inferred where not visible.'}
 for k in ('source_image','candidate_image','candidate_manifest','install_packet'):assert not prov[k].startswith('/') and safe(BOOK,prov[k]).is_file(),(aid,k)
 for k in ('raw_path','request_path','derived_from_candidate_path','recipe_path'):
  x=fields.get(k)
  if x:assert not x.startswith('/') and safe(BOOK,x).is_file(),(aid,k)
 new['provenance']=prov;mt=json.dumps(new,indent=2)+'\n';mh=hashlib.sha256(mt.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
 ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':rel(cp).removeprefix('reusable/views-additional/'),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':rel(packetpath),'candidate_manifest_sha256':sha(manpath)}
 return aid,oid,dst,md,cp,base,cs,new,mt,mh,snap,ent
def main():
 p1=json.loads(P1.read_text());m1=json.loads(M1.read_text());p2=json.loads(P2.read_text());m2=json.loads(M2.read_text())
 assert sha(M1)==p1['accepted_subset_manifest_sha256'] and len(m1['sets'])==19
 assert sha(M2)==p2['manifest_sha256'] and len(m2['sets'])==6
 # Both packets bind the original pre-install state for all objects.
 original={}
 for g in p1['preflight_source_and_six_guards']+p2['original_preinstall_source_and_six_guards']:original[g['object_id']]=g
 for g in original.values():verify_guard(g)
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];emap={e['asset_id']:e for e in entries}
 dirs1=[prep_direction(d,M1,P1,assets) for d in m1['sets']]
 dirs2=[prep_direction(d,M2,P2,assets) for d in m2['sets']]
 allrows=dirs1+dirs2;assert len(allrows)==25 and len({r[0] for r in allrows})==25
 for row in allrows:
  aid,oid,dst,md,cp,base,cs,new,mt,mh,snap,ent=row
  if aid in emap:assert emap[aid]['final_sha256']==cs and emap[aid]['metadata_sha256']==mh,(aid,'recipe')
 # Preserve original bytes and sidecars; then install approved19 before validating post19 guards.
 for row in allrows:
  aid,oid,dst,md,cp,base,cs,new,mt,mh,snap,ent=row;bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json');sp=safe(BOOK,snap)
  if not bp.exists():atomic(bp,dst.read_bytes())
  else:assert sha(bp)==base
  if not jp.exists():atomic(jp,md.read_bytes())
  else:assert json.loads(jp.read_text())['image']['sha256']==base
  if not sp.exists():atomic(sp,mt.encode())
  else:assert sha(sp)==mh
 for row in dirs1:
  aid,oid,dst,md,cp,base,cs,*_=row
  if sha(dst)==base:atomic(dst,cp.read_bytes())
  assert sha(dst)==cs
 # Check the entire exact post-19 source-plus-six state before final-six writes.
 for g in p2['post19_preflight_source_and_six_guards']:
  oid=g['object_id'];assert sha(safe(BOOK,g['source']['path']))==g['source']['sha256'],(oid,'post19 source')
  for v,b in g['views'].items():assert sha(safe(BOOK,b['path']))==b['sha256'],(oid,v,'post19')
 for row in dirs2:
  aid,oid,dst,md,cp,base,cs,*_=row
  assert sha(dst)==base,(aid,'final-six base')
  atomic(dst,cp.read_bytes());assert sha(dst)==cs
 # Commit all metadata/index only after every candidate leaf is live at its approved hash.
 for row in allrows:
  aid,oid,dst,md,cp,base,cs,new,mt,mh,snap,ent=row
  assert sha(dst)==cs
  if sha(md)!=mh:atomic(md,mt.encode())
  assert sha(md)==mh;assets[aid]=copy.deepcopy(new)
  if aid not in emap:entries.append(ent);emap[aid]=ent
  sets[oid]['complete']=False;sets[oid]['notes']='Root-approved Zockau directions installed; waiting for fresh canonical source-plus-six review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[r[0] for r in allrows],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
