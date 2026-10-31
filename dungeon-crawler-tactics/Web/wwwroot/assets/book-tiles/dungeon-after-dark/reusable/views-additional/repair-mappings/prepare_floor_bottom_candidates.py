"""Prepare candidate-only square backing planes for eight floor tiles."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage

ROOT=Path(__file__).resolve().parents[1]; BOOK=ROOT.parents[1]
IDX=json.loads((ROOT/'set-index.json').read_text()); A={a['id']:a for a in IDX['assets']}
VIEWS=('front','top','right','left','bottom','rear')
groups=[
 ('clubs-guilds',[
  'clubs-guilds-club-carpet-floor','clubs-guilds-cracked-club-carpet-floor',
  'clubs-guilds-wet-club-carpet-floor','clubs-guilds-worn-club-carpet-floor'],
  'raw/club-carpet-undersides-v1.png','prompts/club-carpet-undersides-v1.txt','contacts/club-carpet-source-2x2.png'),
 ('larracos',[
  'faction-larracos-drained-city-cobblestone-floor','faction-larracos-cracked-drained-city-cobblestone-floor',
  'faction-larracos-wet-drained-city-cobblestone-floor','faction-larracos-worn-drained-city-cobblestone-floor'],
  'raw/larracos-cobble-undersides-v1.png','prompts/larracos-cobble-undersides-v1.txt','contacts/larracos-cobble-source-2x2.png')]
OUT=ROOT/'candidates/floor-bottoms-v1';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
entries=[]
for family,oids,rawrel,promptrel,contactrel in groups:
 raw=ROOT/rawrel; im=Image.open(raw).convert('RGBA'); labels,n=ndimage.label(np.asarray(im.getchannel('A'))>10); comps=[]
 for k in range(1,n+1):
  y,x=np.where(labels==k)
  if len(x)>10000:comps.append((int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1),len(x)))
 # Atlas order is row-major; sort by cell row, then column.
 comps.sort(key=lambda b:(b[1]//600,b[0]//600))
 assert len(comps)==4,(family,comps)
 for i,(oid,comp) in enumerate(zip(oids,comps)):
  x0,y0,x1,y1,_=comp;crop=im.crop((x0,y0,x1,y1)); ss=next(s for s in IDX['view_sets'] if s['object_id']==oid);asset=A[ss['views']['bottom']];top=Image.open(BOOK/A[ss['views']['top']]['image']['path']).convert('RGBA');tb=top.getchannel('A').getbbox();targetw=tb[2]-tb[0]
  sc=targetw/crop.width;size=(targetw,round(crop.height*sc));crop=crop.resize(size,Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(crop,((256-size[0])//2,(256-size[1])//2))
  cand=OUT/f'{oid}.bottom.png';can.save(cand)
  src=BOOK/asset['source']['source_image']
  entries.append({'object_id':oid,'asset_id':asset['id'],'view':'bottom','method':'generated-opaque-floor-underside','source_image':str(src.relative_to(BOOK)),'source_sha256':sha(src),'raw_atlas':'reusable/views-additional/'+rawrel,'raw_atlas_sha256':sha(raw),'prompt_path':'reusable/views-additional/'+promptrel,'prompt_sha256':sha(ROOT/promptrel),'source_contact_sheet':'reusable/views-additional/'+contactrel,'source_contact_sheet_sha256':sha(ROOT/contactrel),'source_rect':[x0,y0,x1,y1],'uniform_scale':sc,'target_width_px':targetw,'normalized_bbox_size':list(size),'candidate_path':str(cand.relative_to(ROOT)),'candidate_sha256':sha(cand),'notes':'Inferred opaque underside; hidden surface is not recovered source imagery.'})
proof=[]
for e in entries:
 oid=e['object_id'];ss=next(s for s in IDX['view_sets'] if s['object_id']==oid);ims=[];labels=[]
 src=BOOK/e['source_image'];ims.append(Image.open(src).convert('RGBA'));labels.append('SOURCE')
 for v in VIEWS:
  asset=A[ss['views'][v]]
  if v=='bottom':p=ROOT/e['candidate_path']; lab='CANDIDATE BOTTOM'
  else:p=BOOK/asset['image']['path'];lab='LIVE '+v.upper()
  ims.append(Image.open(p).convert('RGBA'));labels.append(lab)
 tile=272;sheet=Image.new('RGB',(tile*7,300),(238,238,238));d=ImageDraw.Draw(sheet)
 for j,(im,lab) in enumerate(zip(ims,labels)):
  bg=Image.new('RGBA',(256,256),(140,140,140,255));bg.alpha_composite(im.resize((256,256),Image.Resampling.NEAREST));sheet.paste(bg.convert('RGB'),(j*tile,28));d.text((j*tile+4,6),lab,fill=(0,0,0))
 cp=ROOT/'qa'/f"{oid}-floor-bottom-v1-candidate-source-live-six.png";sheet.save(cp);proof.append({'object_id':oid,'contact_path':str(cp.relative_to(ROOT)),'contact_sha256':sha(cp),'candidate_sha256':e['candidate_sha256'],'source_sha256':e['source_sha256']})
 spec=OUT/'candidate.json';spec.write_text(json.dumps({'candidate_id':'floor-bottoms-v1','entries':entries,'proofs':proof},indent=2)+'\n')
print(json.dumps({'candidates':len(entries),'proofs':proof},indent=2))
