from PIL import Image,ImageDraw
from scipy import ndimage
import numpy as np,json,hashlib,pathlib
R=pathlib.Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/ink-and-lanterns');H=R/'reusable/views-additional/raw/core-staging-stairs';D=H/'candidates'/'sea-surface-v1';D.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();V=('front','top','right','left','bottom','rear');handoff=json.load(open(H/'core-stairs-current-handoff.json'));rows={x['object_id']:x for x in handoff['sets']}
first=H/'sea-surface-stairs-edits-atlas.png';second=H/'surface-wet-up-rear-atlas.png';ims=[Image.open(p).convert('RGBA') for p in (first,second)]; arrays=[np.array(im)[:,:,3] for im in ims]
# Whole-atlas alpha connected components were inspected and manually mapped by geometry, not blind grid slicing.
requests={'first':{'request_id':'exec-906f4d15-1da6-4ed5-a668-e045ced76c3d','prompt':'Strict orthographic 3x3 atlas; outputs: Sea UP TOP, Surface Wet UP REAR, Surface Wet UP BOTTOM, Surface Wet DOWN REAR. The Surface UP REAR cell contained the wrong front tread view and is explicitly rejected; it is not installed. Other outputs are candidate only.'},'second':{'request_id':'exec-9fbbda75-3a10-4d24-bc21-a8f26b871e39','prompt':'One isolated square transparent sprite, strict orthographic rear elevation of Surface Wet City Pavement stairs UP: full-width level structural back panel, no upper treads, no diagonal brace; inferred hidden face.'}}
# Map requested candidate to atlas index and globally connected alpha component bbox.
entries=[('bubble-sea-seabed-sand-stairs-up','top',0,(468,66,785,385),'sea over-head plan'),('surface-entry-wet-city-pavement-stairs-up','bottom',0,(465,488,789,772),'opaque wet-stone underside'),('surface-entry-wet-city-pavement-stairs-down','rear',0,(851,880,1191,1165),'rear closed support; diagonal bracing is inferred'),('surface-entry-wet-city-pavement-stairs-up','rear',1,None,'rear closed support, no upper treads')]
report={'schema_version':1,'batch':'stairs-06-sea-surface','role':'candidate-only','write_scope':'book-tiles/ink-and-lanterns/reusable/views-additional/raw/core-staging-stairs','no_live_writes':True,'raw_atlases':[{'path':p.name,'sha256':sha(p.read_bytes()),'size_wh':list(im.size),'request':requests['first' if i==0 else 'second']} for i,(p,im) in enumerate(zip((first,second),ims))],'sets':[]}
for oid,view,ai,bb,note in entries:
 item=rows[oid];source=R/item['source']['path'];assert sha(source.read_bytes())==item['source']['sha256'];current={v:item['current_views'][v] for v in V};a=arrays[ai]
 if bb is None:
  l,n=ndimage.label(a>=16);sz=np.bincount(l.ravel());sz[0]=0;k=int(sz.argmax());ys,xs=np.where(l==k);bb=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
 crop=ims[ai].crop(bb);cw,ch=crop.size
 if view in ('rear','front','right','left'):
  elev=[current[v]['alpha_bbox_xyxy'] for v in ('front','right','left')];tz=round(sorted([q[3]-q[1] for q in elev])[1]);ground=round(sorted([q[3] for q in elev])[1]);scale=min(tz/ch,252/cw);w=max(1,round(cw*scale));h=max(1,round(ch*scale));pos=((256-w)//2,ground-h)
 else:
  topbox=current['top']['alpha_bbox_xyxy'];tw=topbox[2]-topbox[0];th=topbox[3]-topbox[1];tz=None;ground=None;scale=min(tw/cw,th/ch,0.95);w=max(1,round(cw*scale));h=max(1,round(ch*scale));pos=((256-w)//2,(256-h)//2)
 res=crop.resize((w,h),Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(res,pos);bbox=list(can.getchannel('A').getbbox());assert min(bbox)>0 and max(bbox)<256,(oid,view,bbox)
 out=D/f'{oid}.{view}.candidate.png';can.save(out,optimize=False);request=requests['first' if ai==0 else 'second']; deriv={'method':'imagegen-orthographic-stair-view-edit','raw_atlas_path':(first if ai==0 else second).name,'raw_atlas_sha256':sha((first if ai==0 else second).read_bytes()),'request_id':request['request_id'],'source_path':item['source']['path'],'source_sha256':item['source']['sha256'],'raw_component_bbox_xyxy':list(bb),'raw_component_size_wh':[cw,ch],'alpha_threshold':16,'normalization':'NEAREST isotropic scale; elevations matched to unchanged current F/R/L median common Z and ground; plans uniformly fit existing top footprint on 256x256 canvas','uniform_scale':scale,'resized_wh':[w,h],'canvas_offset_xy':list(pos),'anchor_px':[128,128],'target_z_px':tz,'ground_line_y':ground,'note':'Candidate only; hidden surfaces explicitly inferred. The Surface UP REAR component from the first atlas was rejected because it repeated the front treads; this separate targeted rear generation replaces it.'}
 cand={'candidate_path':str(out.relative_to(H)),'candidate_sha256':sha(out.read_bytes()),'size_wh':[256,256],'alpha_bbox_xyxy':bbox,'derivation':deriv}
 contact=Image.new('RGBA',(13*164,340),(42,42,46,255));draw=ImageDraw.Draw(contact);panels=[('SOURCE',source)]+[('OLD-'+v.upper(),R/current[v]['path']) for v in V]+[('CAND-'+v.upper(),H/cand['candidate_path'] if v==view else R/current[v]['path']) for v in V]
 for j,(label,p) in enumerate(panels):
  im=Image.open(p).convert('RGBA');im.thumbnail((128,280),Image.Resampling.NEAREST);contact.alpha_composite(im,(j*164+18+(128-im.width)//2,36+(280-im.height)//2));draw.text((j*164+2,16),label,fill='white')
 cp=H/f'{oid}.{view}.candidate-source-current-six.png';contact.save(cp,optimize=False)
 report['sets'].append({'object_id':oid,'source':item['source'],'current_views':current,'review_evidence':item['review_evidence'],'candidate_views':{view:cand},'retained_views':{v:current[v] for v in V if v!=view},'contact_path':cp.name,'contact_sha256':sha(cp.read_bytes()),'normalization_note':note})
(H/'staged-stairs-batch-06-sea-surface.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([(x['object_id'],list(x['candidate_views']),x['contact_path'],x['contact_sha256'],next(iter(x['candidate_views'].values()))['alpha_bbox_xyxy']) for x in report['sets']],indent=2))
