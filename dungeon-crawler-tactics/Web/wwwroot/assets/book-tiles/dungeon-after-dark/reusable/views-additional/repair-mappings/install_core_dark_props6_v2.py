"""Guarded install of Root-approved Core props6 directions (Siege REAR excluded)."""
from pathlib import Path
import copy, hashlib, json, os, struct
from PIL import Image

HERE=Path(__file__).resolve().parent
OUT=HERE.parent
BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'
RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
HANDOFF=OUT/'candidates/core-dark-next-six-props-20261026/approved-all14-installer-handoff-v2.json'
MANIFEST=OUT/'candidates/core-dark-next-six-props-20261026/approved-all14-candidate-manifest-v2.json'
REVIEW=Path('/workspace/scratch/core-dark-next-six-props-handoff-20261026.json')
BEFORE=OUT/'prebuilt/core-dark-props6-v2-before'
SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
PROMPTS=OUT/'prompts/core-dark-next-six-props-20261026'
CID='core-dark-props6-root-approved-v2'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
    im=Image.open(p).convert('RGBA')
    return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,rel):
    p=(root/rel).resolve(); p.relative_to(root.resolve()); return p
def relbook(p): return Path(p).resolve().relative_to(BOOK.resolve()).as_posix()
def atomic(p,data):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+'.tmp'); t.write_bytes(data if isinstance(data,bytes) else data.encode()); os.replace(t,p)

def main():
    hand=json.loads(HANDOFF.read_text()); man=json.loads(MANIFEST.read_text())
    assert sha(MANIFEST)==hand['candidate_manifest_sha256']
    assert len(hand['objects'])==6 and hand['scope'].find('Siege Engine REAR blocked')>=0
    candmap={(c['object_id'],c['direction']):c for c in man['candidates']}
    idx=json.loads(INDEX.read_text()); recipe=json.loads(RECIPE.read_text())
    assets={a['id']:copy.deepcopy(a) for a in idx['assets']}
    sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']}
    entries=recipe['entries']; entrymap={e['asset_id']:e for e in entries}
    prepared=[]
    for obj in hand['objects']:
        oid=obj['object_id']
        src=safe(BOOK,obj['canonical_source']['path'])
        assert sha(src)==obj['canonical_source']['sha256'],oid
        for v,b in obj['current_views'].items(): assert sha(safe(BOOK,b['path']))==b['sha256'],(oid,v)
        directions=[(k,c) for (o,k),c in candmap.items() if o==oid]
        assert directions
        for view,c in directions:
            aid=f'{oid}.{view}'; assert aid in assets
            assert c['candidate_sha256'] and c['candidate_path']
            cand=safe(BOOK,c['candidate_path']); cs=c['candidate_sha256']; assert sha(cand)==cs,(aid,'candidate')
            base=obj['current_views'][view]['sha256']
            a=assets[aid]; dest=safe(BOOK,a['image']['path']); md=safe(BOOK,a['metadata_path'])
            assert sha(dest) in (base,cs),(aid,'live-base')
            old=json.loads(md.read_text()); assert old['image']['sha256'] in (base,cs)
            new=copy.deepcopy(old); im=Image.open(cand).convert('RGBA')
            new['image'].update(width=im.width,height=im.height,sha256=cs,rgba_sha256=rgba(cand))
            new.setdefault('provenance_history',[]).append({'candidate_id':CID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
            deriv=c['derivation']; input_path=deriv.get('input') or deriv.get('input_path')
            raw=Path(input_path).resolve() if input_path else cand
            assert raw.is_file()
            rawsha=deriv.get('input_sha256') if input_path else sha(raw)
            rawsha=rawsha or sha(raw)
            assert sha(raw)==rawsha
            req=raw.with_suffix(raw.suffix+'.request.json') if deriv.get('input') else None
            reqj=json.loads(req.read_text()) if req and req.is_file() else {}
            request_id=reqj.get('request_id')
            prompt=reqj.get('prompt')
            promptpath=PROMPTS/f'{aid}.{request_id or "request"}.{hashlib.sha256(prompt.encode()).hexdigest()[:12] if prompt else "noprompt"}.txt'
            if prompt:
                promptpath.parent.mkdir(parents=True,exist_ok=True)
                if promptpath.exists(): assert promptpath.read_text()==prompt
                else: atomic(promptpath,prompt+'\n')
            prov={'method':'root-approved-source-guided-six-view-repair','source_image':relbook(src),'source_sha256':sha(src),
                  'candidate_image':relbook(cand),'candidate_image_sha256':cs,
                  'candidate_handoff':relbook(HANDOFF),'candidate_handoff_sha256':sha(HANDOFF),
                  'candidate_manifest':relbook(MANIFEST),'candidate_manifest_sha256':sha(MANIFEST),
                  'derivation_input':relbook(raw),'derivation_input_sha256':rawsha,'request_path':relbook(req) if req and req.is_file() else None,'request_sha256':sha(req) if req and req.is_file() else None,'request_id':request_id,
                  'prompt_path':relbook(promptpath) if prompt else None,'prompt_sha256':sha(promptpath) if prompt else None,
                  'normalization':copy.deepcopy(c['derivation']),'notes':'Root-approved scoped candidate. Blocked Siege Engine REAR is excluded; no blocked direction is regenerated or substituted.'}
            assert not prov['source_image'].startswith('/')
            for k in ('candidate_image','candidate_handoff','candidate_manifest','derivation_input'):
                assert not prov[k].startswith('/') and safe(BOOK,prov[k]).is_file(),(aid,k)
            if prov['request_path']: assert not prov['request_path'].startswith('/') and safe(BOOK,prov['request_path']).is_file()
            if prov['prompt_path']: assert not prov['prompt_path'].startswith('/')
            new['provenance']=prov
            mt=json.dumps(new,indent=2)+'\n'; mh=hashlib.sha256(mt.encode()).hexdigest()
            snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
            ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':relbook(cand).removeprefix('reusable/views-additional/'),'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':relbook(HANDOFF),'candidate_manifest_sha256':sha(MANIFEST)}
            if aid in entrymap:
                assert entrymap[aid]['final_sha256']==cs and entrymap[aid]['metadata_sha256']==mh,(aid,'existing recipe mismatch')
            prepared.append((aid,oid,dest,md,cand,base,cs,new,mt,mh,snap,ent))
    assert len(prepared)==14
    # Stage immutable before/snapshot records only after every guard has passed.
    for aid,oid,dest,md,cand,base,cs,new,mt,mh,snap,ent in prepared:
        bp=BEFORE/(aid+'.png'); jp=BEFORE/(aid+'.json'); sp=safe(BOOK,snap)
        if not bp.exists(): atomic(bp,dest.read_bytes())
        else: assert sha(bp)==base
        if not jp.exists(): atomic(jp,md.read_bytes())
        else: assert json.loads(jp.read_text())['image']['sha256']==base
        if not sp.exists(): atomic(sp,mt.encode())
        else: assert sha(sp)==mh
    for aid,oid,dest,md,cand,base,cs,new,mt,mh,snap,ent in prepared:
        if sha(dest)==base: atomic(dest,cand.read_bytes())
        assert sha(dest)==cs
        if sha(md)!=mh: atomic(md,mt.encode())
        assert sha(md)==mh; assets[aid]=copy.deepcopy(new)
        if aid not in entrymap: entries.append(ent); entrymap[aid]=ent
        sets[oid]['complete']=False
        sets[oid]['notes']='Root-approved scoped directions installed; waiting for fresh canonical source-plus-six review.'
    ni=copy.deepcopy(idx)
    ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']]
    ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
    assert len({a['id'] for a in ni['assets']})==len(ni['assets'])
    assert len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
    atomic(RECIPE,json.dumps(recipe,indent=2)+'\n'); atomic(INDEX,json.dumps(ni,indent=2)+'\n')
    print(json.dumps({'installed':[x[0] for x in prepared],'index_sha256':sha(INDEX),'recipe_entry_count':len(entries)},indent=2))

if __name__=='__main__': main()
