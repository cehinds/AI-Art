from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,shutil,os
import numpy as np
from scipy import ndimage
H=Path(__file__).resolve().parent; PACK=H.parents[3]; OID='bubble-sea-submarine-metal-hull-wall-northeast'; REPORT=H/'staged-wall-candidates.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
# Request-specific raw atlas from image_gen response output_hint.
REQ='exec-34cb428b-d9ac-4051-8011-e76b4fcc30ef'
ATLAS=Path('/workspace/generated_images')/(REQ+'.png')
raw_dir=H/'raw';raw_dir.mkdir(exist_ok=True);raw=raw_dir/'bubble-sea-plain-broadfaces-atlas.png'
if not raw.exists():shutil.copy2(ATLAS,raw)
raw_sha=sha(raw.read_bytes())
report=json.loads(REPORT.read_text());s=next(x for x in report['sets'] if x['object_id']==OID)
# Guard target primary and same-kit geometric guide files before use.
HAND=json.loads(Path('/workspace/scratch/inkbook-core-ne-wall-staging-handoff.json').read_text());item=next(x for x in HAND['sets'] if x['object_id']==OID)
if sha((PACK/item['source']['path']).read_bytes())!=item['source']['sha256']:raise SystemExit('canonical target source changed')
for v,c in item['current_views'].items():
 if sha((PACK/c['path']).read_bytes())!=c['sha256']:raise SystemExit(f'live view changed: {OID}.{v}')
# Atlas has two large connected opaque views. Isolate global alpha components, not nominal grid crops.
a=np.array(Image.open(raw).convert('RGBA')); alpha=a[:,:,3]; labels,n=ndimage.label(alpha>16); objs=ndimage.find_objects(labels)
components=[]
for idx,sl in enumerate(objs,1):
 if sl is None:continue
 area=int((labels[sl]==idx).sum())
 if area>10000:components.append((area,idx,sl))
components.sort(reverse=True)
if len(components)!=2:raise SystemExit(f'expected exactly two main views; found {[x[0] for x in components]}')
# Keep left/right source positions so both individually painted plain faces are preserved.
components.sort(key=lambda x:x[2][1].start)
# Match accepted same-kit broad-face common Z, not raw atlas scale.
refpath=H/s['candidates']['right']['candidate_path']; ref=Image.open(refpath).convert('RGBA'); refbbox=ref.getchannel('A').getbbox();target_z=refbbox[3]-refbbox[1]
rows={}
for v,entry in zip(('right','left'),components):
 area,idx,sl=entry; box=(sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)
 cell=Image.fromarray(a,'RGBA').crop(box); b=cell.getchannel('A').getbbox()
 cell=cell.crop(b); scale=target_z/cell.height; nw=max(1,round(cell.width*scale));nh=max(1,round(cell.height*scale))
 resized=cell.resize((nw,nh),Image.Resampling.NEAREST)
 canvas=Image.new('RGBA',(256,256),(0,0,0,0));off=(128-nw//2,128-nh//2);canvas.alpha_composite(resized,off)
 out=H/'candidates'/f'{OID}.{v}.candidate.png';canvas.save(out,optimize=False);bb=canvas.getchannel('A').getbbox()
 live=PACK/s['current_views'][v]['path']; live_bytes=live.read_bytes()
 if sha(live_bytes)!=s['current_views'][v]['sha256']:raise SystemExit(f'live view mismatch {v}')
 guide_id=s['nw_guide_id']; merged=json.loads(Path('/workspace/scratch/view-review-merged.json').read_text());lib=next(x for x in merged['libraries'] if x['scope']=='book-tiles/ink-and-lanterns');guide=next(x for x in lib['sets'] if x['object_id']==guide_id)
 guide_path=guide['views']['front' if v=='right' else 'rear']['path']; guide_sha=guide['views']['front' if v=='right' else 'rear']['sha256']
 rows[v]={'candidate_path':str(out.relative_to(H)),'candidate_sha256':sha(out.read_bytes()),'candidate_rgba_sha256':hashlib.sha256(canvas.tobytes()).hexdigest(),'size':[256,256],'alpha_bbox_xyxy':list(bb),'raw_atlas_path':str(raw.relative_to(H)),'raw_atlas_sha256':raw_sha,'raw_component_bbox_xyxy':list(box),'raw_component_alpha_bbox_xyxy':list((box[0]+b[0],box[1]+b[1],box[0]+b[2],box[1]+b[3])),'raw_component_area_alpha16':area,'uniform_scale':scale,'target_z_px':target_z,'resized_wh':[nw,nh],'canvas_offset_xy':list(off),'derivation':{'method':'generated-inferred-plain-broad-face','request_id':REQ,'prompt':'See adjacent bubble-sea-plain-broadfaces-request.json','source_image':item['source']['path'],'source_sha256':item['source']['sha256'],'guide_object_id':guide_id,'guide_path':guide_path,'guide_sha256':guide_sha,'target_same_kit_height_reference':{'path':s['candidates']['right']['candidate_path'],'sha256':s['candidates']['right']['candidate_sha256']},'binding':'Own canonical NE source remains authoritative; generated unseen plain surface follows same-kit dark riveted metal materials; no unsupported amber porthole.'},'note':'Generated plain riveted broad face, uniformly calibrated to accepted common wall Z; no porthole/window.'}
 s['candidates'][v]=rows[v]
# source+old six+candidate/keep six contact
panels=[('SOURCE',PACK/item['source']['path'])]
for v in ('front','top','right','left','bottom','rear'):panels.append(('OLD-'+v.upper(),PACK/s['current_views'][v]['path']))
for v in ('front','top','right','left','bottom','rear'):
 c=s['candidates'].get(v);panels.append((('CAND-' if v in s['candidates'] else 'KEEP-')+v.upper(),H/c['candidate_path'] if v in s['candidates'] else PACK/s['current_views'][v]['path']))
out=H/'ne-wall-bubble-sea-plain-broadface-candidates.png';contact=Image.new('RGBA',(len(panels)*170,340),(44,44,48,255));d=ImageDraw.Draw(contact)
for i,(label,path) in enumerate(panels):
 im=Image.open(path).convert('RGBA');im.thumbnail((136,280),Image.Resampling.NEAREST);contact.alpha_composite(im,(i*170+17+(136-im.width)//2,38+(280-im.height)//2));d.text((i*170+3,20),label,fill='white')
contact.save(out,optimize=False);s['contact_path']=str(out.relative_to(H));s['contact_sha256']=sha(out.read_bytes())
tmp=REPORT.with_suffix('.json.tmp');tmp.write_text(json.dumps(report,indent=2)+'\n');os.replace(tmp,REPORT)
print(json.dumps({'object_id':OID,'raw_atlas':str(raw),'raw_atlas_sha256':raw_sha,'target_common_z_px':target_z,'staged':rows,'contact':str(out),'contact_sha256':s['contact_sha256']},indent=2))
