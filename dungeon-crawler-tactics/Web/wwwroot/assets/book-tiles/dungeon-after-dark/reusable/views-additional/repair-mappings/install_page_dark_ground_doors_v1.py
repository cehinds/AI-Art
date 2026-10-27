"""Install the eight Page-approved ground-projection doorway views."""
from pathlib import Path
import copy, hashlib, json, os, struct
from PIL import Image

HERE=Path(__file__).resolve().parent
OUT=HERE.parent
BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'
RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
CANDDIR=OUT/'candidates/page-dark-ground-door-plan-v1'
MANIFEST=CANDDIR/'candidate-manifest.json'
MAPPING=CANDDIR/'request-result-mapping.json'
REVIEW=Path('/workspace/scratch/page-dark-ground-door-eight-candidate-review.json')
REVIEW_LOCAL=OUT/'qa/page-dark-ground-door-eight-candidate-review.json'
BEFORE=OUT/'prebuilt/page-dark-ground-door-v1-before'
BATCH='page-dark-ground-door-plan-v1'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(p):
    im=Image.open(p).convert('RGBA')
    return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
    p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp')
    t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)

def main():
    manifest=json.loads(MANIFEST.read_text())
    review=json.loads(REVIEW.read_text())
    mapping=json.loads(MAPPING.read_text())
    assert review['manifest_sha256']==sha(MANIFEST)
    assert review['source_all_six_base_raw_prompt_candidate_hashes_verified']
    assert sha(MAPPING)==manifest['request_result_mapping_sha256']
    accepted={(d['object_id'],d['view']):d['candidate_sha256'] for d in review['decisions']
              if d['status']=='candidate-direction-accepted'}
    candidates={(c['object_id'],c['view']):c for c in manifest['candidates']}
    objects={o['object_id']:o for o in manifest['objects']}
    assert len(accepted)==8 and set(accepted)==set(candidates)
    if REVIEW_LOCAL.exists(): assert sha(REVIEW_LOCAL)==sha(REVIEW)
    else: atomic(REVIEW_LOCAL,REVIEW.read_bytes())
    requestmap={}
    for req in mapping['requests']:
        if req['status'].startswith('valid isolated'):
            raw=safe(BOOK,req['raw_path']);prompt=safe(BOOK,req['prompt_path'])
            assert sha(raw)==req['raw_sha256'] and sha(prompt)==req['prompt_sha256']
            requestmap[req['request_id']]=req

    idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text())
    assets={a['id']:copy.deepcopy(a) for a in idx['assets']}
    sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']}
    entries=recipe['entries'];entrymap={e['asset_id']:e for e in entries};prepared=[]
    for (oid,view),candidate_sha in sorted(accepted.items()):
        c=candidates[(oid,view)];o=objects[oid];aid=f'{oid}.{view}'
        assert c['asset_id']==aid and c['candidate_sha256']==candidate_sha
        src=safe(BOOK,o['source_path']);assert sha(src)==o['source_sha256']
        for direction,b in o['base_six'].items():
            assert sha(safe(BOOK,b['path']))==b['sha256'],f'{aid}: {direction} changed since Page review'
        candidate=safe(BOOK,c['candidate_path']);assert sha(candidate)==candidate_sha
        raw=safe(BOOK,c['raw_atlas_path']);prompt=safe(BOOK,c['prompt_path'])
        assert sha(raw)==c['raw_atlas_sha256'] and sha(prompt)==c['prompt_sha256']
        req=requestmap[c['request_id']]
        assert req['raw_path']==c['raw_atlas_path'] and req['prompt_path']==c['prompt_path']

        asset=assets[aid];dst=safe(BOOK,asset['image']['path']);md=safe(BOOK,asset['metadata_path'])
        base=o['base_six'][view]['sha256'];assert sha(dst) in (base,candidate_sha)
        old=json.loads(md.read_text());assert old['image']['sha256']==base
        new=copy.deepcopy(old);im=Image.open(candidate).convert('RGBA')
        new['image'].update(width=im.width,height=im.height,sha256=candidate_sha,rgba_sha256=rgba_sha(candidate))
        new.setdefault('provenance_history',[]).append({'candidate_id':f'{BATCH}:{aid}',
            'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
        prov={
            'method':'source-guided-imagegen-ground-door-projection',
            'source_image':o['source_path'],'source_sha256':o['source_sha256'],
            'candidate_image':c['candidate_path'],'candidate_image_sha256':candidate_sha,
            'candidate_manifest':'reusable/views-additional/candidates/page-dark-ground-door-plan-v1/candidate-manifest.json',
            'candidate_manifest_sha256':sha(MANIFEST),
            'candidate_review_record':'reusable/views-additional/qa/page-dark-ground-door-eight-candidate-review.json',
            'candidate_review_sha256':sha(REVIEW_LOCAL),
            'request_result_mapping':'reusable/views-additional/candidates/page-dark-ground-door-plan-v1/request-result-mapping.json',
            'request_result_mapping_sha256':sha(MAPPING),
            'request_id':c['request_id'],'raw_atlas':c['raw_atlas_path'],'raw_atlas_sha256':c['raw_atlas_sha256'],
            'prompt_path':c['prompt_path'],'prompt_sha256':c['prompt_sha256'],
            'reference_contact':c['reference_contact_path'],'reference_contact_sha256':c['reference_contact_sha256'],
            'normalization':{'raw_cell_rect':c['raw_cell_rect'],'alpha_bounds_xyxy':c['alpha_bounds_xyxy'],
                'alpha_threshold':c['alpha_threshold'],'component_min_area':c['component_min_area'],
                'uniform_scale':c['uniform_scale'],'output_dimensions':c['output_dimensions'],
                'offset_px':c['offset_px'],'target_world_x_span_px':c['target_world_x_span_px'],
                'method':c['normalization']},
            'notes':c.get('notes','')+' Inferred hidden construction; source state and materials preserved.'}
        for key in ('source_image','candidate_image','candidate_manifest','candidate_review_record',
                    'request_result_mapping','raw_atlas','prompt_path','reference_contact'):
            assert not prov[key].startswith('/') and safe(BOOK,prov[key]).is_file(),(aid,key,prov[key])
        new['provenance']=prov
        meta_bytes=(json.dumps(new,indent=2)+'\n').encode();meta_sha=hashlib.sha256(meta_bytes).hexdigest()
        snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
        entry={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':c['candidate_path'],
            'candidate_sha256':candidate_sha,'base_sha256':base,'final_sha256':candidate_sha,
            'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':meta_sha,
            'live_before_install_sha256':base,'superseded_installed_sha256':base,
            'review_record':prov['candidate_review_record'],'candidate_manifest_sha256':sha(MANIFEST)}
        prior=entrymap.get(aid)
        if prior:
            assert prior['final_sha256']==base,f'{aid}: unexpected previous recipe final'
            entries[entries.index(prior)]=entry
        else: entries.append(entry)
        entrymap[aid]=entry
        prepared.append((aid,oid,dst,md,candidate,base,candidate_sha,new,meta_bytes,meta_sha,snap))

    for aid,oid,dst,md,candidate,base,csha,new,meta_bytes,msha,snap in prepared:
        bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json')
        if bp.exists(): assert sha(bp)==base
        else: atomic(bp,dst.read_bytes())
        if jp.exists(): assert json.loads(jp.read_text())['image']['sha256']==base
        else: atomic(jp,md.read_bytes())
        sp=safe(BOOK,snap)
        if sp.exists(): assert sha(sp)==msha,f'{aid}: snapshot conflict'
        else: atomic(sp,meta_bytes)
    for aid,oid,dst,md,candidate,base,csha,new,meta_bytes,msha,snap in prepared:
        if sha(dst)==base: atomic(dst,candidate.read_bytes())
        assert sha(dst)==csha
        if sha(md)!=msha: atomic(md,meta_bytes)
        assert sha(md)==msha;assets[aid]=copy.deepcopy(new)
    for oid in {r[1] for r in prepared}:
        sets[oid]['complete']=False
        sets[oid]['notes']='Page-approved ground-door projection candidates installed; awaiting live source-plus-six review.'
    newidx=copy.deepcopy(idx)
    newidx['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']]
    newidx['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
    assert len({a['id'] for a in newidx['assets']})==len(newidx['assets'])
    assert len({s['object_id'] for s in newidx['view_sets']})==len(newidx['view_sets'])
    atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(newidx,indent=2)+'\n')
    print(json.dumps({'installed':[r[0] for r in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))

if __name__=='__main__': main()
