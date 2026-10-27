from PIL import Image, ImageDraw
import numpy as np, json, hashlib, os, math
from pathlib import Path
base=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
stage=base/'reusable/views-additional/candidates/equipment-dark-last-seven-fixtures-20261026'
raw=stage/'raw'; imgs=stage/'images'; cont=stage/'contacts'; req=stage/'requests'
proof=json.load(open('/tmp/equipment-last-seven-current-after-accepted-installs.png.json'))
proofobjs={o['object_id']:o for o in proof['objects']}
handoff=json.load(open('/workspace/scratch/equipment-dark-last-seven-fixtures-handoff-20261026.json'))
handobjs={o['object_id']:o for o in handoff['objects']}
# (object, view, rawfile, cell_index, ncols, target max extent)
jobs=[
('over-city-venues-painted-civic-stone-wall-northeast','top','civic-top-v3.png',0,1,202),
('over-city-venues-tavern-bar','top','tavern-top-v2.png',0,1,204),
('over-city-venues-tavern-bar','bottom','tavern-bottom-rear-v2.png',0,2,204),
('over-city-venues-tavern-bar','rear','tavern-rear-v3.png',0,1,204),
('race-circuits-race-descent-checkpoint','top','checkpoint-top-v4.png',0,1,190),
('race-circuits-race-descent-checkpoint','rear','checkpoint-top-rear-v2.png',1,2,180),
('safe-services-restaurant-dining-booth','right','booth-side-rear-v2.png',0,3,128),
('safe-services-restaurant-dining-booth','left','booth-side-rear-v2.png',1,3,128),
('safe-services-restaurant-dining-booth','rear','booth-side-rear-v2.png',2,3,184),
('safe-services-restaurant-dining-booth','bottom','booth-bottom-v2.png',0,1,193),
]
# raw hash manifests and exact object crop/normalization recipes
records=[]
for oid,view,rf,idx,ncols,target in jobs:
    rp=raw/rf; a=np.array(Image.open(rp).convert('RGBA')); H,W=a.shape[:2]
    x0=round(W*idx/ncols); x1=round(W*(idx+1)/ncols); cell=a[:,x0:x1]
    # Extract alpha>=64 connected components, keep main plus near-touching intentional details.
    mask0=cell[:,:,3]>=64
    from scipy import ndimage
    lab,n=ndimage.label(mask0,structure=np.ones((3,3),dtype=np.uint8))
    comps=[]
    for k,sl in enumerate(ndimage.find_objects(lab),1):
        if sl is None: continue
        area=int((lab[sl]==k).sum()); bbox=(sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)
        if area>=20: comps.append((area,k,bbox))
    comps.sort(reverse=True)
    if not comps: raise RuntimeError(f'no alpha in {rf}:{idx}')
    area0,k0,b0=comps[0]
    keep=[]
    for area,k,b in comps:
        bx0,by0,bx1,by1=b; ax0,ay0,ax1,ay1=b0
        gapx=max(0,ax0-bx1,bx0-ax1); gapy=max(0,ay0-by1,by0-ay1)
        if k==k0 or (gapx<=16 and gapy<=16): keep.append(k)
    mask=np.isin(lab,keep); ys,xs=np.where(mask); bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
    crop=cell[bbox[1]:bbox[3],bbox[0]:bbox[2]].copy(); crop[~mask[bbox[1]:bbox[3],bbox[0]:bbox[2]]]=0
    im=Image.fromarray(crop,'RGBA'); scale=target/max(im.size); nw=max(1,round(im.width*scale)); nh=max(1,round(im.height*scale)); im=im.resize((nw,nh),Image.Resampling.NEAREST)
    canvas=Image.new('RGBA',(256,256),(0,0,0,0)); off=[128-nw//2,128-nh//2]; canvas.alpha_composite(im,tuple(off))
    out=imgs/f'{oid}.{view}.png'; canvas.save(out)
    rawsha=hashlib.sha256(rp.read_bytes()).hexdigest(); outsha=hashlib.sha256(out.read_bytes()).hexdigest()
    request_candidates=sorted(req.glob('*.json'))
    # Bind the request explicitly by raw name where available.
    reqfile={'civic-top-v3.png':'civic-top-v3.json','tavern-top-v2.png':'tavern-top-v2.json','tavern-bottom-rear-v2.png':'tavern-bottom-rear-v2.json','tavern-rear-v3.png':'tavern-rear-v3.json','checkpoint-top-v4.png':'checkpoint-top-v4.json','checkpoint-top-rear-v2.png':'checkpoint-top-rear-v2.json','booth-side-rear-v2.png':'booth-side-rear-v2.json','booth-bottom-v2.png':'booth-bottom-v2.json'}[rf]
    q=req/reqfile
    records.append({'object_id':oid,'view':view,'candidate_path':str(out),'candidate_sha256':outsha,'raw_path':str(rp),'raw_sha256':rawsha,'request_path':str(q),'request_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'cell_xyxy':[x0,0,x1,H],'alpha_threshold':64,'connectivity':8,'selected_components':[{'area':ar,'bbox_local_xyxy':list(b)} for ar,k,b in comps if k in keep],'crop_local_xyxy':bbox,'scale':scale,'resized_wh':[nw,nh],'offset_xy':off,'canvas':[256,256],'anchor_px':[128,128]})
# Candidate-specific contact boards with source and all current directions; selected candidate overlays relevant view.
for oid in sorted(set(x['object_id'] for x in records)):
    obj=proofobjs[oid]; src=Image.open(handobjs[oid]['source']['path']).convert('RGBA')
    entries={x['view']:x for x in records if x['object_id']==oid}
    tiles=[]
    tiles.append(('SOURCE',src))
    for v in ['front','top','right','left','bottom','rear']:
        p=entries[v]['candidate_path'] if v in entries else obj['views'][v]['path']
        tiles.append((v.upper()+(' candidate' if v in entries else ''),Image.open(p).convert('RGBA')))
    cw,ch=240,288; board=Image.new('RGB',(cw*len(tiles),ch),(236,236,236)); d=ImageDraw.Draw(board)
    for i,(label,im) in enumerate(tiles):
        d.text((i*cw+5,4),label,fill=(0,0,0)); im.thumbnail((cw-14,ch-34),Image.Resampling.NEAREST)
        if im.mode=='RGBA':
            bg=Image.new('RGBA',im.size,(255,255,255,255)); bg.alpha_composite(im); im=bg.convert('RGB')
        board.paste(im,(i*cw+(cw-im.width)//2,24+(ch-34-im.height)//2))
    cp=cont/f'{oid}-candidate-v3-source-current-six.png'; board.save(cp)
# Versioned manifest per candidate list, current proof is actual post-install source+sibling binding.
manifest={'candidate_id':'equipment-dark-last-seven-focused-v3','candidate_only':True,'scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_equipment','reviewer':'root/page_inventory','installer':'views_dark_books','handoff_path':'/workspace/scratch/equipment-dark-last-seven-fixtures-handoff-20261026.json','handoff_sha256':hashlib.sha256(Path('/workspace/scratch/equipment-dark-last-seven-fixtures-handoff-20261026.json').read_bytes()).hexdigest(),'base_proof_path':proof['contact']+'.json','base_proof_sha256':hashlib.sha256(Path(proof['contact']+'.json').read_bytes()).hexdigest(),'recipe_path':str(stage/'last7-focused-v3-recipe.json'),'recipe_sha256':'pending','sets':[]}
for oid in sorted(set(x['object_id'] for x in records)):
    h=handobjs[oid]; p=proofobjs[oid]; affected={x['view']:x for x in records if x['object_id']==oid}
    sets={'object_id':oid,'source':h['source'],'base_current_views':p['views'],'affected_views':list(affected),'candidates':{v:{'path':r['candidate_path'],'sha256':r['candidate_sha256'],'method':'generated-image-extracted-and-isotropically-normalized','raw_path':r['raw_path'],'raw_sha256':r['raw_sha256'],'request_path':r['request_path'],'request_sha256':r['request_sha256'],'normalizer_path':str(stage/'extract_last7_focused_v3.py'),'normalizer_sha256':'pending'} for v,r in affected.items()},'candidate_contact_path':str(cont/f'{oid}-candidate-v3-source-current-six.png')}
    sets['candidate_contact_sha256']=hashlib.sha256(Path(sets['candidate_contact_path']).read_bytes()).hexdigest(); manifest['sets'].append(sets)
recipe={'input_current_proof':proof['contact']+'.json','input_current_proof_sha256':manifest['base_proof_sha256'],'assets':records}
recpath=stage/'last7-focused-v3-recipe.json'; recpath.write_text(json.dumps(recipe,indent=2)+'\n'); manifest['recipe_sha256']=hashlib.sha256(recpath.read_bytes()).hexdigest()
# Write helper copy of this exact script after command invocation separately.
mp=stage/'candidate-manifest-last7-focused-v3.json'; mp.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'manifest':str(mp),'manifest_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'recipe':str(recpath),'recipe_sha256':manifest['recipe_sha256'],'contacts':[(x['object_id'],str(cont/f"{x['object_id']}-candidate-v3-source-current-six.png"),hashlib.sha256((cont/f"{x['object_id']}-candidate-v3-source-current-six.png").read_bytes()).hexdigest()) for x in manifest['sets']],'candidate_outputs':[(r['object_id'],r['view'],r['resized_wh'],r['candidate_sha256']) for r in records]},indent=2))
