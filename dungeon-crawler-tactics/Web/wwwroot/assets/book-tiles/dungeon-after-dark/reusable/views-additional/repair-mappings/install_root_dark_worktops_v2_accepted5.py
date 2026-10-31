"""Install only the five Root-accepted v2 unblocked worktop views, with source+six guards."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
MANIFEST=OUT/'candidates/root-dark-worktops-unblocked-20261026-v2/candidate-manifest-v2.json'
MANIFEST_SHA='0744c7aa770218f9698cc5a9b9dfd3664dcb6e163821784bb8653a5dd900ebd1'
CONTACT=OUT/'candidates/root-dark-worktops-unblocked-20261026-v2/candidate-source-plus-six-v2.png'
CONTACT_SHA='ab1e2b027765100a768d531f78f83468fb03eab4cb4fd02cb4409c2402f54c77'
ROOT149=Path('/tmp/root149-dark-worktops6.png.json')
BEFORE=OUT/'prebuilt/root-dark-worktops-v2-accepted5-before';CID='root-dark-worktops-v2-accepted5'
ACCEPT={
 ('great-race-transition-selection-chamber-console','right'):'accepted side profile scale',
 ('great-race-transition-selection-chamber-console','left'):'same-target mirrored opposite side profile',
 ('industry-menagerie-pipe-valve-cluster','top'):'accepted upright pipe mouth plan with edge-on valve',
 ('iron-trains-janitor-supply-cart','right'):'accepted short end view with bucket foreground',
 ('iron-trains-janitor-supply-cart','left'):'accepted opposite short end view with yellow bag foreground',
}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,p):
 q=(root/p).resolve();q.relative_to(root.resolve());return q
def rel(p):return Path(p).resolve().relative_to(BOOK.resolve()).as_posix()
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp');tmp.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(tmp,p)
def main():
 assert sha(MANIFEST)==MANIFEST_SHA,sha(MANIFEST);assert sha(CONTACT)==CONTACT_SHA,sha(CONTACT)
 man=json.loads(MANIFEST.read_text());proof=json.loads(ROOT149.read_text());records=proof['records']
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']}
 entries=recipe['entries'];entrymap={e['asset_id']:e for e in entries};manifest_map={(r['object_id'],r['view']):r for r in man['candidates']};prepared=[]
 for oid,v in ACCEPT:
  aid=f'{oid}.{v}';rec=records[f'book-tiles/dungeon-after-dark::{oid}'];src=safe(BOOK,rec['source']);assert sha(src)==rec['source_sha256'],(oid,'source changed')
  for view,path in rec['view_paths'].items():assert sha(safe(BOOK,path))==rec['image_hashes'][view],(oid,view,'source+six base changed')
  base=rec['image_hashes'][v];row=manifest_map[(oid,v)];cand=safe(BOOK,row['candidate_path']);cs=row['candidate_sha256'];assert sha(cand)==cs,(aid,'candidate')
  asset=assets[aid];dst=safe(BOOK,asset['image']['path']);md=safe(BOOK,asset['metadata_path']);assert sha(dst)==base,(aid,'live base')
  old=json.loads(md.read_text());assert old['image']['sha256']==base
  # Prompt/result record for generated raw; left console is an exact same-target mirror of right.
  deriv=copy.deepcopy(row)
  rawpath=OUT/'raw/root-dark-worktops6-20261026'/Path(row['source_raw']).name;assert rawpath.is_file() and sha(rawpath)==row['source_raw_sha256']
  if oid=='great-race-transition-selection-chamber-console': result_path=OUT/'raw/root-dark-worktops6-20261026/console-right-v3.result.json'
  elif oid=='industry-menagerie-pipe-valve-cluster': result_path=OUT/'raw/root-dark-worktops6-20261026/pipe-top-v3.result.json'
  elif v=='right': result_path=OUT/'raw/root-dark-worktops6-20261026/janitor-right-v3.result.json'
  else: result_path=OUT/'raw/root-dark-worktops6-20261026/janitor-left-v2.result.json'
  result=json.loads(result_path.read_text());pp=Path(result['prompt_path']);prompt_path=(BOOK/pp if pp.is_absolute() or str(pp).startswith('reusable/views-additional/') else OUT/'raw/root-dark-worktops6-20261026'/pp);assert sha(prompt_path)==result['prompt_sha256']
  new=copy.deepcopy(old);im=Image.open(cand).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba_sha(cand))
  new.setdefault('provenance_history',[]).append({'candidate_id':CID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  # Keep canonical target source separate from the source/native style/layout references in the local result record.
  prov={'method':'root-approved-candidate-extraction-uniform-normalization','source_image':rel(src),'source_sha256':sha(src),
   'candidate_image':rel(cand),'candidate_image_sha256':cs,'candidate_manifest':rel(MANIFEST),'candidate_manifest_sha256':sha(MANIFEST),
   'candidate_contact':rel(CONTACT),'candidate_contact_sha256':sha(CONTACT),'candidate_review_authority':'Root scoped review; five accepted directions only; Console front/rear and Pipe bottom held.',
   'raw_response':rel(rawpath),'raw_response_sha256':sha(rawpath),'generation_result_record':rel(result_path),'generation_result_sha256':sha(result_path),
   'prompt_path':rel(prompt_path),'prompt_sha256':sha(prompt_path),'normalization':{k:deriv[k] for k in ('dominant_component_alpha64_bbox_xyxy','dominant_component_pixels','connectivity','mask_alpha_threshold','mask_dilation_iterations','crop_alpha0_bbox_xyxy','raw_component_size','target_bbox_size','uniform_scale','output_bbox_size','resample','canvas','anchor','method') if k in deriv},
   'notes':'Only the accepted direction is installed. Hidden surfaces are inferred; no anisotropic rescaling.'}
  if (oid,v)==('great-race-transition-selection-chamber-console','left'):
   prov['symmetry_inference']={'type':'horizontal-mirror','donor_view':'right','donor_candidate':rel(safe(BOOK,manifest_map[(oid,'right')]['candidate_path'])),'donor_candidate_sha256':manifest_map[(oid,'right')]['candidate_sha256'],'reason':'Root accepted opposite console side silhouette as same-target mirror; right/left monitor modules share height/material.'}
  new['provenance']=prov;mb=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(mb).hexdigest();snapshot=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
  ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':rel(cand).replace('reusable/views-additional/','',1),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snapshot,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':rel(MANIFEST),'candidate_manifest_sha256':sha(MANIFEST)}
  if aid in entrymap:assert entrymap[aid]['final_sha256']==base,(aid,'unexpected previous replay');entries[entries.index(entrymap[aid])]=ent
  else:entries.append(ent)
  entrymap[aid]=ent;prepared.append((aid,oid,v,dst,md,cand,base,cs,new,mb,mh,snapshot))
 assert len(prepared)==5
 # Complete preflight for all five before making any production writes.
 for aid,oid,v,dst,md,cand,base,cs,new,mb,mh,snapshot in prepared:
  bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json');sp=safe(BOOK,snapshot)
  if bp.exists():assert sha(bp)==base
  if jp.exists():assert json.loads(jp.read_text())['image']['sha256']==base
  if sp.exists():assert sha(sp)==mh
 # Preserve exact previous bytes and snapshots.
 for aid,oid,v,dst,md,cand,base,cs,new,mb,mh,snapshot in prepared:
  if not (BEFORE/(aid+'.png')).exists():atomic(BEFORE/(aid+'.png'),dst.read_bytes())
  if not (BEFORE/(aid+'.json')).exists():atomic(BEFORE/(aid+'.json'),md.read_bytes())
  sp=safe(BOOK,snapshot)
  if not sp.exists():atomic(sp,mb)
 # Install exact reviewed candidates and sidecars.
 for aid,oid,v,dst,md,cand,base,cs,new,mb,mh,snapshot in prepared:
  atomic(dst,cand.read_bytes());assert sha(dst)==cs;atomic(md,mb);assert sha(md)==mh;assets[aid]=copy.deepcopy(new)
 for oid in {r[1] for r in prepared}:sets[oid]['complete']=False;sets[oid]['notes']='Root-approved scoped v2 candidates installed; held sibling planes remain pending.'
 # This exact two-view mirror relation is accepted directly on the view_set record.
 syms=sets['great-race-transition-selection-chamber-console'].setdefault('symmetry',[])
 decl={'views':['right','left'],'reason':'Root-approved same-target horizontal mirror for the two console side elevations; common-height four-monitor module profile is symmetric.'}
 if decl not in syms:syms.append(decl)
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
