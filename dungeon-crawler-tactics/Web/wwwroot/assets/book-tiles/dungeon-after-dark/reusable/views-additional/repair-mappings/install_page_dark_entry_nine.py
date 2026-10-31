"""Install the nine Page-accepted entry/hull plan directions with exact hash guards."""
from pathlib import Path
import copy, hashlib, json, os, shutil, struct
from PIL import Image

HERE=Path(__file__).resolve().parent
OUT=HERE.parent
BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'
RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
MANIFEST=OUT/'candidates/page-dark-entry-plan-v1/candidate-manifest.json'
REVIEW=Path('/workspace/scratch/page-dark-entry-nine-plane-candidate-review.json')
REVIEW_LOCAL=OUT/'qa/page-dark-entry-nine-plane-candidate-review.json'
SNAPDIR=OUT/'prebuilt/replay-sidecars-final-v1'
BEFORE=OUT/'prebuilt/page-dark-entry-nine-before'
CANDID='page-dark-entry-nine-plane-v1'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(p):
    im=Image.open(p).convert('RGBA')
    return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
    p=(root/rel).resolve(); p.relative_to(root.resolve()); return p
def candidate_path(rel):
    if rel.startswith('reusable/views-additional/'): return safe(BOOK,rel)
    return safe(OUT,rel)
def atomic(p,data):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+'.tmp'); t.write_bytes(data if isinstance(data,bytes) else data.encode()); os.replace(t,p)

def main():
    manifest=json.loads(MANIFEST.read_text()); review=json.loads(REVIEW.read_text())
    assert review['manifest_sha256']==sha(MANIFEST)
    assert review['source_all_six_base_raw_prompt_candidate_hashes_verified'] is True
    accepted={(x['object_id'],x['view']):x['candidate_sha256'] for x in review['decisions'] if x['status']=='candidate-direction-accepted'}
    assert len(accepted)==9
    rows={(x['object_id'],x['view']):x for x in manifest['candidates']}
    assert set(accepted)==set(rows)
    if not REVIEW_LOCAL.exists(): shutil.copyfile(REVIEW,REVIEW_LOCAL)
    else: assert sha(REVIEW_LOCAL)==sha(REVIEW)
    index=json.loads(INDEX.read_text()); recipe=json.loads(RECIPE.read_text())
    assets={x['id']:copy.deepcopy(x) for x in index['assets']}
    sets={x['object_id']:copy.deepcopy(x) for x in index['view_sets']}
    recipe_entries=recipe['entries']; entry_by_id={e['asset_id']:e for e in recipe_entries}
    prepared=[]
    for (oid,view),candidate_sha in sorted(accepted.items()):
        e=rows[(oid,view)]; aid=f'{oid}.{view}'
        assert e['candidate_sha256']==candidate_sha
        assert sha(safe(BOOK,e['source_path']))==e['source_sha256']
        for bv,b in e['base_six'].items(): assert sha(safe(BOOK,b['path']))==b['sha256'], f'{aid}: base {bv} changed'
        cand=candidate_path(e['candidate_path']); assert sha(cand)==candidate_sha
        a=assets[aid]; dst=safe(BOOK,a['image']['path']); md=safe(BOOK,a['metadata_path'])
        base=e['base_six'][view]['sha256']; current=sha(dst)
        assert current in (base,candidate_sha), f'{aid}: live base changed {current}'
        old=json.loads(md.read_text()); assert old['image']['sha256']==base
        new=copy.deepcopy(old); im=Image.open(cand).convert('RGBA')
        new['image'].update(width=im.width,height=im.height,sha256=candidate_sha,rgba_sha256=rgba_sha(cand))
        new.setdefault('provenance_history',[]).append({'candidate_id':CANDID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
        raw_rel='reusable/views-additional/'+e['raw_path']; prompt_rel='reusable/views-additional/'+e['prompt_path']
        candidate_rel=e['candidate_path'] if e['candidate_path'].startswith('reusable/views-additional/') else 'reusable/views-additional/'+e['candidate_path']
        prov={'method':'source-guided-isolated-orthographic-plan-view','source_image':e['source_path'],'source_sha256':e['source_sha256'],
          'raw_atlas':raw_rel,'raw_atlas_sha256':e['raw_sha256'],'prompt_path':prompt_rel,'prompt_sha256':e['prompt_sha256'],
          'candidate_manifest':'reusable/views-additional/candidates/page-dark-entry-plan-v1/candidate-manifest.json','candidate_manifest_sha256':sha(MANIFEST),
          'candidate_review_record':'reusable/views-additional/qa/page-dark-entry-nine-plane-candidate-review.json','candidate_review_sha256':sha(REVIEW_LOCAL),
          'candidate_image':candidate_rel,'candidate_image_sha256':candidate_sha,
          'normalization':{'uniform_scale':e['uniform_scale'],'target_span_px':e['target_world_x_span_px'],'output_dimensions':e['output_dimensions'],'offset_px':e['offset_px'],'resampling':'nearest-neighbor','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; aspect ratio preserved'},
          'notes':e.get('notes','Hidden surfaces are inferred, not recovered source pixels.')}
        assert not prov['source_image'].startswith('/') and safe(BOOK,prov['source_image']).is_file(), f'{aid}: canonical source_image must be pack-relative and resolvable'
        new['provenance']=prov
        mtext=json.dumps(new,indent=2)+'\n'; msha=hashlib.sha256(mtext.encode()).hexdigest()
        snaprel=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
        entry={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':candidate_rel.removeprefix('reusable/views-additional/'),'candidate_sha256':candidate_sha,'base_sha256':base,'final_sha256':candidate_sha,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snaprel,'metadata_sha256':msha,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':'reusable/views-additional/qa/page-dark-entry-nine-plane-candidate-review.json','candidate_manifest_sha256':sha(MANIFEST)}
        if aid in entry_by_id:
            assert entry_by_id[aid]['final_sha256']==candidate_sha and entry_by_id[aid]['metadata_sha256']==msha
        prepared.append((aid,oid,dst,md,cand,base,candidate_sha,old,new,mtext,msha,snaprel,entry))
    # Archive originals and canonical metadata snapshots before writing production paths.
    for aid,oid,dst,md,cand,base,csha,old,new,mtext,msha,snaprel,entry in prepared:
        bp=BEFORE/(aid+'.png'); bj=BEFORE/(aid+'.json')
        if not bp.exists(): atomic(bp,dst.read_bytes())
        else: assert sha(bp)==base
        if not bj.exists(): atomic(bj,md.read_bytes())
        else: assert json.loads(bj.read_text())['image']['sha256']==base
        snap=safe(BOOK,snaprel)
        if snap.exists(): assert sha(snap)==msha
        else: atomic(snap,mtext.encode())
    for aid,oid,dst,md,cand,base,csha,old,new,mtext,msha,snaprel,entry in prepared:
        if sha(dst)==base: atomic(dst,cand.read_bytes())
        assert sha(dst)==csha
        if sha(md)!=msha: atomic(md,mtext.encode())
        assert sha(md)==msha
        assets[aid]=copy.deepcopy(new)
        if aid not in entry_by_id: recipe_entries.append(entry); entry_by_id[aid]=entry
        sets[oid]['complete']=False
        sets[oid]['notes']='Page-accepted plan directions installed; awaiting fresh indexed source-plus-six review. Hidden surfaces are inferred.'
    newindex=copy.deepcopy(index)
    newindex['assets']=[copy.deepcopy(assets[a['id']]) for a in index['assets']]
    newindex['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in index['view_sets']]
    assert len({a['id'] for a in newindex['assets']})==len(newindex['assets'])
    assert len({s['object_id'] for s in newindex['view_sets']})==len(newindex['view_sets'])
    atomic(RECIPE,json.dumps(recipe,indent=2)+'\n'); atomic(INDEX,json.dumps(newindex,indent=2)+'\n')
    print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(recipe_entries)},indent=2))
if __name__=='__main__': main()
