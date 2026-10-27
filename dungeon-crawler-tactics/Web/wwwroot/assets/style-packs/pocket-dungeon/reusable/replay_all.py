#!/usr/bin/env python3
"""Capture and replay all eight Pocket style-pack view indices in isolation.

Raw builders are always attempted from the retained atlases and recipes. Any
leaf they cannot reproduce byte-for-byte is restored from an immutable frozen
PNG/metadata archive and is explicitly marked retained-copy in the report.
The source sidecars are never rewritten to pretend a retained copy was raw-built.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys,struct
from pathlib import Path
from PIL import Image

PACK=Path(__file__).resolve().parent.parent
COMPONENTS=('views-core','views-equipment','views-caverns','views-scenes','views-services','views-roads-forest','views-scenery','views-gear-armor')
INDEXES={name:Path('reusable')/name/'set-index.json' for name in COMPONENTS}
VIEWS={'front','top','right','left','bottom','rear'}

def sha_bytes(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def sha(path:Path)->str:return sha_bytes(path.read_bytes())
def rgba_sha(path:Path)->str:
    im=Image.open(path).convert('RGBA')
    return sha_bytes(struct.pack('>II',*im.size)+im.tobytes())
def dump(path:Path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n')
def safe_rel(value:str)->Path:
    p=Path(value)
    if not value or value in {'.','./'} or p.is_absolute() or '..' in p.parts:raise ValueError(f'unsafe pack-relative path: {value}')
    return p
def path_under(root:Path,rel:str)->Path:
    p=(root/safe_rel(rel)).resolve();p.relative_to(root.resolve());return p
def read_json(p:Path):return json.loads(p.read_text())
def active_index_paths(root:Path):
    result={};asset_count=0;set_count=0
    for comp,rel in INDEXES.items():
        p=path_under(root,rel.as_posix())
        if not p.is_file():raise FileNotFoundError(p)
        idx=read_json(p);assets={a['id']:a for a in idx.get('assets',[])}
        if len(assets)!=len(idx.get('assets',[])):raise ValueError(f'{comp}: duplicate asset ids')
        seen=set()
        for group in idx.get('view_sets',[]):
            oid=group['object_id']
            if oid in seen:raise ValueError(f'{comp}: duplicate view-set id {oid}')
            seen.add(oid)
            if set(group.get('views',{}))!=VIEWS:raise ValueError(f'{comp}:{oid}: expected all six directions')
            for view,aid in group['views'].items():
                if aid not in assets:raise ValueError(f'{comp}:{oid}.{view}: missing asset {aid}')
                a=assets[aid]
                if a.get('object_id')!=oid or a.get('view')!=view:raise ValueError(f'{comp}:{aid}: identity mismatch')
        result[comp]={'index':p,'index_rel':rel.as_posix(),'index_data':idx,'assets':assets}
        asset_count+=len(assets);set_count+=len(seen)
    if asset_count!=1956 or set_count!=326:raise ValueError(f'expected8indices/326sets/1956leaves, got {set_count}/{asset_count}')
    return result

def capture(root:Path,archive:Path,confirm:bool):
    if not confirm:raise SystemExit('capture requires --confirm-frozen after global tagging and review are complete')
    root=root.resolve();archive=archive.resolve()
    if archive==root or root in archive.parents:raise ValueError('archive must be outside the canonical/isolated pack root')
    if archive.exists() and any(archive.iterdir()):raise FileExistsError(f'archive must be new or empty: {archive}')
    data=active_index_paths(root);files={};components={};source_paths=set();active_counts={'active-png':0,'active-sidecar':0,'active-index':0}
    for comp,row in data.items():
        idx=row['index'];idx_hash=sha(idx);roster=[];components[comp]={'index_path':row['index_rel'],'index_sha256':idx_hash,'view_sets':len(row['index_data']['view_sets']),'assets':len(row['assets'])}
        files[row['index_rel']]={'role':'active-index','sha256':idx_hash}
        active_counts['active-index']+=1
        for a in row['assets'].values():
            image_rel=a['image']['path'];meta_rel=a.get('metadata_path')
            if not meta_rel:raise ValueError(f"{a['id']}: missing metadata_path")
            ip=path_under(root,image_rel);mp=path_under(root,meta_rel)
            if not ip.is_file() or not mp.is_file():raise FileNotFoundError(f"{a['id']}: missing PNG or metadata")
            image_sha=sha(ip);rgba=rgba_sha(ip);md=read_json(mp)
            if image_sha!=a['image'].get('sha256') or image_sha!=md.get('image',{}).get('sha256'):
                raise ValueError(f"{a['id']}: index/sidecar/file SHA mismatch")
            if rgba!=a['image'].get('rgba_sha256') or rgba!=md.get('image',{}).get('rgba_sha256'):
                raise ValueError(f"{a['id']}: index/sidecar/file RGBA mismatch")
            files[image_rel]={'role':'active-png','sha256':image_sha,'rgba_sha256':rgba,'asset_id':a['id']}
            files[meta_rel]={'role':'active-sidecar','sha256':sha(mp),'asset_id':a['id']}
            active_counts['active-png']+=1;active_counts['active-sidecar']+=1
            roster.append({'asset_id':a['id'],'object_id':a.get('object_id'),'view':a.get('view'),'image_path':image_rel,'metadata_path':meta_rel,'image_sha256':image_sha,'rgba_sha256':rgba,'metadata_sha256':sha(mp)})
            prov=md.get('provenance',{})
            for key in ('source_image','generated_atlas','native_plan_image','native_front_image'):
                value=prov.get(key)
                if isinstance(value,str):source_paths.add(value)
        components[comp]['asset_roster']=roster
    # Hash all raw generation inputs and referenced native source images. These
    # remain in the pack copy, but their immutable hashes are closed by archive.
    for comp in COMPONENTS:
        raw_dir=path_under(root,f'reusable/{comp}/raw')
        if raw_dir.exists():
            for p in raw_dir.rglob('*'):
                if p.is_file():
                    rel=p.relative_to(root).as_posix();files[rel]={'role':'retained-raw-input','sha256':sha(p)}
        code_dir=path_under(root,f'reusable/{comp}')
        for p in code_dir.glob('*.py'):
            rel=p.relative_to(root).as_posix();files[rel]={'role':'replay-code','sha256':sha(p)}
    # Service normalizer rewrites atlas metadata JSONs in place. They are
    # stable build state, not active leaf sidecars; capture them as explicit
    # replay inputs so their deterministic timestamp preservation is checked.
    for p in path_under(root,'reusable/views-services').glob('atlas-*.json'):
        rel=p.relative_to(root).as_posix();files[rel]={'role':'stable-generated-auxiliary','sha256':sha(p)}
    for rel in sorted(source_paths):
        p=path_under(root,rel)
        if not p.is_file():raise FileNotFoundError(f'metadata source input missing: {rel}')
        if rel in files:
            files[rel].setdefault('also_roles',[]).append('referenced-source-input')
            files[rel]['referenced_source_sha256']=sha(p)
        else:files[rel]={'role':'referenced-source-input','sha256':sha(p)}
    for rel in ('collections/roads/manifest.json','collections/forest/manifest.json'):
        p=path_under(root,rel)
        if p.is_file():files[rel]={'role':'source-catalog','sha256':sha(p)}
    # Store exact active output copies under an immutable, pack-relative tree.
    for rel,item in list(files.items()):
        if item['role'] not in {'active-index','active-png','active-sidecar'}:continue
        src=path_under(root,rel);dst=archive/'release'/safe_rel(rel);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
        if sha(dst)!=item['sha256']:raise IOError(f'archive copy mismatch: {rel}')
    if active_counts!={'active-png':1956,'active-sidecar':1956,'active-index':8}:raise ValueError(f'active output counts mismatch: {active_counts}')
    manifest={'schema':'pocket-style-replay-archive-v1','captured_after_freeze':True,'canonical_pack_root_at_capture':str(root),'components':components,'set_count':sum(c['view_sets'] for c in components.values()),'asset_count':sum(c['assets'] for c in components.values()),'active_output_counts':active_counts,'files':files,'replay_policy':{'raw_build_first':True,'mismatch_fallback':'restore exact archived PNG/sidecar/index bytes; record retained-copy per output in report; do not alter sidecar provenance to imply raw reconstruction'}}
    dump(archive/'archive-manifest.json',manifest)
    print(json.dumps({'archive':str(archive),'components':len(components),'sets':manifest['set_count'],'assets':manifest['asset_count'],'active_outputs':sum(v['role'] in {'active-png','active-sidecar','active-index'} for v in files.values()),'input_closure_files':sum(v['role'] not in {'active-png','active-sidecar','active-index'} for v in files.values())},indent=2))

def verify_inputs(root:Path,manifest):
    errors=[]
    for rel,item in manifest['files'].items():
        if item['role'] in {'active-index','active-png','active-sidecar'}:continue
        p=path_under(root,rel)
        if not p.is_file() or sha(p)!=item['sha256']:errors.append(rel)
    if errors:raise ValueError(f'{len(errors)} replay input/code files changed; first: {errors[:20]}')

def commands_for_component(root:Path,comp:str,component_data):
    base=['python3']
    if comp in {'views-core','views-equipment','views-caverns'}:
        return [[*base,f'reusable/{comp}/build_all.py']]
    if comp in {'views-scenes','views-services'}:
        return [[*base,f'reusable/{comp}/normalize.py']]
    if comp=='views-scenery':return [[*base,'reusable/views-scenery/split_atlas.py']]
    if comp=='views-gear-armor':return [[*base,'reusable/views-gear-armor/build_all.py']]
    if comp=='views-roads-forest':
        raw=path_under(root,'reusable/views-roads-forest/raw');result=[]
        for meta_path in sorted(raw.glob('*.provenance.json')):
            meta=read_json(meta_path);file_rel=meta.get('file');objects=meta.get('objects')
            if not file_rel or not objects:raise ValueError(f'{meta_path}: lacks file/object-row recipe')
            args=[]
            for obj in objects:
                oid=obj['object_id'];row=int(obj['row']);args.append(f'{oid},{row}')
            result.append([*base,'reusable/views-roads-forest/split_atlas.py',file_rel,*args])
        if not result:raise ValueError('roads-forest has no raw provenance row manifests')
        return result
    raise ValueError(f'unsupported Pocket style component: {comp}')

def execute(root:Path,archive:Path):
    root=root.resolve();archive=archive.resolve();manifest_path=archive/'archive-manifest.json'
    if not manifest_path.is_file():raise FileNotFoundError(manifest_path)
    manifest=read_json(manifest_path)
    if manifest.get('schema')!='pocket-style-replay-archive-v1' or not manifest.get('captured_after_freeze'):raise ValueError('not a frozen Pocket style archive')
    if archive==root or archive in root.parents:raise ValueError('archive must be external to isolated pack')
    marker_path=root/'reusable/.pocket-style-replay-marker.json'
    if not marker_path.is_file():raise ValueError('isolated marker missing; use prepare-copy')
    marker=read_json(marker_path)
    if marker.get('schema')!='pocket-style-isolated-v1' or marker.get('isolated_pack_root')!=str(root):raise ValueError('isolated marker does not match this copy')
    if marker.get('archive_manifest_sha256')!=sha(manifest_path):raise ValueError('isolated copy was prepared for another archive')
    if root==Path(manifest['canonical_pack_root_at_capture']).resolve():raise ValueError('refusing to replay into canonical Pocket style pack')
    verify_inputs(root,manifest)
    current=active_index_paths(root)
    # Refuse deletion unless every current output still matches the frozen bytes.
    for rel,item in manifest['files'].items():
        if item['role'] not in {'active-index','active-png','active-sidecar'}:continue
        p=path_under(root,rel)
        if not p.is_file() or sha(p)!=item['sha256']:raise ValueError(f'isolated output changed before reset: {rel}')
    report={'schema':'pocket-style-replay-report-v1','archive_manifest_sha256':sha(manifest_path),'raw_builder_commands':[],'outputs':[],'indexes':[],'cleared_output_count':0,'retained_copy_fallback_count':0}
    # Delete all active outputs, including catalogs. Rehydrate only the index
    # and metadata recipe inputs from the immutable archive; PNG outputs remain
    # absent when raw builders start.
    for rel,item in manifest['files'].items():
        if item['role'] in {'active-index','active-png','active-sidecar'}:
            path_under(root,rel).unlink();report['cleared_output_count']+=1
    for rel,item in manifest['files'].items():
        if item['role'] in {'active-index','active-sidecar'}:
            src=path_under(archive/'release',rel);dst=path_under(root,rel);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
            if sha(dst)!=item['sha256']:raise ValueError(f'catalog bootstrap copy mismatch: {rel}')
    # Raw deterministic sub-builders get first opportunity. All commands are
    # local Python scripts, run sequentially because they update shared indexes.
    for comp in COMPONENTS:
        for argv in commands_for_component(root,comp,manifest['components'][comp]):
            row={'component':comp,'argv':argv,'status':'running'};report['raw_builder_commands'].append(row)
            subprocess.run(argv,cwd=root,check=True);row['status']='passed'
    # Exact per-leaf comparison. A mismatch is repaired from a hash-closed
    # archive, and is explicitly reported as retained-copy fallback.
    for comp,compdata in manifest['components'].items():
        idxpath=path_under(root,compdata['index_path']);idx=read_json(idxpath);assets={a['id']:a for a in idx['assets']}
        expected_roster={x['asset_id']:x for x in compdata['asset_roster']}
        report.setdefault('rebuilt_index_deltas',[]).append({'component':comp,'missing_asset_ids':sorted(set(expected_roster)-set(assets)),'extra_asset_ids':sorted(set(assets)-set(expected_roster))})
        for asset_id,a in expected_roster.items():
            image_rel=a['image_path'];meta_rel=a['metadata_path'];exp_png=manifest['files'][image_rel];exp_meta=manifest['files'][meta_rel]
            for rel,expected,role in ((image_rel,exp_png,'png'),(meta_rel,exp_meta,'metadata')):
                dst=path_under(root,rel);good=dst.is_file() and sha(dst)==expected['sha256']
                if role=='png' and good:good=rgba_sha(dst)==expected['rgba_sha256']
                source=('raw-rebuild' if role=='png' else 'retained-snapshot-equal') if good else 'retained-copy-fallback'
                if not good:
                    src=path_under(archive/'release',rel);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
                    if sha(dst)!=expected['sha256']:raise ValueError(f'retained copy mismatch: {rel}')
                    report['retained_copy_fallback_count']+=1
                report['outputs'].append({'component':comp,'asset_id':asset_id,'role':role,'path':rel,'sha256':sha(dst),'rgba_sha256':rgba_sha(dst) if role=='png' else None,'mode':source,'archive_sha256':expected['sha256']})
        expected_index=manifest['files'][compdata['index_path']]
        if sha(idxpath)!=expected_index['sha256']:
            src=path_under(archive/'release',compdata['index_path']);shutil.copyfile(src,idxpath)
            report['retained_copy_fallback_count']+=1;mode='retained-copy-fallback'
        else:mode='builder-equal-to-retained'
        report['indexes'].append({'component':comp,'path':compdata['index_path'],'sha256':sha(idxpath),'mode':mode})
    # Final exact parity gate includes file bytes and canonical pixel bytes.
    failures=[]
    for rel,item in manifest['files'].items():
        if item['role'] not in {'active-index','active-png','active-sidecar'}:continue
        p=path_under(root,rel)
        if not p.is_file() or sha(p)!=item['sha256']:failures.append(rel);continue
        if item['role']=='active-png' and rgba_sha(p)!=item['rgba_sha256']:failures.append(rel+' [RGBA]')
    verify_inputs(root,manifest)
    if failures:raise ValueError(f'final replay parity failed for {len(failures)} outputs: {failures[:40]}')
    final_counts={'active-png':0,'active-sidecar':0,'active-index':0}
    for item in manifest['files'].values():
        if item['role'] in final_counts:final_counts[item['role']]+=1
    if final_counts!=manifest.get('active_output_counts'):raise ValueError(f'final active output counts changed: {final_counts}')
    report.update({'final_parity':'passed','final_active_pngs':sum(v['role']=='active-png' for v in manifest['files'].values()),'final_sidecars':sum(v['role']=='active-sidecar' for v in manifest['files'].values()),'final_indexes':sum(v['role']=='active-index' for v in manifest['files'].values()),'retained_copy_fallback_count':report['retained_copy_fallback_count']})
    output=archive/'replay-report.json';dump(output,report);print(json.dumps({'report':str(output),'final_parity':'passed','pngs':report['final_active_pngs'],'sidecars':report['final_sidecars'],'indexes':report['final_indexes'],'fallback_leaves':report['retained_copy_fallback_count']},indent=2))

def prepare_copy(source:Path,target:Path,archive:Path):
    source=source.resolve();target=target.resolve();archive=archive.resolve();mp=archive/'archive-manifest.json'
    if not mp.is_file():raise FileNotFoundError(mp)
    if target.exists():raise FileExistsError(f'target must be a new isolated copy: {target}')
    if target==source or source in target.parents or target in source.parents:raise ValueError('source and isolated target must be disjoint')
    shutil.copytree(source,target)
    marker={'schema':'pocket-style-isolated-v1','isolated_pack_root':str(target),'canonical_pack_root':str(source),'archive_manifest_sha256':sha(mp),'active_output_scope':'all indexed PNGs, leaf JSON sidecars, and eight active set-index files'}
    dump(target/'reusable/.pocket-style-replay-marker.json',marker)
    print(json.dumps({'isolated_copy':str(target),'archive_manifest_sha256':marker['archive_manifest_sha256']},indent=2))

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('capture');c.add_argument('--pack-root',type=Path,default=PACK);c.add_argument('--archive',type=Path,required=True);c.add_argument('--confirm-frozen',action='store_true')
    p=sub.add_parser('prepare-copy');p.add_argument('--source-pack',type=Path,default=PACK);p.add_argument('--isolated-pack',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    r=sub.add_parser('replay');r.add_argument('--isolated-pack',type=Path,required=True);r.add_argument('--archive',type=Path,required=True)
    v=sub.add_parser('verify');v.add_argument('--isolated-pack',type=Path,required=True);v.add_argument('--archive',type=Path,required=True)
    a=ap.parse_args()
    if a.cmd=='capture':capture(a.pack_root,a.archive,a.confirm_frozen)
    elif a.cmd=='prepare-copy':prepare_copy(a.source_pack,a.isolated_pack,a.archive)
    elif a.cmd=='replay':execute(a.isolated_pack,a.archive)
    elif a.cmd=='verify':
        m=read_json(a.archive/'archive-manifest.json');root=a.isolated_pack.resolve();errs=[]
        for rel,item in m['files'].items():
            if item['role'] not in {'active-index','active-png','active-sidecar'}:continue
            p=path_under(root,rel)
            if not p.is_file() or sha(p)!=item['sha256'] or (item['role']=='active-png' and rgba_sha(p)!=item['rgba_sha256']):errs.append(rel)
        if errs:raise SystemExit(f'{len(errs)} parity errors: {errs[:30]}')
        print(json.dumps({'parity':'passed','active_output_files':sum(x['role'] in {'active-index','active-png','active-sidecar'} for x in m['files'].values())},indent=2))
if __name__=='__main__':main()
