"""Install the ten Page-accepted Bubble doorway directions with base/candidate hash guards."""
from pathlib import Path
import copy, hashlib, json, os, struct
from PIL import Image

HERE=Path(__file__).resolve().parent
OUT=HERE.parent
BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'
RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
MANIFEST=OUT/'candidates/page-dark-doorways-v1/candidate-manifest.json'
REVIEW=OUT/'qa/page-dark-doorways-v1-final-candidate-review.json'
BEFORE=OUT/'prebuilt/page-dark-doorways-v1-before'
SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
RAW=OUT/'raw/page-dark-doorways-airship-lintel-v1.png'
PROMPT=OUT/'prompts/page-dark-doorways-airship-lintel-v1.txt'
CONTACT=OUT/'qa/page-dark-doorways-v1-source-six-candidates.png'
CANDID='page-dark-doorways-v1'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rgba_sha(path):
    im=Image.open(path).convert('RGBA')
    return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def alpha_bbox_for(candidate_path,cell):
    raw=Image.open(RAW).convert('RGBA')
    x0,y0,x1,y1=cell
    mask=raw.getchannel('A').crop((x0,y0,x1,y1)).point(lambda a:255 if a>=16 else 0)
    return list(mask.getbbox())
def safe(root,rel):
    path=(root/rel).resolve()
    path.relative_to(root.resolve())
    return path
def atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    tmp.write_bytes(data if isinstance(data,bytes) else data.encode())
    os.replace(tmp,path)

def main():
    manifest=json.loads(MANIFEST.read_text())
    review=json.loads(REVIEW.read_text())
    assert review['manifest_sha256']==sha(MANIFEST), 'Page review does not bind current manifest'
    accepted={(r['object_id'],r['view']):r['candidate_sha256'] for r in review['results'] if r['status']=='candidate-direction-accepted'}
    assert len(accepted)==10, f'Expected 10 accepted candidates, got {len(accepted)}'
    assert manifest['status']=='candidate-only-not-installed'
    index=json.loads(INDEX.read_text())
    assert sha(INDEX)==manifest['current_set_index_sha256'], 'set-index changed since candidate review'
    assetmap={a['id']:a for a in index['assets']}
    setmap={s['object_id']:s for s in index['view_sets']}
    recipe=json.loads(RECIPE.read_text())
    entries=recipe['entries']
    existing={e['asset_id']:e for e in entries}
    objects={o['object_id']:o for o in manifest['objects']}
    prepared=[]
    for (oid,view),accepted_sha in sorted(accepted.items()):
        obj=objects[oid]
        candidate=obj['candidate_views'][view]
        assert candidate['candidate_sha256']==accepted_sha
        srcpath=safe(BOOK,obj['source_path'])
        assert sha(srcpath)==obj['source_sha256'], f'{oid}: canonical source changed'
        # All six review bases are immutable guards, not just the directions being replaced.
        for bv,b in obj['base_views'].items():
            assert sha(safe(BOOK,b['path']))==b['sha256'], f'{oid}.{bv}: reviewed base changed'
        aid=f'{oid}.{view}'
        asset=assetmap[aid]
        dest=safe(BOOK,asset['image']['path'])
        metadata=safe(BOOK,asset['metadata_path'])
        candpath=safe(BOOK,candidate['candidate_path'])
        assert sha(candpath)==accepted_sha, f'{aid}: accepted candidate changed'
        base_sha=obj['base_views'][view]['sha256']
        current_png=sha(dest)
        old_meta=metadata.read_bytes()
        old_meta_sha=hashlib.sha256(old_meta).hexdigest()
        old_doc=json.loads(old_meta)
        assert old_doc['image']['sha256']==base_sha, f'{aid}: sidecar does not describe base PNG'
        if current_png not in {base_sha,accepted_sha}:
            raise AssertionError(f'{aid}: live PNG changed after review ({current_png})')
        # Idempotent resume is allowed only if both PNG and sidecar already match this candidate.
        if current_png==accepted_sha:
            live=json.loads(metadata.read_text())
            assert live['image']['sha256']==accepted_sha, f'{aid}: installed image/sidecar mismatch'
            if aid in existing:
                assert existing[aid]['final_sha256']==accepted_sha
                continue
        new=copy.deepcopy(old_doc)
        image=Image.open(candpath).convert('RGBA')
        new['image'].update({'width':image.width,'height':image.height,'sha256':accepted_sha,'rgba_sha256':rgba_sha(candpath)})
        new.setdefault('provenance_history',[]).append({'candidate_id':CANDID+':'+aid,'previous_provenance':copy.deepcopy(old_doc.get('provenance',{})),'previous_image_sha256':base_sha})
        prov={'source_image':obj['source_path'],'source_sha256':obj['source_sha256'],'candidate_contact':str(CONTACT.relative_to(BOOK)),'candidate_contact_sha256':sha(CONTACT),'candidate_manifest':str(MANIFEST.relative_to(BOOK)),'candidate_manifest_sha256':sha(MANIFEST),'candidate_review_record':str(REVIEW.relative_to(BOOK)),'candidate_review_manifest_sha256':review['manifest_sha256']}
        deriv=candidate['derivation']
        if candidate['method']=='imagegen-atlas-cell-uniform-normalization':
            prov.update({'method':'imagegen-source-specific-doorway-lintel-orthographic','raw_atlas':str(RAW.relative_to(BOOK)),'raw_atlas_sha256':sha(RAW),'prompt_path':str(PROMPT.relative_to(BOOK)),'prompt_sha256':sha(PROMPT),'source_rect':{'cell_rect_atlas_px':deriv['raw_cell'],'alpha_bounds_in_cell_px':alpha_bbox_for(candidate['candidate_path'],deriv['raw_cell']),'threshold_alpha_min':16},'normalization':{'uniform_scale':deriv['uniform_scale'],'target_span_px':deriv['target_span_px'],'resampling':'nearest-neighbor','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; aspect ratio preserved'},'notes':deriv['notes']})
        else:
            donor=deriv['derived_from_asset_id']; donor_path=deriv['derived_from_png']
            prov.update({'method':'accepted-sibling-view-orthographic-symmetry','derived_from_asset_id':donor,'derived_from_image_path':donor_path,'derived_from_image_sha256':deriv['derived_from_sha256'],'rotation_degrees':deriv.get('rotation_degrees',0),'mirror_horizontal':bool(deriv.get('mirror_horizontal',False)),'normalization':{'uniform_scale':1.0,'resampling':'exact pixel copy' if not deriv.get('mirror_horizontal') else 'nearest-neighbor rigid horizontal reflection','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none'},'alias_reason':deriv['alias_reason'],'notes':'Symmetric or mirrored hidden construction is inferred, not recovered source pixels.'})
            if deriv.get('superseded_candidate_archive'):
                prov['superseded_candidate_path']=deriv['superseded_candidate_archive'];prov['superseded_candidate_sha256']=deriv.get('superseded_candidate_sha256')
        new['provenance']=prov
        metadata_text=json.dumps(new,indent=2)+'\n'
        metadata_sha=hashlib.sha256(metadata_text.encode()).hexdigest()
        snapshot_rel=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
        entry={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':candidate['candidate_path'].removeprefix('reusable/views-additional/'),'candidate_sha256':accepted_sha,'base_sha256':base_sha,'final_sha256':accepted_sha,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snapshot_rel,'metadata_sha256':metadata_sha,'live_before_install_sha256':base_sha,'superseded_installed_sha256':base_sha,'review_record':'/workspace/scratch/page-dark-doorways-v1-final-candidate-review.json','candidate_manifest_sha256':review['manifest_sha256']}
        prepared.append({'aid':aid,'oid':oid,'view':view,'dest':dest,'metadata':metadata,'candidate':candpath,'base_sha':base_sha,'accepted_sha':accepted_sha,'old_meta':old_meta,'old_meta_sha':old_meta_sha,'new':new,'metadata_text':metadata_text,'metadata_sha':metadata_sha,'snapshot_rel':snapshot_rel,'entry':entry,'current_png_sha':current_png})
    # Preserve pre-install bytes and write canonical sidecar snapshots before changing live files.
    for x in prepared:
        before_png=BEFORE/(x['aid']+'.png');before_json=BEFORE/(x['aid']+'.json')
        if not before_png.exists(): atomic(before_png,x['dest'].read_bytes())
        else: assert sha(before_png)==x['base_sha']
        if not before_json.exists(): atomic(before_json,x['old_meta'])
        else:
            # Existing archive must be a prior exact snapshot; do not rewrite it.
            assert json.loads(before_json.read_text())['image']['sha256']==x['base_sha']
        snap=safe(BOOK,x['snapshot_rel'])
        if snap.exists(): assert sha(snap)==x['metadata_sha']
        else: atomic(snap,x['metadata_text'].encode())
    # Install PNG and sidecar per direction, guarded at each replace; index is committed last.
    for x in prepared:
        live=sha(x['dest'])
        assert live in {x['base_sha'],x['accepted_sha']}
        if live==x['base_sha']: atomic(x['dest'],x['candidate'].read_bytes())
        assert sha(x['dest'])==x['accepted_sha']
        if sha(x['metadata'])!=x['metadata_sha']:
            live_meta=json.loads(x['metadata'].read_text())
            assert live_meta['image']['sha256']==x['base_sha']
            atomic(x['metadata'],x['metadata_text'].encode())
        assert sha(x['metadata'])==x['metadata_sha']
        assetmap[x['aid']]=copy.deepcopy(x['new'])
        if x['aid'] not in existing:
            entries.append(x['entry']);existing[x['aid']]=x['entry']
        else: assert existing[x['aid']]['final_sha256']==x['accepted_sha']
    # Keep whole-set flags pending until Page's fresh live source-plus-six review.
    for oid in {o['object_id'] for o in manifest['objects']}:
        setmap[oid]['complete']=False
        setmap[oid]['notes']='Page-accepted scoped doorway candidates installed with source state/materials retained; awaiting fresh indexed source-plus-six whole-set review. Hidden surfaces are inferred.'
    newindex=copy.deepcopy(index)
    newindex['assets']=[copy.deepcopy(assetmap[a['id']]) for a in index['assets']]
    newindex['view_sets']=[copy.deepcopy(setmap[s['object_id']]) for s in index['view_sets']]
    assert len({a['id'] for a in newindex['assets']})==len(newindex['assets'])
    assert len({s['object_id'] for s in newindex['view_sets']})==len(newindex['view_sets'])
    # Recipe first, canonical index last; both use temp+replace.
    atomic(RECIPE,json.dumps(recipe,indent=2)+'\n')
    atomic(INDEX,json.dumps(newindex,indent=2)+'\n')
    print(json.dumps({'installed':[x['aid'] for x in prepared],'accepted_total':len(accepted),'index_sha256':sha(INDEX),'recipe_entries':len(entries),'all_png_sidecar_guards_passed':True},indent=2))

if __name__=='__main__':main()
