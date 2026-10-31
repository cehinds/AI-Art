"""Install Page-approved scoped directions for the final-three 2026-10-26 batch."""
from pathlib import Path
import copy, hashlib, json, os, struct
from PIL import Image

HERE=Path(__file__).resolve().parent
OUT=HERE.parent
BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'
RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
MANIFEST=OUT/'candidates/page-dark-final-three-v1/candidate-manifest.json'
REVIEW=OUT/'qa/page-dark-final-three-candidate-review.json'
BEFORE=OUT/'prebuilt/page-dark-final-three-v1-before'
SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
EXPECTED_REVIEW_SHA=''

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rgba_sha(path):
    im=Image.open(path).convert('RGBA')
    return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
    p=(root/rel).resolve();p.relative_to(root.resolve());return p

def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    if isinstance(data,bytes):tmp.write_bytes(data)
    else:tmp.write_text(data)
    os.replace(tmp,path)

manifest=json.loads(MANIFEST.read_text())
review=json.loads(REVIEW.read_text())
assert review['status']=='candidate-directions-accepted'
assert review['manifest_sha256']==sha(MANIFEST)
if EXPECTED_REVIEW_SHA: assert sha(REVIEW)==EXPECTED_REVIEW_SHA
idx=json.loads(INDEX.read_text())
assets={a['id']:a for a in idx['assets']}
sets={s['object_id']:s for s in idx['view_sets']}
recipe=json.loads(RECIPE.read_text())
entries=recipe['entries']
lookup={e['asset_id']:i for i,e in enumerate(entries)}
# Recipe is an ordered history; duplicate asset IDs are valid and latest wins.
reviewed={o['object_id']:o['accepted'] for o in review['objects']}
prepared=[]
for obj in manifest['objects']:
    oid=obj['object_id'];assert oid in reviewed and oid in sets
    source_rel=assets[f'{oid}.front']['source']['source_image']
    source_hash=assets[f'{oid}.front']['source']['source_sha256']
    assert sha(safe(BOOK,source_rel))==source_hash==obj['source_sha256'], f'{oid}: canonical source changed'
    base_views=obj['base_views']
    # Candidate review guards the source and every sibling, not only the edited directions.
    for view,base in base_views.items():
        current=safe(BOOK,assets[f'{oid}.{view}']['image']['path'])
        assert sha(current)==base['sha256'], f'{oid}.{view}: live base changed after candidate review'
    assert set(obj['candidate_views'])==set(reviewed[oid]), f'{oid}: review scope mismatch'
    for view,e in obj['candidate_views'].items():
        aid=f'{oid}.{view}';a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path'])
        candidate=safe(OUT,e['candidate_path'])
        base=base_views[view]['sha256'];assert sha(dst)==base
        assert sha(candidate)==e['candidate_sha256']==reviewed[oid][view]
        assert a['source']['source_image']==source_rel and a['source']['source_sha256']==source_hash
        oldmeta=sha(mdst);new=copy.deepcopy(a)
        im=Image.open(candidate).convert('RGBA')
        new['image'].update({'width':im.width,'height':im.height,'sha256':sha(candidate),'rgba_sha256':rgba_sha(candidate)})
        new.setdefault('provenance_history',[]).append({'candidate_id':'page-dark-final-three-v1:'+aid,'previous_provenance':copy.deepcopy(a.get('provenance',{})),'previous_image_sha256':base})
        provenance={'source_image':source_rel,'source_sha256':source_hash,'normalization':{'frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; all scale changes isotropic'}}
        if oid.startswith('masquerade-'):
            raw='reusable/views-additional/raw/exec-f13de6f5-cbee-4a5b-8702-9095881718b6.png'
            pr='reusable/views-additional/prompts/masquerade-pointed-side-caps-v1.txt'
            provenance.update({'method':'imagegen-pointed-side-cap-atlas-uniform-component-normalization','raw_atlas':raw,'raw_atlas_sha256':sha(safe(BOOK,raw)),'prompt_path':pr,'prompt_sha256':sha(safe(BOOK,pr)),'reference_paths':[source_rel,'reusable/views-additional/images/'+oid+'.front.png','reusable/views-additional/images/'+oid+'.right.png'],'reference_sha256':[source_hash,base_views['front']['sha256'],base_views['right']['sha256']],'source_rect':{'component_bbox':e['raw_component_bbox'],'component_pixels':e['raw_component_pixels'],'extraction':'remove outer connected neutral checkerboard pixels; select full connected art component'},'normalization':{'scale':114/e['uniform_normalized_size'][1],'offset_px':[128-e['uniform_normalized_size'][0]//2,128-e['uniform_normalized_size'][1]//2],'source_size':e['uniform_normalized_size'],'target_frame':[256,256],'anchor_px':[128,128],'resampling':'nearest','distortion':'none; uniform isotropic scaling'},'notes':'Pointed finial and blue-trimmed marble side profiles are inferred illustrative views, not recovered hidden pixels.'})
        elif oid.startswith('starter-dungeon-') and view in ('top','bottom'):
            provenance.update({'method':'native-square-cap-plan-uniform-normalization' if view=='top' else 'inferred-symmetric-native-cap-underside','source_rect':{'alpha_bbox':e['source_crop_bbox']},'normalization':{'scale':119/e['uniform_normalized_size'][0],'source_size':e['uniform_normalized_size'],'target_size':e['uniform_normalized_size'],'frame_size':[256,256],'anchor_px':[128,128],'resampling':'nearest','distortion':'none; uniform isotropic scaling'},'notes':'Single-cap square footprint comes from the canonical source. Bottom repeats the native plan as an explicit inferred symmetry because the hidden underside is not recoverable.'})
        elif oid.startswith('starter-dungeon-'):
            donor=e['donor_view'];provenance.update({'method':'accepted-front-rear-inferred-side-alias','derived_from_asset_id':f'{oid}.{donor}','derived_from_image_sha256':e['donor_sha256'],'normalization':{'resampling':'none; exact accepted PNG alias','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none'},'notes':'Inferred side face aliases preserve the two accepted masonry courses, common height, and native material. Hidden faces are not recovered.'})
        else:
            raw='reusable/views-additional/raw/exec-e46a2508-0edf-4518-bf05-d05c311ef055.png'
            pr='reusable/views-additional/prompts/over-city-townhouse-plan-views-v1.txt'
            provenance.update({'method':'imagegen-orthographic-rectangular-roof-and-foundation-plans','raw_atlas':raw,'raw_atlas_sha256':sha(safe(BOOK,raw)),'prompt_path':pr,'prompt_sha256':sha(safe(BOOK,pr)),'reference_paths':[source_rel,'reusable/views-additional/images/'+oid+'.front.png','reusable/views-additional/images/'+oid+'.right.png'],'reference_sha256':[source_hash,base_views['front']['sha256'],base_views['right']['sha256']],'source_rect':{'component_bbox':e['raw_component_bbox'],'component_pixels':e['raw_component_pixels'],'extraction':'remove outer connected neutral checkerboard pixels; select full connected art component'},'normalization':{'scale':180/e['uniform_normalized_size'][0],'source_size':e['uniform_normalized_size'],'normalized_size':e['uniform_normalized_size'],'frame_size':[256,256],'anchor_px':[128,128],'resampling':'nearest','distortion':'none; uniform isotropic scaling'},'notes':'Rectangular plan width/depth follows accepted facade and side projections. BOTTOM is an inferred stone footing/support surface, not recovered source pixels.' if view=='bottom' else 'Direct overhead roof preserves red roof fragments, exposed timber and roof gaps; no facade plane.'})
        new['provenance']=provenance
        md=json.dumps(new,indent=2)+'\n';mdsha=hashlib.sha256(md.encode()).hexdigest()
        snapshot_rel=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
        backup_png=BEFORE/(aid+'.png');backup_meta=BEFORE/(aid+'.json')
        prepared.append({'aid':aid,'dst':dst,'mdst':mdst,'candidate':candidate,'new':new,'md':md,'mdsha':mdsha,'base':base,'oldmeta':oldmeta,'snapshot_rel':snapshot_rel,'backup_png':backup_png,'backup_meta':backup_meta,'e':e})
# Snapshot all before bytes first, then atomically install PNGs and sidecars.
for x in prepared:
    assert sha(x['dst'])==x['base'] and sha(x['mdst'])==x['oldmeta']
    x['backup_png'].parent.mkdir(parents=True,exist_ok=True)
    if x['backup_png'].exists(): assert sha(x['backup_png'])==x['base']
    else:x['backup_png'].write_bytes(x['dst'].read_bytes())
    if x['backup_meta'].exists(): assert sha(x['backup_meta'])==x['oldmeta']
    else:x['backup_meta'].write_bytes(x['mdst'].read_bytes())
    snap=safe(BOOK,x['snapshot_rel']);atomic(snap,x['md'].encode())
for x in prepared:
    assert sha(x['dst'])==x['base'] and sha(x['mdst'])==x['oldmeta']
    atomic(x['dst'],x['candidate'].read_bytes());atomic(x['mdst'],x['md'])
    assert sha(x['dst'])==x['e']['candidate_sha256'] and sha(x['mdst'])==x['mdsha']
    assets[x['aid']]=copy.deepcopy(x['new'])
    entry={'asset_id':x['aid'],'image_path':x['new']['image']['path'],'candidate_path':x['e']['candidate_path'].replace(str(OUT)+'/',''),'candidate_sha256':x['e']['candidate_sha256'],'base_sha256':x['base'],'final_sha256':x['e']['candidate_sha256'],'metadata_path':x['new']['metadata_path'],'metadata_snapshot_path':x['snapshot_rel'],'metadata_sha256':x['mdsha'],'live_before_install_sha256':x['base'],'superseded_installed_sha256':x['base'],'review_record':'reusable/views-additional/qa/page-dark-final-three-candidate-review.json'}
    entries.append(entry)
for oid in reviewed:
    sets[oid]['complete']=False
    sets[oid]['notes']='Page-approved scoped repairs installed; source and siblings preserved. Awaiting current indexed source-plus-six whole-set hash review.'
# Rebuild fresh index structures, avoiding aliased dict mutation.
newidx=copy.deepcopy(idx)
newidx['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']]
newidx['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
# Uniqueness and link integrity before writing.
assert len({a['id'] for a in newidx['assets']})==len(newidx['assets'])
assert len({s['object_id'] for s in newidx['view_sets']})==len(newidx['view_sets'])
tmp=RECIPE.with_suffix('.json.tmp');tmp.write_text(json.dumps(recipe,indent=2)+'\n');os.replace(tmp,RECIPE)
tmp=INDEX.with_suffix('.json.tmp');tmp.write_text(json.dumps(newidx,indent=2)+'\n');os.replace(tmp,INDEX)
print(json.dumps({'installed':[x['aid'] for x in prepared],'sets_pending_review':sorted(reviewed),'recipe_entries':len(entries),'index_sha256':sha(INDEX)},indent=2))
