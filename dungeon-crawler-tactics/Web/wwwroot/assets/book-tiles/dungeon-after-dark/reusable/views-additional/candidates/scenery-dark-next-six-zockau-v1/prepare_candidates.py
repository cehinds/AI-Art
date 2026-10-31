#!/usr/bin/env python3
"""Extract orthographic candidates from bound generated atlases; source/current leaves stay read-only."""
from pathlib import Path
from PIL import Image,ImageDraw
from scipy import ndimage
import numpy as np,json,hashlib
PACK=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
BASE=PACK/'reusable/views-additional'; C=BASE/'candidates/scenery-dark-next-six-zockau-v1'
HAND=Path('/workspace/scratch/scenery-dark-next-six-zockau-handoff-20261026.json')
VIEW_ORDER=['front','top','right','left','bottom','rear']
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bbox64(path):
 im=Image.open(path).convert('RGBA'); a=np.asarray(im.getchannel('A')); yy,xx=np.where(a>=64)
 return None if not len(xx) else [int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
def components(path):
 im=Image.open(path).convert('RGBA'); a=np.asarray(im.getchannel('A')); labels,n=ndimage.label(a>=64,structure=np.ones((3,3),np.uint8)); out=[]
 for lab in range(1,n+1):
  yy,xx=np.where(labels==lab)
  if len(xx)>500: out.append({'label':int(lab),'area':int(len(xx)),'bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'centroid':[float(xx.mean()),float(yy.mean())]})
 return im,labels,out
def select(raw_path,grid_cols,grid_rows,row,col):
 im,labels,cs=components(raw_path); cw=im.width/grid_cols; ch=im.height/grid_rows; cx=(col+.5)*cw;cy=(row+.5)*ch
 ranked=sorted(cs,key=lambda q:(q['centroid'][0]-cx)**2+(q['centroid'][1]-cy)**2)
 assert ranked and (ranked[0]['centroid'][0]-cx)**2+(ranked[0]['centroid'][1]-cy)**2 < (min(cw,ch)*.4)**2,(raw_path,row,col,ranked[:2])
 comp=ranked[0]; label=comp['label']; mask=(labels==label)
 # Preserve connected component + two-pixel alpha fringe only, never a neighboring cell.
 mask=ndimage.binary_dilation(mask,structure=np.ones((3,3),bool),iterations=2)
 x0=max(int(col*cw),int(comp['bbox'][0])-2);y0=max(int(row*ch),int(comp['bbox'][1])-2);x1=min(int((col+1)*cw),int(comp['bbox'][2])+2);y1=min(int((row+1)*ch),int(comp['bbox'][3])+2)
 crop=im.crop((x0,y0,x1,y1)); ca=np.asarray(crop).copy(); m=mask[y0:y1,x0:x1];ca[~m,3]=0;crop=Image.fromarray(ca,'RGBA')
 return crop,{'component':comp,'cell_bbox':[int(col*cw),int(row*ch),int((col+1)*cw),int((row+1)*ch)],'crop_bbox':[x0,y0,x1,y1],'alpha_threshold':64,'dilation_footprint':[3,3],'dilation_iterations':2}
hand=json.loads(HAND.read_text()); objs={x['object_id']:x for x in hand['objects']}
# Atlas sources and row maps. First atlas is superseded only for wall rows; endcaps remain active.
atlas={
 'cap_ne':(C/'raw-zockau-four-atlas.png',6,4,0),
 'cap_nw':(C/'raw-zockau-four-atlas.png',6,4,1),
 'wall_ne':(C/'raw-zockau-walls-v3-atlas.png',6,2,0),
 'wall_nw':(C/'raw-zockau-nw-wall-v4-atlas.png',3,2,0),
 'jungle':(C/'raw-jungle-bear-atlas.png',6,2,0),
 'bear':(C/'raw-jungle-bear-atlas.png',6,2,1),
}
ids_to_kind={
 'hunting-jungle-vine-covered-ruin-stone-endcap-northwest':'jungle',
 'hunting-zockau-bear-head-square-statue':'bear',
 'hunting-zockau-painted-town-brick-endcap-northeast':'cap_ne',
 'hunting-zockau-painted-town-brick-endcap-northwest':'cap_nw',
 'hunting-zockau-painted-town-brick-wall-northeast':'wall_ne',
 'hunting-zockau-painted-town-brick-wall-northwest':'wall_nw',
}
affected={o['object_id']:o['affected_views'] for o in hand['objects']}
# Shared uniform scale per object; target extents preserve accepted neighboring projection scale where available.
target={
 'hunting-jungle-vine-covered-ruin-stone-endcap-northwest':170,
 'hunting-zockau-bear-head-square-statue':190,
 'hunting-zockau-painted-town-brick-endcap-northeast':180,
 'hunting-zockau-painted-town-brick-endcap-northwest':156,
 'hunting-zockau-painted-town-brick-wall-northeast':180,
 'hunting-zockau-painted-town-brick-wall-northwest':190,
}
manifest={'candidate_id':'scenery-dark-next-six-zockau-v1','scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_scenery','reviewer':'root','installer':'views_dark_books','candidate_only':True,'handoff_path':str(HAND),'handoff_sha256':sha(HAND),'source_six_proof_path':'/tmp/root148-dark-zockau6.png.json','source_six_proof_sha256':sha('/tmp/root148-dark-zockau6.png.json'),'sets':[],'held_directions':[],'superseded_attempts':[{'atlas':'candidates/scenery-dark-next-six-zockau-v1/raw-zockau-four-atlas.png','reason':'Wall rows had NE RIGHT/LEFT mismatch; endcap rows retained.'},{'atlas':'candidates/scenery-dark-next-six-zockau-v1/raw-zockau-walls-v2-atlas.png','reason':'NE axis correct but plan footprint was ~7.5:1 against native ~4:1; superseded for both walls.'},{'atlas':'candidates/scenery-dark-next-six-zockau-v1/raw-zockau-walls-v3-atlas.png','reason':'NE row active; NW row too tall against accepted short front and superseded by NW v4.'}]}
for oid,kind in ids_to_kind.items():
 o=objs[oid]; assert sha(o['source']['path'])==o['source']['sha256']
 for v,d in o['views'].items(): assert sha(d['path'])==d['sha256'],(oid,v)
 raw,cols,rows,row=atlas[kind]; req={'cap_ne':'request-zockau-four.json','cap_nw':'request-zockau-four.json','wall_ne':'request-zockau-walls-v3.json','wall_nw':'request-zockau-nw-wall-v4.json','jungle':'request-jungle-bear.json','bear':'request-jungle-bear.json'}[kind]; rawsha=sha(raw)
 cell_crops={}; maxdim=0
 for vi,v in enumerate(VIEW_ORDER):
  if kind=='wall_nw': rr=0 if v in ('front','top','right') else 1;cc={'front':0,'top':1,'right':2,'left':0,'bottom':1,'rear':2}[v]
  else: rr=row;cc=vi
  crop,recipe=select(raw,cols,rows,rr,cc);cell_crops[v]=(crop,recipe);maxdim=max(maxdim,*crop.size)
 scale=target[oid]/maxdim
 entry={'object_id':oid,'source_path':o['source']['path'].replace(str(PACK)+'/',''),'source_sha256':o['source']['sha256'],'source_absolute_path':o['source']['path'],'base_current_views':{},'affected_views':list(affected[oid]),'candidates':{},'notes':'Source and the current six-view proof remain authoritative. All generated views are inferred orthographic illustrations; no live leaves are modified.'}
 for v,x in o['views'].items():entry['base_current_views'][v]={'path':x['path'].replace(str(PACK)+'/',''),'absolute_path':x['path'],'sha256':x['sha256']}
 for v in affected[oid]:
  crop,rec=cell_crops[v]; dims=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale))); z=crop.resize(dims,Image.Resampling.NEAREST); xy=((256-dims[0])//2,(256-dims[1])//2); out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(z,xy)
  path=C/'images'/f'{oid}.{v}.candidate-v1.png';path.parent.mkdir(exist_ok=True);out.save(path,optimize=False)
  entry['candidates'][v]={'candidate_path':str(path.relative_to(BASE)),'candidate_sha256':sha(path),'raw_path':str(raw.relative_to(BASE)),'raw_sha256':rawsha,'request_path':str((C/req).relative_to(BASE)),'request_sha256':sha(C/req),'crop_bbox_alpha64':rec['crop_bbox'],'cell_bbox':rec['cell_bbox'],'raw_component':rec['component'],'component_mask':{'threshold':64,'dilation_footprint':rec['dilation_footprint'],'iterations':rec['dilation_iterations']},'uniform_scale':scale,'resized_dimensions':list(dims),'canvas':[256,256],'placement_xy':list(xy),'filter':'NEAREST','base_sha256':x['sha256'],'source_path':o['source']['path'].replace(str(PACK)+'/',''),'source_sha256':o['source']['sha256'],'notes':'Generated orthographic projection; unseen surfaces are inferred. Candidate-only; live source/view PNGs remain unchanged.'}
 manifest['sets'].append(entry)
# Full current source+six/candidate contact, candidates only in affected directions.
W=160;H=160;labelh=22;pad=8;rowh=H+labelh+pad;sheet=Image.new('RGBA',(pad+7*(W+pad),pad+len(manifest['sets'])*rowh),(35,35,40,255));draw=ImageDraw.Draw(sheet)
for ri,e in enumerate(manifest['sets']):
 o=objs[e['object_id']];y=pad+ri*rowh;draw.text((pad,y),e['object_id'],fill='white');y+=labelh
 imgs=[Image.open(o['source']['path']).convert('RGBA')]
 for v in VIEW_ORDER:
  if v in e['candidates']:p=BASE/e['candidates'][v]['candidate_path']
  else:p=o['views'][v]['path']
  imgs.append(Image.open(p).convert('RGBA'))
 for ci,im in enumerate(imgs):
  x=pad+ci*(W+pad);im.thumbnail((W,H),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+(W-im.width)//2,y+(H-im.height)//2));draw.text((x,y+H+2),['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR'][ci],fill='white')
contact=C/'candidate-source-plus-six.png';sheet.save(contact,optimize=False);manifest['contact_path']=str(contact.relative_to(BASE));manifest['contact_sha256']=sha(contact);mp=C/'candidate-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'manifest':str(mp),'manifest_sha256':sha(mp),'contact':str(contact),'contact_sha256':sha(contact),'sets':len(manifest['sets']),'candidate_views':sum(len(x['affected_views']) for x in manifest['sets']),'held':manifest['held_directions']},indent=2))
