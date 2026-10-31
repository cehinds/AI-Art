#!/usr/bin/env python3
"""Hash-guarded installer for the Root-reviewed October 26 candidate batch."""
from pathlib import Path
import hashlib, json, os, tempfile, struct, shutil
from PIL import Image
OUT=Path(__file__).resolve().parent
PACK=OUT.parents[1]
PLAN=OUT/'root-approved-views-20261026-ink-batch-v1.install-plan.json'
INDEX=OUT/'set-index.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def atomic(path,data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
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
    plan=json.loads(PLAN.read_text()); index=json.loads(INDEX.read_text())
    assets={a['id']:a for a in index['assets']}; groups={g['object_id']:g for g in index['view_sets']}
    if len(assets)!=len(index['assets']) or len(groups)!=len(index['view_sets']): raise RuntimeError('duplicate index IDs')
    checked=[]
    for op in plan['operations']:
        aid=op['asset_id']; oid=op['object_id']; view=op['view']
        if aid not in assets or oid not in groups: raise KeyError(aid)
        asset=assets[aid]; group=groups[oid]
        if group['views'].get(view)!=aid: raise RuntimeError(f'group mapping mismatch: {aid}')
        source=PACK/op['source_image']; candidate=PACK/op['candidate_path']; recipe=PACK/op['recipe_path']
        if not source.is_file() or sha(source)!=op['source_sha256']: raise RuntimeError(f'source guard failed: {aid}')
        if not candidate.is_file() or sha(candidate)!=op['candidate_sha256']: raise RuntimeError(f'candidate guard failed: {aid}')
        if not recipe.is_file() or sha(recipe)!=op['recipe_sha256']: raise RuntimeError(f'recipe guard failed: {aid}')
        for vv,guard in op['current_views'].items():
            if group['views'].get(vv)!=f'{oid}.{vv}': raise RuntimeError(f'view mapping changed: {oid}.{vv}')
            live=PACK/guard['path']
            # Candidate view itself is checked against its target hash here, as are retained siblings.
            if not live.is_file() or sha(live)!=guard['sha256']: raise RuntimeError(f'current six guard failed: {oid}.{vv}')
        live=PACK/asset['image']['path']
        if sha(live)!=op['target_current_sha256']: raise RuntimeError(f'target differs from captured current six: {aid}')
        im=Image.open(candidate).convert('RGBA')
        if im.size!=(256,256): raise RuntimeError(f'candidate canvas mismatch: {aid} {im.size}')
        checked.append((op,asset,group,live,candidate,recipe))
    # Persist an exact before snapshot only after every operation passes preflight.
    snap=OUT/'raw'/'root-approved-views-20261026-batch-v1-before'
    snap.mkdir(parents=True,exist_ok=True)
    shutil.copy2(INDEX,snap/'set-index.json')
    before=[]
    for op,asset,group,live,candidate,recipe in checked:
        side=PACK/asset['metadata_path']
        dst=snap/op['asset_id']
        dst.mkdir(parents=True,exist_ok=True)
        shutil.copy2(live,dst/'view.png'); shutil.copy2(side,dst/'metadata.json')
        before.append({'asset_id':op['asset_id'],'path':asset['image']['path'],'sha256':sha(live),'metadata_path':asset['metadata_path'],'metadata_sha256':sha(side)})
    atomic_json(snap/'snapshot.json',{'schema_version':1,'plan':PLAN.relative_to(PACK).as_posix(),'plan_sha256':sha(PLAN),'index_sha256':sha(snap/'set-index.json'),'before':before})
    updated=[]
    for op,asset,group,live,candidate,recipe in checked:
        payload=candidate.read_bytes(); atomic(live,payload)
        im=Image.open(live).convert('RGBA'); file_hash=sha(live); rgba_hash=sha_bytes(struct.pack('>II',*im.size)+im.tobytes())
        side=PACK/asset['metadata_path']; meta=json.loads(side.read_text()); old=meta.get('provenance',{}).copy(); prov=meta.setdefault('provenance',{})
        recipe_obj=json.loads(recipe.read_text())
        prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),old]
        prov['repair_candidate']={'candidate_path':op['candidate_path'],'candidate_sha256':op['candidate_sha256'],'recipe_path':op['recipe_path'],'recipe_sha256':op['recipe_sha256'],'method':recipe_obj.get('method','generated orthographic correction'),'notes':recipe_obj.get('notes','Root-reviewed inferred view candidate; not recovered hidden pixels.'),'root_approval':'Scoped approval recorded by Root on 2026-10-26; fresh canonical source-plus-six review required after install.'}
        prov['source_image']=op['source_image']; prov['source_sha256']=op['source_sha256']
        prov['notes']='Inferred orthographic view, not recovered pixels; not calibrated 3D.'
        meta['image'].update({'path':asset['image']['path'],'width':im.width,'height':im.height,'sha256':file_hash,'rgba_sha256':rgba_hash})
        atomic_json(side,meta); asset['image']=meta['image']; asset['provenance']=prov
        group['complete']=False; group.setdefault('geometry_qa',{})['status']='pending-review'
        updated.append({'asset_id':op['asset_id'],'view_path':asset['image']['path'],'sha256':file_hash,'rgba_sha256':rgba_hash,'recipe':op['recipe_path']})
    index['assets']=list(assets.values()); index['view_sets']=list(groups.values())
    atomic_json(INDEX,index)
    report={'schema_version':1,'batch_id':plan['batch_id'],'plan_sha256':sha(PLAN),'preflight_count':len(checked),'updated':updated,'snapshot':'reusable/views-additional/raw/root-approved-views-20261026-batch-v1-before/snapshot.json','result':'installed; awaiting fresh canonical source-plus-six review'}
    atomic_json(OUT/'root-approved-views-20261026-batch-v1-install-report.json',report)
    print(json.dumps(report,indent=2))
if __name__=='__main__': install()
