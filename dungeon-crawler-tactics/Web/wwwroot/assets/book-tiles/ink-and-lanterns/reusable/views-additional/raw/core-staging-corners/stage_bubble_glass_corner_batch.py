from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,os,sys
H=Path(__file__).resolve().parent;BASE=H.parents[3];OUT=H/'candidates';OUT.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest();V=('front','top','right','left','bottom','rear')
HAND=json.loads((H/'current-corner-handoff.json').read_text()); hand={x['object_id']:x for x in HAND['sets']};root=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed']
BATCH={
 'bubble-glass-sand-coloured-glass-inner-corner':('bubble-glass-sand-coloured-glass-wall-northeast','bubble-glass-sand-coloured-glass-wall-northeast'),
 'bubble-glass-sand-coloured-glass-outer-corner':('bubble-glass-sand-coloured-glass-wall-northeast','bubble-glass-sand-coloured-glass-wall-northeast'),
}
report={'schema_version':1,'batch':'03','role':'candidate-only wall-corner constructions','no_live_writes':True,'handoff_sha256':sha((H/'current-corner-handoff.json').read_bytes()),'geometry_policy':'own target source provides the top L footprint; bottom is an explicit inferred alias; four cardinal elevations use current root-PASS same-kit wall faces at one isotropic scale and shared anchor.','sets':[]}
for oid,(nw_id,ne_id) in BATCH.items():
 item=hand[oid];sp=BASE/item['source']['path'];source_bytes=sp.read_bytes();
 if sha(source_bytes)!=item['source']['sha256']:raise SystemExit(f'target source changed: {oid}')
 source=Image.open(sp).convert('RGBA');source_bbox=source.getchannel('A').getbbox();cut=source.crop(source_bbox);curtop=Image.open(BASE/item['current_views']['top']['path']).convert('RGBA');tb=curtop.getchannel('A').getbbox();plan_span=round(((tb[2]-tb[0])+(tb[3]-tb[1]))/2);pscale=plan_span/max(cut.size);pw=ph=round(max(cut.size)*pscale);plan=cut.resize((pw,ph),Image.Resampling.NEAREST);top=Image.new('RGBA',(256,256),(0,0,0,0));topoff=(128-pw//2,128-ph//2);top.alpha_composite(plan,topoff)
 candidates={};topout=OUT/f'{oid}.top.candidate.png';top.save(topout,optimize=False);candidates['top']={'candidate_path':str(topout.relative_to(H)),'candidate_sha256':sha(topout.read_bytes()),'size_wh':[256,256],'alpha_bbox_xyxy':list(top.getchannel('A').getbbox()),'derivation':{'method':'native-source-top-reframe','source_path':item['source']['path'],'source_sha256':item['source']['sha256'],'source_alpha_bbox_xyxy':list(source_bbox),'crop_xyxy':list(source_bbox),'uniform_scale':pscale,'resized_wh':[pw,ph],'offset_xy':list(topoff),'anchor_px':[128,128],'note':'Target source itself is the top-map L footprint; crop and uniformly frame its native pixels.'}}
 bot=top.transpose(Image.Transpose.ROTATE_180);bo=OUT/f'{oid}.bottom.candidate.png';bot.save(bo,optimize=False);candidates['bottom']={'candidate_path':str(bo.relative_to(H)),'candidate_sha256':sha(bo.read_bytes()),'size_wh':[256,256],'alpha_bbox_xyxy':list(bot.getchannel('A').getbbox()),'derivation':{'method':'explicit-inferred-underside-alias','donor_candidate_path':str(topout.relative_to(H)),'donor_sha256':candidates['top']['candidate_sha256'],'transform':'180-degree rotation about anchor [128,128]','anchor_px':[128,128],'note':'Unseen bottom is inferred from the source L plan; no hidden underside detail is claimed recovered.'}}
 guide_ids={'front':(nw_id,'front'),'rear':(nw_id,'rear'),'right':(ne_id,'right'),'left':(ne_id,'left')};guideinfo={};guidedata={}
 for view,(gid,gv) in guide_ids.items():
  r=root.get(f'book-tiles/ink-and-lanterns::{gid}')
  if not r or r.get('status') not in ('pass','passed'):raise SystemExit(f'no root PASS for guide {gid}')
  path=Path(r['view_paths'][gv]);data=path.read_bytes();gh=sha(data)
  if gh!=r['image_hashes'][gv]:raise SystemExit(f'current guide mismatch {gid}.{gv}')
  with Image.open(path) as im:bb=im.convert('RGBA').getchannel('A').getbbox()
  guideinfo[view]={'object_id':gid,'view':gv,'path':f'reusable/views-additional/{path.name}','sha256':gh,'source_sha256':r['source_sha256'],'root_reviewed_at':r['reviewed_at'],'root_status':r['status'],'alpha_bbox_xyxy':list(bb)}
  guidedata[view]=(path,gh,bb,gid,gv,r)
 # Use one shared isotropic scale across four face projections, matching broad face span to target L plan span.
 widths=[g[2][2]-g[2][0] for g in guidedata.values()]; guide_width=sum(widths)/len(widths); gscale=plan_span/guide_width
 for view,(path,gh,bb,gid,gv,r) in guidedata.items():
  im=Image.open(path).convert('RGBA');wh=(round(im.width*gscale),round(im.height*gscale));res=im.resize(wh,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));pos=(128-wh[0]//2,128-wh[1]//2);canvas.alpha_composite(res,pos);out=OUT/f'{oid}.{view}.candidate.png';canvas.save(out,optimize=False)
  candidates[view]={'candidate_path':str(out.relative_to(H)),'candidate_sha256':sha(out.read_bytes()),'size_wh':[256,256],'alpha_bbox_xyxy':list(canvas.getchannel('A').getbbox()),'derivation':{'method':'same-kit-root-approved-wall-face','guide_object_id':gid,'guide_view':gv,'guide_path':guideinfo[view]['path'],'guide_sha256':gh,'guide_source_sha256':r['source_sha256'],'guide_root_status':'pass','guide_reviewed_at':r['reviewed_at'],'target_source_path':item['source']['path'],'target_source_sha256':item['source']['sha256'],'shared_uniform_scale':gscale,'guide_alpha_bbox_xyxy':list(bb),'target_plan_span_px':plan_span,'mean_guide_face_width_px':guide_width,'resized_canvas_wh':list(wh),'canvas_offset_xy':list(pos),'anchor_px':[128,128],'note':'Broad wall arm inferred from current root-approved same-kit face; all four faces use one isotropic scale. Wall junction/hidden returns are inferred.'}}
 panels=[('SOURCE',sp)]+[('OLD-'+v.upper(),BASE/item['current_views'][v]['path']) for v in V]+[('CAND-'+v.upper(),H/candidates[v]['candidate_path']) for v in V];contact=Image.new('RGBA',(13*164,340),(42,42,46,255));dr=ImageDraw.Draw(contact)
 for col,(lab,path) in enumerate(panels):
  im=Image.open(path).convert('RGBA');im.thumbnail((128,280),Image.Resampling.NEAREST);contact.alpha_composite(im,(col*164+18+(128-im.width)//2,36+(280-im.height)//2));dr.text((col*164+2,16),lab,fill='white')
 cp=H/f'corner-candidates-{oid}.png';contact.save(cp,optimize=False)
 report['sets'].append({'object_id':oid,'source':item['source'],'current_views':item['current_views'],'review_evidence':item['review_evidence'],'candidate_views':candidates,'same_kit_wall_references':guideinfo,'contact_path':cp.name,'contact_sha256':sha(cp.read_bytes()),'plan_source_crop':{'source_alpha_bbox_xyxy':list(source_bbox),'current_top_bbox_xyxy':list(tb),'target_plan_span_px':plan_span,'uniform_scale':pscale},'elevation_calibration':{'shared_uniform_scale':gscale,'guide_face_width_px':guide_width,'target_plan_span_px':plan_span}})
out=H/'staged-corners-batch-03.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(out),'sets':[{'id':s['object_id'],'contact':s['contact_path'],'sha256':s['contact_sha256'],'guide_scale':s['elevation_calibration']['shared_uniform_scale'],'plan_scale':s['plan_source_crop']['uniform_scale']} for s in report['sets']]},indent=2))
