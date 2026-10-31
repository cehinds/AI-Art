from PIL import Image, ImageDraw
import numpy as np, pathlib, hashlib, json
from scipy.ndimage import label, find_objects
ROOT=pathlib.Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon')
OUT=ROOT/'reusable/views-additional/raw/candidates/iron-tracks-rail-junctions-v4'
ATLAS=OUT/'raw-atlas.png'
ids=['iron-tracks-rail-curve','iron-tracks-rail-t-junction','iron-tracks-rail-crossroads','iron-tracks-rail-siding-junction']
views=['front','top','right','left','bottom','rear']
cols=[128,384,640,896,1152,1408]; rowcenters=[147,387,627,868]
im=Image.open(ATLAS).convert('RGBA'); a=np.array(im)[:,:,3]
lab,n=label(a>8); comps=[]
for i,s in enumerate(find_objects(lab),1):
 if not s: continue
 y,x=s; area=int((lab[s]==i).sum())
 if area<1000: continue
 comps.append({'label':i,'bbox':[x.start,y.start,x.stop,y.stop],'area':area,'cx':(x.start+x.stop)/2,'cy':(y.start+y.stop)/2})
assert len(comps)==24, f'expected 24 coherent cells; got {len(comps)}'
used=set(); rows=[]; records=[]
for ri,oid in enumerate(ids):
 row={}
 for vi,v in enumerate(views):
  c=min((z for z in comps if z['label'] not in used),key=lambda z:abs(z['cx']-cols[vi])+abs(z['cy']-rowcenters[ri]))
  used.add(c['label']); x0,y0,x1,y1=c['bbox']
  cell=im.crop((x0,y0,x1,y1))
  canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(cell,((256-cell.width)//2,248-cell.height))
  # Generated candidate leaves are kept in staging only; TOP/BOTTOM are shown for context but not marked for install.
  if v in ('front','right','left','rear'):
   dest=OUT/f'{oid}.{v}.candidate.png';canvas.save(dest)
   target=ROOT/'reusable/views-additional'/f'{oid}.{v}.png'
   rec={'object_id':oid,'view':v,'candidate_path':dest.name,'candidate_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'target_path':target.relative_to(ROOT).as_posix(),'target_sha256_before':hashlib.sha256(target.read_bytes()).hexdigest(),'crop_bbox':c['bbox'],'component_area_alpha_gt8':c['area'],'normalization':{'scale':1.0,'resampling':'none; preserve source atlas pixels','anchor_px':[128,248]}}
   records.append(rec); row[v]=canvas
  elif v in ('top','bottom'):
   src=Image.open(ROOT/'reusable/views-additional'/f'{oid}.{v}.png').convert('RGBA'); row[v]=src
 row['source']=Image.open(ROOT/'iron-tracks'/'components'/f'{oid}.png').convert('RGBA')
 rows.append((oid,row))
# Contact: source + six principal directions, candidate elevations / retained current plans.
W,H=7*256,4*256
sheet=Image.new('RGBA',(W,H),(230,230,230,255)); dr=ImageDraw.Draw(sheet)
for r,(oid,row) in enumerate(rows):
 for c,key in enumerate(['source']+views):
  tile=row[key]
  if key=='source':
   # composite canonical source on white, retaining original transparency appearance
   bg=Image.new('RGBA',(256,256),(255,255,255,255)); bg.alpha_composite(tile)
   tile=bg
  sheet.alpha_composite(tile,(c*256,r*256))
  dr.text((c*256+4,r*256+4),key,fill=(0,0,0,255),stroke_width=1,stroke_fill=(255,255,255,255))
 dr.text((4,r*256+238),oid,fill=(0,0,0,255),stroke_width=1,stroke_fill=(255,255,255,255))
contact=OUT/'candidate-source-plus-six.png';sheet.convert('RGB').save(contact)
atlas_sha=hashlib.sha256(ATLAS.read_bytes()).hexdigest()
manifest={'schema_version':1,'batch_id':'iron-tracks-junctions-v4-20261026','status':'staged-unreviewed','raw_atlas':{'path':ATLAS.relative_to(ROOT).as_posix(),'sha256':atlas_sha,'output_binding':'/workspace/generated_images/exec-eb1014dd-eeff-4fc2-b774-6d6d1b8b5e91.png'},'source_rows':[{'object_id':oid,'path':f'iron-tracks/components/{oid}.png','sha256':hashlib.sha256((ROOT/'iron-tracks'/'components'/f'{oid}.png').read_bytes()).hexdigest()} for oid in ids],'candidates':records,'contact':contact.relative_to(ROOT).as_posix(),'contact_sha256':hashlib.sha256(contact.read_bytes()).hexdigest(),'notes':'Four elevations only are proposed. TOP/BOTTOM in contact are exact current target PNGs. Alpha extraction was from full atlas connected components grouped one component per view by row/column centroid; no fixed-cell crop. Candidate alpha islands stay within crop bounds.'}
(OUT/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'contact':str(contact),'contact_sha256':manifest['contact_sha256'],'candidate_count':len(records),'atlas_sha256':atlas_sha,'component_count':len(comps)},indent=2))
