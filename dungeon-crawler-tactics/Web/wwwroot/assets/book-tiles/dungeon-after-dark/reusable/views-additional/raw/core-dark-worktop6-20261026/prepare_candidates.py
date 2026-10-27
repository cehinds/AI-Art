import os,json,hashlib
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from scipy.ndimage import label
ROOT='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'
STAGE=ROOT+'/reusable/views-additional/raw/core-dark-worktop6-20261026'
HANDOFF='/workspace/scratch/core-dark-worktop6-candidate-handoff-20261026.json'
h=json.load(open(HANDOFF)); byid={o['object_id']:o for o in h['objects']}
sel={
 'clubs-guilds-mercenary-reception-desk':('clubs-guilds-mercenary-reception-desk.top-v2.raw-response.png','exec-2c40102f-30db-4a23-9521-93e460c7d681','clubs-guilds-mercenary-reception-desk.top-v2.request.json'),
 'personal-space-alchemy-station':('personal-space-alchemy-station.top-v2.raw-response.png','exec-7e22de1a-e10a-4c69-8d7f-05305ec061ae','personal-space-alchemy-station.top-v2.request.json'),
 'personal-space-kitchen-counter':('personal-space-kitchen-counter.top.raw-response.png','exec-c8c39734-8f60-41c9-a70f-ef11366ca45a','personal-space-kitchen-counter.top.request.json'),
 'race-circuits-vehicle-upgrade-workbench':('race-circuits-vehicle-upgrade-workbench.top-v5.raw-response.png','exec-4ecd310d-f824-474a-a28c-b2e656c1f5f6',None),
 'race-circuits-pit-repair-station':('race-circuits-pit-repair-station.top.raw-response.png','exec-f9e0de75-35ba-4c57-addc-062d34fa9975','race-circuits-pit-repair-station.top.request.json'),
 'over-city-venues-administrative-office-desk':('over-city-venues-administrative-office-desk.top-v3.raw-response.png','exec-fdac1348-0d19-408c-b8df-cb19a6fb7c70',None),
}
new_prompts={
 'race-circuits-vehicle-upgrade-workbench':"Draw one isolated pixel-art orthographic TOP view of the exact same compact vehicle repair workbench. Directly overhead camera, straight down; no perspective. The tabletop must have a plausible compact rectangular footprint, about 1.4 times as wide as deep, matching the source icon proportions (not a long narrow plank). Main tabletop is dark steel gray with blue metal rim and small red accents; preserve a red toolbox on the right, wrench and sockets/bolts on the left in source-relative positions. The upright rear pegboard projects only as a narrow blue strip at the far edge, with tiny colored tool caps; no broad vertical pegboard face. Absolutely no drawer fascia, cabinet fronts or legs because they are below the tabletop. No extra object, no labels/text, transparent background, crisp dark-outlined pixel art. Reference 1 is canonical sprite, reference 2 is accepted front view.",
 'over-city-venues-administrative-office-desk':"Edit this exact desk and chair into one orthographic principal TOP projection, looking straight down. Transparent background. Keep the rectangular golden wood tabletop and the same left book stack, central pale parchment with quill at its right edge, and right blue book stack, in their source positions. Show only their overhead surfaces. The red upholstered chair sits behind the desk: from directly above show only the compact red chair crown/upper footprint at the far edge if visible; never show its upright crest face. The red-and-gold hanging banner/emblem is vertical and must be fully occluded by the tabletop, not shown hanging down. Absolutely remove front drawer fascia and all vertical furniture faces. Do not add or remove tabletop objects. Maintain the exact warm pixel-art material, proportions, crisp outlines, isolated tabletop silhouette; no isometric angle, no text."
}
# selected raw input and associated request details
records=[]; contact_rows=[]
for oid,(rawname,request_id,reqname) in sel.items():
 o=byid[oid]; rawp=STAGE+'/'+rawname; raw=Image.open(rawp).convert('RGBA')
 arr=np.array(raw.getchannel('A')); lab,n=label(arr>=16); counts=np.bincount(lab.ravel()); counts[0]=0; biggest=int(counts.argmax()); mask=(lab==biggest)
 yy,xx=np.where(mask)
 if not len(xx): raise RuntimeError('empty alpha CC '+oid)
 bbox=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)); crop=raw.crop(bbox)
 # Exclude detached components/noise using threshold-16 global CC; preserve source alpha on its selected component.
 ca=np.array(crop.getchannel('A')); submask=mask[bbox[1]:bbox[3],bbox[0]:bbox[2]]
 ca[~submask]=0; crop.putalpha(Image.fromarray(ca))
 top=Image.open(o['views']['top']['path']).convert('RGBA'); top_alpha=np.array(top.getchannel('A')); ty,tx=np.where(top_alpha>=16)
 tbbox=(int(tx.min()),int(ty.min()),int(tx.max()+1),int(ty.max()+1)); target_w=tbbox[2]-tbbox[0]
 scale=target_w/crop.width; nw=target_w; nh=max(1,round(crop.height*scale))
 if nh>220:
  scale=min(scale,220/crop.height); nw=round(crop.width*scale); nh=round(crop.height*scale)
 scaled=crop.resize((nw,nh),Image.Resampling.NEAREST)
 out=Image.new('RGBA',(256,256),(0,0,0,0)); x=(256-nw)//2; y=(256-nh)//2; out.alpha_composite(scaled,(x,y))
 cand=STAGE+'/'+oid+'.top.candidate-v1.png'; out.save(cand,optimize=False)
 rawsha=hashlib.sha256(open(rawp,'rb').read()).hexdigest(); candsha=hashlib.sha256(open(cand,'rb').read()).hexdigest()
 reqpath=STAGE+'/'+reqname if reqname else None
 oldreq=json.load(open(reqpath)) if reqpath else {}
 prompt=new_prompts.get(oid,oldreq.get('prompt',''))
 if not prompt: raise RuntimeError('missing prompt '+oid)
 if reqname:
  refs=oldreq.get('referenced_image_paths',[])
  refshas=[]
  for p in refs:
   if os.path.exists(p): refshas.append({'path':p,'sha256':hashlib.sha256(open(p,'rb').read()).hexdigest()})
 else:
  refs=[o['source']['path'],o['views']['front']['path']]
  refshas=[{'path':p,'sha256':hashlib.sha256(open(p,'rb').read()).hexdigest()} for p in refs]
 record={'object_id':oid,'direction':'top','request_id':request_id,'candidate_status':'unreviewed-staged-only','raw_response':{'path':rawp,'sha256':rawsha,'dimensions_px':list(raw.size)},'prompt':prompt,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'references':refshas,'canonical_source':{'path':o['source']['path'],'sha256':o['source']['sha256']},'base_six':{v:dict(x) for v,x in o['views'].items()},'normalization':{'alpha_threshold':16,'connected_component_connectivity':8,'selected_component_pixels':int(counts[biggest]),'component_count':int(n),'crop_bounds_xyxy_px':list(bbox),'isotropic_scale':scale,'resized_dimensions_px':[nw,nh],'target_width_px_from_current_top_alpha_bbox':target_w,'current_top_alpha_bbox_xyxy_px':list(tbbox),'canvas_px':[256,256],'centering_offsets_xy_px':[x,y],'shared_anchor_px':[128,128],'resampling':'nearest-neighbor','disconnected_alpha_dropped':True},'candidate':{'path':cand,'sha256':candsha,'dimensions_px':[256,256],'alpha_bbox_xyxy_px':list(out.getchannel('A').getbbox() or ())}}
 reqout=STAGE+'/'+oid+'.top.candidate-v1.request.json'; json.dump(record,open(reqout,'w'),indent=2)
 records.append(record)
 # Source + six existing + proposed TOP, all shown as direct labeled cells.
 source=Image.open(o['source']['path']).convert('RGBA')
 cells=[('SOURCE',source)]+[(v,Image.open(o['views'][v]['path']).convert('RGBA')) for v in ('front','top','right','left','bottom','rear')]+[('TOP CANDIDATE',out)]
 row=[]
 for cell_label,im in cells:
  im.thumbnail((220,210),Image.Resampling.NEAREST)
  cell=Image.new('RGBA',(240,245),(38,38,38,255)); cell.alpha_composite(im,((240-im.width)//2,28+(210-im.height)//2))
  ImageDraw.Draw(cell).text((5,5),cell_label,fill=(255,255,255,255))
  row.append(cell.convert('RGB'))
 contact_rows.append((oid,row))
# one object row per 8 cells
contact=Image.new('RGB',(240*8,245*len(contact_rows)),(24,24,24)); draw=ImageDraw.Draw(contact)
for ri,(oid,row) in enumerate(contact_rows):
 draw.text((4,ri*245+230),oid,fill='white')
 for ci,im in enumerate(row): contact.paste(im,(ci*240,ri*245))
contactpath=STAGE+'/contacts/core-dark-worktop6-source-six-candidate-v1.png'; os.makedirs(os.path.dirname(contactpath),exist_ok=True); contact.save(contactpath)
report={'schema_version':1,'scope':'candidate-only staging; no production writes','handoff_source':HANDOFF,'contact':contactpath,'contact_sha256':hashlib.sha256(open(contactpath,'rb').read()).hexdigest(),'objects':records}
json.dump(report,open(STAGE+'/core-dark-worktop6-candidate-report-v1.json','w'),indent=2)
print(json.dumps({'contact':contactpath,'contact_sha256':report['contact_sha256'],'objects':[{ 'id':r['object_id'],'candidate':r['candidate'],'crop':r['normalization']['crop_bounds_xyxy_px'],'scale':r['normalization']['isotropic_scale'],'bbox':r['normalization']['crop_bounds_xyxy_px'],'source_sha':r['canonical_source']['sha256']} for r in records]},indent=2))
