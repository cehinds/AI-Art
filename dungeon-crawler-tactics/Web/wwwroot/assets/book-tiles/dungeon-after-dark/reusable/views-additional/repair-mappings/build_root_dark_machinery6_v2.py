"""Rebuild Root machinery6 v2 candidates from retained raw response PNGs with isotropic scale only."""
from pathlib import Path
import json,hashlib,copy
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;R=HERE.parent;PACK=R.parent.parent;RAW=R/'raw/root-dark-machinery6-20261026';OUT=R/'candidates/root-dark-machinery6-v2';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def extract(raw):
 im=Image.open(raw).convert('RGBA'); a=np.array(im.getchannel('A')); assert a.min()<255,'opaque generated background: '+str(raw)
 mask=a>=64; lab,n=ndimage.label(mask,structure=np.ones((3,3),dtype=np.uint8)); counts=np.bincount(lab.ravel());counts[0]=0;idx=int(counts.argmax()); main=(lab==idx);keep=ndimage.binary_dilation(main,iterations=2); yy,xx=np.where(keep); box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)); rgba=np.array(im);rgba[:,:,3]=np.where(keep,a,0).astype('uint8');return Image.fromarray(rgba,'RGBA').crop(box),box,n,int(counts[idx])
def render(raw,target_h,bottom,flip=False):
 crop,bbox,n,area=extract(raw)
 if flip:crop=crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 scale=target_h/crop.height;nw=round(crop.width*scale);nh=round(crop.height*scale);crop=crop.resize((nw,nh),Image.Resampling.NEAREST)
 assert nw<=256 and nh<=256,(nw,nh)
 can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(crop,(round(128-nw/2),bottom-nh));return can,{'raw_alpha_bbox_xyxy':list(bbox),'connected_components':int(n),'selected_component_area':area,'uniform_scale':scale,'resized_dimensions':[nw,nh],'offset_px':[round(128-nw/2),bottom-nh],'anchor_px':[128,bottom],'distortion':'none','resampling':'nearest'}
# Input object/direction, exact raw response, common world-Z projected height and shared groundline.
plans={
('iron-tracks-rail-buffer-stop','front'):('rail-front.png',126,202),('iron-tracks-rail-buffer-stop','rear'):('rail-rear.png',126,202),
('iron-tracks-rail-signal-mast','front'):('signal-front.png',201,230),
('iron-tracks-track-switch-lever','front'):('switch-front-v2.png',201,229),('iron-tracks-track-switch-lever','rear'):('switch-rear-v2.png',201,229),('iron-tracks-track-switch-lever','right'):('lever-right.png',201,229),('iron-tracks-track-switch-lever','left'):('lever-left.png',201,229),
('iron-tracks-tunnel-ventilation-fan','front'):('fan-front.png',175,215),('iron-tracks-tunnel-ventilation-fan','rear'):('fan-rear.png',175,215),
('iron-trains-open-service-hatch','rear'):('hatch-rear.png',144,200),
('early-arenas-huge-rubbish-heap','right'):('heap-right.png',144,200)}
entries=[]
for (oid,v),(rawname,h,bottom) in plans.items():
 raw=RAW/rawname;im,norm=render(raw,h,bottom);name=f'{oid}.{v}.png';dst=OUT/name;im.save(dst,optimize=False)
 entries.append({'object_id':oid,'view':v,'candidate_path':dst.relative_to(R).as_posix(),'candidate_sha256':sha(dst),'raw_path':raw.relative_to(PACK).as_posix(),'raw_sha256':sha(raw),'normalization':norm,'method':'imagegen orthographic candidate with transparent foreground extraction and uniform height calibration','tool_request_id':None,'request_label':raw.stem})
# Hatch TOP is calibrated isotropically from staged v1 TOP to measured existing plan span 187x145.
prev=R/'candidates/root-dark-machinery6-v1/iron-trains-open-service-hatch.top.png'; im=Image.open(prev).convert('RGBA'); bb=im.getchannel('A').getbbox();crop=im.crop(bb);scale=187/crop.width;nw=187;nh=round(crop.height*scale); assert abs(nh-145)<=8
crop=crop.resize((nw,nh),Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(crop,(round(128-nw/2),round(128-nh/2)));dst=OUT/'iron-trains-open-service-hatch.top.png';can.save(dst,optimize=False)
entries.append({'object_id':'iron-trains-open-service-hatch','view':'top','candidate_path':dst.relative_to(R).as_posix(),'candidate_sha256':sha(dst),'raw_path':prev.relative_to(R).as_posix(),'raw_sha256':sha(prev),'normalization':{'method':'uniform fit to accepted same-target plan width','uniform_scale':scale,'resized_dimensions':[nw,nh],'anchor_px':[128,128],'resampling':'nearest','distortion':'none'},'derived_from_candidate_path':prev.relative_to(R).as_posix(),'derived_from_candidate_sha256':sha(prev),'tool_request_id':None})
# Exact same-source opposite heap-side texture inference: mirror only RIGHT candidate, uniform 144px Z already applied.
right=OUT/'early-arenas-huge-rubbish-heap.right.png'; base=Image.open(right).convert('RGBA'); left=base.transpose(Image.Transpose.FLIP_LEFT_RIGHT);dst=OUT/'early-arenas-huge-rubbish-heap.left.png';left.save(dst,optimize=False)
entries.append({'object_id':'early-arenas-huge-rubbish-heap','view':'left','candidate_path':dst.relative_to(R).as_posix(),'candidate_sha256':sha(dst),'raw_path':(RAW/'heap-left.png').relative_to(PACK).as_posix(),'raw_sha256':sha(RAW/'heap-left.png'),'normalization':{'method':'same-target mirrored opposite side from accepted-source-guided RIGHT candidate; uniform scale inherited','mirror':'horizontal','distortion':'none'},'derived_from_candidate_path':right.relative_to(R).as_posix(),'derived_from_candidate_sha256':sha(right),'tool_request_id':None,'notes':'Opposite-side heap texture is inferred by same-object symmetry; underlying piece layout is not claimed recovered.'})
# Preserve accepted FAN TOP exact rigid rotation from v1.
f=R/'candidates/root-dark-machinery6-v1/iron-tracks-tunnel-ventilation-fan.top.png'; dst=OUT/'iron-tracks-tunnel-ventilation-fan.top.png';Image.open(f).save(dst);entries.append({'object_id':'iron-tracks-tunnel-ventilation-fan','view':'top','candidate_path':dst.relative_to(R).as_posix(),'candidate_sha256':sha(dst),'raw_path':(RAW/'fan-top-existing-live.png').relative_to(PACK).as_posix(),'raw_sha256':sha(RAW/'fan-top-existing-live.png'),'normalization':{'method':'same accepted exact source TOP rigid rotation 90 degrees clockwise; no resize','rotation_degrees_clockwise':90,'distortion':'none'},'derived_from_candidate_path':f.relative_to(R).as_posix(),'derived_from_candidate_sha256':sha(f),'tool_request_id':None})
# Exact prompts/response mapping for the two v2 switch requests (local API labels only; no tool request ID was returned).
exact_prompts={
'switch-front-v2':'Orthographic FRONT elevation of the exact supplied Iron Tracks switch lever. Preserve the existing source pose: red lever tilted diagonally about 45 degrees up toward world-X RIGHT, matching the canonical top-view axis direction. Show the broad front mechanism face and its level rectangular base, full Z height comparable to the existing right/left views. Do not flatten the lever to horizontal; do not add the far-side housing or perspective. Pixel-art metal palette, isolated on transparent background.',
'switch-rear-v2':'Orthographic REAR elevation of the exact supplied Iron Tracks switch lever. Show the same full-height broad mechanism backside and base; the red lever tilts diagonally about 45 degrees up toward world-X LEFT, opposite its canonical top/front direction. Keep the same lever angle and Z scale as the FRONT; no horizontal flattening, no perspective, no added far-side housing. Pixel-art metal palette, isolated on transparent background.'}
request_map=[]
for key,prompt in exact_prompts.items():
 pp=R/'prompts'/(key+'.txt');pp.write_text(prompt+'\n');raw=RAW/(key+'.png');request_map.append({'local_request_label':key,'tool_request_id':None,'tool_request_id_status':'not returned by imagegen API','prompt_path':pp.relative_to(PACK).as_posix(),'prompt_sha256':sha(pp),'raw_response_path':raw.relative_to(PACK).as_posix(),'raw_response_sha256':sha(raw),'returned_generated_output_filename':{'switch-front-v2':'exec-f9c04cce-eaf1-45ed-b479-286e31f0c360.png','switch-rear-v2':'exec-7fce70e6-22fe-4efc-bda0-907956582abd.png'}[key]})
for e in entries:
 if e.get('request_label') in exact_prompts:
  key=e['request_label'];e['prompt_path']=(R/'prompts'/(key+'.txt')).relative_to(PACK).as_posix();e['prompt_sha256']=sha(R/'prompts'/(key+'.txt'));e['request_label']=key;e['tool_request_id']=None;e['request_id_status']='not returned by imagegen API'
(RAW/'request-result-mapping-v2.json').write_text(json.dumps(request_map,indent=2)+'\n')
# Source and current-six hash guards are copied from the active handoff; every row remains target-specific.
h=json.load(open('/workspace/scratch/root-dark-next-six-machinery-handoff-20261026.json'));objmap={o['object_id']:o for o in h['objects']}
for e in entries:
 o=objmap[e['object_id']];e['canonical_source_image']=str(Path(o['source']['path']).relative_to(PACK));e['canonical_source_sha256']=o['source']['sha256'];e['base_six']={v:{'path':str(Path(q['path']).relative_to(PACK)),'sha256':q['sha256']} for v,q in o['views'].items()}
manifest={'schema_version':1,'status':'candidate-only; Root review required','candidate_id':'root-dark-machinery6-v2','candidate_owner':'views_dark_books','reviewer':'root','installer':'views_dark_books','scope':'book-tiles/dungeon-after-dark','source_and_six_proof_path':'reusable/views-additional/qa/root-dark-machinery6-v1-source-six.json','source_and_six_proof_sha256':sha(R/'qa/root-dark-machinery6-v1-source-six.json'),'candidate_contact_path':'reusable/views-additional/qa/root-dark-machinery6-v2-source-six-candidates.png','objects':entries,'path_convention':'all paths pack-relative unless under assets folder as given','notes':'Fan TOP was accepted by Root in v1; preserved unchanged. All dimension corrections use one uniform scale per leaf. Prompt text is retained where captured; original v1 prompts are reconstructed and request IDs unavailable.'}
mp=OUT/'root-dark-machinery6-v2-candidate-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');print(mp,sha(mp),len(entries))
for e in entries:print(e['object_id'],e['view'],e['candidate_sha256'])
