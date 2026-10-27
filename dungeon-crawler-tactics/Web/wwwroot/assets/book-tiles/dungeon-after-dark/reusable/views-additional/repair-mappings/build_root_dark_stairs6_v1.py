"""Build source-bound stair candidates from retained raw imagegen outputs; no live outputs are edited."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;R=HERE.parent;PACK=R.parent.parent;RAW=R/'raw/root-dark-stairs6-20261026';PROMPTS=R/'prompts/root-dark-stairs6-20261026';OUT=R/'candidates/root-dark-stairs6-v1';OUT.mkdir(parents=True,exist_ok=True);PROMPTS.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def extract(path):
 im=Image.open(path).convert('RGBA');a=np.array(im.getchannel('A'));assert a.min()<255,'opaque background '+str(path);mask=a>=64;lab,n=ndimage.label(mask,structure=np.ones((3,3),dtype=np.uint8));counts=np.bincount(lab.ravel());counts[0]=0;idx=int(counts.argmax());main=lab==idx;keep=ndimage.binary_dilation(main,iterations=1);yy,xx=np.where(keep);bbox=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));rgba=np.array(im);rgba[:,:,3]=np.where(keep,a,0).astype('uint8');return Image.fromarray(rgba,'RGBA').crop(bbox),bbox,n,int(counts[idx])
def fit(path,target_w,target_h,anchor,center=True):
 crop,bbox,n,area=extract(path);scale=min(target_w/crop.width,target_h/crop.height);nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale));crop=crop.resize((nw,nh),Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));x=round(anchor[0]-nw/2);y=round(anchor[1]-nh/2) if center else anchor[1]-nh;can.alpha_composite(crop,(x,y));return can,{'raw_alpha_bbox_xyxy':list(bbox),'connected_components':n,'selected_component_area':area,'uniform_scale':scale,'resized_dimensions':[nw,nh],'offset_px':[x,y],'anchor_px':list(anchor),'distortion':'none','resampling':'nearest'}
def height_fit(path,target_h,bottom):
 crop,bbox,n,area=extract(path);scale=target_h/crop.height;nw=round(crop.width*scale);nh=round(crop.height*scale);assert nw<=256 and nh<=256,(nw,nh);crop=crop.resize((nw,nh),Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));x=round((256-nw)/2);y=bottom-nh;can.alpha_composite(crop,(x,y));return can,{'raw_alpha_bbox_xyxy':list(bbox),'connected_components':n,'selected_component_area':area,'uniform_scale':scale,'resized_dimensions':[nw,nh],'offset_px':[x,y],'anchor_px':[128,bottom],'distortion':'none','resampling':'nearest'}
# Exact generated response filename mapping recorded per completed imagegen call.
returned={
'havana-up-right':'exec-cc65d0e3-5c10-4df3-8313-a4c23b38d965.png','havana-up-right-v2':'exec-68d92518-a4c5-4c29-96f6-f186febb354c.png','havana-down-right':'exec-61f03fd5-76f0-42b9-bb26-95de7c91fcd7.png','havana-down-right-v2':'exec-26812ae3-a77c-4d40-8936-25e5494ed650.png','havana-down-right-v3':'exec-03129551-1697-49f5-8c4d-497f60acc48a.png',
'diner-up-right':'exec-dba39a32-6d22-439a-8365-d68f52e00d24.png','diner-down-right':'exec-b0bfab1e-ee02-4302-b7c7-6db741c082d3.png','diner-up-right-v2':'exec-e14f0f43-c2e4-47da-b5c8-72af1d66643c.png','diner-down-right-v2':'exec-c2b40c1a-1b67-4240-9db4-721577a59936.png','diner-down-right-v3':'exec-22b74614-7bd7-473b-a4a5-3f340e4b7dcc.png',
'larracos-right':'exec-11e69021-519d-436f-ac2b-dc3f8fc93f00.png','glass-descent-right':'exec-e58c322d-da63-4a64-b109-6d1656f0d5f7.png','havana-up-rear':'exec-69532982-294c-4ddc-8b52-d9530b3f070f.png','havana-down-rear':'exec-c2030a95-59f9-4909-adb6-f7c3188633db.png','diner-up-rear':'exec-9e4d3636-d34b-4ed1-be8f-9f059afc4f20.png','havana-up-rear-v2':'exec-e96e616e-46eb-4d79-be48-81c996e61759.png','havana-down-rear-v2':'exec-03487524-3546-4fdd-9e08-9e99dbab5b93.png','diner-down-rear':'exec-e91a0dc7-311e-4cda-aeb3-a26256edd3ad.png','larracos-rear':'exec-b60db19e-8b72-4df6-b51a-59a8efcd82a0.png','glass-descent-rear':'exec-4fc2f084-dee5-4eea-a2e6-b365da128240.png','havana-up-bottom':'exec-9a3a9cfb-293b-40ac-bfb4-7386fbb47557.png','havana-down-bottom':'exec-99c15096-2fd0-4641-b6c4-d7be3b3455a9.png','glass-descent-bottom':'exec-11b95b33-df28-4da6-ae13-0833fcd217a5.png','larracos-rear-v2':'exec-5a5bfad0-955d-4dd7-801a-eaf9d6780476.png'}
for key,filename in returned.items():
 raw=RAW/(key+'.png');assert raw.is_file(),key
 # Exact final prompts are retained in adjacent raw .txt files, then copied into pack prompts folder.
 pp=RAW/(key+'.txt')
 if pp.exists():shutil.copy2(pp,PROMPTS/(key+'.txt'))
mp=json.load(open('/workspace/scratch/root-dark-next-six-stairs-handoff-20261026.json'));obj={o['object_id']:o for o in mp['objects']}
# Side profile targets derive directly from accepted sibling Z/front and Y/top bounds measured at alpha >=64.
plans={
'ghost-havana-colonial-street-paving-stairs-up':{'side':('havana-up-right-v2',167,211),'rear':('havana-up-rear-v2',167,211),'bottom':('havana-up-bottom',182,166)},
'ghost-havana-colonial-street-paving-stairs-down':{'side':('havana-down-right-v3',169,213),'rear':('havana-down-rear-v2',169,213),'bottom':('havana-down-bottom',183,171)},
'safe-services-diner-checker-tile-stairs-up':{'side':('diner-up-right-v2',151,203),'rear':('diner-up-rear',151,203)},
'safe-services-diner-checker-tile-stairs-down':{'side':('diner-down-right-v3',154,205),'rear':('diner-down-rear',154,205)},
'faction-larracos-tiered-city-stairway':{'side':('larracos-right',158,207),'rear':('larracos-rear-v2',157,206)},
'great-race-transition-glass-descent-steps':{'side':('glass-descent-right',160,208),'rear':('glass-descent-rear',159,208),'bottom':('glass-descent-bottom',195,175)}}
# Collect directions in exact handoff order. Side profiles have mirrored opposite-camera aliases.
entries=[]
def emit(oid,v,rawkey,kind,tw=None,th=None,bottom=None,mirror=False,derived=None):
 raw=RAW/(rawkey+'.png')
 if kind=='footprint':im,norm=fit(raw,tw,th,(128,128),True)
 else:im,norm=height_fit(raw,th,bottom)
 if mirror:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 dst=OUT/(oid+'.'+v+'.png');im.save(dst,optimize=False)
 src=obj[oid];vmeta=src['views'];
 e={'object_id':oid,'view':v,'candidate_path':dst.relative_to(PACK).as_posix(),'candidate_sha256':sha(dst),'canonical_source_image':Path(src['source']['path']).relative_to(PACK).as_posix(),'canonical_source_sha256':src['source']['sha256'],'base_six':{vv:{'path':Path(b['path']).relative_to(PACK).as_posix(),'sha256':b['sha256']} for vv,b in vmeta.items()},'raw_path':(RAW/(rawkey+'.png')).relative_to(PACK).as_posix(),'raw_sha256':sha(raw),'normalization':norm,'tool_request_id':None,'returned_generated_output_filename':returned.get(rawkey),'notes':'Perspective-free orthographic illustration; hidden/support geometry inferred.'}
 prompt=RAW/(rawkey+'.txt')
 if prompt.exists(): e['prompt_path']=(PROMPTS/(rawkey+'.txt')).relative_to(PACK).as_posix();e['prompt_sha256']=sha(PROMPTS/(rawkey+'.txt'))
 if derived:e['derived_from_candidate_path']=derived['path'];e['derived_from_candidate_sha256']=derived['sha'];e['notes']+=' Opposite side is an explicitly inferred horizontal mirror of the same target side; underlying symmetry is illustrative.'
 e['target_dimensions_from_alpha64']={'profile_height_from_accepted_front_px':th,'baseline_px':bottom,'plan_width_from_accepted_top_px':tw,'plan_depth_from_accepted_top_px':th if kind=='footprint' else None}
 entries.append(e);return {'path':dst.relative_to(R).as_posix(),'sha':sha(dst)}
for oid,p in plans.items():
 s=p['side']
 if s:
  name,h,b=s; target_depth=obj[oid]['views']['top']['path']; # dimensions measured from accepted source-index PNGs below at review time
  emit(oid,'right',name,'profile',th=h,bottom=b)
  right=entries[-1];emit(oid,'left',name,'profile',th=h,bottom=b,mirror=True,derived={'path':right['candidate_path'],'sha':right['candidate_sha256']})
 rear=p.get('rear')
 if rear:
  name,h,b=rear;emit(oid,'rear',name,'profile',th=h,bottom=b)
 bottom=p.get('bottom')
 if bottom:
  name,w,h=bottom;emit(oid,'bottom',name,'footprint',tw=w,th=h)
# Exact proof copy; hash-bound to fresh Root source+six proof.
proof_src=Path('/tmp/root133-dark-stairs6.png.json');proof_dst=R/'qa/root-dark-stairs6-v1-source-six.json';proof_dst.parent.mkdir(exist_ok=True)
if not proof_dst.exists():shutil.copy2(proof_src,proof_dst)
manifest={'schema_version':1,'candidate_id':'root-dark-stairs6-v1','status':'candidate-only; Root visual decision required','candidate_owner':'views_dark_books','reviewer':'root','installer':'views_dark_books','scope':'book-tiles/dungeon-after-dark','source_and_six_proof_path':proof_dst.relative_to(PACK).as_posix(),'source_and_six_proof_sha256':sha(proof_dst),'objects':entries,'path_convention':'All paths are relative to book-tiles/dungeon-after-dark.','notes':'All generated requests have tool_request_id:null because the imagegen API did not return request IDs; exact returned PNG filename mappings are retained in raw/request-result-mapping-v1.json. Prompt text is preserved verbatim for each completed call. Isotropic scales use accepted current alpha64 dimensions; mirrored opposite side views are explicitly inferred.'}
(RAW/'request-result-mapping-v1.json').write_text(json.dumps([{'local_request_label':k,'tool_request_id':None,'tool_request_id_status':'not returned','returned_generated_output_filename':v,'raw_path':(RAW/(k+'.png')).relative_to(PACK).as_posix(),'raw_sha256':sha(RAW/(k+'.png')),'prompt_path':(PROMPTS/(k+'.txt')).relative_to(PACK).as_posix() if (PROMPTS/(k+'.txt')).exists() else None,'prompt_sha256':sha(PROMPTS/(k+'.txt')) if (PROMPTS/(k+'.txt')).exists() else None} for k,v in returned.items()],indent=2)+'\n')
mpath=OUT/'root-dark-stairs6-v1-candidate-manifest.json';mpath.write_text(json.dumps(manifest,indent=2)+'\n')
print('MANIFEST',mpath,sha(mpath),'CANDIDATES',len(entries))
for e in entries:print(e['object_id'],e['view'],e['candidate_sha256'],e['normalization'].get('resized_dimensions'))
