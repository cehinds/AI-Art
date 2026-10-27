from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,os
H=Path(__file__).resolve().parent;BASE=H.parents[3];PACK='book-tiles/ink-and-lanterns';OUT=H/'candidates';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();V=('front','top','right','left','bottom','rear')
handoff=json.loads((H/'current-corner-handoff.json').read_text());by={s['object_id']:s for s in handoff['sets']};root=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed'];idx=json.loads((BASE/'reusable/index.json').read_text());assets={a['id']:a for a in idx['assets']}
report={'schema_version':1,'role':'candidate-only wall-corner constructions','no_live_writes':True,'handoff_sha256':sha((H/'current-corner-handoff.json').read_bytes()),'wall_guide_policy':'Use only current root-PASS same-kit wall face outputs; preserve target source for top L footprint; bottom is explicit inferred 180-degree top-plan alias.','sets':[]}
for oid in ['bubble-desert-adobe-desert-plaster-inner-corner','bubble-desert-adobe-desert-plaster-outer-corner']:
 item=by[oid];source=BASE/item['source']['path'];sb=source.read_bytes();
 if sha(sb)!=item['source']['sha256']:raise SystemExit(f'target source changed {oid}')
 src=Image.open(source).convert('RGBA');srcbox=src.getchannel('A').getbbox();cropped=src.crop(srcbox);curtop=Image.open(BASE/item['current_views']['top']['path']).convert('RGBA');topbox=curtop.getchannel('A').getbbox();plan_span=round(((topbox[2]-topbox[0])+(topbox[3]-topbox[1]))/2);scale=plan_span/max(cropped.size);nw=nh=round(max(cropped.size)*scale);plan=cropped.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));offset=(128-nw//2,128-nh//2);canvas.alpha_composite(plan,offset)
 candidates={}
 topout=OUT/f'{oid}.top.candidate.png';canvas.save(topout,optimize=False);candidates['top']={'candidate_path':str(topout.relative_to(H)),'candidate_sha256':sha(topout.read_bytes()),'size_wh':[256,256],'alpha_bbox_xyxy':list(canvas.getchannel('A').getbbox()),'derivation':{'method':'native-source-top-reframe','source_path':item['source']['path'],'source_sha256':item['source']['sha256'],'source_alpha_bbox_xyxy':list(srcbox),'crop_xyxy':list(srcbox),'uniform_scale':scale,'crop_resized_wh':[nw,nh],'offset_xy':list(offset),'anchor_px':[128,128],'note':'Target primary source is the top-map L footprint; crop and uniformly frame its native pixels to the existing footprint span.'}}
 bottom=canvas.transpose(Image.Transpose.ROTATE_180);bout=OUT/f'{oid}.bottom.candidate.png';bottom.save(bout,optimize=False);candidates['bottom']={'candidate_path':str(bout.relative_to(H)),'candidate_sha256':sha(bout.read_bytes()),'size_wh':[256,256],'alpha_bbox_xyxy':list(bottom.getchannel('A').getbbox()),'derivation':{'method':'explicit-inferred-underside-alias','donor_candidate_path':str(topout.relative_to(H)),'donor_sha256':candidates['top']['candidate_sha256'],'transform':'180-degree rotation about shared anchor [128,128]','anchor_px':[128,128],'note':'Underside geometry is inferred by aliasing the target-native L plan. No underside surface detail is claimed recovered.'}}
 guide_ids={'front':('bubble-desert-adobe-desert-plaster-wall-northwest','front'),'rear':('bubble-desert-adobe-desert-plaster-wall-northwest','rear'),'right':('bubble-desert-adobe-desert-plaster-wall-northeast','right'),'left':('bubble-desert-adobe-desert-plaster-wall-northeast','left')}
 guide_refs={}
 for target,(gid,gv) in guide_ids.items():
  r=root.get(f'{PACK}::{gid}')
  if not r or r.get('status') not in ('pass','passed'):raise SystemExit(f'guide lacks current root PASS {gid}')
  p=Path(r['view_paths'][gv]);data=p.read_bytes();gh=sha(data)
  if gh!=r['image_hashes'][gv]:raise SystemExit(f'guide hash mismatch {gid}.{gv}')
  im=Image.open(p).convert('RGBA');bb=im.getchannel('A').getbbox();
  # Target plan span sets wall-face X length; one shared isotropic scale is used for all elevations.
  if target not in ('front','rear'): pass
  gscale=plan_span/(bb[2]-bb[0]);newwh=(round(im.width*gscale),round(im.height*gscale));res=im.resize(newwh,Image.Resampling.NEAREST);outim=Image.new('RGBA',(256,256),(0,0,0,0));pos=(128-newwh[0]//2,128-newwh[1]//2);outim.alpha_composite(res,pos);out=OUT/f'{oid}.{target}.candidate.png';outim.save(out,optimize=False)
  candidates[target]={'candidate_path':str(out.relative_to(H)),'candidate_sha256':sha(out.read_bytes()),'size_wh':[256,256],'alpha_bbox_xyxy':list(outim.getchannel('A').getbbox()),'derivation':{'method':'same-kit-root-approved-wall-face','guide_object_id':gid,'guide_view':gv,'guide_path':f'reusable/views-additional/{Path(r["view_paths"][gv]).name}','guide_sha256':gh,'guide_source_sha256':r['source_sha256'],'guide_status':'root-PASS current hash','target_source_path':item['source']['path'],'target_source_sha256':item['source']['sha256'],'uniform_scale':gscale,'guide_alpha_bbox_xyxy':list(bb),'canvas_wh':[256,256],'offset_xy':list(pos),'anchor_px':[128,128],'note':'Joined-wall elevation inferred from a root-approved same-kit broad wall face. One isotropic scale matches target top-plan long span; hidden corner junction details remain inferred.'}}
  guide_refs[target]={'object_id':gid,'view':gv,'path':f'reusable/views-additional/{Path(r["view_paths"][gv]).name}','sha256':gh,'source_sha256':r['source_sha256']}
 # Contact source + old six + proposed six.
 panels=[('SOURCE',source)]+[('OLD-'+v.upper(),BASE/item['current_views'][v]['path']) for v in V]
 panels += [('CAND-'+v.upper(),H/candidates[v]['candidate_path']) for v in V]
 contact=Image.new('RGBA',(13*164,340),(42,42,46,255));dr=ImageDraw.Draw(contact)
 for col,(lab,p) in enumerate(panels):
  x=Image.open(p).convert('RGBA');x.thumbnail((128,280),Image.Resampling.NEAREST);contact.alpha_composite(x,(col*164+18+(128-x.width)//2,36+(280-x.height)//2));dr.text((col*164+2,16),lab,fill='white')
 cp=H/f'corner-candidates-{oid}.png';contact.save(cp,optimize=False)
 report['sets'].append({'object_id':oid,'source':item['source'],'current_views':item['current_views'],'review_evidence':item['review_evidence'],'candidate_views':candidates,'same_kit_wall_references':guide_refs,'contact_path':cp.name,'contact_sha256':sha(cp.read_bytes()),'plan_source_crop':{'source_alpha_bbox_xyxy':list(srcbox),'current_top_bbox_xyxy':list(topbox),'target_plan_span_px':plan_span,'uniform_scale':scale}})
 p=H/'staged-corners-batch-01.json';p.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'report':str(H/'staged-corners-batch-01.json'),'sets':[{'id':s['object_id'],'contact':s['contact_path'],'sha256':s['contact_sha256'],'candidate_hashes':{v:c['candidate_sha256'] for v,c in s['candidate_views'].items()},'plan':s['plan_source_crop']} for s in report['sets']]},indent=2))
