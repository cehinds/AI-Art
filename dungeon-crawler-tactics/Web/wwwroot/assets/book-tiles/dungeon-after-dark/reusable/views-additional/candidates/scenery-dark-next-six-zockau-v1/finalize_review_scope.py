#!/usr/bin/env python3
"""Split Root-approved Zockau candidates from six held directions and stage the held corrections."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
from scipy import ndimage
import numpy as np,json,hashlib
PACK=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark');BASE=PACK/'reusable/views-additional';C=BASE/'candidates/scenery-dark-next-six-zockau-v1'
HAND=Path('/workspace/scratch/scenery-dark-next-six-zockau-handoff-20261026.json');PROOF=Path('/tmp/root148-dark-zockau6.png.json')
VIEW_ORDER=['front','top','right','left','bottom','rear']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bbox64(im):
 a=np.asarray(im.convert('RGBA').getchannel('A'));y,x=np.where(a>=64);return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
def clean_component(raw,cellbox):
 im=Image.open(raw).convert('RGBA');a=np.asarray(im.getchannel('A'));labels,n=ndimage.label(a>=64,structure=np.ones((3,3),np.uint8));x0,y0,x1,y1=cellbox;cx=(x0+x1)/2;cy=(y0+y1)/2;cs=[]
 for lab in range(1,n+1):
  yy,xx=np.where(labels==lab)
  if len(xx)>500:cs.append((len(xx),lab,float(xx.mean()),float(yy.mean()),[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]))
 q=min(cs,key=lambda z:(z[2]-cx)**2+(z[3]-cy)**2);assert (q[2]-cx)**2+(q[3]-cy)**2 < (min(x1-x0,y1-y0)*.4)**2
 lab=q[1];mask=ndimage.binary_dilation(labels==lab,structure=np.ones((3,3),bool),iterations=2);bx0=max(x0,q[4][0]-2);by0=max(y0,q[4][1]-2);bx1=min(x1,q[4][2]+2);by1=min(y1,q[4][3]+2);crop=im.crop((bx0,by0,bx1,by1));arr=np.asarray(crop).copy();arr[~mask[by0:by1,bx0:bx1],3]=0;return Image.fromarray(arr,'RGBA'),{'component_label':lab,'component_area':q[0],'component_bbox':q[4],'cell_bbox':cellbox,'crop_bbox':[bx0,by0,bx1,by1]}
def centered(im):
 xy=((256-im.width)//2,(256-im.height)//2);out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(im,xy);return out,xy
h=json.loads(HAND.read_text());objs={x['object_id']:x for x in h['objects']};orig=json.loads((C/'candidate-manifest.json').read_text());byid={x['object_id']:x for x in orig['sets']}
# Revalidate all 42 handoff source/current hashes immediately before staging.
for o in h['objects']:
 assert sha(o['source']['path'])==o['source']['sha256'],o['object_id']
 for v,x in o['views'].items():assert sha(x['path'])==x['sha256'],(o['object_id'],v)
assert sha(PROOF)==h['source_and_six_proof']['sha256']
accepted_ids={'hunting-jungle-vine-covered-ruin-stone-endcap-northwest':['top','bottom'],'hunting-zockau-bear-head-square-statue':['bottom'],'hunting-zockau-painted-town-brick-endcap-northeast':VIEW_ORDER,'hunting-zockau-painted-town-brick-endcap-northwest':['top','right','left','bottom'],'hunting-zockau-painted-town-brick-wall-northeast':['front','right','left','rear']}
held_ids={'hunting-zockau-painted-town-brick-wall-northeast':['top','bottom'],'hunting-zockau-painted-town-brick-wall-northwest':['front','right','left','rear']}
# Exact accepted-candidate bundle: one record per leaf to install.
accepted={'candidate_id':'scenery-dark-zockau-approved-subset-v1','scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_scenery','reviewer':'root','installer':'views_dark_books','candidate_only':True,'handoff_path':str(HAND),'handoff_sha256':sha(HAND),'source_six_proof_path':str(PROOF),'source_six_proof_sha256':sha(PROOF),'sets':[],'retained_accepted_unchanged':[{'object_id':'hunting-zockau-painted-town-brick-wall-northwest','view':v,'path':objs['hunting-zockau-painted-town-brick-wall-northwest']['views'][v]['path'].replace(str(PACK)+'/',''),'sha256':objs['hunting-zockau-painted-town-brick-wall-northwest']['views'][v]['sha256']} for v in ('top','bottom')],'held_directions':[]}
for oid,views in accepted_ids.items():
 s=byid[oid];o=objs[oid]
 for v in views:
  c=s['candidates'][v].copy();c.update({'object_id':oid,'view':v,'base_path':o['views'][v]['path'].replace(str(PACK)+'/',''),'base_sha256':o['views'][v]['sha256'],'source_path':o['source']['path'].replace(str(PACK)+'/',''),'source_sha256':o['source']['sha256']});accepted['sets'].append(c)
accepted_path=C/'accepted-subset-manifest.json';accepted_path.write_text(json.dumps(accepted,indent=2)+'\n')
# Pending six candidates: NE wall plans are exact rigid rotations of current; NW wall uses source-faithful geometry.
ops={'candidate_id':'scenery-dark-zockau-held-six-v1','scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_scenery','reviewer':'root','installer':'views_dark_books','candidate_only':True,'handoff_path':str(HAND),'handoff_sha256':sha(HAND),'source_six_proof_path':str(PROOF),'source_six_proof_sha256':sha(PROOF),'sets':[],'notes':'No canonical writes. NW wall front/rear derived from native source crop by uniform scale; R/L from v4 generated atlas cells uniformly calibrated to same Z height. NE top/bottom are rigid 90-degree rotations of held current plans.'}
# NE top/bottom 90 deg counterclockwise.
o=objs['hunting-zockau-painted-town-brick-wall-northeast']
for v in ('top','bottom'):
 x=o['views'][v];im=Image.open(x['path']).convert('RGBA');rot=im.rotate(90,resample=Image.Resampling.NEAREST,expand=True);out,xy=centered(rot);p=C/'images'/f'{o["object_id"]}.{v}.candidate-v2.png';out.save(p,optimize=False)
 req={'operation':'rigid-rotation','object_id':o['object_id'],'view':v,'source_path':x['path'],'source_sha256':x['sha256'],'rotation_degrees_ccw':90,'resample':'NEAREST','expand':True,'canvas':[256,256],'placement_xy':list(xy),'anchor_px':[128,128],'notes':'The retained footprint is long along X but this NE wall is long along Y; rigidly rotate the plan without anisotropic scaling.'};rp=C/f'{o["object_id"]}.{v}.rotation-recipe.json';rp.write_text(json.dumps(req,indent=2)+'\n')
 ops['sets'].append({'object_id':o['object_id'],'view':v,'candidate_path':str(p.relative_to(BASE)),'candidate_sha256':sha(p),'base_sha256':x['sha256'],'source_path':o['source']['path'].replace(str(PACK)+'/',''),'source_sha256':o['source']['sha256'],'method':'rigid-90-degree-rotation','recipe_path':str(rp.relative_to(BASE)),'recipe_sha256':sha(rp),'raw_path':x['path'].replace(str(PACK)+'/',''),'raw_sha256':x['sha256'],'uniform_scale':1.0,'resized_dimensions':[rot.width,rot.height],'placement_xy':list(xy)})
# NW source normalized front, exact mirrored inferred rear.
o=objs['hunting-zockau-painted-town-brick-wall-northwest'];src=Image.open(o['source']['path']).convert('RGBA');bb=bbox64(src);crop=src.crop(bb);scale=190/crop.width;dims=(190,round(crop.height*scale));z=crop.resize(dims,Image.Resampling.NEAREST);front,xy=centered(z);frontp=C/'images'/f'{o["object_id"]}.front.candidate-v2.png';front.save(frontp,optimize=False)
front_recipe={'operation':'canonical-source-crop-uniform-nearest','object_id':o['object_id'],'view':'front','source_path':o['source']['path'],'source_sha256':o['source']['sha256'],'alpha64_crop_bbox':bb,'uniform_scale':scale,'resized_dimensions':list(dims),'canvas':[256,256],'placement_xy':list(xy),'filter':'NEAREST','notes':'Replaces historically squashed front with an isotropic native-source crop calibrated to the accepted 190px broad-face width; no anisotropic stretch.'};frp=C/'hunting-zockau-painted-town-brick-wall-northwest.front-source-recipe.json';frp.write_text(json.dumps(front_recipe,indent=2)+'\n')
ops['sets'].append({'object_id':o['object_id'],'view':'front','candidate_path':str(frontp.relative_to(BASE)),'candidate_sha256':sha(frontp),'base_sha256':o['views']['front']['sha256'],'source_path':o['source']['path'].replace(str(PACK)+'/',''),'source_sha256':o['source']['sha256'],'method':'canonical-source-crop-uniform-nearest','recipe_path':str(frp.relative_to(BASE)),'recipe_sha256':sha(frp),'raw_path':o['source']['path'].replace(str(PACK)+'/',''),'raw_sha256':o['source']['sha256'],'alpha64_crop_bbox':bb,'uniform_scale':scale,'resized_dimensions':list(dims),'placement_xy':list(xy)})
rear=ImageOps.mirror(front);rearp=C/'images'/f'{o["object_id"]}.rear.candidate-v2.png';rear.save(rearp,optimize=False);rr={'operation':'horizontal-mirror-of-source-derived-front','object_id':o['object_id'],'view':'rear','donor_path':str(frontp.relative_to(BASE)),'donor_sha256':sha(frontp),'canonical_source_path':o['source']['path'],'canonical_source_sha256':o['source']['sha256'],'symmetry':'Inferred same construction and brick pattern on the opposite broad face; mirror places asymmetrical brick motifs in opposite screen order.','canvas':[256,256]};rrp=C/'hunting-zockau-painted-town-brick-wall-northwest.rear-mirror-recipe.json';rrp.write_text(json.dumps(rr,indent=2)+'\n')
ops['sets'].append({'object_id':o['object_id'],'view':'rear','candidate_path':str(rearp.relative_to(BASE)),'candidate_sha256':sha(rearp),'base_sha256':o['views']['rear']['sha256'],'source_path':o['source']['path'].replace(str(PACK)+'/',''),'source_sha256':o['source']['sha256'],'method':'horizontal-mirror-of-source-derived-front','recipe_path':str(rrp.relative_to(BASE)),'recipe_sha256':sha(rrp),'derived_from':str(frontp.relative_to(BASE)),'derived_sha256':sha(frontp)})
# NW generated narrow ends, scaled uniformly until their Z matches native-derived front Z.
raw=C/'raw-zockau-nw-wall-v4-atlas.png';rawim=Image.open(raw).convert('RGBA');aw,ah=rawim.size;cellw=aw/3;cellh=ah/2
for v,row,col in [('right',0,2),('left',1,0)]:
 x0,y0=int(col*cellw),int(row*cellh);x1,y1=int((col+1)*cellw),int((row+1)*cellh);cropr,crecipe=clean_component(raw,(x0,y0,x1,y1));scale=92/cropr.height;dims=(round(cropr.width*scale),92);z=cropr.resize(dims,Image.Resampling.NEAREST);out,xy=centered(z);p=C/'images'/f'{o["object_id"]}.{v}.candidate-v2.png';out.save(p,optimize=False)
 rec={'operation':'generated-atlas-component-uniform-nearest-to-shared-Z','object_id':o['object_id'],'view':v,'raw_atlas':str(raw.relative_to(BASE)),'raw_sha256':sha(raw),'cell_bbox':crecipe['cell_bbox'],'alpha64_component':crecipe['component_label'],'component_bbox':crecipe['component_bbox'],'crop_bbox':crecipe['crop_bbox'],'mask_dilation':[3,3],'mask_iterations':2,'shared_Z_target_px':92,'uniform_scale':scale,'resized_dimensions':list(dims),'canvas':[256,256],'placement_xy':list(xy),'filter':'NEAREST','source_path':o['source']['path'],'source_sha256':o['source']['sha256'],'notes':'Narrow end profile; uniform calibration to 92px Z matching isotropically normalized source face; preserves aspect, no anisotropic stretch.'};rp=C/f'{o["object_id"]}.{v}.generated-recipe.json';rp.write_text(json.dumps(rec,indent=2)+'\n')
 ops['sets'].append({'object_id':o['object_id'],'view':v,'candidate_path':str(p.relative_to(BASE)),'candidate_sha256':sha(p),'base_sha256':o['views'][v]['sha256'],'source_path':o['source']['path'].replace(str(PACK)+'/',''),'source_sha256':o['source']['sha256'],'method':'generated-atlas-component-uniform-nearest-to-shared-Z','recipe_path':str(rp.relative_to(BASE)),'recipe_sha256':sha(rp),'raw_path':str(raw.relative_to(BASE)),'raw_sha256':sha(raw),'crop_bbox_alpha64':crecipe['crop_bbox'],'uniform_scale':scale,'resized_dimensions':list(dims),'placement_xy':list(xy)})
# accepted packet complete guards for every affected object (including retained NW top/bottom state).
accepted_objects=sorted({x['object_id'] for x in accepted['sets']})
preflight=[]
for oid in accepted_objects:
 o=objs[oid];preflight.append({'object_id':oid,'source':{'path':o['source']['path'].replace(str(PACK)+'/',''),'sha256':o['source']['sha256']},'views':{v:{'path':x['path'].replace(str(PACK)+'/',''),'sha256':x['sha256']} for v,x in o['views'].items()}})
accepted_packet={'schema_version':1,'packet_id':'scenery-dark-zockau-approved17-install-packet','status':'authorized scoped install of 17 reviewed candidate directions; retain two accepted NW wall plan views unchanged','installer':'views_dark_books','reviewer':'root','accepted_subset_manifest_path':str(accepted_path.relative_to(BASE)),'accepted_subset_manifest_sha256':sha(accepted_path),'accepted_direction_count':17,'retained_accepted_unchanged_count':2,'held_candidates_excluded':['hunting-zockau-painted-town-brick-wall-northeast.top','hunting-zockau-painted-town-brick-wall-northeast.bottom','hunting-zockau-painted-town-brick-wall-northwest.front','hunting-zockau-painted-town-brick-wall-northwest.right','hunting-zockau-painted-town-brick-wall-northwest.left','hunting-zockau-painted-town-brick-wall-northwest.rear'],'preflight_source_and_six_guards':preflight,'contact_path':'reusable/views-additional/candidates/scenery-dark-next-six-zockau-v1/candidate-source-plus-six.png','contact_sha256':sha(C/'candidate-source-plus-six.png'),'install_rule':'Install only listed candidate_path leaves after exact source and all-six base hashes match. Do not modify preserved or held views.'}
pp=C/'accepted-subset-install-packet.json';pp.write_text(json.dumps(accepted_packet,indent=2)+'\n')
# Remaining-six contact combines approved candidate layers and new held candidates for the two wall sets.
remaining_contact=[]
for oid in ('hunting-zockau-painted-town-brick-wall-northeast','hunting-zockau-painted-town-brick-wall-northwest'):
 o=objs[oid];ims=[Image.open(o['source']['path']).convert('RGBA')]
 for v in VIEW_ORDER:
  if oid=='hunting-zockau-painted-town-brick-wall-northeast':
   if v in ('top','bottom'):p=C/'images'/f'{oid}.{v}.candidate-v2.png'
   elif v in ('front','right','left','rear'):p=BASE/byid[oid]['candidates'][v]['candidate_path']
   else:p=Path(o['views'][v]['path'])
  else:
   if v in ('front','right','left','rear'):p=C/'images'/f'{oid}.{v}.candidate-v2.png'
   else:p=Path(o['views'][v]['path'])
  ims.append(Image.open(p).convert('RGBA'))
 remaining_contact.append((oid,ims))
W=180;H=180;lh=24;pad=10;rowh=H+lh+pad;sheet=Image.new('RGBA',(pad+7*(W+pad),pad*2+2*rowh),(38,38,44,255));draw=ImageDraw.Draw(sheet)
for r,(oid,ims) in enumerate(remaining_contact):
 y=pad+r*rowh;draw.text((pad,y),oid,fill='white');y+=lh
 for c,im in enumerate(ims):
  x=pad+c*(W+pad);im.thumbnail((W,H),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+(W-im.width)//2,y+(H-im.height)//2));draw.text((x,y+H+2),['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR'][c],fill='white')
rc=C/'remaining-six-source-plus-six-v1.png';sheet.save(rc,optimize=False)
ops['contact_path']=str(rc.relative_to(BASE));ops['contact_sha256']=sha(rc);ops['held_direction_count']=len(ops['sets']);op= C/'remaining-six-manifest.json';op.write_text(json.dumps(ops,indent=2)+'\n')
print(json.dumps({'accepted_manifest':str(accepted_path),'accepted_manifest_sha256':sha(accepted_path),'accepted_packet':str(pp),'accepted_packet_sha256':sha(pp),'accepted_candidate_count':len(accepted['sets']),'retained_accepted_unchanged':2,'remaining_manifest':str(op),'remaining_manifest_sha256':sha(op),'remaining_contact':str(rc),'remaining_contact_sha256':sha(rc),'remaining_count':len(ops['sets'])},indent=2))
