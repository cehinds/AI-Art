import hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon')
VIEWS=ROOT/'reusable/views-additional'
STAGE=VIEWS/'raw/candidates/race-workbench-left-alias-v1'
OID='race-circuits-vehicle-upgrade-workbench'
sha=lambda b: hashlib.sha256(b).hexdigest()
pathsha=lambda p: sha(Path(p).read_bytes())
def main_component(im):
    a=np.array(im.getchannel('A'))>0
    labs,n=label(a,np.ones((3,3),dtype=np.uint8)); comps=[]
    for i in range(1,n+1):
        ys,xs=np.where(labs==i)
        comps.append((len(xs),(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)),labs==i))
    return sorted(comps,key=lambda z:z[0],reverse=True)
def bounds(im):
    a=np.array(im.getchannel('A'))>0; ys,xs=np.where(a)
    return [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if len(xs) else None
ops=[]
# Remove only alpha-connected isolated guide strokes documented by bbox/area in the source review.
remove={
 'front':[(27,[174,50,201,51]),(21,[92,50,113,51]),(20,[57,50,77,51]),(17,[139,50,156,51])],
 'right':[(23,[121,50,144,51]),(17,[99,50,116,51])],
 'rear':[(4,[135,49,139,50])],
}
for v, expected in remove.items():
    p=VIEWS/f'{OID}.{v}.png'; im=Image.open(p).convert('RGBA'); comps=main_component(im)
    observed=[(area,bb) for area,bb,_ in comps]
    for area,bb in expected:
        match=next((mask for n,b,mask in comps if n==area and list(b)==bb),None)
        assert match is not None,(v,area,bb,observed)
        arr=np.array(im); arr[match]=0; im=Image.fromarray(arr,'RGBA')
        ops.append({'operation':'remove-disconnected-guide-component','view':v,'component_area':area,'bbox':bb})
    dest=STAGE/f'{v}.clean.candidate.png'; im.save(dest)
# Left candidate: remove both detached alpha islands, then uniform nearest-neighbour calibration
# to the 140px main-body Z shared by the guide-clean front/right/rear bodies (140/142/141).
p=STAGE/'left.candidate.png'; im=Image.open(p).convert('RGBA'); comps=main_component(im)
observed=[(area,bb) for area,bb,_ in comps]
assert len(comps)==1 and comps[0][1]==(62,50,193,248),observed
body=bounds(im)
# The candidate workbench is one connected silhouette; crop its full body and uniformly
# calibrate to the median 141px body Z of the guide-clean front/right/rear views.
crop=im.crop(tuple(body)); target_z=141; scale=target_z/crop.height; nw=round(crop.width*scale); nh=target_z
crop=crop.resize((nw,nh),Image.Resampling.NEAREST)
out=Image.new('RGBA',(256,256),(0,0,0,0)); out.alpha_composite(crop,(128-nw//2,248-nh))
leftout=STAGE/'left.calibrated.candidate.png'; out.save(leftout)
ops.append({'operation':'uniform-nearest-calibration-to-common-z','view':'left','source_body_bbox':body,'source_body_size':[body[2]-body[0],body[3]-body[1]],'target_body_size':[nw,nh],'scale':scale,'anchor_px':[128,248],'reference_body_z':{'front':140,'right':142,'rear':141},'target_z':141})
# Remove only the two root-confirmed isolated marks above the workbench BOTTOM silhouette.
bp=VIEWS/f'{OID}.bottom.png'; bim=Image.open(bp).convert('RGBA'); bcomps=main_component(bim); bobs=[(area,bb) for area,bb,_ in bcomps]
for area,bb in [(22,[30,67,52,68]),(5,[237,58,238,63])]:
    match=next((mask for n,b,mask in bcomps if n==area and list(b)==bb),None)
    assert match is not None,(area,bb,bobs)
    ba=np.array(bim); ba[match]=0; bim=Image.fromarray(ba,'RGBA')
    ops.append({'operation':'remove-disconnected-guide-component','view':'bottom','component_area':area,'bbox':bb})
bottomout=STAGE/'bottom.clean.candidate.png'; bim.save(bottomout)
# Compose source plus staged-clean current views. Source is shown as native source; six columns are principal views.
contact=Image.new('RGBA',(7*256,256),(236,236,236,255)); draw=ImageDraw.Draw(contact)
src=Image.open(ROOT/'race-circuits/components'/f'{OID}.png').convert('RGBA')
# fit source proportionally into one cell for a clear comparison
src.thumbnail((220,220),Image.Resampling.NEAREST); contact.alpha_composite(src,(18+(256-src.width)//2,25+(220-src.height)//2)); draw.text((8,5),'source',fill='black')
for c,v in enumerate(['front','top','right','left','bottom','rear'],1):
    if v in ['front','right','rear']:
        im=Image.open(STAGE/f'{v}.clean.candidate.png').convert('RGBA')
    elif v=='left': im=Image.open(leftout).convert('RGBA')
    elif v=='bottom': im=Image.open(bottomout).convert('RGBA')
    else: im=Image.open(VIEWS/f'{OID}.{v}.png').convert('RGBA')
    contact.alpha_composite(im,(c*256,0)); draw.text((c*256+5,5),v,fill='black')
cp=STAGE/'cleaned-calibrated-source-plus-six.png'; contact.convert('RGB').save(cp)
# Body bounds after ignoring isolated guide islands are recorded for geometric review.
records={}
for v in ['front','right','left','bottom','rear']:
    im=Image.open(STAGE/f'{v}.clean.candidate.png').convert('RGBA') if v in ['front','right','rear','bottom'] else Image.open(leftout).convert('RGBA')
    records[v]={'bbox':bounds(im),'sha256':pathsha(STAGE/f'{v}.clean.candidate.png' if v in ['front','right','rear','bottom'] else leftout)}
recipe={'schema_version':1,'object_id':OID,'source_path':'race-circuits/components/'+OID+'.png','source_sha256':pathsha(ROOT/'race-circuits/components'/f'{OID}.png'),'staged_only':True,'current_live_images_unchanged':True,'operations':ops,'body_bounds_after_cleanup':records,'contact_path':cp.relative_to(ROOT).as_posix(),'contact_sha256':pathsha(cp),'images':{v:{'path':(STAGE/f'{v}.clean.candidate.png').relative_to(ROOT).as_posix(),'sha256':pathsha(STAGE/f'{v}.clean.candidate.png')} for v in ['front','right','rear']}|{'left':{'path':leftout.relative_to(ROOT).as_posix(),'sha256':pathsha(leftout)},'bottom':{'path':bottomout.relative_to(ROOT).as_posix(),'sha256':pathsha(bottomout)}}}
(STAGE/'cleanup-calibration-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
print(json.dumps(recipe,indent=2))
