"""Prepare source-true orthogonal remaps for a paving corner and camera."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];BOOK=ROOT.parent.parent;IDX=json.loads((ROOT/'set-index.json').read_text());A={a['id']:a for a in IDX['assets']};OUT=ROOT/'candidates/axis-remaps-v1';OUT.mkdir(parents=True,exist_ok=True);V=('front','top','right','left','bottom','rear')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fit_source(oid,view,targetw):
 a=A[f'{oid}.{view}'];src=BOOK/a['source']['source_image'];im=Image.open(src).convert('RGBA');b=im.getchannel('A').getbbox();crop=im.crop(b);scale=targetw/crop.width;size=(targetw,round(crop.height*scale));crop=crop.resize(size,Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(crop,((256-size[0])//2,(256-size[1])//2));return can,{'method':'source-view-normalization','source_image':str(src.relative_to(BOOK)),'source_sha256':sha(src),'source_rect':list(b),'uniform_scale':scale,'normalized_bbox_size':list(size)}
def rot(oid,view,sourceview,angle):
 src=BOOK/A[f'{oid}.{sourceview}']['image']['path']
 if sourceview==view:
  retained=ROOT/'prebuilt/axis-remap-before-v1'/f'{oid}.{view}.png'
  if retained.exists():src=retained
 im=Image.open(src).convert('RGBA');trans={90:Image.Transpose.ROTATE_90,270:Image.Transpose.ROTATE_270}[angle];meta={'method':'90-degree-exact-orthographic-axis-rotation','transform_input_path':str(src.relative_to(BOOK)),'source_sha256':sha(src),'transform':f'rotate_ccw_{angle}' if angle==90 else f'rotate_cw_{angle}'}
 if sourceview!=view:meta['alias_from_asset_id']=f'{oid}.{sourceview}'
 return im.transpose(trans),meta
spec=[]
oid='ghost-havana-colonial-street-paving-corner-transition'
for view,sv in [('right','front'),('left','rear')]:
 src=BOOK/A[f'{oid}.{sv}']['image']['path'];im=Image.open(src).convert('RGBA');cand=OUT/f'{oid}.{view}.png';im.save(cand);spec.append({'object_id':oid,'asset_id':f'{oid}.{view}','view':view,'candidate_path':str(cand.relative_to(ROOT)),'candidate_sha256':sha(cand),'method':'symmetric-square-paving-edge-alias','alias_from_asset_id':f'{oid}.{sv}','source_sha256':sha(src),'notes':'The corner-transition tile is square; use the full-span horizontal edge silhouette instead of the failed vertical-strip projection.'})
oid='broadcast-portals-studio-camera'
for view in ['top','bottom']:
 im,meta=rot(oid,view,view,270);cand=OUT/f'{oid}.{view}.png';im.save(cand);spec.append({'object_id':oid,'asset_id':f'{oid}.{view}','view':view,'candidate_path':str(cand.relative_to(ROOT)),'candidate_sha256':sha(cand),**meta,'notes':'Root queue direction: align TOP camera lens toward image-bottom and BOTTOM lens toward image-top.'})
oid='thresholds-red-carpet-runner';a=A[f'{oid}.top'];frontpath=BOOK/A[f'{oid}.front']['image']['path'];retained_front=ROOT/'prebuilt/axis-remap-before-v1'/f'{oid}.front.png'
if retained_front.exists():frontpath=retained_front
front=Image.open(frontpath).convert('RGBA');targetw=front.getchannel('A').getbbox()[2]-front.getchannel('A').getbbox()[0]
im,meta=fit_source(oid,'top',targetw);cand=OUT/f'{oid}.top.png';im.save(cand);spec.append({'object_id':oid,'asset_id':f'{oid}.top','view':'top','candidate_path':str(cand.relative_to(ROOT)),'candidate_sha256':sha(cand),**meta,'notes':'Native source is a long-Y plan; uniformly normalized to the existing runner transverse span.'})
bottom=OUT/f'{oid}.bottom.png';Image.open(cand).convert('RGBA').save(bottom);spec.append({'object_id':oid,'asset_id':f'{oid}.bottom','view':'bottom','candidate_path':str(bottom.relative_to(ROOT)),'candidate_sha256':sha(bottom),'method':'exact-symmetric-runner-plan-alias','alias_from_asset_id':f'{oid}.top','source_sha256':sha(cand),'notes':'The flat reversible carpet runner has the same long-Y footprint from below; exact plan alias keeps dimensions coherent.'})
for target,srcview in [('front','right'),('rear','left')]:
 src=BOOK/A[f'{oid}.{srcview}']['image']['path'];im=Image.open(src).convert('RGBA');cand=OUT/f'{oid}.{target}.png';im.save(cand);spec.append({'object_id':oid,'asset_id':f'{oid}.{target}','view':target,'candidate_path':str(cand.relative_to(ROOT)),'candidate_sha256':sha(cand),'method':'exact-thin-runner-edge-alias','alias_from_asset_id':f'{oid}.{srcview}','source_sha256':sha(src),'notes':'Reuse the existing thin horizontal runner edge instead of a full face-on carpet plan.'})
proofs=[]
for obj in ['ghost-havana-colonial-street-paving-corner-transition','broadcast-portals-studio-camera','thresholds-red-carpet-runner']:
 s=next(x for x in IDX['view_sets'] if x['object_id']==obj);src=BOOK/A[s['views']['front']]['source']['source_image'];ims=[Image.open(src).convert('RGBA')];labs=['SOURCE'];pr={'object_id':obj,'source_image':str(src.relative_to(BOOK)),'source_sha256':sha(src),'views':{}};chosen={e['view']:e for e in spec if e['object_id']==obj}
 for v in V:
  a=A[s['views'][v]]
  if v in chosen:p=ROOT/chosen[v]['candidate_path'];lab='CANDIDATE '+v.upper()
  else:p=BOOK/a['image']['path'];lab='LIVE '+v.upper()
  ims.append(Image.open(p).convert('RGBA'));labs.append(lab);pr['views'][v]={'path':str(p.relative_to(BOOK)) if p.is_relative_to(BOOK) else str(p.relative_to(ROOT)),'sha256':sha(p),'status':lab}
 sheet=Image.new('RGB',(272*7,300),(238,238,238));d=ImageDraw.Draw(sheet)
 for i,(im,lab) in enumerate(zip(ims,labs)):
  bg=Image.new('RGBA',(256,256),(140,140,140,255));bg.alpha_composite(im.resize((256,256),Image.Resampling.NEAREST));sheet.paste(bg.convert('RGB'),(i*272,28));d.text((i*272+4,6),lab,fill='black')
 cp=ROOT/'qa'/f'{obj}-axis-remaps-v1-candidate-source-live-six.png';sheet.save(cp);pr['contact_path']=str(cp.relative_to(ROOT));pr['contact_sha256']=sha(cp);cp.with_suffix('.json').write_text(json.dumps(pr,indent=2)+'\n');proofs.append({'object_id':obj,'contact_path':pr['contact_path'],'contact_sha256':pr['contact_sha256']})
(OUT/'candidate.json').write_text(json.dumps({'candidate_id':'axis-remaps-v1','entries':spec,'proofs':proofs},indent=2)+'\n');print(json.dumps(proofs,indent=2))
