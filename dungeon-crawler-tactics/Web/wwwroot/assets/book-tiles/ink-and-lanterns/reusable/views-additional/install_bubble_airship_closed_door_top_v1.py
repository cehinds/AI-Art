#!/usr/bin/env python3
"""Install the root-approved closed-door bottom candidate after hash preflight."""
import hashlib, json, os, struct, tempfile
from pathlib import Path
from PIL import Image

HERE=Path(__file__).resolve().parent
PACK=HERE.parents[1]
OBJ='bubble-airship-riveted-scrap-hull-closed-doorway'
INDEX=HERE/'set-index.json'
RECIPE=HERE/'raw'/f'{OBJ}-top-v1-candidate.recipe.json'
REQUEST=HERE/'raw'/f'{OBJ}-top-v1.request.json'
ATLAS=HERE/'raw'/f'{OBJ}-top-v1-atlas.png'
CANDIDATE=HERE/'raw'/f'{OBJ}-top-v1-candidate.png'
SOURCE=PACK/'bubble-airship'/'components'/f'{OBJ}.png'
CONTACT=HERE/'qa-bubble-airship-closed-door-source-six-top-repair-v1.png'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,data):
    fd,tmp=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    except BaseException:
        try:os.unlink(tmp)
        except FileNotFoundError:pass
        raise
def atomic_json(p,x): atomic(p,(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())

def main():
    recipe=json.loads(RECIPE.read_text())
    idx=json.loads(INDEX.read_text())
    assets={a['id']:a for a in idx['assets']}
    groups={g['object_id']:g for g in idx['view_sets']}
    aid=OBJ+'.top';a=assets[aid];assert a['view']=='top' and a['id']==OBJ+'.top' and a['image']['path'].endswith(OBJ+'.top.png');live=PACK/a['image']['path'];meta_path=PACK/a['metadata_path']
    meta=json.loads(meta_path.read_text())
    assert recipe['status']=='candidate-ready-for-independent-review'
    assert sha(REQUEST)==recipe['request_sha256'] and sha(ATLAS)==recipe['source_atlas_sha256']
    assert sha(SOURCE)==recipe['canonical_source_sha256'] and sha(CONTACT)==recipe['contact_reference_sha256']
    assert sha(CANDIDATE)==recipe['candidate_sha256']
    for direction,expected in recipe['preinstall_view_hashes'].items():
        path=PACK/f'reusable/views-additional/{OBJ}.{direction}.png'
        assert sha(path)==expected,(direction,sha(path),expected)
    prior=meta.get('provenance',{})
    new_prov={**prior,
      'superseded_provenance':[*prior.get('superseded_provenance',[]),{k:v for k,v in prior.items() if k!='superseded_provenance'}],
      'method':'generated',
      'source_image':'bubble-airship/components/'+SOURCE.name,
      'source_sha256':sha(SOURCE),
      'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,
      'source_atlas_sha256':sha(ATLAS),
      'generation_recipe':'reusable/views-additional/raw/'+REQUEST.name,
      'generation_recipe_sha256':sha(REQUEST),
      'normalization_recipe':'reusable/views-additional/raw/'+RECIPE.name,
      'normalization_recipe_sha256':sha(RECIPE),
      'normalization':{'operation':recipe['operation'],'alpha_threshold':recipe['alpha_threshold'],'component_labels':[recipe.get('component_label')],'component_bounds_xyxy_px':recipe['component_bounds_xyxy_px'],'scale':recipe['scale'],'resized_dimensions_px':recipe['resized_dimensions_px'],'canvas_offset_xy_px':recipe['canvas_offset_xy_px']},
      'notes':'Inferred bottom principal view with a narrow overhead wall/door edge beneath lintel, no broad red door face; not recovered pixels or calibrated 3D.'}
    atomic(live,CANDIDATE.read_bytes())
    im=Image.open(live).convert('RGBA'); fh=sha(live)
    image={'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':fh,'rgba_sha256':hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()}
    meta['image']=image;meta['provenance']=new_prov;atomic_json(meta_path,meta)
    a['image']=image;a['provenance']=new_prov
    groups[OBJ]['complete']=False
    idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());atomic_json(INDEX,idx)
    report={'schema':'bubble-airship-closed-door-top-v1-install-v1','object_id':OBJ,'direction':'top','image_sha256':fh,'rgba_sha256':image['rgba_sha256'],'preinstall_sha256':recipe['preinstall_view_hashes']['top'],'preserved_directions':['front','right','left','bottom','rear'],'review_contact_reference_sha256':sha(CONTACT),'status':'installed-pending-current-source-six-review'}
    atomic_json(HERE/'bubble-airship-closed-door-top-v1-install-report.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
