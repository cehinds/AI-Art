from PIL import Image,ImageDraw,ImageOps
import scipy.ndimage as ndi,numpy as np,json,hashlib,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];BOOK=ROOT.parents[1];IDX=json.loads((ROOT/'set-index.json').read_text());A={a['id']:a for a in IDX['assets']};V=['front','top','right','left','bottom','rear'];OUT=ROOT/'candidates/transitions-boundary-remaps-v1';OUT.mkdir(parents=True,exist_ok=True);ALIAS=ROOT/'prebuilt/transition-alias-snapshots-v1';ALIAS.mkdir(parents=True,exist_ok=True)
def sh(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def onecomp(p):
 im=Image.open(p).convert('RGBA');lab,n=ndi.label(np.array(im.getchannel('A'))>10);cs=[]
 for i in range(1,n+1):
  y,x=np.where(lab==i)
  if len(x)>1000:cs.append((int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)))
 assert len(cs)==1,(p,cs);return im,cs[0]
def fit(crop,targetw):
 sc=targetw/crop.width;w=round(crop.width*sc);h=round(crop.height*sc);return crop.resize((w,h),Image.Resampling.NEAREST),(w,h),sc
def generated(oid,view,rawrel,bbox,targetw,prompt,sourcecontact,transform='none'):
 raw=ROOT/rawrel;im=Image.open(raw).convert('RGBA');crop=im.crop(bbox)
 if transform=='mirror_horizontal':crop=ImageOps.mirror(crop)
 crop,size,sc=fit(crop,targetw);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(crop,((256-size[0])//2,(256-size[1])//2));p=OUT/f'{oid}.{view}.png';canvas.save(p)
 a=A[f'{oid}.{view}'];src=BOOK/a['source']['source_image']
 return {'view':view,'asset_id':f'{oid}.{view}','method':'generated','source_image':a['source']['source_image'],'source_sha256':a['source']['source_sha256'],'raw_atlas':'reusable/views-additional/'+rawrel,'raw_atlas_sha256':sh(raw),'prompt_path':'reusable/views-additional/'+prompt,'prompt_sha256':sh(ROOT/prompt),'source_contact_sheet':'reusable/views-additional/'+sourcecontact,'source_contact_sheet_sha256':sh(ROOT/sourcecontact),'source_rect':list(bbox),'transform':transform,'uniform_scale':sc,'target_width_px':targetw,'normalized_bbox_size':list(size),'candidate_path':str(p.relative_to(ROOT)),'candidate_sha256':sh(p)}
def alias(oid,target,source_view,reason):
 aid=f'{oid}.{target}';srcid=f'{oid}.{source_view}';a=A[aid];sp=BOOK/A[srcid]['image']['path'];snap=ALIAS/f'{aid}.png';shutil.copy2(sp,snap);p=OUT/f'{aid}.png';shutil.copy2(sp,p);src=BOOK/a['source']['source_image']
 return {'view':target,'asset_id':aid,'method':'exact-view-alias','source_image':a['source']['source_image'],'source_sha256':a['source']['source_sha256'],'alias_from_asset_id':srcid,'alias_from_view':source_view,'alias_reason':reason,'retained_alias_png':str(snap.relative_to(BOOK)),'candidate_path':str(p.relative_to(ROOT)),'candidate_sha256':sh(p)}
# Alpha component geometry
wetright,bb_wetright=onecomp(ROOT/'raw/wet-edge-right-full-curb-v3.png');wetrear,bb_wetrear=onecomp(ROOT/'raw/wet-corner-rear-two-caps-v3.png')
gold=Image.open(ROOT/'raw/gold-transition-two-rails-v1.png').convert('RGBA');lab,n=ndi.label(np.array(gold.getchannel('A'))>10);gb=[]
for i in range(1,n+1):
 y,x=np.where(lab==i)
 if len(x)>1000:gb.append((int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)))
gb.sort(key=lambda q:q[1]);assert len(gb)==2
# Wet edge
O='surface-entry-wet-city-pavement-edge-transition';rows=[]
for v in ['right']:
 a=A[f'{O}.{v}'];im=Image.open(BOOK/a['image']['path']).convert('RGBA');target=im.getchannel('A').getbbox()[2]-im.getchannel('A').getbbox()[0];rows.append(generated(O,v,'raw/wet-edge-right-full-curb-v3.png',bb_wetright,target,'prompts/wet-edge-right-full-curb-v3.txt','contacts/transition-front-four-source.png'))
rows += [alias(O,'left','rear','Root-directed reuse of the accepted opposite profile; swap only left/rear mapping.'),alias(O,'rear','left','Root-directed reuse of the accepted opposite profile; swap only left/rear mapping.')]
SETS=[{'object_id':O,'views':rows}]
# Wet corner
O='surface-entry-wet-city-pavement-corner-transition';rows=[]
# Native source TOP U-plan, uniformly enlarged to a 180px footprint.
a=A[f'{O}.top'];src=BOOK/a['source']['source_image'];im=Image.open(src).convert('RGBA');b=im.getchannel('A').getbbox();crop=im.crop(b);crop,size,sc=fit(crop,180);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(crop,((256-size[0])//2,(256-size[1])//2));p=OUT/f'{O}.top.png';can.save(p);rows.append({'view':'top','asset_id':f'{O}.top','method':'source-top-plan','source_image':a['source']['source_image'],'source_sha256':a['source']['source_sha256'],'source_rect':list(b),'uniform_scale':sc,'normalized_bbox_size':list(size),'candidate_path':str(p.relative_to(ROOT)),'candidate_sha256':sh(p),'notes':'Exact native source top-plan, uniformly normalized; restores U-shaped curb on left/bottom/right and rounded lower-left.'})
# Full opaque inferred underside.
raw=ROOT/'raw/wet-corner-bottom-underside-v1.png';im,b=onecomp(raw);crop=im.crop(b);crop,size,sc=fit(crop,180);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(crop,((256-size[0])//2,(256-size[1])//2));p=OUT/f'{O}.bottom.png';can.save(p);a=A[f'{O}.bottom'];rows.append({'view':'bottom','asset_id':f'{O}.bottom','method':'generated-opaque-underside','source_image':a['source']['source_image'],'source_sha256':a['source']['source_sha256'],'raw_atlas':'reusable/views-additional/raw/wet-corner-bottom-underside-v1.png','raw_atlas_sha256':sh(raw),'prompt_path':'reusable/views-additional/prompts/wet-corner-bottom-underside-v1.txt','prompt_sha256':sh(ROOT/'prompts/wet-corner-bottom-underside-v1.txt'),'source_rect':list(b),'uniform_scale':sc,'normalized_bbox_size':list(size),'candidate_path':str(p.relative_to(ROOT)),'candidate_sha256':sh(p),'notes':'Inferred full opaque slab underside with rounded lower-left footprint.'})
for v in ['front','left','right']:
 a=A[f'{O}.{v}'];im=Image.open(BOOK/a['image']['path']).convert('RGBA');bbox=im.getchannel('A').getbbox();target=bbox[2]-bbox[0];rows.append(generated(O,v,'raw/wet-edge-right-full-curb-v3.png',bb_wetright,target,'prompts/wet-edge-right-full-curb-v3.txt','contacts/transition-front-four-source.png','mirror_horizontal' if v=='left' else 'none'))
a=A[f'{O}.rear'];im=Image.open(BOOK/a['image']['path']).convert('RGBA');bbox=im.getchannel('A').getbbox();target=bbox[2]-bbox[0];rows.append(generated(O,'rear','raw/wet-corner-rear-two-caps-v3.png',bb_wetrear,target,'prompts/wet-corner-rear-two-caps-v3.txt','contacts/transition-front-four-source.png'))
SETS.append({'object_id':O,'views':rows})
# Gold edge
O='thresholds-gold-brick-edge-transition';rows=[alias(O,'front','rear','Root-directed symmetry: front uses plain gold blocks from the accepted rear profile.')]
a=A[f'{O}.rear'];im=Image.open(BOOK/a['image']['path']).convert('RGBA');bbox=im.getchannel('A').getbbox();rows.append(generated(O,'rear','raw/gold-transition-two-rails-v1.png',gb[0],bbox[2]-bbox[0],'prompts/gold-transition-two-rails-v1.txt','contacts/gold-transition-two-rows-source.png'));SETS.append({'object_id':O,'views':rows})
# Gold corner
O='thresholds-gold-brick-corner-transition';rows=[alias(O,'front','left','Root-directed symmetric front/left cap reuse.')]
a=A[f'{O}.rear'];im=Image.open(BOOK/a['image']['path']).convert('RGBA');bbox=im.getchannel('A').getbbox();rail=generated(O,'rear','raw/gold-transition-two-rails-v1.png',gb[1],bbox[2]-bbox[0],'prompts/gold-transition-two-rails-v1.txt','contacts/gold-transition-two-rows-source.png');rows.append(rail);p=ROOT/rail['candidate_path'];dst=OUT/f'{O}.left.png';shutil.copy2(p,dst);left=dict(rail);left.update({'view':'left','asset_id':f'{O}.left','candidate_path':str(dst.relative_to(ROOT)),'candidate_sha256':sh(dst),'alias_from_asset_id':f'{O}.rear','alias_reason':'Root-approved symmetric full rail profile reused for left and rear.'});rows.append(left);SETS.append({'object_id':O,'views':rows})
# source + proposed/live six proofs
for s in SETS:
 oid=s['object_id'];vs=next(x for x in IDX['view_sets'] if x['object_id']==oid);src=BOOK/A[vs['views']['front']]['source']['source_image'];items=[Image.open(src).convert('RGBA')];labels=['SOURCE'];proposal={r['view']:r for r in s['views']};proof={'object_id':oid,'source_image':str(src.relative_to(BOOK)),'source_sha256':sh(src),'views':{}}
 for v in V:
  a=A[vs['views'][v]];r=proposal.get(v)
  if r:
   p=ROOT/r['candidate_path'];im=Image.open(p).convert('RGBA');label='PROPOSED '+v.upper();proof['views'][v]={'status':'proposed','path':r['candidate_path'],'sha256':sh(p)}
  else:
   p=BOOK/a['image']['path'];im=Image.open(p).convert('RGBA');label='LIVE '+v.upper();proof['views'][v]={'status':'live','path':str(p.relative_to(BOOK)),'sha256':sh(p)}
  items.append(im);labels.append(label)
 tile=272;sheet=Image.new('RGB',(tile*7,300),(238,238,238));d=ImageDraw.Draw(sheet)
 for i,(im,label) in enumerate(zip(items,labels)):
  bg=Image.new('RGBA',(256,256),(140,140,140,255));bg.alpha_composite(im.resize((256,256),Image.Resampling.NEAREST));sheet.paste(bg.convert('RGB'),(i*tile,28));d.text((i*tile+4,6),label,fill=(0,0,0))
 cp=ROOT/'qa'/f'{oid}-boundary-v1-candidate-source-live-six.png';sheet.save(cp);proof['contact_path']=str(cp.relative_to(ROOT));proof['contact_sha256']=sh(cp);cp.with_suffix('.json').write_text(json.dumps(proof,indent=2)+'\n');s['contact_path']=proof['contact_path'];s['contact_sha256']=proof['contact_sha256']
(ROOT/'candidates/transitions-boundary-remaps-v1/candidate.json').write_text(json.dumps({'candidate_id':'transitions-boundary-remaps-v1','sets':SETS},indent=2)+'\n')
print([(s['object_id'],[r['view'] for r in s['views']],s['contact_path']) for s in SETS])
