"""Prepare rear-curb and plain-asphalt edge profiles from retained family pixels."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];BOOK=ROOT.parent.parent;IDX=json.loads((ROOT/'set-index.json').read_text());A={a['id']:a for a in IDX['assets']};OUT=ROOT/'candidates/cemetery-race-edges-v1';OUT.mkdir(parents=True,exist_ok=True);V=('front','top','right','left','bottom','rear')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
entries=[]
# Cemetery transition: plain front from accepted material-matched floor edge.
oid='ghost-cemetery-cemetery-flagstone-edge-transition';baseoid='ghost-cemetery-cemetery-flagstone-floor'
for view in ['front']:
 src=BOOK/A[f'{baseoid}.{view}']['image']['path'];im=Image.open(src).convert('RGBA');p=OUT/f'{oid}.{view}.png';im.save(p);entries.append({'object_id':oid,'asset_id':f'{oid}.{view}','view':view,'candidate_path':str(p.relative_to(ROOT)),'candidate_sha256':sha(p),'method':'accepted-family-plain-edge-alias','alias_from_asset_id':f'{baseoid}.{view}','source_image':A[f'{oid}.{view}']['source']['source_image'],'source_sha256':A[f'{oid}.{view}']['source']['source_sha256'],'alias_png_sha256':sha(src),'notes':'The open front edge has no curb; reuses the accepted plain cemetery flagstone edge profile.'})
# RIGHT/LEFT retain only curb-end caps; the center profile is the accepted plain edge.
for view in ['right','left']:
 src=BOOK/A[f'{oid}.{view}']['image']['path'];im=Image.open(src).convert('RGBA');base=Image.open(BOOK/A[f'{baseoid}.front']['image']['path']).convert('RGBA');out=base.copy()
 bbox=im.getchannel('A').getbbox();x0,y0,x1,y1=bbox
 # The north/rear curb meets this side elevation at one endpoint only.
 if view=='right': crop=(x1-34,y0,x1,y1); dest=(x1-34,y0)
 else: crop=(x0,y0,x0+34,y1); dest=(x0,y0)
 cap=im.crop(crop);out.alpha_composite(cap,dest)
 p=OUT/f'{oid}.{view}.png';out.save(p);entries.append({'object_id':oid,'asset_id':f'{oid}.{view}','view':view,'candidate_path':str(p.relative_to(ROOT)),'candidate_sha256':sha(p),'method':'single-rear-curb-end-cap-over-plain-edge','source_image':A[f'{oid}.{view}']['source']['source_image'],'source_sha256':A[f'{oid}.{view}']['source']['source_sha256'],'profile_input_path':str(src.relative_to(BOOK)),'profile_input_sha256':sha(src),'plain_edge_input_path':str((BOOK/A[f'{baseoid}.front']['image']['path']).relative_to(BOOK)),'plain_edge_input_sha256':sha(BOOK/A[f'{baseoid}.front']['image']['path']),'source_rect':list(crop),'destination_xy':list(dest),'notes':'Single curb end cap at the rear/north end of this side elevation, consistent with the TOP hybrid plan; plain paving edge elsewhere.'})
# Race asphalt: source-material strip from the newly accepted opaque plain underside.
oid='race-circuits-painted-grid-asphalt-floor';bottom=Image.open(BOOK/A[f'{oid}.bottom']['image']['path']).convert('RGBA');bbox=bottom.getchannel('A').getbbox();targetw=Image.open(BOOK/A[f'{oid}.top']['image']['path']).convert('RGBA').getchannel('A').getbbox()[2]-Image.open(BOOK/A[f'{oid}.top']['image']['path']).convert('RGBA').getchannel('A').getbbox()[0];crop=bottom.crop((bbox[0],bbox[3]-20,bbox[2],bbox[3]));scale=targetw/crop.width;size=(targetw,round(crop.height*scale));crop=crop.resize(size,Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(crop,((256-size[0])//2,(256-size[1])//2));profile=OUT/f'{oid}.edge-profile.png';can.save(profile)
for view in ['front','right','left','rear']:
 p=OUT/f'{oid}.{view}.png';can.save(p);entries.append({'object_id':oid,'asset_id':f'{oid}.{view}','view':view,'candidate_path':str(p.relative_to(ROOT)),'candidate_sha256':sha(p),'method':'plain-asphalt-edge-from-accepted-underside-material','source_image':A[f'{oid}.{view}']['source']['source_image'],'source_sha256':A[f'{oid}.{view}']['source']['source_sha256'],'profile_input_path':str((BOOK/A[f'{oid}.bottom']['image']['path']).relative_to(BOOK)),'profile_input_sha256':sha(BOOK/A[f'{oid}.bottom']['image']['path']),'source_rect':[bbox[0],bbox[3]-20,bbox[2],bbox[3]],'uniform_scale':scale,'normalized_bbox_size':list(size),'notes':'Thin unpainted asphalt edge; road markings appear only on TOP, as requested.'})
proofs=[]
for oid in [ 'ghost-cemetery-cemetery-flagstone-edge-transition','race-circuits-painted-grid-asphalt-floor']:
 s=next(x for x in IDX['view_sets'] if x['object_id']==oid);src=BOOK/A[s['views']['top']]['source']['source_image'];src_rel=str(src.relative_to(BOOK)) if isinstance(src,Path) else src;src=BOOK/src;ims=[Image.open(src).convert('RGBA')];labs=['SOURCE'];chosen={e['view']:e for e in entries if e['object_id']==oid};proof={'object_id':oid,'source_image':src_rel,'source_sha256':sha(src),'views':{}}
 for v in V:
  a=A[s['views'][v]];p=ROOT/chosen[v]['candidate_path'] if v in chosen else BOOK/a['image']['path'];lab='CANDIDATE '+v.upper() if v in chosen else 'LIVE '+v.upper();ims.append(Image.open(p).convert('RGBA'));labs.append(lab);proof['views'][v]={'path':str(p.relative_to(BOOK)) if p.is_relative_to(BOOK) else str(p.relative_to(ROOT)),'sha256':sha(p),'status':lab}
 sheet=Image.new('RGB',(272*7,300),(238,238,238));d=ImageDraw.Draw(sheet)
 for i,(im,lab) in enumerate(zip(ims,labs)):
  bg=Image.new('RGBA',(256,256),(140,140,140,255));bg.alpha_composite(im.resize((256,256),Image.Resampling.NEAREST));sheet.paste(bg.convert('RGB'),(i*272,28));d.text((i*272+4,6),lab,fill='black')
 cp=ROOT/'qa'/f'{oid}-cemetery-race-edges-v1-candidate-source-six.png';sheet.save(cp);proof['contact_path']=str(cp.relative_to(ROOT));proof['contact_sha256']=sha(cp);cp.with_suffix('.json').write_text(json.dumps(proof,indent=2)+'\n');proofs.append({'object_id':oid,'contact_path':proof['contact_path'],'contact_sha256':proof['contact_sha256']})
(OUT/'candidate.json').write_text(json.dumps({'candidate_id':'cemetery-race-edges-v1','entries':entries,'proofs':proofs},indent=2)+'\n');print(json.dumps(proofs,indent=2))
