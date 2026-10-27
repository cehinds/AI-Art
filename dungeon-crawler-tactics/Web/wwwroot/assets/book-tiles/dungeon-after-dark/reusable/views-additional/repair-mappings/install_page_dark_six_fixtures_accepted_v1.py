"""Install only the seven Page-accepted directions; leave held propeller/arch views untouched."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
MANIFEST=OUT/'candidates/page-dark-next-six-fixtures-v1/candidate-manifest.json';REVIEW=OUT/'qa/page-dark-six-fixtures-candidate-review-v1.json';BEFORE=OUT/'prebuilt/page-dark-six-fixtures-v1-before';SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(tmp,path)
manifest=json.loads(MANIFEST.read_text());review=json.loads(REVIEW.read_text());assert review['manifest_sha256']==sha(MANIFEST)
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};sets={s['object_id']:s for s in idx['view_sets']};recipe=json.loads(RECIPE.read_text());entries=recipe['entries'];accepted={(r['object_id'],r['view']):r['candidate_sha256'] for r in review['results'] if r['status']=='candidate-direction-accepted'}
assert len(accepted)==7
mobj={o['object_id']:o for o in manifest['objects']};prepared=[]
for (oid,view),approved_sha in accepted.items():
 obj=mobj[oid];e=obj['candidate_views'][view];assert e['candidate_sha256']==approved_sha
 src=assets[f'{oid}.front']['source'];assert sha(safe(BOOK,src['source_image']))==src['source_sha256']==obj['source_sha256']
 for v,b in obj['base_views'].items():assert sha(safe(BOOK,b['path']))==b['sha256'],f'{oid}.{v}: base changed'
 aid=f'{oid}.{view}';a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);cand=safe(BOOK,e['candidate_path']);base=obj['base_views'][view]['sha256'];assert sha(dst)==base and sha(cand)==approved_sha
 oldmeta=sha(mdst);new=copy.deepcopy(a);im=Image.open(cand).convert('RGBA');new['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)})
 new.setdefault('provenance_history',[]).append({'candidate_id':'page-dark-six-fixtures-v1:'+aid,'previous_provenance':copy.deepcopy(a.get('provenance',{})),'previous_image_sha256':base})
 prov={'source_image':src['source_image'],'source_sha256':src['source_sha256']}
 if 'donor_asset_id' in e:
  donor=assets[e['donor_asset_id']];prov.update({'method':'accepted-edge-elevation-inferred-rotational-symmetry-alias','derived_from_asset_id':e['donor_asset_id'],'derived_from_image_sha256':e['donor_sha256'],'alias_reason':'Thin uniform horizontal frame has equal front/rear edge geometry; approved accepted RIGHT/LEFT art is reused by inferred rotational symmetry.','normalization':{'resampling':'none; exact PNG alias','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none'}})
  prompt=e.get('prompt_path');raw=e.get('raw_atlas')
 else:
  prompt=e['prompt_path'];raw=e['raw_atlas'];prov.update({'method':'imagegen-source-guided-orthographic-view','raw_atlas':raw,'raw_atlas_sha256':e['raw_atlas_sha256'],'prompt_path':prompt,'prompt_sha256':e['prompt_sha256'],'source_rect':{'crop_bbox':e['source_crop_bbox'],'cell_region':e['cell_region'],'normalization_recipe':e['normalization']},'normalization':{'scale':e['uniform_scale'],'normalized_size':e['normalized_size'],'frame_size':[256,256],'anchor_px':[128,128],'resampling':'nearest','distortion':'none; uniform isotropic scaling'}})
  prov['notes']=('Opaque backs on all three monitors preserve the console identity; overhead controls/seat are inferred from accepted elevations.' if oid.endswith('command-console') else 'Horizontal sheet-metal roof plan or inferred ribbed underside; no upright arch facade.' if oid.endswith('hangar-arch') else 'Fixed source pipe axes and two-valve count retained; edge-on left valve and top-facing upper-right valve.' if oid.endswith('pipe-manifold') else 'Narrow arch-cap plan is composited over the complete accepted sand/coral footprint; hidden construction inferred.')
 new['provenance']=prov;md=json.dumps(new,indent=2)+'\n';mdsha=hashlib.sha256(md.encode()).hexdigest();snaprel=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json';backup=BEFORE/(aid+'.png');backupmeta=BEFORE/(aid+'.json')
 prepared.append({'aid':aid,'oid':oid,'dst':dst,'mdst':mdst,'cand':cand,'new':new,'md':md,'mdsha':mdsha,'base':base,'oldmeta':oldmeta,'snaprel':snaprel,'backup':backup,'backupmeta':backupmeta,'e':e})
# Snapshot before bytes and new sidecars before any live write.
for x in prepared:
 assert sha(x['dst'])==x['base'] and sha(x['mdst'])==x['oldmeta'];x['backup'].parent.mkdir(parents=True,exist_ok=True)
 if x['backup'].exists():assert sha(x['backup'])==x['base']
 else:x['backup'].write_bytes(x['dst'].read_bytes())
 if x['backupmeta'].exists():assert sha(x['backupmeta'])==x['oldmeta']
 else:x['backupmeta'].write_bytes(x['mdst'].read_bytes())
 atomic(safe(BOOK,x['snaprel']),x['md'].encode())
for x in prepared:
 assert sha(x['dst'])==x['base'] and sha(x['mdst'])==x['oldmeta'];atomic(x['dst'],x['cand'].read_bytes());atomic(x['mdst'],x['md']);assert sha(x['dst'])==sha(x['cand']) and sha(x['mdst'])==x['mdsha'];assets[x['aid']]=copy.deepcopy(x['new'])
 rel_candidate=x['e']['candidate_path'].removeprefix('reusable/views-additional/')
 entries.append({'asset_id':x['aid'],'image_path':x['new']['image']['path'],'candidate_path':rel_candidate,'candidate_sha256':sha(x['cand']),'base_sha256':x['base'],'final_sha256':sha(x['cand']),'metadata_path':x['new']['metadata_path'],'metadata_snapshot_path':x['snaprel'],'metadata_sha256':x['mdsha'],'live_before_install_sha256':x['base'],'superseded_installed_sha256':x['base'],'review_record':'reusable/views-additional/qa/page-dark-six-fixtures-candidate-review-v1.json'})
for x in prepared:
 sets[x['oid']]['complete']=False;sets[x['oid']]['notes']='Page-approved direction(s) installed; source and all unlisted accepted views preserved. Awaiting current indexed source-plus-six whole-set review.'
newidx=copy.deepcopy(idx);newidx['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];newidx['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
assert len({a['id'] for a in newidx['assets']})==len(newidx['assets']) and len({s['object_id'] for s in newidx['view_sets']})==len(newidx['view_sets'])
tmp=RECIPE.with_suffix('.json.tmp');tmp.write_text(json.dumps(recipe,indent=2)+'\n');os.replace(tmp,RECIPE);tmp=INDEX.with_suffix('.json.tmp');tmp.write_text(json.dumps(newidx,indent=2)+'\n');os.replace(tmp,INDEX)
print(json.dumps({'installed':[x['aid'] for x in prepared],'sets_pending_review':sorted({x['oid'] for x in prepared}),'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
