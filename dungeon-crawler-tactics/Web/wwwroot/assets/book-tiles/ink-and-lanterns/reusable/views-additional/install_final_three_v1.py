"""Guarded installer for the last three Root-approved Ink view sets."""
from pathlib import Path
import hashlib, json, os, shutil, struct, tempfile
from PIL import Image
OUT=Path(__file__).resolve().parent
PACK=OUT.parents[1]
INDEX=OUT/'set-index.json'
MANIFEST=OUT/'raw/final-three-approved-install-v1.json'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
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
def jwrite(path,obj): atomic(path,(json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode())
def canonical_rgba(path):
    im=Image.open(path).convert('RGBA')
    return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest(), im.size

def main():
    m=json.loads(MANIFEST.read_text()); assert m['status']=='root-approved-candidate-install'
    idx=json.loads(INDEX.read_text()); assets={a['id']:a for a in idx['assets']}; groups={g['object_id']:g for g in idx['view_sets']}
    plan=[]
    # Entire batch preflight before any mutation.
    for obj in m['objects']:
        source=PACK/obj['canonical_source']['path']; assert sha(source)==obj['canonical_source']['sha256'],f"source changed: {obj['object_id']}"
        g=groups[obj['object_id']]
        assert g['views']==obj['view_ids'],f"view map changed: {obj['object_id']}"
        for view,guard in obj['current_views'].items():
            aid=g['views'][view]; a=assets[aid]; live=PACK/a['image']['path']
            assert a['image']['path']==guard['path'] and sha(live)==guard['sha256'],f"live hash changed: {obj['object_id']}.{view}"
        for view,c in obj['candidates'].items():
            a=assets[g['views'][view]]; cand=PACK/c['path']
            assert sha(cand)==c['sha256'],f"candidate hash changed: {obj['object_id']}.{view}"
            im=Image.open(cand); assert im.size==(256,256),f"candidate canvas: {obj['object_id']}.{view}"
            live=PACK/a['image']['path']; side=PACK/a['metadata_path']
            plan.append((obj,view,c,a,live,side,cand,g))
        contact=PACK/obj['approval_contact']['path']; assert sha(contact)==obj['approval_contact']['sha256'],f"contact changed: {obj['object_id']}"
    # Snapshot exact current index and every target image/sidecar before writes.
    snap=OUT/'raw/final-three-before-install-v1'; snap.mkdir(parents=True,exist_ok=True)
    shutil.copy2(INDEX,snap/'set-index.json')
    before=[]
    for obj,view,c,a,live,side,cand,g in plan:
        name=f"{obj['object_id']}.{view}"
        shutil.copy2(live,snap/(name+'.png')); shutil.copy2(side,snap/(name+'.json'))
        before.append({'object_id':obj['object_id'],'view':view,'path':a['image']['path'],'sha256':sha(live),'metadata_path':a['metadata_path'],'metadata_sha256':sha(side)})
    jwrite(snap/'snapshot.json',{'schema_version':1,'manifest_path':MANIFEST.relative_to(PACK).as_posix(),'manifest_sha256':sha(MANIFEST),'before':before})
    installed=[]
    for obj,view,c,a,live,side,cand,g in plan:
        atomic(live,cand.read_bytes())
        rgba,size=canonical_rgba(live); filehash=sha(live)
        meta=json.loads(side.read_text()); prov=meta.setdefault('provenance',{})
        history=list(prov.get('superseded_provenance',[])); history.append({k:v for k,v in prov.items() if k!='superseded_provenance'}); prov['superseded_provenance']=history
        prov['method']='generated-inferred-orthographic'
        prov['source_image']=obj['canonical_source']['path']; prov['source_sha256']=obj['canonical_source']['sha256']
        prov['notes']='Inferred orthographic view; not recovered pixels or calibrated 3D.'
        prov['approved_repair']={'candidate_path':c['path'],'candidate_sha256':filehash,'contact_path':obj['approval_contact']['path'],'contact_sha256':obj['approval_contact']['sha256'],'request_path':c.get('request_path'),'request_sha256':c.get('request_sha256'),'raw_output_path':c.get('raw_output_path'),'raw_output_sha256':c.get('raw_output_sha256'),'recipe_path':c.get('recipe_path'),'recipe_sha256':c.get('recipe_sha256'),'approval':'Root scoped-approved direction(s) for installation; whole-set independent review pending.'}
        meta['image'].update({'path':a['image']['path'],'width':size[0],'height':size[1],'sha256':filehash,'rgba_sha256':rgba})
        jwrite(side,meta); a['image']=meta['image']; a['provenance']=prov
        installed.append({'object_id':obj['object_id'],'view':view,'asset_id':a['id'],'path':a['image']['path'],'sha256':filehash,'rgba_sha256':rgba})
    for obj in m['objects']:
        g=groups[obj['object_id']]; g['complete']=False; g['review_status']='pending-independent-whole-set-qa'
    idx['assets']=list(assets.values()); idx['view_sets']=list(groups.values()); jwrite(INDEX,idx)
    report={'schema_version':1,'manifest_path':MANIFEST.relative_to(PACK).as_posix(),'manifest_sha256':sha(MANIFEST),'installed':installed,'snapshot_path':'reusable/views-additional/raw/final-three-before-install-v1/snapshot.json','result':'installed; fresh canonical source-plus-six independent review required'}
    jwrite(OUT/'final-three-v1-install-report.json',report); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
