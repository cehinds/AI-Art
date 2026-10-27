#!/usr/bin/env python3
"""Install root-approved Core corner candidates after strict source/current hash preflight."""
import hashlib, json, os, pathlib, struct, tempfile, shutil
from PIL import Image
OUT=pathlib.Path(__file__).resolve().parent
PACK=OUT.parents[1]
STAGE=OUT/'raw/core-staging-corners'
INDEX=OUT/'set-index.json'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
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
    files=sorted(STAGE.glob('installer-handoff-*.json'))
    if len(files)!=10: raise RuntimeError(f'Expected currently approved 10 handoffs, found {len(files)}; rerun after explicit review.')
    index=json.loads(INDEX.read_text()); assets={a['id']:a for a in index['assets']}; groups={s['object_id']:s for s in index['view_sets']}
    plans=[]
    # Full preflight before any write.
    for fp in files:
        m=json.loads(fp.read_text())
        if m.get('status')!='root-approved-candidates-pending-live-install' or m.get('approved_by')!='root': raise RuntimeError(f'Not root-approved: {fp.name}')
        oid=m['object_id']; source=PACK/m['source']['path']
        if not source.is_file() or sha(source)!=m['source']['sha256'] or sha(source)!=m['source_actual_sha256']: raise RuntimeError(f'Source hash mismatch: {oid}')
        if oid not in groups: raise KeyError(oid)
        if set(m['current_views'])!=set(['front','top','right','left','bottom','rear']): raise RuntimeError(f'Incomplete current hashes: {oid}')
        targets=[]
        for d,cur in m['current_views'].items():
            aid=cur['asset_id']
            if aid not in assets or aid not in groups[oid]['views'].values(): raise RuntimeError(f'Index asset mismatch {aid}')
            live=PACK/cur['path']
            if not live.is_file() or sha(live)!=cur['sha256']: raise RuntimeError(f'Current {oid}.{d} changed since handoff')
            a=assets[aid]
            if a['image']['sha256']!=cur['sha256']: raise RuntimeError(f'Index hash mismatch {aid}')
            if d in m['candidate_views']:
                c=m['candidate_views'][d]; cand=STAGE/c['candidate_path']
                if not cand.is_file() or sha(cand)!=c['candidate_sha256']: raise RuntimeError(f'Candidate mismatch {oid}.{d}')
                with Image.open(cand) as image:
                    if image.size!=(256,256): raise RuntimeError(f'Candidate size {oid}.{d}: {image.size}')
                deriv=c.get('derivation',{})
                guidepath=PACK/deriv['guide_path'] if deriv.get('guide_path') else None
                if guidepath and (not guidepath.is_file() or sha(guidepath)!=deriv['guide_sha256']): raise RuntimeError(f'Guide mismatch {oid}.{d}')
                targets.append((d,aid,live,cand,c,deriv))
            elif d in m.get('retained_views',{}):
                retained=m['retained_views'][d]
                if retained['sha256']!=cur['sha256']: raise RuntimeError(f'Retained hash mismatch {oid}.{d}')
        if set(m['candidate_views'])|set(m.get('retained_views',{}))!=set(m['current_views']): raise RuntimeError(f'Candidate/retained direction coverage mismatch {oid}')
        plans.append((fp,m,oid,source,targets))
    # Immutable snapshots before replacements.
    backup=STAGE/'before-install'
    backups=[]
    for fp,m,oid,source,targets in plans:
        for d,cur in m['current_views'].items():
            live=PACK/cur['path']; dest=backup/oid/f'{d}.png';dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists(): shutil.copy2(live,dest)
            if sha(dest)!=cur['sha256']: raise RuntimeError(f'Backup mismatch {oid}.{d}')
            backups.append({'object_id':oid,'direction':d,'path':dest.relative_to(PACK).as_posix(),'sha256':sha(dest)})
    updated=[]
    for fp,m,oid,source,targets in plans:
        for d,aid,live,cand,c,deriv in targets:
            atomic(live,cand.read_bytes())
            with Image.open(live) as im0: im=im0.convert('RGBA')
            asset=assets[aid]; sidecar=PACK/asset['metadata_path']; meta=json.loads(sidecar.read_text())
            old=meta.get('provenance',{}).copy(); prov=meta.setdefault('provenance',{}); prov['superseded_provenance']=[*prov.get('superseded_provenance',[]),old]
            prov['derivation']={**deriv,'method':deriv.get('method','root-approved-core-corner-view'),'candidate_path':c['candidate_path'],'candidate_sha256':c['candidate_sha256'],'staging_handoff':fp.relative_to(PACK).as_posix(),'source_path':m['source']['path'],'source_sha256':m['source']['sha256'],'note':deriv.get('note','Root-approved inferred orthographic corner view; target remains linked to its canonical source.')}
            fsha=sha(live); rgba=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
            meta['image'].update({'path':asset['image']['path'],'width':im.width,'height':im.height,'sha256':fsha,'rgba_sha256':rgba})
            atomic_json(sidecar,meta); asset['image']=meta['image']; asset['provenance']=prov
            updated.append({'object_id':oid,'direction':d,'asset_id':aid,'path':asset['image']['path'],'before_sha256':m['current_views'][d]['sha256'],'after_sha256':fsha,'candidate_sha256':c['candidate_sha256'],'source_sha256':m['source']['sha256'],'handoff':fp.relative_to(PACK).as_posix()})
        groups[oid]['complete']=False
    index['assets']=list(assets.values());index['view_sets']=list(groups.values());atomic_json(INDEX,index)
    report={'schema_version':1,'batch':'core-approved-corner-handoffs-v1','approved_handoff_count':len(plans),'updated_direction_count':len(updated),'updated':updated,'retained_snapshots':backups,'validation':'All source, target-live, index, guide, retained-direction and candidate hashes were checked before writes. Only candidate_views were changed; retained directions were hash-verified and untouched.','root_review':'Fresh current source+six review still required; this install does not change review status.'}
    atomic_json(OUT/'core-approved-corner-handoffs-v1-install-report.json',report)
    print(json.dumps({'sets':len(plans),'directions':len(updated),'objects':[x[2] for x in plans],'report':report['schema_version']},indent=2))
if __name__=='__main__': install()
