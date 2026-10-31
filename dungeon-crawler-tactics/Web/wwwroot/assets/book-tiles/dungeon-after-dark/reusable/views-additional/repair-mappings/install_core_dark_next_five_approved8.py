"""Install the Root-approved eight-direction Core structures subset with exact guards."""
from pathlib import Path
import copy, hashlib, json, os, struct
from PIL import Image
HERE=Path(__file__).resolve().parent
OUT=HERE.parent
BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'
RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
PACKET=OUT/'candidates/core-dark-next-five-structures-20261026/approved-eight-installer-handoff-v1.json'
PACKET_SHA='2a51e0708255005c138df083c37d22ce8f7568aaf0676babef347dc4103aa360'
MANIFEST_SHA='8ecfe172c5c2f88f6e478421fac33ea38009025daed8adb8cf7ad65fdbd9b816'
BEFORE=OUT/'prebuilt/core-dark-next-five-approved8-before'
CID='core-dark-next-five-approved8-v1'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(p):
    im=Image.open(p).convert('RGBA')
    return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root, value):
    p=(root/value).resolve(); p.relative_to(root.resolve()); return p
def rel(p): return Path(p).resolve().relative_to(BOOK.resolve()).as_posix()
def atomic(path, data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    tmp.write_bytes(data if isinstance(data,bytes) else data.encode())
    os.replace(tmp,path)
def pack_path(value):
    p=Path(value)
    if p.is_absolute(): return rel(p)
    if safe(BOOK,value).is_file(): return Path(value).as_posix()
    raise AssertionError(f'non-pack provenance path {value}')

def main():
    assert sha(PACKET)==PACKET_SHA,sha(PACKET)
    packet=json.loads(PACKET.read_text())
    manifest_path=safe(BOOK,packet['candidate_manifest'])
    assert sha(manifest_path)==MANIFEST_SHA,sha(manifest_path)
    manifest=json.loads(manifest_path.read_text())
    assert len(packet['objects'])==5
    assert packet['root_acceptance']
    idx=json.loads(INDEX.read_text()); recipe=json.loads(RECIPE.read_text())
    assets={a['id']:copy.deepcopy(a) for a in idx['assets']}
    sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']}
    entries=recipe['entries']; entrymap={e['asset_id']:e for e in entries}
    prepared=[]
    for obj in packet['objects']:
        oid=obj['object_id']; source=obj['canonical_source']; src=safe(BOOK,source['path'])
        assert sha(src)==source['sha256'],(oid,'canonical source changed')
        for view, binding in obj['current_views'].items():
            assert sha(safe(BOOK,binding['path']))==binding['sha256'],(oid,view,'base changed')
        for candidate in obj['candidates']:
            view=candidate['view']; aid=f'{oid}.{view}'
            cand=safe(BOOK,candidate['path']); cs=candidate['sha256']
            assert sha(cand)==cs,(aid,'candidate mismatch')
            assert list(Image.open(cand).size)==candidate['dimensions_px'],(aid,'dimensions')
            binding=obj['current_views'][view]; base=binding['sha256']
            asset=assets[aid]; dst=safe(BOOK,asset['image']['path']); md=safe(BOOK,asset['metadata_path'])
            assert sha(dst)==base,(aid,'live base changed')
            old=json.loads(md.read_text()); assert old['image']['sha256']==base,(aid,'sidecar/base mismatch')
            new=copy.deepcopy(old); image=Image.open(cand).convert('RGBA')
            new['image'].update(width=image.width,height=image.height,sha256=cs,rgba_sha256=rgba_sha(cand))
            new.setdefault('provenance_history',[]).append({'candidate_id':CID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
            deriv=copy.deepcopy(candidate.get('derivation',{}))
            def normalize(v):
                if isinstance(v,dict):
                    return {k:normalize(x) for k,x in v.items()}
                if isinstance(v,list): return [normalize(x) for x in v]
                if isinstance(v,str) and v.startswith('/'):
                    try: return rel(v)
                    except ValueError: return v
                return v
            deriv=normalize(deriv)
            prov={'method':'root-approved-scoped-candidate-install','source_image':rel(src),'source_sha256':sha(src),
                'candidate_image':rel(cand),'candidate_image_sha256':cs,
                'candidate_manifest':rel(manifest_path),'candidate_manifest_sha256':sha(manifest_path),
                'installer_packet':rel(PACKET),'installer_packet_sha256':sha(PACKET),
                'handoff_sha256':packet['source_handoff_sha256'],
                'approved_contacts':[{'path':rel(c['path']),'sha256':c['sha256']} for c in packet['root_accepted_contacts']],
                'derivation':deriv,'notes':'Root-approved target-specific illustrative view; any hidden geometry is inferred, not recovered.'}
            for key in ('source_image','candidate_image','candidate_manifest','installer_packet'):
                assert not prov[key].startswith('/') and safe(BOOK,prov[key]).is_file(),(aid,key)
            new['provenance']=prov
            metadata=(json.dumps(new,indent=2)+'\n').encode(); mh=hashlib.sha256(metadata).hexdigest()
            snapshot=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
            entry={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':candidate['path'].replace('reusable/views-additional/','',1),
                'candidate_sha256':cs,'base_sha256':base,'final_sha256':cs,'metadata_path':new['metadata_path'],
                'metadata_snapshot_path':snapshot,'metadata_sha256':mh,'live_before_install_sha256':base,
                'superseded_installed_sha256':base,'review_record':rel(PACKET),'candidate_manifest_sha256':sha(manifest_path)}
            prior=entrymap.get(aid)
            if prior:
                assert prior['final_sha256']==base,(aid,'existing replay entry is not supersedable')
                entries[entries.index(prior)]=entry
            else: entries.append(entry)
            entrymap[aid]=entry
            prepared.append((aid,oid,view,dst,md,cand,base,cs,new,metadata,mh,snapshot))
    assert len(prepared)==8 and len({x[0] for x in prepared})==8
    # Verify all targets before making any live writes.
    for aid,oid,view,dst,md,cand,base,cs,new,metadata,mh,snapshot in prepared:
        snap=safe(BOOK,snapshot); before_png=BEFORE/(aid+'.png'); before_json=BEFORE/(aid+'.json')
        if before_png.exists(): assert sha(before_png)==base
        if before_json.exists(): assert json.loads(before_json.read_text())['image']['sha256']==base
        if snap.exists(): assert sha(snap)==mh,(aid,'snapshot conflict')
    # Retain exact previous bytes; then write images/sidecars, followed by atomic recipe/index.
    for aid,oid,view,dst,md,cand,base,cs,new,metadata,mh,snapshot in prepared:
        bp=BEFORE/(aid+'.png'); jp=BEFORE/(aid+'.json'); snap=safe(BOOK,snapshot)
        if not bp.exists(): atomic(bp,dst.read_bytes())
        if not jp.exists(): atomic(jp,md.read_bytes())
        if not snap.exists(): atomic(snap,metadata)
    for aid,oid,view,dst,md,cand,base,cs,new,metadata,mh,snapshot in prepared:
        atomic(dst,cand.read_bytes()); assert sha(dst)==cs
        atomic(md,metadata); assert sha(md)==mh
        assets[aid]=copy.deepcopy(new)
    for oid in {x[1] for x in prepared}:
        sets[oid]['complete']=False
        sets[oid]['notes']='Root-approved Core scoped views installed; awaiting fresh current source-plus-six review.'
    # Declare explicit inferred alias groups where accepted candidate directions are aliases.
    aliases={
      'faction-larracos-city-bridge-segment':{'views':['front','rear'],'reason':'Root-approved same-target endpoint projection aliases for this symmetric low bridge; hidden endpoint differences are inferred.'},
      'ghost-havana-weathered-stucco-closed-doorway':{'views':['front','rear'],'reason':'Root-approved horizontal mirror symmetry; rear finish is inferred for a closed doorway.'}
    }
    for oid,row in aliases.items():
        group=copy.deepcopy(row)
        decls=sets[oid].setdefault('symmetry',[])
        if group not in decls: decls.append(group)
    ni=copy.deepcopy(idx)
    ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']]
    ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
    assert len({a['id'] for a in ni['assets']})==len(ni['assets'])
    assert len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
    atomic(RECIPE,json.dumps(recipe,indent=2)+'\n')
    atomic(INDEX,json.dumps(ni,indent=2)+'\n')
    print(json.dumps({'installed':[r[0] for r in prepared],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__': main()
