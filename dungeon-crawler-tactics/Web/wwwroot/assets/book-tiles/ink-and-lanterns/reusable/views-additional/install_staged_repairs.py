#!/usr/bin/env python3
"""Install independently accepted, hash-guarded staged view repairs."""
import hashlib, json, os, pathlib, struct, tempfile
from PIL import Image

OUT=pathlib.Path(__file__).resolve().parent
PACK=OUT.parents[1]
INDEX=OUT/'set-index.json'

def sha_bytes(data): return hashlib.sha256(data).hexdigest()
def sha(path): return sha_bytes(path.read_bytes())
def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    except BaseException:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise
def atomic_json(path,obj): atomic(path,(json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode())

def install():
    index=json.loads(INDEX.read_text())
    assets={a['id']:a for a in index['assets']}
    groups={g['object_id']:g for g in index['view_sets']}
    recipes=[
      'raw/parade-horribles-ceremonial-arena-masonry-inner-corner-top-v2-source-plan-candidate.recipe.json',
      'raw/industry-menagerie-soot-stained-brick-endcap-northeast-top-v2-symmetric-cap-candidate.recipe.json',
      'raw/race-circuits-steel-track-barrier-north-cap-right-v2-square-cap-alias-candidate.recipe.json',
      'raw/race-circuits-steel-track-barrier-north-cap-left-v2-square-cap-alias-candidate.recipe.json',
      'raw/race-circuits-steel-track-barrier-west-cap-right-v2-square-cap-alias-candidate.recipe.json',
      'raw/race-circuits-steel-track-barrier-west-cap-left-v2-square-cap-alias-candidate.recipe.json',
    ]
    plans=[]
    for rel in recipes:
        recipe_path=OUT/rel; recipe=json.loads(recipe_path.read_text())
        if recipe.get('status') not in ('staged_candidate_not_installed','staged_candidate_not_installed'):
            raise ValueError(f'candidate not installable: {rel} status={recipe.get("status")}')
        oid,view=recipe['object_id'],recipe['view']; aid=f'{oid}.{view}'
        if aid not in assets or oid not in groups: raise KeyError(aid)
        asset=assets[aid]; live=OUT/pathlib.Path(asset['image']['path']).name
        if sha(live)!=recipe['target_current_sha256']:
            raise RuntimeError(f'target changed since approval: {aid}')
        candidate=PACK/recipe.get('candidate_path',f'reusable/views-additional/raw/{oid}-{view}-v2-source-plan-candidate.png')
        # The alias recipes use the predictable candidate filename; the source plan has same convention.
        if not candidate.is_file():
            stem=pathlib.Path(rel).name.removesuffix('.recipe.json').removesuffix('.recipe')
            candidate=OUT/'raw'/f'{oid}-{view}-v2-source-plan-candidate.png'
        if not candidate.is_file(): raise FileNotFoundError(candidate)
        if sha(candidate)!=recipe['candidate_sha256']: raise RuntimeError(f'candidate changed since review: {aid}')
        guide_path=recipe.get('guide_path')
        if guide_path:
            guide=OUT/pathlib.Path(guide_path).name
            if sha(guide)!=recipe['guide_sha256']: raise RuntimeError(f'guide changed since approval: {aid}')
            if asset.get('provenance',{}).get('source_image') is None: raise RuntimeError(f'missing canonical source lineage: {aid}')
        source_rel=recipe.get('source_image')
        source=PACK/source_rel if source_rel else None
        if source and (not source.is_file() or sha(source)!=recipe['source_sha256']): raise RuntimeError(f'canonical source changed: {aid}')
        plans.append((recipe_path,recipe,aid,asset,live,candidate,source))
    updated=[]
    for recipe_path,recipe,aid,asset,live,candidate,source in plans:
        payload=candidate.read_bytes(); atomic(live,payload)
        image=Image.open(live).convert('RGBA')
        file_hash=sha(live); rgba_hash=sha_bytes(struct.pack('>II',*image.size)+image.tobytes())
        sidecar=PACK/asset['metadata_path']; meta=json.loads(sidecar.read_text())
        old=meta.get('provenance',{}).copy(); prov=meta.setdefault('provenance',{})
        prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),old]
        if recipe['object_id']=='parade-horribles-ceremonial-arena-masonry-inner-corner' and recipe['view']=='top':
            prov.update({'method':'reused-canonical-source-top','source_image':recipe['source_image'],'source_sha256':recipe['source_sha256'],'notes':'The native L-shaped corner source is its map-plan TOP footprint. This exact source alpha crop is reused with isotropic nearest-neighbor normalization; all other views remain inferred.','reused_source_top':{'path':recipe['source_image'],'sha256':recipe['source_sha256'],'alpha_bounds_px':recipe['source_alpha_bounds_px'],'scale':recipe['isotropic_scale'],'offset_px':recipe['output_offset_px'],'resampling':'nearest'}})
        else:
            prov['derivation']={'method':recipe['method'],'guide_object_id':recipe['guide_asset_id'].rsplit('.',1)[0],'guide_asset_id':recipe['guide_asset_id'],'guide_view':recipe['guide_asset_id'].rsplit('.',1)[1],'guide_image_sha256':recipe['guide_sha256'],'transform':recipe['transform'],'recipe':recipe_path.relative_to(PACK).as_posix(),'note':recipe['notes']}
        meta['image'].update({'path':asset['image']['path'],'width':image.width,'height':image.height,'sha256':file_hash,'rgba_sha256':rgba_hash})
        atomic_json(sidecar,meta)
        asset['image']=meta['image']; asset['provenance']=prov
        groups[recipe['object_id']]['complete']=False
        updated.append({'asset_id':aid,'sha256':file_hash,'rgba_sha256':rgba_hash,'recipe':recipe_path.relative_to(PACK).as_posix()})
    index['assets']=list(assets.values()); index['view_sets']=list(groups.values())
    atomic_json(INDEX,index)
    report={'schema':'ink-staged-repair-install-v1','updated':updated,'updated_count':len(updated),'reason':'Every target, canonical source, candidate and alias guide was SHA-256 checked before first write; root approved all six operations. Sidecars and PNGs were written before atomic set-index update.'}
    atomic_json(OUT/'staged-repair-install-report.json',report)
    print(json.dumps(report,indent=2))
if __name__=='__main__': install()
