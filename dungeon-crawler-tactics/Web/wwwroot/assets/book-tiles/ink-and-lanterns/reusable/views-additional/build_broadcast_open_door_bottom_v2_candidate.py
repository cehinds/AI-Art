#!/usr/bin/env python3
"""Rebuild a bottom-only open doorway candidate from its retained atlas."""
import hashlib, json, os, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[1]
OBJ = "broadcast-portals-studio-partition-open-doorway"
ATLAS = HERE / "raw" / f"{OBJ}-bottom-v2-atlas.png"
REQUEST = HERE / "raw" / f"{OBJ}-bottom-v2.request.json"
CONTACT = HERE / "qa-broadcast-open-door-source-six-v1.png"
SOURCE = PACK / "broadcast-portals" / "components" / f"{OBJ}.png"
CANDIDATE = HERE / "raw" / f"{OBJ}-bottom-v2-candidate.png"
RECIPE = HERE / "raw" / f"{OBJ}-bottom-v2-candidate.recipe.json"
QA = HERE / f"qa-{OBJ}-bottom-v2-candidate-source-six.png"
VIEWS = ("front", "top", "right", "left", "bottom", "rear")
TARGET_WIDTH = 232

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p, data):
    fd, tmp = tempfile.mkstemp(prefix=p.name+'.', suffix='.tmp', dir=p.parent)
    try:
        with os.fdopen(fd, 'wb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, p)
    except BaseException:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise
def png(im):
    import io
    b=io.BytesIO(); im.save(b,'PNG',optimize=True); return b.getvalue()

def main():
    req=json.loads(REQUEST.read_text().removesuffix('\\n'))
    assert req['object_id']==OBJ and req['view']=='bottom' and req['status']=='generated-atlas-ready-for-normalization'
    assert sha(ATLAS)==req['generated_atlas_sha256'] and sha(SOURCE)==req['reference_inputs'][0]['sha256'] and sha(CONTACT)==req['reference_inputs'][1]['sha256']
    im=Image.open(ATLAS).convert('RGBA'); alpha=np.asarray(im)[:,:,3]; labels,n=ndimage.label(alpha>=245); comps=[]
    for label in range(1,n+1):
        ys,xs=np.nonzero(labels==label)
        if len(xs)>=50: comps.append((len(xs),label,(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)))
    if not comps: raise RuntimeError('No substantial alpha components')
    comps.sort(reverse=True); largest=comps[0][0]; keep=[c for c in comps if c[0]>=largest*.02]
    bounds=(min(c[2][0] for c in keep),min(c[2][1] for c in keep),max(c[2][2] for c in keep),max(c[2][3] for c in keep))
    crop=im.crop(bounds); scale=TARGET_WIDTH/crop.width; size=(TARGET_WIDTH,max(1,round(crop.height*scale)))
    crop=crop.resize(size,Image.Resampling.NEAREST); offset=((256-size[0])//2,(256-size[1])//2)
    canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(crop,offset); data=png(canvas); atomic(CANDIDATE,data)
    lives=[HERE/f'{OBJ}.{v}.png' for v in VIEWS]; before={v:sha(p) for v,p in zip(VIEWS,lives)}
    recipe={'schema_version':1,'status':'candidate-ready-for-independent-review','object_id':OBJ,'direction':'bottom','request_path':'reusable/views-additional/raw/'+REQUEST.name,'request_sha256':sha(REQUEST),'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,'source_atlas_sha256':sha(ATLAS),'canonical_source':'broadcast-portals/components/'+SOURCE.name,'canonical_source_sha256':sha(SOURCE),'contact_reference':'reusable/views-additional/'+CONTACT.name,'contact_reference_sha256':sha(CONTACT),'operation':'keep full bounds of all alpha-connected components at alpha>=245 with area>=2% of largest; isotropic nearest-neighbor scale to target span; center on transparent 256x256','alpha_threshold':245,'component_labels':[c[1] for c in keep],'component_bounds_xyxy_px':list(bounds),'crop_dimensions_px':[bounds[2]-bounds[0],bounds[3]-bounds[1]],'scale':scale,'resized_dimensions_px':list(size),'canvas_offset_xy_px':list(offset),'target_width_px':TARGET_WIDTH,'candidate_path':'reusable/views-additional/raw/'+CANDIDATE.name,'candidate_sha256':hashlib.sha256(data).hexdigest(),'preinstall_view_hashes':before,'preserved_views':['front','top','right','left','rear'],'inference_note':'Two separated jamb underside footprints and open central gap; inferred orthographic view, not recovered pixels or calibrated 3D.'}
    atomic(RECIPE,(json.dumps(recipe,indent=2)+'\n').encode())
    source=Image.open(SOURCE).convert('RGBA'); cells=[canvas if v=='bottom' else Image.open(p).convert('RGBA') for v,p in zip(VIEWS,lives)]
    sheet=Image.new('RGBA',(7*184,216),(239,235,226,255)); draw=ImageDraw.Draw(sheet)
    for col,(cell,label) in enumerate(zip([source]+cells,['source',*VIEWS])):
        x=col*184; draw.text((x+4,22),label,fill=(15,15,15,255)); cell.thumbnail((168,168),Image.Resampling.LANCZOS); sheet.alpha_composite(cell,(x+8+(168-cell.width)//2,42+(168-cell.height)//2))
    atomic(QA,png(sheet)); print(json.dumps({'candidate':str(CANDIDATE),'candidate_sha256':recipe['candidate_sha256'],'recipe_sha256':sha(RECIPE),'qa_contact':str(QA),'bounds':bounds,'size':size,'scale':scale},indent=2))

if __name__=='__main__': main()
