#!/usr/bin/env python3
"""Rebuild candidate-only orthographic ground/platform views from retained atlases."""
from PIL import Image, ImageDraw
import json, hashlib, os, math, struct

PACK='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'
BASE=os.path.join(PACK,'reusable/views-additional')
CAND=os.path.join(BASE,'candidates/equipment-dark-six-ground-platforms-20261026')
HAND='/workspace/scratch/equipment-dark-six-ground-platforms-handoff-20261026.json'
HAND_SHA='322d4973ff94801647c5094eda70c11347a20325b66dd0f61c62c4ccff7eb0d9'

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def rgba_sha(im):
    im=im.convert('RGBA'); w,h=im.size
    return hashlib.sha256(struct.pack('>II',w,h)+im.tobytes()).hexdigest()
def bbox_alpha(im, threshold=64):
    a=im.convert('RGBA').getchannel('A').point(lambda x:255 if x>=threshold else 0)
    return a.getbbox()
def cell_crop(raw_path, cols, rows, idx, inset=0):
    im=Image.open(raw_path).convert('RGBA'); w,h=im.size
    col=idx%cols; row=idx//cols
    x0=round(col*w/cols)+inset; x1=round((col+1)*w/cols)-inset
    y0=round(row*h/rows)+inset; y1=round((row+1)*h/rows)-inset
    cell=im.crop((x0,y0,x1,y1)); bb=bbox_alpha(cell,64)
    if not bb: raise RuntimeError(f'empty cell {raw_path} idx={idx}')
    return cell.crop(bb),[x0+bb[0],y0+bb[1],x0+bb[2],y0+bb[3]],cell.size
def normalize(crop, max_w=216, max_h=104, ycenter=130):
    w,h=crop.size; scale=min(max_w/w,max_h/h,1.0)
    nw=max(1,round(w*scale)); nh=max(1,round(h*scale))
    scaled=crop.resize((nw,nh),Image.Resampling.NEAREST)
    out=Image.new('RGBA',(256,256),(0,0,0,0))
    out.alpha_composite(scaled,((256-nw)//2, max(0,min(256-nh,round(ycenter-nh/2)))))
    return out,scale,(nw,nh)

hand=json.load(open(HAND)); assert sha(HAND)==HAND_SHA, 'handoff SHA changed'
objects={o['object_id']:o for o in hand['objects']}
atlases={
 'industry-menagerie-industrial-brick-edge-transition':('industry-atlas-v1.png',2,2,['front','right','left','rear'],216,104),
 'iron-stations-platform-edge-segment':('station-edge-atlas-v1.png',2,2,['front','right','left','rear'],216,104),
 'iron-stations-platform-end-ramp':('ramp-ends-atlas-v1.png',2,1,['front','rear'],210,134),
 'over-city-city-cobblestone-corner-transition':('overcity-corner-atlas-v1.png',3,1,['front','right','left'],216,104),
 'over-city-city-cobblestone-edge-transition':('overcity-edge-atlas-v1.png',3,1,['front','right','left'],216,104),
 'over-city-venues-civic-stone-tile-corner-transition':('civic-corner-front-atlas-v1.png',1,1,['front'],216,104),
}
manifest={'candidate_id':'equipment-dark-six-ground-platforms-v1','candidate_only':True,'scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_equipment','reviewer':'page_inventory','installer':'views_dark_books','handoff_path':HAND,'handoff_sha256':HAND_SHA,'source_and_six_activation_proof':'/tmp/page-qa-dark-unowned-twelve-current-20261026-01.png.json','source_and_six_activation_proof_sha256':'1be1842a0e85b06a7739ad2c53f97412b03f8f90ea5611008fc4eb11502d0e3d','normalizer_path':'reusable/views-additional/candidates/equipment-dark-six-ground-platforms-20261026/raw/prepare_ground_candidates_v1.py','sets':[]}
contact_rows=[]
for oid,(rawname,cols,rows,views,maxw,maxh) in atlases.items():
    o=objects[oid]; raw=os.path.join(CAND,'raw',rawname); rawsha=sha(raw)
    generated=rawname.replace('-atlas','').replace('-front-atlas','')
    outviews={}
    # Native top plans are source-backed identity copies, for exact source-supported footprint.
    if oid in ('industry-menagerie-industrial-brick-edge-transition','over-city-city-cobblestone-edge-transition'):
        src=o['source']['path']; dest=os.path.join(CAND,'images',oid+'.top.candidate-v1.png')
        Image.open(src).convert('RGBA').save(dest,optimize=False)
        outviews['top']={'path':dest,'sha256':sha(dest),'method':'native-source-copy','source_path':src,'source_sha256':sha(src),'normalization':'unchanged source pixels/aspect; native top plan'}
    for idx,v in enumerate(views):
        crop,bb,cellsize=cell_crop(raw,cols,rows,idx)
        out,scale,size=normalize(crop,maxw,maxh)
        dest=os.path.join(CAND,'images',oid+'.'+v+'.candidate-v1.png')
        out.save(dest,optimize=False)
        outviews[v]={'path':dest,'sha256':sha(dest),'method':'generated-atlas-cell','generated_atlas':raw,'generated_atlas_sha256':rawsha,'cell_index':idx,'cell_grid':[cols,rows],'cell_order':views,'cell_size':list(cellsize),'alpha64_crop_bbox_global':bb,'normalization':{'filter':'NEAREST','uniform_scale':scale,'resized_dimensions':list(size),'canvas':[256,256],'anchor_px':[128,128],'placement_xy':[(256-size[0])//2,max(0,min(256-size[1],round(130-size[1]/2)))]}}
    # Scope-safe native/candidate/base closure for every changed view.
    src=o['source']['path']
    entry={'object_id':oid,'source_path':src,'source_sha256':sha(src),'affected_views':sorted(outviews.keys()),'base_current_views':{},'candidates':outviews,'notes':'Generated orthographic views are inferred illustrations of unseen surfaces; native source-backed plan copies retain original pixels. Candidate only; no production files changed.'}
    for v in ('front','top','right','left','bottom','rear'):
        p=o['views'][v]['path']; entry['base_current_views'][v]={'path':p,'sha256':sha(p)}
    # Validate all source and view bytes still match activation guard before staging them.
    assert entry['source_sha256']==o['source']['sha256'], oid+' source changed since activation'
    for v in ('front','top','right','left','bottom','rear'):
        assert entry['base_current_views'][v]['sha256']==o['views'][v]['sha256'], oid+' '+v+' changed since activation'
    manifest['sets'].append(entry)
    # Contact strip: native source followed by current six, replacing each changed target.
    tiles=[]; labels=['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR']
    sm=Image.open(src).convert('RGBA'); tiles.append(sm)
    for v in ('front','top','right','left','bottom','rear'):
        if v in outviews: tiles.append(Image.open(outviews[v]['path']).convert('RGBA'))
        else: tiles.append(Image.open(o['views'][v]['path']).convert('RGBA'))
    contact_rows.append((oid,labels,tiles))

# Save hash-bound manifest and a visual source+six contact for Page.
mp=os.path.join(CAND,'candidate-manifest-v1.json')
open(mp,'w').write(json.dumps(manifest,indent=2)+'\n')
tile_w=170; tile_h=170; label_h=26; pad=8; row_h=tile_h+label_h+pad
sheet=Image.new('RGBA',(pad+7*(tile_w+pad),pad+len(contact_rows)*row_h),(34,34,40,255)); dr=ImageDraw.Draw(sheet)
for ri,(oid,labels,tiles) in enumerate(contact_rows):
    y=pad+ri*row_h; dr.text((pad,y),oid,fill=(255,255,255,255))
    ty=y+label_h
    for ci,(lab,im) in enumerate(zip(labels,tiles)):
        x=pad+ci*(tile_w+pad)
        im.thumbnail((tile_w,tile_h),Image.Resampling.NEAREST)
        sheet.alpha_composite(im,(x+(tile_w-im.width)//2,ty+(tile_h-im.height)//2))
        dr.text((x,ty+tile_h),lab,fill=(255,255,255,255))
cp=os.path.join(CAND,'contacts','source-six-candidate-v1.png'); sheet.save(cp)
receipt={'candidate_manifest_path':os.path.relpath(mp,PACK),'candidate_manifest_sha256':sha(mp),'contact_path':cp,'contact_sha256':sha(cp),'contact_rows':[x[0] for x in contact_rows],'candidate_only':True,'install_authorized':False}
rp=os.path.join(CAND,'contact-receipt-v1.json'); open(rp,'w').write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'manifest':mp,'manifest_sha256':sha(mp),'contact':cp,'contact_sha256':sha(cp),'sets':len(manifest['sets']),'directions':sum(len(x['candidates']) for x in manifest['sets'])},indent=2))
