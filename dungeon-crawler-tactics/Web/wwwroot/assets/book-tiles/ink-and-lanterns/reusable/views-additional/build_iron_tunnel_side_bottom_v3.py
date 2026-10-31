"""Stage orthogonal tunnel sides and a rigidly rotated underside candidate."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageOps
import numpy as np
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];OID='iron-tracks-tunnel-portal-frame';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();idx=json.loads((OUT/'set-index.json').read_text());assets={a['id']:a for a in idx['assets']};g=next(x for x in idx['view_sets'] if x['object_id']==OID);source=PACK/'iron-tracks/components/iron-tracks-tunnel-portal-frame.png';cand={};recipes={}
def alpha_crop(im,threshold=245):
 a=np.array(im.convert('RGBA'));m=a[:,:,3]>=threshold;y,x=np.where(m)
 if not len(x):raise ValueError('empty')
 box=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1));return Image.fromarray(a).crop(box),box
def make(view,crop,scale,transform,extra):
 sz=(round(crop.width*scale),round(crop.height*scale));res=crop.resize(sz,Image.Resampling.NEAREST);xy=((256-sz[0])//2,(256-sz[1])//2);can=Image.new('RGBA',(256,256));can.alpha_composite(res,xy);p=OUT/'raw'/f'{OID}.{view}.candidate-v3.png';can.save(p);return {'path':p.relative_to(PACK).as_posix(),'sha256':sha(p),'resized_wh':list(sz),'offset_xy':list(xy),'uniform_scale':scale,'resampler':'NEAREST','transform':transform,**extra}
# Keep Root-scoped-accepted three candidates exactly byte-identical.
for v in ('front','top','rear'):
 p=OUT/'raw'/f'{OID}.{v}.candidate-v2.png';cand[v]={'path':p.relative_to(PACK).as_posix(),'sha256':sha(p),'reuse':'root-accepted-v2 candidate unchanged'}
# Strip only the arch-mouth face/foreshortened rail exit from the right-side art; retain wall end blocks.
right=Image.open(OUT/'raw'/f'{OID}.right.candidate-v2.png').convert('RGBA').crop((60,0,230,256));right,rb=alpha_crop(right);rscale=196/right.width;cand['right']=make('right',right,rscale,'crop-to-flat-wall-profile; uniform scale to TOP Y span',{ 'original_candidate':'reusable/views-additional/raw/iron-tracks-tunnel-portal-frame.right.candidate-v2.png','original_sha256':sha(OUT/'raw'/f'{OID}.right.candidate-v2.png'),'crop_bbox_xyxy_in_original':[60+rb[0],rb[1],60+rb[2],rb[3]],'geometry_note':'Removed facing arch mouth and foreshortened rail exit while retaining edge stone blocks and thin lantern edge.'})
# Opposite camera side uses exact horizontal mirror of the flat wall profile.
left=ImageOps.mirror(right);cand['left']=make('left',left,rscale,'horizontal mirror of right; same-object tunnel symmetry',{'donor_view':'right','donor_sha256':cand['right']['sha256'],'geometry_note':'Same masonry side profile seen from the opposite orthographic camera.'})
# Rotate the existing horizontal underside strip rigidly 90 degrees; uniformly fit long Y to accepted TOP depth.
bot0=Image.open(OUT/'raw'/f'{OID}.bottom.candidate-v2.png').convert('RGBA');botcrop,bb=alpha_crop(bot0);rot=botcrop.rotate(90,expand=True);bscale=196/rot.height;cand['bottom']=make('bottom',rot,bscale,'rigid_rotation_ccw_90_then_uniform_fit_to_TOP_Y',{ 'donor_view':'bottom-v2','donor_path':'reusable/views-additional/raw/iron-tracks-tunnel-portal-frame.bottom.candidate-v2.png','donor_sha256':sha(OUT/'raw'/f'{OID}.bottom.candidate-v2.png'),'crop_bbox_xyxy_in_donor':list(bb),'geometry_note':'Rigid 90-degree rotation corrects long-X to long-Y; uniform scale matches accepted TOP longitudinal span.'})
# canonical contact: accepted F/T/REAR plus new R/L/B, all source bound.
sheet=Image.new('RGB',(7*220,236),(239,235,226));d=ImageDraw.Draw(sheet);paths=[source]
for v in ('front','top','right','left','bottom','rear'):
 p=PACK/assets[g['views'][v]]['image']['path'];paths.append(p)
for i,(p,label) in enumerate(zip(paths,('source','front','top','right','left','bottom','rear'))):
 d.text((i*220+4,2),label,fill=(0,0,0));art=Image.open(cand[label]['path'].replace('reusable/views-additional/','') if False else (PACK/cand[label]['path'] if label in cand else p)).convert('RGBA') if label in cand else Image.open(p).convert('RGBA');art.thumbnail((208,208),Image.Resampling.NEAREST);sheet.paste(art,(i*220+(220-art.width)//2,24+(208-art.height)//2),art)
contact=OUT/'raw/qa-iron-tracks-tunnel-portal-frame-candidate-v3-source-plus-six.png';sheet.save(contact,optimize=True)
current={v:{'path':assets[g['views'][v]]['image']['path'],'sha256':sha(PACK/assets[g['views'][v]]['image']['path'])} for v in ('front','top','right','left','bottom','rear')}
rec={'schema_version':1,'object_id':OID,'status':'candidate only; Root review required','source':{'path':source.relative_to(PACK).as_posix(),'sha256':sha(source)},'current_views':current,'supersedes_contact':'reusable/views-additional/raw/qa-iron-tracks-tunnel-portal-frame-candidate-v2-source-plus-six.png','directions':cand,'shared_guidance':{'accepted_front_top_rear':'reuse accepted v2 candidates unchanged','side_wall_span_px':196,'accepted_top_y_span_px':196,'bottom_transform_scale':bscale},'contact_path':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'notes':'R/L removes facing portal-end perspective while retaining the broad masonry wall; bottom rotates 90 degrees and is isotropically scaled. Inferred orthographic views.'};p=OUT/'raw/iron-tracks-tunnel-portal-frame-candidates-v3.json';p.write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({'contact':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'receipt':p.relative_to(PACK).as_posix(),'receipt_sha256':sha(p),'right_scale':rscale,'bottom_scale':bscale,'candidate_hashes':{v:c['sha256'] for v,c in cand.items()}},indent=2))
