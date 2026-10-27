"""Extract and uniformly normalize six isolated submarine endcap projections."""
from pathlib import Path
import hashlib, json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent
OUT=HERE.parent
RAW=OUT/'raw'
CAND=OUT/'candidates/submarine-endcaps-v1'
VIEWS=('front','top','right','left','bottom','rear')
IDS=(
 'bubble-sea-submarine-metal-hull-endcap-northeast',
 'bubble-sea-submarine-metal-hull-endcap-northwest',
)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def components(im):
    alpha=np.asarray(im.getchannel('A'))
    labels,n=ndimage.label(alpha>=32)
    result=[]
    for i,sl in enumerate(ndimage.find_objects(labels),1):
        if sl is None: continue
        y,x=sl; area=int(np.count_nonzero(labels[sl]==i))
        if area>=1000: result.append((area,(x.start,y.start,x.stop,y.stop)))
    result.sort(key=lambda z:(z[1][0]+z[1][2])/2)
    if len(result)!=6: raise ValueError(f'Expected six alpha-isolated views, got {len(result)}')
    return result

def main():
    CAND.mkdir(parents=True,exist_ok=True)
    records=[]
    for oid in IDS:
        raw=RAW/f'{oid}-candidate-sixview-v1.png'
        im=Image.open(raw).convert('RGBA')
        comps=components(im)
        max_h=max(b[3]-b[1] for _,b in comps)
        scale=172.0/max_h
        for view,(area,bbox) in zip(VIEWS,comps):
            x0,y0,x1,y1=bbox
            # Include a 2px transparent edge around the full connected silhouette.
            x0=max(0,x0-2); y0=max(0,y0-2); x1=min(im.width,x1+2); y1=min(im.height,y1+2)
            crop=im.crop((x0,y0,x1,y1))
            nw=max(1,round(crop.width*scale)); nh=max(1,round(crop.height*scale))
            resized=crop.resize((nw,nh),Image.Resampling.NEAREST)
            canvas=Image.new('RGBA',(256,256),(0,0,0,0))
            ox=(256-nw)//2; oy=(256-nh)//2
            canvas.alpha_composite(resized,(ox,oy))
            dst=CAND/f'{oid}.{view}.png'; canvas.save(dst)
            records.append({'object_id':oid,'view':view,'candidate_path':str(dst.relative_to(OUT)),
              'candidate_sha256':sha(dst),'raw_atlas':str(raw.relative_to(OUT)),'raw_atlas_sha256':sha(raw),
              'component_bbox_threshold32':list(bbox),'component_area_threshold32':area,
              'crop_rect_with_2px_silhouette_padding':[x0,y0,x1,y1],'uniform_scale':scale,
              'normalized_size':[nw,nh],'anchor_px':[128,128]})
    spec={'candidate_id':'submarine-endcaps-v1','sets':[],'extraction':'six isolated connected alpha components, sorted by horizontal center; alpha threshold >=32; crop whole component plus 2 transparent pixels; one isotropic factor per object; nearest-neighbour; centered 256x256.'}
    for oid in IDS:
        spec['sets'].append({'object_id':oid,'views':[r for r in records if r['object_id']==oid]})
    (OUT/'candidates/submarine-endcaps-v1/candidate.json').write_text(json.dumps(spec,indent=2)+'\n')
    print(json.dumps({'candidate_sets':len(IDS),'candidate_pngs':len(records),'entries':records},indent=2))
if __name__=='__main__': main()
