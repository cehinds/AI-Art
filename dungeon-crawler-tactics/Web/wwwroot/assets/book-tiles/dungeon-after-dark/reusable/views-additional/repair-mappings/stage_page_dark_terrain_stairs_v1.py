"""Stage terrain-stair view candidates by alpha-component extraction from six exact ImageGen responses."""
from pathlib import Path
import json,hashlib,copy,shutil
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parents[1];PACK=OUT.parent.parent
HAND=Path('/workspace/scratch/page-dark-future-six-terrain-stairs-handoff-v2-20261026.json')
CDIR=OUT/'candidates/page-dark-next-six-terrain-stairs-v1'; IMG=CDIR/'images';RAW=CDIR/'raw';PROMPT=CDIR/'prompts'
for p in (IMG,RAW,PROMPT):p.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def rel(p):return Path(p).resolve().relative_to(PACK.resolve()).as_posix()
def rgba(p):return Image.open(p).convert('RGBA')
def atomic(p,obj):Path(p).write_text(json.dumps(obj,indent=2)+'\n')
def components(raw,min_area=1000):
 im=rgba(raw);a=np.asarray(im)[:,:,3];labels,n=ndimage.label(a>=32);items=[]
 for i in range(1,n+1):
  if int((labels==i).sum())<min_area:continue
  ys,xs=np.where(labels==i);items.append({'i':i,'bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'area':int((labels==i).sum()),'cx':float(xs.mean()),'cy':float(ys.mean())})
 return im,labels,items
def crop_component(im,labels,item,halo=2):
 i=item['i'];main=labels==i;alpha=np.asarray(im)[:,:,3];keep=ndimage.binary_dilation(main,iterations=halo)&(alpha>0);ys,xs=np.where(keep);box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];arr=np.asarray(im).copy();arr[:,:,3]=np.where(keep,alpha,0).astype(np.uint8);return Image.fromarray(arr,'RGBA').crop(tuple(box)),box
def fit_canvas(crop,target_w,target_h,fit='contain'):
 w,h=crop.size;scale=min(target_w/w,target_h/h) if fit=='contain' else target_w/w
 nw=max(1,round(w*scale));nh=max(1,round(h*scale));im=crop.resize((nw,nh),Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256),(0,0,0,0));x=(256-nw)//2;y=(256-nh)//2;frame.alpha_composite(im,(x,y));return frame,{'uniform_scale':scale,'resized_dimensions_px':[nw,nh],'offset_px':[x,y],'anchor_px':[128,128],'resampling':'nearest'}
# Three exact prompts and returned response paths, bound to their request IDs.
groups=[
 {'id':'battlefield-earth-up-down','raw':'exec-53d18104-6a7f-4218-8a05-bb8501ad1529.png','request_id':'imagegen-battlefield-earth-up-down-20261026','prompt':"Create a clean orthographic sprite contact sheet, transparent background, exactly TWO rows by FOUR columns with wide transparent gutters, no labels or text. Row 1 depicts the supplied Battlefield EARTH STAIRS UP object; row 2 depicts its DOWN counterpart. Each row has four same-scale independent view sprites in this exact column order: RIGHT SIDE PROFILE, LEFT SIDE PROFILE, BOTTOM UNDERSIDE, REAR ELEVATION. Every view must show the complete same stair object. Side views must be full length stepped ramps with visible descending/rising treads, retaining brown packed-earth risers and timber/stone edge supports, not two vertical posts. Bottom views are opaque earthy support footprints with muted soil/stone texture, no top-facing stair channels. Rear views are solid full-height earth/stone support faces behind the steps, no upper treads showing through. Preserve each up/down identity from its source reference pair; source image 1/2 is UP identity and source image 3/4 is DOWN identity. No perspective, no isometric camera. Keep each sprite isolated and small enough to fit its invisible equal cell; use generous gutters, no cells touching."},
 {'id':'larracos-cobble-up-down','raw':'exec-2058fcfd-a29c-49cf-bde3-7f31bf786623.png','request_id':'imagegen-larracos-cobble-up-down-20261026','prompt':"Create a clean orthographic sprite contact sheet, transparent background, exactly TWO rows by FOUR columns with wide transparent gutters, no labels or text. Row 1 is the supplied Larracos COBBLESTONE STAIRS UP object; row 2 is its DOWN counterpart. Four same-scale independent view sprites per row in this exact column order: RIGHT SIDE PROFILE, LEFT SIDE PROFILE, BOTTOM UNDERSIDE, REAR ELEVATION. Side views are full depth stepped stone flights with visible steps and coherent common height, retaining source pale gray/green cobblestone, moss, and coral edge overhang only where supported. Bottom views show full opaque matching stone support footprints with flat stone surface, no upper tread channels. Rear views are full opaque stone support faces, never upper-facing steps visible through wedge. Preserve source up/down distinction, palette and pattern from image references (first pair UP, second pair DOWN). No perspective or isometric tilt. Each view isolated, generous transparent gutters, all equal scale, no labels, no cell collisions."},
 {'id':'cemetery-flagstone-up-down','raw':'exec-d9a26cd6-69ae-41da-9b30-c7202513474c.png','request_id':'imagegen-cemetery-flagstone-up-down-20261026','prompt':"Create a clean orthographic sprite contact sheet, transparent background, exactly TWO rows by FOUR columns with wide transparent gutters, no labels or text. Row 1 is the supplied Cemetery FLAGSTONE STAIRS UP; row 2 is the DOWN counterpart. Four same-scale independent view sprites per row in this exact column order: RIGHT SIDE PROFILE, LEFT SIDE PROFILE, BOTTOM UNDERSIDE, REAR ELEVATION. Side views are complete full-depth stepped flights with visible staircase rise and all steps, consistent height, retaining pale cemetery flagstone, dark seams, moss and source green-gray wear. Bottom views are full opaque stone support footprints, no top-facing tread pattern. Rear views are true full-height rear support faces with opaque stone backing, no upper steps visible through the base. Preserve up/down source identity from image pairs; first pair UP, second pair DOWN. No perspective or isometric. Keep each sprite separate with large transparent gutters, equal scale, no labels or overlap."},
 {'id':'battlefield-earth-rear','raw':'exec-cf888908-9ef7-4e90-b390-ac91702f40b5.png','request_id':'imagegen-battlefield-earth-rear-20261026','prompt':"Create exactly TWO separate orthographic REAR ELEVATION sprite views stacked vertically on transparent background with a wide transparent gap, no labels or text. Upper is Battlefield churned earth stairs UP; lower is DOWN, matching supplied source/reference pairs. Camera is horizontal and directly behind the staircase support. The back of each stair flight is one continuous broad earthy support/back wall with full ground-to-top height and complete width, with only the target's narrow source-supported wood/stone side framing at its ends. There must be NO visible treads, NO stair channels, NO stair fronts, NO sloped side elevation, and no top plan; the opposite rear camera must show a solid continuous earth/stone backing surface. Retain source brown churned soil, timber, dark metal joints and block count/material. Full silhouette, axis-aligned orthographic, no perspective/isometric."},
 {'id':'larracos-cobble-rear','raw':'exec-bb2e08dd-dac8-409b-93d0-4b1b3c5384ce.png','request_id':'imagegen-larracos-cobble-rear-20261026','prompt':"Create exactly TWO separate orthographic REAR ELEVATION sprite views stacked vertically on transparent background with a wide transparent gap, no labels or text. Upper is Larracos drained-city cobblestone stairs UP; lower is DOWN, matched to supplied source/reference pairs. Camera is horizontal and directly behind the complete stair support. Show a broad continuous full-height rear backing of pale gray-green masonry/cobblestone, with source-matched dark grout, moss and only the actual supported coral edge detail. NO visible stair treads, NO stair channels, NO front risers, NO sloped side profile, NO top-down face. A rear orthographic view must be a single opaque full-width backing face behind the steps. Keep full object width and common height like accepted side profiles. No perspective/isometric."},
 {'id':'cemetery-flagstone-rear','raw':'exec-8da0a943-83e6-4ab9-9a0f-ede1a3406b5c.png','request_id':'imagegen-cemetery-flagstone-rear-20261026','prompt':"Create exactly TWO separate orthographic REAR ELEVATION sprite views stacked vertically on transparent background with a wide transparent gap, no labels or text. Upper is Cemetery pale flagstone stairs UP; lower is DOWN. Match supplied source/reference pairs. Camera is horizontal and directly behind the entire stair support. Show a broad continuous full-height back face of pale cemetery stone with dark seams and source green-gray moss/wear, opaque across the stair opening. NO visible tread faces, NO stair channels, NO stair fronts, NO sloped side profile, and NO plan view. Rear camera should show the solid stone backing behind the flight, matching the accepted full-height scale. Axis-aligned orthographic, no perspective/isometric."}
]
# Verify handoff source and all-six, and capture current proof.
hand=json.loads(HAND.read_text());objmap={o['object_id']:o for o in hand['objects']};objects=[];contactrows=[]
for o in hand['objects']:
 source={'path':Path(o['source']['path']).resolve().relative_to(PACK.resolve()).as_posix(),'sha256':o['source']['sha256']};assert sha(safe(PACK,source['path']))==source['sha256']
 base={v:{'path':Path(x['path']).resolve().relative_to(PACK.resolve()).as_posix(),'sha256':x['sha256']} for v,x in o['views'].items()}
 for v,x in base.items():assert sha(safe(PACK,x['path']))==x['sha256'],(o['object_id'],v)
 objects.append({'object_id':o['object_id'],'source':source,'base_six':base,'affected_views':o['affected_views'],'notes':o['notes']})
# Copy raw/prompt records, component-segment and extract 4x2 atlases; per-side atlases contain the first three requested views.
raw_records=[];candidate_map={};target_front={};
for oid,o in objmap.items():
 a=Image.open(o['views']['front']['path']).convert('RGBA');box=a.getchannel('A').getbbox();target_front[oid]={'bbox':box,'width':box[2]-box[0],'height':box[3]-box[1]}
for group in groups:
 raw_src=Path('/workspace/generated_images')/group['raw'];assert raw_src.is_file();raw_dst=RAW/(group['id']+'.png');shutil.copyfile(raw_src,raw_dst)
 prompt_path=PROMPT/(group['id']+'.txt');prompt_path.write_text(group['prompt']+'\n')
 raw_records.append({'group_id':group['id'],'request_id':group['request_id'],'raw_path':rel(raw_dst),'raw_sha256':sha(raw_dst),'prompt_path':rel(prompt_path),'prompt_sha256':sha(prompt_path)})
 im,labels,items=components(raw_dst);assert len(items)==(8 if 'rear' not in group['id'] else 2),(group['id'],len(items))
 items=sorted(items,key=lambda x:(x['cy'],x['cx']))
 rows=[('up',items[:4]),('down',items[4:])] if len(items)==8 else [('up',items[:1]),('down',items[1:])]
 if len(items)==8:
  view_names=['right','left','bottom','rear']
 else:view_names=['rear']
 style=group['id'].split('-')[0]
 for rowname, comps in rows:
  oid=next(x for x in objmap if x.startswith({'battlefield':'faction-battlefield','larracos':'faction-larracos','cemetery':'ghost-cemetery'}[style]) and x.endswith('stairs-'+rowname))
  for col,item in enumerate(comps):
   v=view_names[col]
   if style=='larracos' and v in ('right','left'):
    continue  # handoff explicitly preserves Larracos RIGHT/LEFT
   crop,cropbox=crop_component(im,labels,item,halo=2)
   if v in ('right','left'):
    th=target_front[oid]['height'];targetw=225;scale=th/crop.height;w=round(crop.width*scale)
    # Use shared Z from accepted front and keep full projected depth; no independent axis scaling.
    frame,norm=fit_canvas(crop,targetw,th,fit='contain')
   elif v=='bottom':
    # Isotropic fit to the source-backed square footprint; center any remaining margin.
    frame,norm=fit_canvas(crop,205,205,fit='contain')
   else:
    fw,fh=target_front[oid]['width'],target_front[oid]['height'];frame,norm=fit_canvas(crop,fw,fh,fit='contain')
   path=IMG/(oid+'.'+v+'.candidate-v1.png');frame.save(path,format='PNG',optimize=False)
   candidate_map[(oid,v)]={'object_id':oid,'asset_id':oid+'.'+v,'view':v,'candidate_path':rel(path),'candidate_sha256':sha(path),'dimensions_px':[256,256],'anchor_px':[128,128],'source_path':next(x for x in objects if x['object_id']==oid)['source']['path'],'source_sha256':next(x for x in objects if x['object_id']==oid)['source']['sha256'],'baseline_six':copy.deepcopy(next(x for x in objects if x['object_id']==oid)['base_six']),'raw_path':rel(raw_dst),'raw_sha256':sha(raw_dst),'prompt_path':rel(prompt_path),'prompt_sha256':sha(prompt_path),'request_id':group['request_id'],'references':[next(x for x in objects if x['object_id']==oid)['source']['path'],next(x for x in objects if x['object_id']==oid)['base_six']['front']['path']],'extraction':{'alpha_threshold':32,'component_index':item['i'],'component_count':len(items),'component_bbox_xyxy':item['bbox'],'component_area':item['area'],'soft_alpha_halo_px':2,'crop_bbox_xyxy':cropbox},'normalization':norm,'notes':objmap[oid]['notes'][0]}
# Native source-backed plan reuse for Larracos and Cemetery TOP only.
for oid in [x for x in objmap if x.startswith('faction-larracos') or x.startswith('ghost-cemetery')]:
 objects_by_id={x['object_id']:x for x in objects};src=objects_by_id[oid]['source'];srcpath=safe(PACK,src['path']);im=rgba(srcpath);bbox=im.getchannel('A').getbbox();crop=im.crop(bbox);frame,normal=fit_canvas(crop,205,205,fit='contain');path=IMG/(oid+'.top.native-source-plan-v1.png');frame.save(path,format='PNG',optimize=False)
 candidate_map[(oid,'top')]={'object_id':oid,'asset_id':oid+'.top','view':'top','candidate_path':rel(path),'candidate_sha256':sha(path),'dimensions_px':[256,256],'anchor_px':[128,128],'source_path':src['path'],'source_sha256':src['sha256'],'baseline_six':copy.deepcopy(objects_by_id[oid]['base_six']),'derived_from':{'kind':'canonical_native_plan_reuse','source_path':src['path'],'source_sha256':src['sha256'],'source_alpha_bbox_xyxy':list(bbox)},'normalization':{'source_alpha_bbox_xyxy':list(bbox),'source_crop_dimensions_px':list(crop.size),**normal},'notes':'Canonical hybrid source used as the already-authentic stair plan; uniformly normalized, no foreign pixels.'}
# Build contact with source, six current views, then every candidate scoped to the row.
contact=Image.new('RGBA',(200*12,220*6),(13,16,21,255));proofrows=[]
for ri,o in enumerate(objects):
 oid=o['object_id'];cells=[];ordered=[('SOURCE',o['source'])]+[(v,o['base_six'][v]) for v in ['front','top','right','left','bottom','rear']]+[(v.upper()+' NEW',{'path':c['candidate_path'],'sha256':c['candidate_sha256']}) for (co,v),c in candidate_map.items() if co==oid]
 for ci,(lab,rec) in enumerate(ordered):
  p=safe(PACK,rec['path']);assert sha(p)==rec['sha256'],(oid,lab)
  im=rgba(p);im.thumbnail((180,180),Image.Resampling.NEAREST);tile=Image.new('RGBA',(200,220),(31,34,39,255));tile.alpha_composite(im,((200-im.width)//2,8+(180-im.height)//2));ImageDraw.Draw(tile).text((4,195),lab,fill='white');contact.alpha_composite(tile,(ci*200,ri*220));cells.append({'label':lab,**rec})
 proofrows.append({'object_id':oid,'cells':cells})
contactpath=CDIR/'terrain-stairs-source-six-candidates.png';contact.save(contactpath)
manifest={'status':'candidate-only; Page review requested','scope':'six terrain stair objects; 24 directions','handoff_id':'page-dark-future-six-terrain-stairs-handoff-v2-20261026.json','handoff_sha256':sha(HAND),'objects':objects,'raw_requests':raw_records,'candidates':list(candidate_map.values()),'candidate_contact_path':rel(contactpath),'candidate_contact_sha256':sha(contactpath),'rules':['Per-object canonical source and all-six current hashes were validated before staging.','The four output components per atlas are mapped by measured alpha-component centers in row-major order; no fixed-grid clipping.','No anisotropic scaling; all candidate crops use one uniform factor and remain centered in transparent 256x256 RGBA frames.','Native top plans are copied from their own source only for Larracos and Cemetery; Battlefield TOP is preserved unchanged.']}
mp=CDIR/'terrain-stairs-candidate-manifest-v1.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');proof={'manifest_path':rel(mp),'manifest_sha256':sha(mp),'contact_path':rel(contactpath),'contact_sha256':sha(contactpath),'rows':proofrows};(CDIR/'terrain-stairs-candidate-contact-proof-v1.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'manifest':rel(mp),'manifest_sha256':sha(mp),'contact':rel(contactpath),'contact_sha256':sha(contactpath),'candidates':len(candidate_map),'raw_requests':len(raw_records)},indent=2))
