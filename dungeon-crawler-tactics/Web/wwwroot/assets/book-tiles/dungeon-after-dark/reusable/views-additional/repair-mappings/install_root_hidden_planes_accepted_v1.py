"""Guarded install of Root-accepted hidden planes; memorial planes remain held."""
from pathlib import Path
import json,hashlib,copy,struct,os
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json';CD=OUT/'candidates/root-dark-hidden-planes-20261026'
MAN=CD/'root-hidden-planes-candidate-manifest-v1.json';HAND=CD/'root-hidden-planes-handoff.json';PROOF=CD/'root-hidden-planes-candidate-proof-v1.json';DEC=OUT/'qa/root-dark-hidden-planes-v1-review.json';BEFORE=OUT/'prebuilt/root-dark-hidden-planes-before-v1'
ACCEPTED={('bubble-sea-coral-cluster','top'),('early-arenas-scrap-throne','top'),('safe-services-food-service-counter','top'),('starter-dungeon-bookcase-with-framed-photographs','top'),('starter-dungeon-wall-torch','rear')}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 m=json.loads(MAN.read_text());proof=json.loads(PROOF.read_text());hand=json.loads(HAND.read_text());idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']};entries=recipe['entries'];emap={e['asset_id']:e for e in entries}
 assert sha(MAN)==proof['manifest_sha256'] and sha(BOOK/proof['contact_path'])==proof['contact_sha256']
 assert sha(HAND)==m['handoff_original_sha256'] and sha(Path(hand['source_and_six_proof']['path']))==hand['source_and_six_proof']['sha256']
 bykey={(c['object_id'],c['view']):c for c in m['candidates']};assert set(bykey)==ACCEPTED|{('ghost-cemetery-memorial-stone','top'),('ghost-cemetery-memorial-stone','bottom')}
 # Persist the exact reviewer decision locally before any production write.
 decision={'reviewer':'root','decision':'five accepted; memorial TOP/BOTTOM held','manifest_path':MAN.relative_to(BOOK).as_posix(),'manifest_sha256':sha(MAN),'contact_path':m['contact_path'],'contact_sha256':m['contact_sha256'],'accepted':[{'object_id':o,'view':v,'candidate_path':bykey[(o,v)]['candidate_path'],'candidate_sha256':bykey[(o,v)]['candidate_sha256']} for o,v in sorted(ACCEPTED)],'held':[{'object_id':'ghost-cemetery-memorial-stone','view':v,'reason':'Root found candidate lacked shallow overhead cap/footprint and retained upright cross/candles; bottom wrongly full-square footprint versus thin slab side depth.'} for v in ('top','bottom')],'review_notes':'Install only exact accepted hashes. Memorial leaves remain unchanged and incomplete.'}
 decdata=json.dumps(decision,indent=2)+'\n'
 if DEC.exists(): assert DEC.read_text()==decdata
 else: atomic(DEC,decdata)
 dsha=sha(DEC);prepared=[]
 for key in sorted(ACCEPTED):
  c=bykey[key];oid,v=key;aid=oid+'.'+v;a=assets[aid];dest=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path']);cand=safe(BOOK,c['candidate_path']);src=safe(BOOK,c['source_path'])
  assert sha(src)==c['source_sha256'];assert sha(cand)==c['candidate_sha256'];assert c['dimensions_px']==[256,256]
  # Exact current six guard from the candidate row and current live files.
  for bv,r in c['base_six'].items():assert sha(safe(BOOK,r['path']))==r['sha256'],(oid,bv,'base changed')
  base=c['base_six'][v]['sha256'];assert sha(dest) in (base,c['candidate_sha256']), (aid,'live target differs from bound base')
  old=json.loads(md.read_text());assert old['image']['sha256']==base
  new=copy.deepcopy(old);new['image'].update(width=256,height=256,sha256=c['candidate_sha256'],rgba_sha256=rgba(cand))
  new.setdefault('provenance_history',[]).append({'candidate_id':'root-hidden-planes-v1:'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  inp=c['input'];new['provenance']={'method':'source-guided-orthographic-hidden-plane-correction','source_image':c['source_path'],'source_sha256':c['source_sha256'],'candidate_image':c['candidate_path'],'candidate_image_sha256':c['candidate_sha256'],'candidate_manifest':MAN.relative_to(BOOK).as_posix(),'candidate_manifest_sha256':sha(MAN),'candidate_contact':m['contact_path'],'candidate_contact_sha256':m['contact_sha256'],'candidate_review_record':DEC.relative_to(BOOK).as_posix(),'candidate_review_sha256':dsha,'raw_response':inp['raw_path'],'raw_response_sha256':inp['raw_sha256'],'tool_request_id':None,'local_request_label':c['local_request_label'],'tool_response_name':c['tool_response_name'],'tool_response_sha256':c['tool_response_sha256'],'prompt_path':inp['prompt_path'],'prompt_sha256':inp['prompt_sha256'],'normalization':copy.deepcopy(inp['normalization']),'extraction':copy.deepcopy(inp['extraction']),'notes':'Root-approved hidden view is illustrative inferred art, not recovered hidden pixels.'}
  for field in ('source_image','candidate_image','candidate_manifest','candidate_contact','candidate_review_record','raw_response','prompt_path'):
   assert not new['provenance'][field].startswith('/'),(aid,field)
   assert (BOOK/new['provenance'][field]).is_file(),(aid,field)
  mt=json.dumps(new,indent=2)+'\n';mh=hashlib.sha256(mt.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  e={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':c['candidate_path'].removeprefix('reusable/views-additional/'),'candidate_sha256':c['candidate_sha256'],'base_sha256':base,'final_sha256':c['candidate_sha256'],'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':DEC.relative_to(BOOK).as_posix(),'candidate_manifest_sha256':sha(MAN)}
  if aid in emap:assert emap[aid]['final_sha256']==c['candidate_sha256'] and emap[aid]['metadata_sha256']==mh
  prepared.append((aid,oid,dest,md,cand,base,c['candidate_sha256'],new,mt,mh,snap,e))
 for aid,oid,dest,md,cand,base,final,new,mt,mh,snap,e in prepared:
  bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json')
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
  sets[oid]['complete']=False;sets[oid]['notes']='Root-approved hidden-plane candidate installed; awaiting fresh live source-plus-six review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n');print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries),'review_sha256':dsha},indent=2))
if __name__=='__main__':main()
