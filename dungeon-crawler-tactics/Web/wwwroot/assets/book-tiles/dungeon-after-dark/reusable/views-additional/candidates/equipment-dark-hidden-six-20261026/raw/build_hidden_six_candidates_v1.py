#!/usr/bin/env python3
"""Extract and normalize candidate-only hidden-plane repairs from retained generated atlases."""
from PIL import Image, ImageDraw
from scipy import ndimage
import numpy as np, json, hashlib, os

PACK='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'
ROOT=PACK+'/reusable/views-additional/candidates/equipment-dark-hidden-six-20261026'
RAW=ROOT+'/raw'; OUT=ROOT+'/images'; os.makedirs(OUT,exist_ok=True)
HAND='/workspace/scratch/equipment-dark-next-six-hidden-planes-handoff-20261026.json'
PROOF='/tmp/page-qa-equipment-next-six-reassessed-hidden-current-20261026-01.png.json'
VIEWS=['front','top','right','left','bottom','rear']

def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def component_table(path, threshold=64):
    im=Image.open(path).convert('RGBA'); a=np.asarray(im)[:,:,3]
    labels,n=ndimage.label(a>=threshold,structure=np.ones((3,3),dtype=np.uint8))
    rows=[]
    for i,s in enumerate(ndimage.find_objects(labels),1):
        if not s: continue
        yy,xx=np.where(labels[s]==i); area=len(xx)
        if area<100: continue
        rows.append({'label':i,'bbox':[s[1].start,s[0].start,s[1].stop,s[0].stop],'area':area,'centroid':[float(xx.mean()+s[1].start),float(yy.mean()+s[0].start)]})
    return im,labels,rows

def crop_component(im,labels,comp,scale):
    x0,y0,x1,y1=comp['bbox']; lab=comp['label']
    arr=np.asarray(im.convert('RGBA'))[y0:y1,x0:x1].copy(); local=labels[y0:y1,x0:x1]
    mask=(local==lab); keep=ndimage.binary_dilation(mask,structure=np.ones((5,5),dtype=bool))
    arr[:,:,3]=np.where(keep,arr[:,:,3],0)
    h,w=arr.shape[:2]; nw=max(1,round(w*scale)); nh=max(1,round(h*scale))
    art=Image.fromarray(arr,'RGBA').resize((nw,nh),Image.Resampling.NEAREST)
    canvas=Image.new('RGBA',(256,256),(0,0,0,0)); off=(128-nw//2,128-nh//2); canvas.alpha_composite(art,off)
    return canvas,[nw,nh],list(off)

handoff=json.load(open(HAND)); objects={o['object_id']:o for o in handoff['objects']}
proofsha=sha(PROOF); handsha=sha(HAND)
# raw_path,prompt_path,component index within global alpha-threshold component list,
# isotropic scale calibrated to visible target source/current accepted axes.
specs={
('ghost-havana-city-descent-stairwell','rear'):{'raw':'first-three-output-v3.png','prompt':'first-three-request-v3.json','index':0,'scale':204/575,'note':'Inferred reverse stair support elevation guided by current-hash-approved same-ID silhouette; hidden back support is illustrative.'},
('ghost-cemetery-cemetery-flagstone-corner-transition','bottom'):{'raw':'first-three-output-v3.png','prompt':'first-three-request-v3.json','index':1,'scale':181/558,'note':'Inferred opaque underside; complete L footprint and source cracked-stone material retained.'},
('surface-entry-snowy-sidewalk-tree','bottom'):{'raw':'first-three-output-v3.png','prompt':'first-three-request-v3.json','index':2,'scale':172/654,'note':'Inferred soil/root center beneath opaque tree bed; snowy canopy retained only as true peripheral overhang.'},
('ghost-cemetery-mausoleum-facade','top'):{'raw':'mausoleum-plans-output-v2.png','prompt':'mausoleum-plans-request-v2.json','index':0,'scale':0.205,'note':'Inferred shallow overhead roof/cap plane calibrated to source facade width and accepted side depth; cross face foreshortened.'},
('ghost-cemetery-mausoleum-facade','bottom'):{'raw':'mausoleum-plans-output-v2.png','prompt':'mausoleum-plans-request-v2.json','index':1,'scale':0.22,'note':'Inferred shallow stone foundation underside with compact column-foot projections; dimensions use isotropic calibration.'},
('bubble-glass-sand-filled-chamber-mound','front'):{'raw':'glass-chamber-output-v1.png','prompt':'glass-chamber-request-v1.json','index':0,'scale':0.54,'note':'Generated level front wall-arm projection; two visible endpoint posts belong to the source three-post open corner.'},
('bubble-glass-sand-filled-chamber-mound','top'):{'raw':'glass-chamber-output-v1.png','prompt':'glass-chamber-request-v1.json','index':1,'scale':0.45,'note':'Inferred open L overhead with exactly three post caps; transparent glass and sand layout retained.'},
('bubble-glass-sand-filled-chamber-mound','bottom'):{'raw':'glass-chamber-output-v1.png','prompt':'glass-chamber-request-v1.json','index':2,'scale':0.46,'note':'Inferred open L underside with three support contacts, no fourth post or closed box.'},
('bubble-glass-sand-filled-chamber-mound','rear'):{'raw':'glass-chamber-output-v1.png','prompt':'glass-chamber-request-v1.json','index':3,'scale':0.53,'note':'Generated opposite broad wall-arm elevation; open-corner three-post assembly inferred from source.'},
('thresholds-quadrant-selection-wheel','top'):{'raw':'quadrant-top-output-v1.png','prompt':'quadrant-top-request-v1.json','index':0,'scale':0.22,'note':'Inferred overhead armillary projection preserves separate intersecting ring bands and left/right source landmark placement.'}}
# Validate exact source/current-six bindings before materializing any candidate.
for oid,o in objects.items():
    assert os.path.isfile(o['source']['path']) and sha(o['source']['path'])==o['source']['sha256'],oid+' source changed'
    for v,x in o['views'].items(): assert os.path.isfile(x['path']) and sha(x['path'])==x['sha256'],oid+' '+v+' changed'
assert proofsha==handoff['source_and_six_proof']['sha256']

prepared={}; records=[]
for (oid,v),s in specs.items():
    rawp=RAW+'/'+s['raw']; promptp=RAW+'/'+s['prompt']; img,labels,comps=component_table(rawp,64)
    assert s['index']<len(comps),(oid,v,len(comps),s)
    comp=comps[s['index']]
    art,wh,off=crop_component(img,labels,comp,s['scale'])
    name=f'{oid}.{v}.candidate-v1.png'; outp=OUT+'/'+name; art.save(outp)
    ob=objects[oid]; base=ob['views'][v]
    # Determine geometry guide lineage from request JSON, retaining only hash-verified donor contact/guide refs.
    req=json.load(open(promptp)); guides=[x for x in req.get('references',[]) if 'geometry' in x.get('role','') or 'geometry' in x.get('role','').lower()]
    prepared[(oid,v)]={'path':outp,'sha256':sha(outp),'name':name}
    record={'object_id':oid,'view':v,'candidate_path':os.path.relpath(outp,PACK),'candidate_sha256':sha(outp),'source_path':os.path.relpath(ob['source']['path'],PACK),'source_sha256':ob['source']['sha256'],'base_path':os.path.relpath(base['path'],PACK),'base_sha256':base['sha256'],'raw_path':os.path.relpath(rawp,PACK),'raw_sha256':sha(rawp),'prompt_path':os.path.relpath(promptp,PACK),'prompt_sha256':sha(promptp),'source_and_six_proof_path':PROOF,'source_and_six_proof_sha256':proofsha,'component_bbox_global_xyxy':comp['bbox'],'component_area_alpha64':comp['area'],'alpha_threshold':64,'connectivity':8,'uniform_scale':s['scale'],'resized_dimensions':wh,'offset_px':off,'anchor_px':[128,128],'canvas':[256,256],'resampler':'PIL.Image.Resampling.NEAREST','alpha_mask':'selected whole-atlas alpha>=64 component plus 2px dilation for antialias pixels','geometry_guides':guides,'geometry_note':s['note'],'provenance_method':'generated'}
    records.append(record)

# Versioned manifest and contact; contact replaces only the 10 activated directions.
script=ROOT+'/raw/build_hidden_six_candidates_v1.py'
manifest={'candidate_id':'equipment-dark-hidden-six-candidate-v1','scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_equipment','reviewer':'page_inventory','installer':'views_dark_books','candidate_only':True,'handoff_path':HAND,'handoff_sha256':handsha,'source_and_six_proof_path':PROOF,'source_and_six_proof_sha256':proofsha,'sets':records,'reproducibility':{'script_path':os.path.relpath(script,PACK),'script_sha256':sha(script),'canvas':[256,256],'anchor_px':[128,128],'resampler':'PIL.Image.Resampling.NEAREST','component_connectivity_2d':8,'threshold':64,'note':'Uses whole-atlas alpha components; no nominal cell crop. Per-view uniform calibration is explicit because generated row/camera drawing scales varied. Unchanged accepted current views are preserved.'}}
mp=ROOT+'/hidden-six-candidate-manifest-v1.json';open(mp,'w').write(json.dumps(manifest,indent=2)+'\n')
cell=180;contact=Image.new('RGBA',(cell*7,cell*len(objects)),(228,228,228,255));draw=ImageDraw.Draw(contact)
for ri,(oid,ob) in enumerate(objects.items()):
    paths=[ob['source']['path']]+[prepared.get((oid,v),{}).get('path',ob['views'][v]['path']) for v in VIEWS]
    for ci,p in enumerate(paths):
        im=Image.open(p).convert('RGBA');b=im.getchannel('A').getbbox();im=im.crop(b) if b else im;im.thumbnail((138,132),Image.Resampling.NEAREST)
        bg=Image.new('RGBA',im.size,(225,225,225,255));bg.alpha_composite(im);contact.alpha_composite(bg,(ci*cell+(cell-im.width)//2,ri*cell+28+(132-im.height)//2))
        draw.text((ci*cell+3,ri*cell+4),('SOURCE' if ci==0 else VIEWS[ci-1]),fill=(0,0,0,255))
    draw.text((2,ri*cell+160),oid,fill=(0,0,0,255))
cp=ROOT+'/hidden-six-source-current-candidate-contact-v1.png';contact.save(cp)
meta={'contact_path':os.path.relpath(cp,PACK),'contact_sha256':sha(cp),'manifest_path':os.path.relpath(mp,PACK),'manifest_sha256':sha(mp),'handoff_path':HAND,'handoff_sha256':handsha,'proof_path':PROOF,'proof_sha256':proofsha,'candidates':[{k:x[k] for k in ['object_id','view','candidate_path','candidate_sha256','source_path','source_sha256','base_path','base_sha256','raw_path','raw_sha256','prompt_path','prompt_sha256','component_bbox_global_xyxy','uniform_scale']} for x in records]}
open(ROOT+'/hidden-six-source-current-candidate-contact-v1.json','w').write(json.dumps(meta,indent=2)+'\n')
print('manifest',sha(mp),'directions',len(records));print('contact',sha(cp));
