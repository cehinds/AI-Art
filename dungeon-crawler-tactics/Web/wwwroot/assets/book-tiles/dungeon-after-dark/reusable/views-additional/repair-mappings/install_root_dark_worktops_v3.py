from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
MAN=OUT/'candidates/root-dark-worktops-unblocked-20261026-v3/candidate-manifest-v3.json';MAN_SHA='1304a65409888de0a8bf186fa1cdbc3e03a45b96fe5f433694b58621e0fd1ce5'
BEFORE=OUT/'prebuilt/root-dark-worktops-v3-before';CID='root-dark-worktops-v3-root-approved-three';VIEWS=('front','top','right','left','bottom','rear')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,p):
 q=(Path(p) if Path(p).is_absolute() else root/p).resolve();q.relative_to(root.resolve());return q
def rel(p):return Path(p).resolve().relative_to(BOOK.resolve()).as_posix()
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 assert sha(MAN)==MAN_SHA
 m=json.loads(MAN.read_text());assert m['reviewer']=='root' and m['installer']=='views_dark_books'
 ix=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in ix['assets']};sets={s['object_id']:copy.deepcopy(s) for s in ix['view_sets']};entries=recipe['entries'];emap={e['asset_id']:e for e in entries};prepared=[];snapshot={}
 rows=m['candidates'];assert len(rows)==3
 # Capture and guard the actual full six-view bases for each target object before any output changes.
 for oid in sorted({r['object_id'] for r in rows}):
  srows=[r for r in rows if r['object_id']==oid];source=safe(BOOK,srows[0]['source_path']);assert sha(source)==srows[0]['source_sha256']
  snapshot[oid]={'source_path':rel(source),'source_sha256':sha(source),'views':{}}
  for v in VIEWS:
   aid=f'{oid}.{v}';a=assets[aid];p=safe(BOOK,a['image']['path']);h=sha(p);snapshot[oid]['views'][v]={'path':rel(p),'sha256':h}
   r=next((x for x in srows if x['view']==v),None)
   if r: assert h==r['current_sha256'],(aid,'candidate base changed')
 for r in rows:
  oid,v=r['object_id'],r['view'];aid=f'{oid}.{v}';source=safe(BOOK,r['source_path']);candidate=safe(BOOK,r['candidate_path']);raw=safe(BOOK,r['raw_path']);result=safe(BOOK,r['result_path']);prompt=safe(BOOK,r['prompt_path'])
  for p,k in ((source,'source_sha256'),(candidate,'candidate_sha256'),(raw,'raw_sha256'),(result,'result_sha256'),(prompt,'prompt_sha256')):assert sha(p)==r[k],(aid,k)
  a=assets[aid];dst=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path']);base=r['current_sha256'];assert sha(dst)==base,(aid,'live base')
  old=json.loads(md.read_text());assert old['image']['sha256']==base
  new=copy.deepcopy(old);im=Image.open(candidate).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=sha(candidate),rgba_sha256=rgba(candidate));new.setdefault('provenance_history',[]).append({'candidate_id':CID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  deriv={k:r[k] for k in ('method','raw_path','raw_sha256','result_path','result_sha256','prompt_path','prompt_sha256','component_alpha64_bbox_xyxy','component_pixels','target_bbox_size','output_bbox_size','uniform_scale','anchor','connectivity','alpha_threshold','resample','tool_request_id','request_label')}
  contact=m['contacts'][oid];prov={'method':'root-approved-source-bound-candidate-uniform-extraction','source_image':rel(source),'source_sha256':sha(source),'candidate_image':rel(candidate),'candidate_image_sha256':sha(candidate),'candidate_manifest':rel(MAN),'candidate_manifest_sha256':sha(MAN),'candidate_contact':contact['path'],'candidate_contact_sha256':contact['sha256'],'derivation':deriv,'notes':'Root accepted this scoped direction from source-plus-six candidate contact; fitted isotropically without stretching. Hidden construction is inferred where not visible.'}
  for key in ('source_image','candidate_image','candidate_manifest','candidate_contact'):
   assert not prov[key].startswith('/') and safe(BOOK,prov[key]).is_file(),(aid,key)
  new['provenance']=prov;mb=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(mb).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json';ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':rel(candidate).removeprefix('reusable/views-additional/'),'candidate_sha256':sha(candidate),'base_sha256':base,'final_sha256':sha(candidate),'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':rel(MAN),'candidate_manifest_sha256':sha(MAN)}
  if aid in emap:assert emap[aid]['final_sha256']==base,(aid,'existing replay chain must start at current base')
  prepared.append((aid,oid,dst,md,candidate,base,new,mb,mh,snap,ent));r['output_candidate_sha256']=sha(candidate)
 assert len(prepared)==3 and len({x[0] for x in prepared})==3
 for aid,oid,dst,md,candidate,base,new,mb,mh,snap,ent in prepared:
  bp=BEFORE/f'{aid}.png';jp=BEFORE/f'{aid}.json';sp=safe(BOOK,snap)
  if bp.exists():assert sha(bp)==base
  if jp.exists():assert json.loads(jp.read_text())['image']['sha256']==base
  if sp.exists():assert sha(sp)==mh
 for aid,oid,dst,md,candidate,base,new,mb,mh,snap,ent in prepared:
  bp=BEFORE/f'{aid}.png';jp=BEFORE/f'{aid}.json';sp=safe(BOOK,snap)
  if not bp.exists():atomic(bp,dst.read_bytes())
  if not jp.exists():atomic(jp,md.read_bytes())
  if not sp.exists():atomic(sp,mb)
 for aid,oid,dst,md,candidate,base,new,mb,mh,snap,ent in prepared:
  atomic(dst,candidate.read_bytes());atomic(md,mb);assert sha(dst)==sha(candidate) and sha(md)==mh;assets[aid]=copy.deepcopy(new)
  if aid in emap:entries[entries.index(emap[aid])]=ent
  else:entries.append(ent)
  emap[aid]=ent;sets[oid]['complete']=False;sets[oid]['notes']='Root-approved final scoped views installed; awaiting fresh whole-set review.'
 ni=copy.deepcopy(ix);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in ix['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in ix['view_sets']];assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 tx={'candidate_id':CID,'manifest_path':rel(MAN),'manifest_sha256':sha(MAN),'preinstall_source_six':snapshot,'installed':{r[0]:{'candidate_sha256':sha(r[4]),'previous_sha256':r[5]} for r in prepared},'index_sha256':sha(INDEX),'recipe_sha256':sha(RECIPE)};tp=OUT/'qa/root-dark-worktops-v3-install-transaction.json';atomic(tp,json.dumps(tx,indent=2)+'\n');print(json.dumps({'installed':list(tx['installed']),'index_sha256':tx['index_sha256'],'recipe_sha256':tx['recipe_sha256'],'transaction':rel(tp),'transaction_sha256':sha(tp)},indent=2))
if __name__=='__main__':main()
