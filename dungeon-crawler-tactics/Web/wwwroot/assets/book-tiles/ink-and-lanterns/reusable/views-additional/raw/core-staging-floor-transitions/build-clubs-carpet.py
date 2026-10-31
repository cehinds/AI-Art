from PIL import Image,ImageDraw
from scipy import ndimage
import numpy as np,json,hashlib,pathlib
P=pathlib.Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/ink-and-lanterns');H=P/'reusable/views-additional/raw/core-staging-floor-transitions';D=H/'candidates'/'clubs-carpet-v1';D.mkdir(parents=True,exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest();V=('front','top','right','left','bottom','rear');hand=json.load(open(H/'current-floor-transition-handoff.json'));rows={x['object_id']:x for x in hand['objects']}
raws={'atlas':H/'clubs-carpet-transitions-atlas.png','corner_right':H/'clubs-corner-right-edge-rear-atlas.png','edge_rear':H/'clubs-edge-rear-atlas.png'}
# Global-alpha CC bboxes measured from each retained whole atlas; invalid duplicate plan cells deliberately excluded.
regions={
('clubs-guilds-club-carpet-corner-transition','front'):('atlas',[80,164,363,284]),
('clubs-guilds-club-carpet-corner-transition','left'):('atlas',[844,178,1140,292]),
('clubs-guilds-club-carpet-corner-transition','rear'):('atlas',[1234,180,1528,293]),
('clubs-guilds-club-carpet-corner-transition','bottom'):('atlas',[1630,104,1907,357]),
('clubs-guilds-club-carpet-corner-transition','right'):('corner_right',[82,334,791,555]),
('clubs-guilds-club-carpet-edge-transition','front'):('atlas',[75,526,370,644]),
('clubs-guilds-club-carpet-edge-transition','right'):('atlas',[844,520,1143,642]),
('clubs-guilds-club-carpet-edge-transition','left'):('atlas',[1235,520,1529,643]),
('clubs-guilds-club-carpet-edge-transition','rear'):('edge_rear',[285,339,1782,405]),
}
reqs={
'atlas':{'request_id':'exec-b4998cf0-583f-4062-929e-2664a3804935','file':'clubs-carpet-transitions.request.json'},
'corner_right':{'request_id':'exec-b5e39f1e-4e28-4e39-9ff9-9d4b69f77669','file':'clubs-corner-right-edge-rear.request.json'},
'edge_rear':{'request_id':'exec-79f9be46-be50-47cc-b206-5949cb994a27','file':'clubs-edge-rear.request.json'}}
report={'schema_version':1,'batch':'floor-transitions-01-clubs-carpet','role':'candidate-only','write_scope':'book-tiles/ink-and-lanterns/reusable/views-additional/raw/core-staging-floor-transitions','no_live_writes':True,'raw_inputs':[],'sets':[]}
for name,p in raws.items():
 im=Image.open(p).convert('RGBA');report['raw_inputs'].append({'path':p.name,'sha256':sha(p.read_bytes()),'size_wh':list(im.size),'request':reqs[name]})
for oid in ['clubs-guilds-club-carpet-corner-transition','clubs-guilds-club-carpet-edge-transition']:
 row=rows[oid];source=P/row['source']['path'];assert sha(source.read_bytes())==row['source']['sha256'];current=row['live_views']; candidates={};views_for={v:Image.open(P/current[v]['path']).convert('RGBA') for v in V}
 tops={v:Image.open(P/current[v]['path']).convert('RGBA').getchannel('A').getbbox() for v in V};plan=tops['top'];xspan=plan[2]-plan[0];yspan=plan[3]-plan[1];ground=round(sorted([tops[v][3] for v in ['front','right','left','rear']])[1])
 for (obj,v),(rawname,bb) in regions.items():
  if obj!=oid:continue
  raw=Image.open(raws[rawname]).convert('RGBA');a=np.array(raw)[:,:,3];x0,y0,x1,y1=bb;lab,n=ndimage.label(a>=16);# Confirm the exact selected alpha component aligns with recorded global bbox.
  comp_ids=np.unique(lab[y0:y1,x0:x1]);comp_ids=[int(i) for i in comp_ids if i];assert comp_ids,(oid,v,'no alpha component');k=max(comp_ids,key=lambda i:int((lab==i).sum()));ys,xs=np.where(lab==k);actual=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];bb=actual
  crop=raw.crop(tuple(bb));cw,ch=crop.size
  if v in ('front','rear'):target=xspan
  elif v in ('right','left'):target=yspan
  else:target=min(xspan,yspan)
  scale=target/cw if v!='bottom' else min(xspan/cw,yspan/ch);w=max(1,round(cw*scale));h=max(1,round(ch*scale));res=crop.resize((w,h),Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0))
  if v=='bottom':pos=((256-w)//2,(256-h)//2)
  else:pos=((256-w)//2,ground-h)
  can.alpha_composite(res,pos);bbox=list(can.getchannel('A').getbbox());assert min(bbox)>0 and max(bbox)<256,(oid,v,bbox)
  out=D/f'{oid}.{v}.candidate.png';can.save(out,optimize=False);candidate={'candidate_path':str(out.relative_to(H)),'candidate_sha256':sha(out.read_bytes()),'size_wh':[256,256],'alpha_bbox_xyxy':bbox,'derivation':{'method':'imagegen-orthographic-floor-view-edit','raw_atlas_path':raws[rawname].name,'raw_atlas_sha256':sha(raws[rawname].read_bytes()),'request_id':reqs[rawname]['request_id'],'request_file':reqs[rawname]['file'],'source_path':row['source']['path'],'source_sha256':row['source']['sha256'],'raw_component_bbox_xyxy':bb,'raw_component_size_wh':[cw,ch],'alpha_threshold':16,'normalization':'NEAREST isotropic scale to source plan world-X/world-Y extent; shared existing ground line for elevations; centered anchor contract 128,128','uniform_scale':scale,'resized_wh':[w,h],'canvas_offset_xy':list(pos),'anchor_px':[128,128],'target_world_x_px':xspan,'target_world_y_px':yspan,'ground_line_y':None if v=='bottom' else ground,'note':'Candidate only; inferred hidden underside/edge surfaces are not recovered pixels. L corner underside preserves native transparent quadrant.'}}
  candidates[v]=candidate
 contact=Image.new('RGBA',(13*164,340),(42,42,46,255));draw=ImageDraw.Draw(contact);panels=[('SOURCE',source)]+[('OLD-'+vv.upper(),P/current[vv]['path']) for vv in V]+[('CAND-'+vv.upper(),H/candidates[vv]['candidate_path'] if vv in candidates else P/current[vv]['path']) for vv in V]
 for j,(label,path) in enumerate(panels):
  im=Image.open(path).convert('RGBA');im.thumbnail((128,280),Image.Resampling.NEAREST);contact.alpha_composite(im,(j*164+18+(128-im.width)//2,36+(280-im.height)//2));draw.text((j*164+2,16),label,fill='white')
 cp=H/f'{oid}.candidate-source-current-six.png';contact.save(cp,optimize=False);report['sets'].append({'object_id':oid,'source':row['source'],'current_views':current,'review':row['review'],'candidate_views':candidates,'retained_views':{v:current[v] for v in V if v not in candidates},'contact_path':cp.name,'contact_sha256':sha(cp.read_bytes()),'rejected_cells':{'corner-transition-right-from-first-atlas':'Wrong duplicate plan footprint, rejected and excluded; targeted right-elevation request supplies candidate.','edge-transition-top-cell':'Duplicate plan view, rejected; not installed.'}})
(H/'staged-floor-transitions-batch-01-clubs-carpet.json').write_text(json.dumps(report,indent=2)+'\n');print([(x['object_id'],list(x['candidate_views']),x['contact_path'],x['contact_sha256']) for x in report['sets']])
