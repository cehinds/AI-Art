from pathlib import Path
import hashlib, json
from PIL import Image

ASSETS=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets')
PACK=ASSETS/'book-tiles/dungeon-after-dark'
CAND=PACK/'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026'
RAW,OUT=CAND/'raw',CAND/'images'
HAND=json.loads(Path('/workspace/scratch/equipment-dark-masonry-rail8-handoff-20261026.json').read_text())
OBJECTS={o['object_id']:o for o in HAND['objects']}
VIEWS=['front','top','right','left','bottom','rear']
INNER='iron-trains-riveted-carriage-metal-inner-corner'
CAP='iron-trains-riveted-carriage-metal-endcap-northwest'
INNER_ATLAS=RAW/'iron-trains-innercorner-endcap-output-v3.png'
CAP_ATLAS=RAW/'iron-trains-endcap-source-only-output-v1.png'
INNER_PROMPT=RAW/'iron-trains-innercorner-endcap-request-v3.json'
CAP_PROMPT=RAW/'iron-trains-endcap-source-only-request-v1.json'
THRESHOLD=64; TARGET=186

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def crop(image,cell,threshold=THRESHOLD):
    image=image.convert('RGBA'); a=image.getchannel('A').point(lambda x:255 if x>=threshold else 0); box=a.getbbox()
    if not box:raise ValueError('empty cell')
    im=image.crop(box); im.putalpha(im.getchannel('A').point(lambda x:0 if x<32 else x))
    return im,list(box)
def fit(im,scale):
    w,h=im.size;nw,nh=max(1,round(w*scale)),max(1,round(h*scale))
    if nw>TARGET or nh>TARGET:raise ValueError(f'no-fit {nw}x{nh}')
    im=im.resize((nw,nh),Image.Resampling.NEAREST); canvas=Image.new('RGBA',(256,256),(0,0,0,0));off=((256-nw)//2,(256-nh)//2);canvas.alpha_composite(im,off)
    return canvas,[nw,nh],list(off)

inner=Image.open(INNER_ATLAS).convert('RGBA')
if inner.width%6:raise ValueError('inner atlas not 6 columns')
iw,ih=inner.width//6,inner.height//2
inner_cells={}
for col,v in enumerate(VIEWS):
    x0=col*iw;x1=(col+1)*iw;y0=0;y1=ih
    im,bb=crop(inner.crop((x0,y0,x1,y1)),None) if False else crop(inner.crop((x0,y0,x1,y1)),None)
    inner_cells[v]=(im,bb,[x0,y0,x1-x0,y1-y0])
INNER_SOURCE=Path(OBJECTS[INNER]['source']['path'])
inner_top,inner_top_bb=crop(Image.open(INNER_SOURCE).convert('RGBA'),None,1)
inner_cells['top']=(inner_top,inner_top_bb,[0,0,256,256])
inner_scale=TARGET/max(max(inner_cells[v][0].size) for v in ('front','right','left','bottom','rear'))

cap=Image.open(CAP_ATLAS).convert('RGBA')
if cap.width%6:raise ValueError('cap atlas not 6 columns')
cw=cap.width//6
# Six source-only generated cells visibly share the same rotationally symmetric square face.
# Cell 2 has a near-square full border and is used as the same unmarked face for all views.
cap_view='top';col=2;cellbox=(col*cw,0,(col+1)*cw,cap.height)
cap_cell,cap_bb=crop(cap.crop(cellbox),None)
cap_scale=TARGET/max(cap_cell.size)

sets=[]
for oid in [INNER,CAP]:
    source=Path(OBJECTS[oid]['source']['path']);source_sha=sha(source)
    if oid==INNER:
        per_view={v:inner_cells[v][0] for v in VIEWS}; scale=inner_scale
        raw_path,prompt_path=INNER_ATLAS,INNER_PROMPT
    else:
        per_view={v:cap_cell for v in VIEWS};scale=cap_scale
        raw_path,prompt_path=CAP_ATLAS,CAP_PROMPT
    for v in VIEWS:
        im=per_view[v]
        view_scale=TARGET/max(im.size) if oid==INNER and v=='top' else scale
        if oid==INNER and v=='top':
            raw_view_path,prompt_view_path=INNER_SOURCE,None
        else:
            raw_view_path,prompt_view_path=raw_path,prompt_path
        canvas,dims,offset=fit(im,view_scale)
        out=OUT/f'{oid}.{v}.stage2.png';out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,optimize=False)
        base=OBJECTS[oid]['views'][v]
        if sha(base['path'])!=base['sha256']:raise RuntimeError(f'base changed: {oid}.{v}')
        if oid==INNER and v=='top':
            rect=[0,0,256,256];bbox=inner_top_bb
            note='Native source top plan preserved exactly in shape and uniformly normalized; generated side views retain inferred same-ID construction.'
        elif oid==INNER:
            col=VIEWS.index(v);x0=col*iw;y0=0;rect=[x0,y0,iw,ih];bbox=inner_cells[v][1]
            note='Generated same-ID guided principal view, extracted from its assigned six-column atlas cell; L plans and cardinal faces inferred from target source and approved geometry guide.'
        else:
            rect=[cellbox[0],cellbox[1],cellbox[2]-cellbox[0],cellbox[3]-cellbox[1]];bbox=cap_bb
            note='Generated symmetric square cap face reused across six principal views because the target is an unmarked compact four-corner-riveted square block; hidden faces inferred. No artificial perspective or mirrored depth.'
        sets.append({'object_id':oid,'view':v,'candidate_path':f'candidates/equipment-dark-masonry-rail8-20261026/images/{out.name}',
          'candidate_sha256':sha(out),'raw_path':(f'iron-trains/components/{oid}.png' if oid==INNER and v=='top' else f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{raw_view_path.name}'),
          'raw_sha256':sha(raw_view_path),'raw_cell_rect_xywh':rect,'alpha_threshold':1 if oid==INNER and v=='top' else THRESHOLD,'alpha_bbox_cell_xyxy':bbox,
          'prompt_path':(f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{prompt_view_path.name}' if prompt_view_path else None),
          'prompt_sha256':sha(prompt_view_path) if prompt_view_path else None,'source_path':f'iron-trains/components/{oid}.png','source_sha256':source_sha,
          'geometry_guide_path':('reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/iron-trains-sources-guide-v1.png' if oid==INNER else None),
          'geometry_guide_sha256':(sha(RAW/'iron-trains-sources-guide-v1.png') if oid==INNER else None),
          'normalization_scale':view_scale,'resampling':'PIL.Image.Resampling.NEAREST','dimensions':dims,'offset_px':offset,'anchor_px':[128,128],
          'base_path':base['path'],'base_sha256':base['sha256'],'geometry_note':note,'provenance_method':('source-derived' if oid==INNER and v=='top' else 'generated')})

manifest={'candidate_id':'equipment-dark-masonry-rail8-trains-v2','sets':sets,'reproducibility':{
 'script_path':'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/build_iron_trains_candidates_v1.py',
 'script_sha256':sha(Path(__file__)),'resampler':'PIL.Image.Resampling.NEAREST','canvas':[256,256],
 'anchor_px':[128,128],'alpha_crop_threshold':THRESHOLD,'transparent_threshold':32,
 'endcap_symmetry':'same square generated unmarked face in all six views; inferred rotational symmetry','candidate_only':True}}
mp=CAND/'iron-trains-candidate-manifest-v2.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'sets':len(sets),'manifest_sha256':sha(mp),'inner_shared_scale':inner_scale,'endcap_scale':cap_scale},indent=2))
