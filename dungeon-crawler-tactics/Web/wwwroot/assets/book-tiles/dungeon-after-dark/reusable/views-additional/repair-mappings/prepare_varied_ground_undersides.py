"""Prepare six candidate-only opaque substrate bottoms across ground styles."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[1];BOOK=ROOT.parent.parent;IDX=json.loads((ROOT/'set-index.json').read_text());A={a['id']:a for a in IDX['assets']}
IDS=['bubble-desert-wet-sandstone-and-sand-floor','bubble-sea-coral-seabed-floor','faction-battlefield-worn-churned-battlefield-earth-floor','ghost-cemetery-cemetery-flagstone-edge-transition','race-circuits-painted-grid-asphalt-floor','early-arenas-wet-arena-stone-floor'];V=('front','top','right','left','bottom','rear')
RAW=ROOT/'raw/varied-ground-undersides-v1.png';PROMPT=ROOT/'prompts/varied-ground-undersides-v1.txt';CONTACT=ROOT/'contacts/varied-ground-underside-sources-3x2.png';OUT=ROOT/'candidates/varied-ground-undersides-v1';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
im=Image.open(RAW).convert('RGBA');labels,n=ndimage.label(np.asarray(im.getchannel('A'))>10);comps=[]
for k in range(1,n+1):
 y,x=np.where(labels==k)
 if len(x)>10000:comps.append((int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)))
comps.sort(key=lambda b:(b[1]//600,b[0]//600));assert len(comps)==6,comps
entries=[]
for oid,b in zip(IDS,comps):
 s=next(x for x in IDX['view_sets'] if x['object_id']==oid);a=A[s['views']['bottom']];src=BOOK/a['source']['source_image'];top=Image.open(BOOK/A[s['views']['top']]['image']['path']).convert('RGBA').getchannel('A').getbbox();crop=im.crop(b);target=top[2]-top[0];scale=target/crop.width;size=(target,round(crop.height*scale));crop=crop.resize(size,Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(crop,((256-size[0])//2,(256-size[1])//2));p=OUT/f'{oid}.bottom.png';can.save(p)
 entries.append({'object_id':oid,'asset_id':a['id'],'view':'bottom','method':'generated-inferred-opaque-ground-underside','source_image':str(src.relative_to(BOOK)),'source_sha256':sha(src),'raw_atlas':'reusable/views-additional/raw/varied-ground-undersides-v1.png','raw_atlas_sha256':sha(RAW),'prompt_path':'reusable/views-additional/prompts/varied-ground-undersides-v1.txt','prompt_sha256':sha(PROMPT),'source_contact_sheet':'reusable/views-additional/contacts/varied-ground-underside-sources-3x2.png','source_contact_sheet_sha256':sha(CONTACT),'source_rect':list(b),'uniform_scale':scale,'target_width_px':target,'normalized_bbox_size':list(size),'candidate_path':str(p.relative_to(ROOT)),'candidate_sha256':sha(p),'notes':'Inferred opaque underside; source does not expose hidden support pixels.'})
proofs=[]
for e in entries:
 s=next(x for x in IDX['view_sets'] if x['object_id']==e['object_id']);src=BOOK/e['source_image'];ims=[Image.open(src).convert('RGBA')];labs=['SOURCE']
 for v in V:
  p=ROOT/e['candidate_path'] if v=='bottom' else BOOK/A[s['views'][v]]['image']['path'];ims.append(Image.open(p).convert('RGBA'));labs.append('CANDIDATE BOTTOM' if v=='bottom' else 'LIVE '+v.upper())
 sheet=Image.new('RGB',(272*7,300),(238,238,238));d=ImageDraw.Draw(sheet)
 for i,(pic,lab) in enumerate(zip(ims,labs)):
  bg=Image.new('RGBA',(256,256),(140,140,140,255));bg.alpha_composite(pic.resize((256,256),Image.Resampling.NEAREST));sheet.paste(bg.convert('RGB'),(i*272,28));d.text((i*272+4,6),lab,fill='black')
 cp=ROOT/'qa'/f"{e['object_id']}-underside-v1-candidate-source-six.png";sheet.save(cp);proofs.append({'object_id':e['object_id'],'contact_path':str(cp.relative_to(ROOT)),'contact_sha256':sha(cp),'source_sha256':e['source_sha256'],'candidate_sha256':e['candidate_sha256']})
(OUT/'candidate.json').write_text(json.dumps({'candidate_id':'varied-ground-undersides-v1','entries':entries,'proofs':proofs},indent=2)+'\n');print(json.dumps({'candidates':len(entries),'proofs':proofs},indent=2))
