"""Guarded install of the accepted 14 + final 3 Scenery ground/opening leaves."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent; OUT=HERE.parent; BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'; RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
BASE=OUT/'candidates/scenery-dark-six-ground-openings-v2'
P1=BASE/'accepted-subset-install-packet.json'; M1=BASE/'accepted-subset-manifest.json'
P2=BASE/'final-three-install-packet.json'; M2=BASE/'final-three-manifest.json'
BEFORE=OUT/'prebuilt/scenery-ground-openings-17-before'; SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
CID='scenery-ground-openings-root-approved-17-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,p):
 q=(root/p).resolve();q.relative_to(root.resolve());return q
def rel(p):return Path(p).resolve().relative_to(BOOK.resolve()).as_posix()
def packrel(p):
 p=Path(p).as_posix()
 return p if p.startswith('reusable/') else 'reusable/views-additional/'+p
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 packet1=json.loads(P1.read_text());packet2=json.loads(P2.read_text());m1=json.loads(M1.read_text());m2=json.loads(M2.read_text())
 assert sha(M1)==packet1['accepted_subset_manifest_sha256']
 assert sha(M2)==packet2['manifest_sha256']
 assert len(m1['directions'])==14 and len(m2['directions'])==3
 directions=m1['directions']+m2['directions']; assert len({(x['object_id'],x['view']) for x in directions})==17
 # Verify every source and six-view preinstall guard before preparing any write.
 guards={}
 for man in (m1,m2):
  for g in man.get('preflight_source_and_six_guards',[]):
   oid=g['object_id']; guards[oid]=g
 for oid,g in guards.items():
  src=g.get('source',{});assert sha(safe(BOOK,src['path']))==src['sha256'],(oid,'source')
  for v,b in g.get('views',{}).items():assert sha(safe(BOOK,b['path']))==b['sha256'],(oid,v,'base')
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text())
 assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];emap={e['asset_id']:e for e in entries}
 prepared=[]
 for d in directions:
  oid=d['object_id'];v=d['view'];aid=f'{oid}.{v}';assert d['acceptance']['status']=='accepted_scoped'
  src=safe(BOOK,d['source_path']);assert sha(src)==d['source_sha256']
  cp=safe(OUT,d['candidate_path']);cs=d['candidate_sha256'];assert sha(cp)==cs
  a=assets[aid];dst=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path']);base=d['target_current_sha256']
  assert sha(dst) in (base,cs),(aid,'live target')
  old=json.loads(md.read_text());assert old['image']['sha256'] in (base,cs)
  new=copy.deepcopy(old);im=Image.open(cp).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(cp));new.setdefault('provenance_history',[]).append({'candidate_id':CID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  norm={k:d[k] for k in ('raw_atlas_path','raw_atlas_sha256','request_path','request_sha256','output_binding_path','output_binding_sha256','crop_bbox_alpha32_atlas','crop_raw_size','uniform_scale','normalized_size','anchor_px','resampling') if k in d}
  for k in ('raw_atlas_path','request_path','output_binding_path'):
   if norm.get(k): norm[k]=packrel(norm[k])
  carry=packrel(d['carried_from_candidate']) if d.get('carried_from_candidate') else None
  prov={'method':'scenery-source-ground-openings-candidate-install','source_image':rel(src),'source_sha256':sha(src),'candidate_image':rel(cp),'candidate_image_sha256':cs,'candidate_manifest':'reusable/views-additional/'+M1.relative_to(OUT).as_posix() if d in m1['directions'] else 'reusable/views-additional/'+M2.relative_to(OUT).as_posix(),'candidate_manifest_sha256':sha(M1) if d in m1['directions'] else sha(M2),'install_packet':'reusable/views-additional/'+P1.relative_to(OUT).as_posix() if d in m1['directions'] else 'reusable/views-additional/'+P2.relative_to(OUT).as_posix(),'install_packet_sha256':sha(P1) if d in m1['directions'] else sha(P2),'acceptance_note':d['acceptance']['note'],'carried_from_candidate':carry,'carried_candidate_sha256':d.get('carried_candidate_sha256'),'normalization':norm,'notes':'Root-approved candidate; hidden support/substrate construction is inferred where the view is occluded.'}
  for k in ('source_image','candidate_image','candidate_manifest','install_packet'):
   assert not prov[k].startswith('/') and safe(BOOK,prov[k]).is_file(),(aid,k)
  for k in ('carried_from_candidate','raw_atlas_path','request_path','output_binding_path'):
   val=prov.get(k) if k=='carried_from_candidate' else prov['normalization'].get(k)
   if val: assert not val.startswith('/') and safe(BOOK,val).is_file(),(aid,k,val)
  new['provenance']=prov;mt=json.dumps(new,indent=2)+'\n';mh=hashlib.sha256(mt.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':rel(cp).removeprefix('reusable/views-additional/'),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':prov['install_packet'],'candidate_manifest_sha256':prov['candidate_manifest_sha256']}
  if aid in emap:assert emap[aid]['final_sha256']==cs and emap[aid]['metadata_sha256']==mh
  prepared.append((aid,oid,dst,md,cp,base,cs,new,mt,mh,snap,ent))
 assert len(prepared)==17
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
  sets[oid]['complete']=False;sets[oid]['notes']='Root-approved ground/opening leaves installed; waiting for fresh source-plus-six review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
