"""Install Page-accepted corrected propeller axial and ruin cap plan directions."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json';MANIFEST=OUT/'candidates/page-dark-next-six-fixtures-v1/candidate-manifest.json';REVIEW=OUT/'qa/page-dark-fixtures-v2-held-three-candidate-review.json';BEFORE=OUT/'prebuilt/page-dark-fixtures-v2-before';SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(tmp,path)
m=json.loads(MANIFEST.read_text());r=json.loads(REVIEW.read_text());assert r['status']=='candidate-directions-accepted' and r['manifest_sha256']==sha(MANIFEST)
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};sets={s['object_id']:s for s in idx['view_sets']};recipe=json.loads(RECIPE.read_text());accepted={(e['object_id'],e['view']):e['sha256'] for e in r['accepted']};assert len(accepted)==3
mobjects={o['object_id']:o for o in m['objects']};prepared=[]
for (oid,v),approved in accepted.items():
 obj=mobjects[oid];e=obj['candidate_views'][v];assert e['candidate_sha256']==approved
 src=assets[f'{oid}.front']['source'];assert sha(safe(BOOK,src['source_image']))==src['source_sha256']==obj['source_sha256']
 for bv,b in obj['base_views'].items():assert sha(safe(BOOK,b['path']))==b['sha256'],f'{oid}.{bv}: base changed'
 aid=f'{oid}.{v}';a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);cand=safe(BOOK,e['candidate_path']);base=obj['base_views'][v]['sha256'];assert sha(dst)==base and sha(cand)==approved
 oldmeta=sha(mdst);new=copy.deepcopy(a);im=Image.open(cand).convert('RGBA');new['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)});new.setdefault('provenance_history',[]).append({'candidate_id':'page-dark-fixtures-v2-held-three:'+aid,'previous_provenance':copy.deepcopy(a.get('provenance',{})),'previous_image_sha256':base})
 prov={'source_image':src['source_image'],'source_sha256':src['source_sha256']}
 if oid=='bubble-airship-propeller-engine':
  prov.update({'method':'imagegen-leading-edge-vertical-rotor-top' if v=='top' else 'inferred-symmetric-vertical-rotor-underside-alias','raw_atlas':'reusable/views-additional/raw/fixture-propeller-leading-end-overhead-v2.png','raw_atlas_sha256':sha(safe(BOOK,'reusable/views-additional/raw/fixture-propeller-leading-end-overhead-v2.png')),'prompt_path':'reusable/views-additional/prompts/bubble-airship-propeller-leading-edge-plan-v3.txt','prompt_sha256':sha(safe(BOOK,'reusable/views-additional/prompts/bubble-airship-propeller-leading-edge-plan-v3.txt')),'reference_paths':[src['source_image'],'reusable/views-additional/images/'+oid+'.right.png','reusable/views-additional/images/'+oid+'.left.png'],'reference_sha256':[src['source_sha256'],obj['base_views']['right']['sha256'],obj['base_views']['left']['sha256']],'source_rect':{'crop_bbox':e['source_crop_bbox'],'normalized_size':e['normalized_size']},'normalization':{'scale':e['uniform_scale'],'frame_size':[256,256],'anchor_px':[128,128],'resampling':'nearest','distortion':'none; uniform isotropic scaling'},'notes':'Rotor edge lies at the leading Y end; dark scrap-metal engine body extends behind. Bottom reuses the top geometry by explicitly inferred rotational symmetry; underside is not recovered.'})
  if v=='bottom':prov.update({'derived_from_asset_id':oid+'.top','derived_from_image_sha256':approved,'alias_reason':'The axial geometry is treated as symmetric above and below; this is an inferred underside.'})
 else:
  prov.update({'method':'accepted-sand-footprint-with-arch-cap-top-composite','raw_atlas':'reusable/views-additional/raw/fixture-arch-exec-3754817c-c857-4b60-b29d-456778528e83.png','raw_atlas_sha256':sha(safe(BOOK,'reusable/views-additional/raw/fixture-arch-exec-3754817c-c857-4b60-b29d-456778528e83.png')),'prompt_path':'reusable/views-additional/prompts/bubble-sea-ruin-arch-top-v1.txt','prompt_sha256':sha(safe(BOOK,'reusable/views-additional/prompts/bubble-sea-ruin-arch-top-v1.txt')),'base_asset_id':e['base_asset_id'],'base_image_sha256':e['base_sha256'],'source_rect':{'cap_crop_bbox':e['source_crop_bbox'],'base_full_footprint':'reusable/views-additional/images/'+oid+'.bottom.png','overlay_offset_px':e['overlay_offset_px']},'normalization':{'frame_size':[256,256],'anchor_px':[128,128],'base':'exact accepted square sand/coral footprint','cap_scale':'uniform from generated cap crop','distortion':'none'},'notes':'Full sand/coral support footprint remains visible with the narrow stone arch cap and plant crowns along its front edge. Hidden construction inferred.'})
 new['provenance']=prov;md=json.dumps(new,indent=2)+'\n';mdsha=hashlib.sha256(md.encode()).hexdigest();snaprel=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json';prepared.append({'aid':aid,'oid':oid,'dst':dst,'mdst':mdst,'cand':cand,'new':new,'md':md,'mdsha':mdsha,'base':base,'oldmeta':oldmeta,'snaprel':snaprel,'e':e})
for x in prepared:
 assert sha(x['dst'])==x['base'] and sha(x['mdst'])==x['oldmeta'];b=BEFORE/(x['aid']+'.png');bm=BEFORE/(x['aid']+'.json');b.parent.mkdir(parents=True,exist_ok=True)
 if b.exists():assert sha(b)==x['base']
 else:b.write_bytes(x['dst'].read_bytes())
 if bm.exists():assert sha(bm)==x['oldmeta']
 else:bm.write_bytes(x['mdst'].read_bytes())
 atomic(safe(BOOK,x['snaprel']),x['md'].encode())
for x in prepared:
 assert sha(x['dst'])==x['base'] and sha(x['mdst'])==x['oldmeta'];atomic(x['dst'],x['cand'].read_bytes());atomic(x['mdst'],x['md']);assert sha(x['dst'])==sha(x['cand']) and sha(x['mdst'])==x['mdsha'];assets[x['aid']]=copy.deepcopy(x['new']);entries=recipe['entries'];rel_candidate=x['e']['candidate_path'].removeprefix('reusable/views-additional/')
 entries.append({'asset_id':x['aid'],'image_path':x['new']['image']['path'],'candidate_path':rel_candidate,'candidate_sha256':sha(x['cand']),'base_sha256':x['base'],'final_sha256':sha(x['cand']),'metadata_path':x['new']['metadata_path'],'metadata_snapshot_path':x['snaprel'],'metadata_sha256':x['mdsha'],'live_before_install_sha256':x['base'],'superseded_installed_sha256':x['base'],'review_record':'reusable/views-additional/qa/page-dark-fixtures-v2-held-three-candidate-review.json'})
for oid in {'bubble-airship-propeller-engine','bubble-sea-underwater-ruin-arch'}:sets[oid]['complete']=False;sets[oid]['notes']='Page-approved corrected directions installed; source and accepted siblings preserved. Awaiting current indexed source-plus-six whole-set review.'
# Record previously adjudicated complete fixtures now that their current whole-set hashes passed.
for oid in {'bubble-airship-aircraft-hangar-arch','bubble-sea-submarine-command-console','bubble-sea-pressure-pipe-manifold','thresholds-nebula-ceiling-panel'}:sets[oid]['complete']=True;sets[oid]['notes']='Whole-set current-hash source-plus-six PASS recorded by independent Page review after scoped repairs. Hidden surfaces and rotational symmetry are inferred, not recovered.'
newidx=copy.deepcopy(idx);newidx['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];newidx['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']];assert len({a['id'] for a in newidx['assets']})==len(newidx['assets']) and len({s['object_id'] for s in newidx['view_sets']})==len(newidx['view_sets'])
t=RECIPE.with_suffix('.json.tmp');t.write_text(json.dumps(recipe,indent=2)+'\n');os.replace(t,RECIPE);t=INDEX.with_suffix('.json.tmp');t.write_text(json.dumps(newidx,indent=2)+'\n');os.replace(t,INDEX);print(json.dumps({'installed':[x['aid'] for x in prepared],'completed_sets':['bubble-airship-aircraft-hangar-arch','bubble-sea-submarine-command-console','bubble-sea-pressure-pipe-manifold','thresholds-nebula-ceiling-panel'],'index_sha256':sha(INDEX),'recipe_entries':len(recipe['entries'])},indent=2))
