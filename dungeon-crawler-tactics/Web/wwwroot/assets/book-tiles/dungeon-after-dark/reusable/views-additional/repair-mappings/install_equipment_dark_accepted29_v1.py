"""Install exactly the 29 Page-accepted Equipment dark masonry directions from their guard."""
from pathlib import Path
import json,hashlib,copy,struct,os,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;CD=OUT/'candidates/equipment-dark-masonry-rail8-20261026';GUARD=CD/'iron-station-trains-accepted29-install-guard-v1.json';INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json';BEFORE=OUT/'prebuilt/equipment-dark-accepted29-before-v1';QA=OUT/'qa'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 g=json.loads(GUARD.read_text());idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assert len(g['accepted_directions'])==29 and len(g['held_directions'])==7;assert g['install_authorized_for_accepted_directions'] is True
 for r in g['review_bindings']:
  candidate_root=CD
  review=Path('/workspace/scratch')/r['review_path'];assert review.exists() and sha(review)==r['review_sha256'];
  cp=candidate_root/r['review_contact_path'].split('/')[-1] if not r['review_contact_path'].startswith('reusable/') else BOOK/r['review_contact_path'];assert cp.exists() and sha(cp)==r['review_contact_sha256']
  manifest=candidate_root/r['candidate_manifest_path'];script=BOOK/r['corrected_script_path'];assert manifest.exists() and sha(manifest)==r['candidate_manifest_sha256'];assert script.exists() and sha(script)==r['corrected_script_sha256']
 # Copy immutable reviewer records into pack-owned QA for portable provenance, exact byte equality.
 QA.mkdir(exist_ok=True);reviews={}
 for r in g['review_bindings']:
  src=Path('/workspace/scratch')/r['review_path'];dst=QA/r['review_path'];
  if dst.exists():assert sha(dst)==r['review_sha256']
  else:atomic(dst,src.read_bytes())
  reviews[r['review_path']]=dst.relative_to(BOOK).as_posix()
 assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];emap={e['asset_id']:e for e in entries};symgroups=g['metadata_overrides']['symmetry_groups'];prepared=[]
 for c in g['accepted_directions']:
  oid,v=c['object_id'],c['view'];aid=oid+'.'+v;a=assets[aid];cand=safe(BOOK,c['candidate_path']);src=safe(BOOK,c['source_path']);dest=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path'])
  assert sha(cand)==c['candidate_sha256'] and sha(src)==c['source_sha256']
  assert sha(safe(BOOK,c['base_path']))==c['base_sha256'] and sha(dest) in (c['base_sha256'],c['candidate_sha256'])
  assert sha(safe(BOOK,c['raw_path']))==c['raw_sha256']
  if c.get('prompt_path'):assert sha(safe(BOOK,c['prompt_path']))==c['prompt_sha256']
  if c.get('geometry_guide_path'):assert sha(safe(BOOK,c['geometry_guide_path']))==c['geometry_guide_sha256']
  old=json.loads(md.read_text());assert old['image']['sha256']==c['base_sha256'];new=copy.deepcopy(old);im=Image.open(cand).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=c['candidate_sha256'],rgba_sha256=rgba(cand));new.setdefault('provenance_history',[]).append({'candidate_id':'equipment-dark-accepted29-v1:'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':c['base_sha256']})
  reviewbind=next(r for r in g['review_bindings'] if ('station' in oid and 'iron-stations' in r['candidate_manifest_path']) or ('iron-trains' in oid and 'iron-trains' in r['candidate_manifest_path']))
  manrel='reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/'+reviewbind['candidate_manifest_path'];manifest=BOOK/manrel;scriptpath=g['metadata_overrides']['iron_stations_script_path' if 'iron-stations' in oid else 'iron_trains_script_path']
  reviewpath=reviews[reviewbind['review_path']]
  prov={'method':'page-approved-source-bound-same-kit-orthographic-correction','source_image':c['source_path'],'source_sha256':c['source_sha256'],'candidate_image':c['candidate_path'],'candidate_image_sha256':c['candidate_sha256'],'candidate_manifest':manrel,'candidate_manifest_sha256':reviewbind['candidate_manifest_sha256'],'candidate_contact':reviewbind['review_contact_path'],'candidate_contact_sha256':reviewbind['review_contact_sha256'],'candidate_review_record':reviewpath,'candidate_review_sha256':reviewbind['review_sha256'],'installer_guard':GUARD.relative_to(BOOK).as_posix(),'installer_guard_sha256':sha(GUARD),'corrected_replay_script':scriptpath,'corrected_replay_script_sha256':sha(BOOK/scriptpath),'raw_response':c['raw_path'],'raw_response_sha256':c['raw_sha256'],'tool_request_id':None,'geometry_guide':c.get('geometry_guide_path'),'geometry_guide_sha256':c.get('geometry_guide_sha256'),'review_decisions':c.get('review_decision',[]),'notes':'Canonical target source remains identity authority; guide used for geometry only.'}
  if c.get('prompt_path'):prov.update(prompt_path=c['prompt_path'],prompt_sha256=c['prompt_sha256'])
  if 'iron-stations-station-tiled-masonry' in oid and v=='top':prov['source_plan_reuse']='native source plan after alpha cleanup; no redraw.'
  sym=next((x for x in symgroups if x['object_id']==oid and v in x['views']),None)
  if sym:prov['symmetry_group']={'views':sym['views'],'method':sym['method'],'reason':sym['reason']}
  for k in ['source_image','candidate_image','candidate_manifest','candidate_contact','candidate_review_record','installer_guard','corrected_replay_script','raw_response']:
   assert not prov[k].startswith('/') and (BOOK/prov[k]).is_file(),(aid,k,prov[k])
  if prov.get('geometry_guide'):assert not prov['geometry_guide'].startswith('/') and (BOOK/prov['geometry_guide']).is_file()
  if prov.get('prompt_path'):assert not prov['prompt_path'].startswith('/') and (BOOK/prov['prompt_path']).is_file()
  new['provenance']=prov;mt=json.dumps(new,indent=2)+'\n';mh=hashlib.sha256(mt.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json';entry={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':c['candidate_path'].removeprefix('reusable/views-additional/'),'candidate_sha256':c['candidate_sha256'],'base_sha256':c['base_sha256'],'final_sha256':c['candidate_sha256'],'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':c['base_sha256'],'superseded_installed_sha256':c['base_sha256'],'review_record':reviewpath,'candidate_manifest_sha256':reviewbind['candidate_manifest_sha256'],'installer_guard':GUARD.relative_to(BOOK).as_posix(),'installer_guard_sha256':sha(GUARD)}
  if aid in emap:assert emap[aid]['final_sha256']==entry['final_sha256'] and emap[aid]['metadata_sha256']==mh
  prepared.append((aid,oid,dest,md,cand,c['base_sha256'],c['candidate_sha256'],new,mt,mh,snap,entry))
 # Snapshot every guarded base before any production mutation.
 for aid,oid,dest,md,cand,base,final,new,mt,mh,snap,e in prepared:
  bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json');
  if bp.exists():assert sha(bp)==base
  else:atomic(bp,dest.read_bytes())
  if jp.exists():assert json.loads(jp.read_text())['image']['sha256']==base
  else:atomic(jp,md.read_bytes())
  sp=safe(BOOK,snap)
  if sp.exists():assert sha(sp)==mh
  else:atomic(sp,mt.encode())
 for aid,oid,dest,md,cand,base,final,new,mt,mh,snap,e in prepared:
  if sha(dest)==base:atomic(dest,cand.read_bytes())
  assert sha(dest)==final
  if sha(md)!=mh:atomic(md,mt.encode())
  assert sha(md)==mh;assets[aid]=copy.deepcopy(new)
  if aid not in emap:entries.append(e);emap[aid]=e
  sets[oid]['complete']=False;sets[oid]['notes']='Page-accepted Equipment directions installed; waiting for fresh current source-plus-six review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']];assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets']);atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n');print(json.dumps({'installed_count':len(prepared),'installed':[x[0] for x in prepared],'held_untouched':g['held_direction_count'],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
