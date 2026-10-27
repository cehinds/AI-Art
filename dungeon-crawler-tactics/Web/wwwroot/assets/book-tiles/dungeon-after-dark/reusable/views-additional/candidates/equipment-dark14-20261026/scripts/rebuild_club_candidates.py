from PIL import Image,ImageDraw
import numpy as np,json,os,hashlib,shutil
from scipy import ndimage
ROOT='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'
BASE=ROOT+'/reusable/views-additional/candidates/equipment-dark14-20261026'
D=json.load(open('/workspace/scratch/equipment-dark14-candidate-handoff-20261026.json'))
sha=lambda p:hashlib.sha256(open(p,'rb').read()).hexdigest()
# Preserve portable refs, replacing temp-only geometry sheet.
shutil.copy2('/tmp/club-guide-six.jpg',BASE+'/references/club-guide-six.jpg')
# Keep the exact imagegen-generated inputs local to candidate root.
rawdefs={
 'club-atlas':('/workspace/generated_images/exec-e5bd705f-1225-49f6-9890-c7f58e250854.png','clubs-corners-batch02-approved-candidate-atlas.png'),
 'club-plan-correction':('/workspace/generated_images/exec-a70a89c0-bd2c-4f6d-925a-815d1c5cf372.png','club-inner-plans-charcoal-correction.png'),
 'stone':('/workspace/generated_images/exec-2ed4158d-7876-4392-a82e-7794feb7afff.png','stone-corners-batch01-atlas.png'),
 'faction':('/workspace/generated_images/exec-72285e6c-93f7-43ab-b43c-9f56e9efa631.png','faction-corners-batch01-atlas.png')}
raws={}
for key,(src,name) in rawdefs.items():
 p=BASE+'/raw/'+name;shutil.copy2(src,p);raws[key]={'generated_path':src,'staged_path':'raw/'+name,'sha256':sha(p),'dimensions':list(Image.open(p).size)}
# Persist exact prompts used for stone/faction and correction as JSON text.
for name,txt in [('stone-corners-batch01.prompt.json','Use reference 1 only as simple silhouette/camera diagram; reference 2 is a verified approved same-kit geometry/view guide; reference 3 is the exact target source contact and controls all stone materials, banners, metal rings and identity. Generate one transparent pixel-art atlas with TWO rows (outer corner first, inner corner second) and FOUR equal cells per row, columns FRONT, RIGHT, LEFT, REAR. These four are true level 90-degree elevations with vertical axis world Z, and all four show a broad rectangular joined wall face at the same total height; no isometric corners, no L silhouette, no standalone narrow post, no visible top surface. The physical object is a compact L-footprint corner of two perpendicular joined stone wings. From each camera, show the face-on branch as a broad rectangular elevation and only the physically visible narrow end of the perpendicular branch; maintain consistent dimensions and corner orientation across opposite directions. Use exactly the number and placement of source banners per row: outer source has one red hanging banner and one bronze ring detail; inner has two red hanging banners. Retain blue-gray masonry blocks, pale sandstone cap blocks and dark mortar/iron outline from the target source. Hidden faces inferred conservatively. No extra props, no letters, no shadows beyond the sprite, no cell spill. Crisp orthographic pixel art, transparent background.'),('faction-corners-batch01.prompt.json','Use reference 1 only as simple silhouette/camera diagram; reference 2 is a verified approved same-kit geometry/view guide; reference 3 is the exact target source contact and controls all materials, fortification design and identity. Generate one transparent pixel-art atlas with TWO rows (outer corner first, inner corner second) and FOUR equal cells per row, columns FRONT, RIGHT, LEFT, REAR. These four are true level 90-degree elevations with vertical axis world Z, and all four show a broad rectangular joined wall face at the same total height; no isometric corners, no L silhouette, no standalone narrow post, no visible top surface. The physical object is a compact L-footprint corner of two perpendicular joined fortification wings. From each camera, show the face-on branch as a broad rectangular elevation and only the physically visible narrow end of the perpendicular branch; maintain consistent dimensions and corner orientation across opposite directions. Preserve target source identity: earth-toned field walls, timber braces, sandbag or plank supports, capstones and any red banner exactly as each row source supports. Do not duplicate, drop or move distinctive hardware. Hidden faces are conservative inferences. No extra props, no text, no shadows beyond the sprite, no cell spill. Crisp orthographic pixel art, transparent background.')]:
 open(BASE+'/prompts/'+name,'w').write(json.dumps({'prompt':txt},indent=2)+'\n')
# Update prior raw request records; no fabricated request IDs. All prompts and generated file paths retained.
for fn in ['clubs-corners-batch01-rejected.json','clubs-corners-batch02-approved-candidate-atlas.json']:
 p=BASE+'/raw/'+fn
 if os.path.exists(p):
  x=json.load(open(p))
  if fn.startswith('clubs-corners-batch01'):
   x['raw_sha256']=sha(BASE+'/raw/clubs-corners-batch01-rejected-inferred-front-rear-isometric.png')
   x['prompt_text']='Using the first reference image as the exact appearance source for two distinct Dark polished club-panel corner objects, and the second reference image ONLY as approved camera/geometry guidance for a joined corner wall, create a clean transparent-background pixel-art atlas. Draw exactly TWO rows, one object per row, each row with six equal-width cells ordered exactly FRONT, TOP, RIGHT, LEFT, BOTTOM, REAR. Keep the rows in source order: row 1 outer corner; row 2 inner corner. Every cell is a separate true orthographic principal view, no isometric or perspective. The corner is two perpendicular, joined, equal-height wall wings. FRONT and REAR are broad rectangular constant-height elevations of the full joined corner assembly as seen along the chosen axis, showing both joined branches meeting at the corner; RIGHT and LEFT are the corresponding other pair of broad rectangular elevations, never a lone post. TOP is the same L-shaped footprint from directly above, with the two wall caps meeting at a right angle; BOTTOM is the matching L-shaped root/underside footprint from directly below. Do not draw the L plan as an elevation and do not turn the footprint into a square. Preserve each row\'s specific panel orientation and source identity: black inset panels, red panel fields where present, thick black framing, narrow gold trim, corner blocks, restrained pixel texture. Infer hidden surfaces conservatively and consistently. Match camera orientation across opposite directions; no extra objects, no labels, no shadows outside silhouettes, no cell spill or overlap. Align the six cells in each row precisely on a regular 6-column by 2-row grid with generous transparent gutters; each object fully inside its cell. Pixel-art game asset, crisp edges, restrained highlights, transparent background.'
   x['qa']={'status':'rejected-candidate-only','notes':'Transparent 6x2 atlas; front/rear retained source isometric angle. Retained as failed QA evidence; not a candidate for install.'}
  if fn.startswith('clubs-corners-batch02'):
   x['input_refs'][1]={'path':'../references/club-guide-six.jpg','sha256':sha(BASE+'/references/club-guide-six.jpg')}
  open(p,'w').write(json.dumps(x,indent=2)+'\n')
# Persist plan correction raw record.
planp=BASE+'/raw/'+rawdefs['club-plan-correction'][1]
plan_prompt=json.load(open(BASE+'/prompts/club-inner-plans-charcoal.prompt.json'))['prompt']
open(BASE+'/raw/club-inner-plans-charcoal-correction.json','w').write(json.dumps({'batch':'club-inner-plans-charcoal','tool':'image_gen.imagegen','tool_request_id':None,'generated_path':rawdefs['club-plan-correction'][0],'staged_raw_path':'raw/'+rawdefs['club-plan-correction'][1],'raw_sha256':raws['club-plan-correction']['sha256'],'dimensions':raws['club-plan-correction']['dimensions'],'prompt_path':'../prompts/club-inner-plans-charcoal.prompt.json','prompt_text':plan_prompt,'input_refs':[{'path':'../references/club-inner-plans-color-guide.png','sha256':sha(BASE+'/references/club-inner-plans-color-guide.png')},{'path':'clubs-guilds/components/clubs-guilds-dark-polished-club-panel-inner-corner.png','sha256':sha(D['objects'][1]['source']['path'])}],'qa':'Color-only corrective atlas visually replaces unsupported red plan surfaces with dark charcoal; candidate-only.'},indent=2)+'\n')
# Build club candidate from full-atlas connected components (by centroid), use correction atlas for inner plan cells.
views=['front','top','right','left','bottom','rear']
clubraw=Image.open(BASE+'/raw/clubs-corners-batch02-approved-candidate-atlas.png').convert('RGBA');W,H=clubraw.size;cw=W//6;ch=H//2
la=np.array(clubraw.getchannel('A'))>=64;lab,n=ndimage.label(la);sizes=np.bincount(lab.ravel());sizes[0]=0
# choose component by centroid within each nominal cell; compute all centroids once.
club_cells={};cc_qa={}; centers=ndimage.center_of_mass(la,lab,index=np.arange(1,len(sizes)))
for rr,o in enumerate(D['objects'][:2]):
 for cc,v in enumerate(views):
  candidates=[]
  for k,center in enumerate(centers,1):
   cy,cx=center
   if cc*cw <= cx < (cc+1)*cw and rr*ch <= cy < (rr+1)*ch:
    candidates.append((int(sizes[k]),int(k)))
  assert candidates,(rr,cc,'no component')
  candidates.sort(reverse=True);pix,k=candidates[0]
  yy,xx=np.where(lab==k);mask=lab==k;box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
  cell=clubraw.copy();cell.putalpha(Image.fromarray((mask*255).astype('uint8')))
  crop=cell.crop(box)
  club_cells[(rr,v)]=crop
  cc_qa[(rr,v)]={'component_label':k,'area_pixels':pix,'component_bbox_global_xyxy':list(box),'nominal_cell_xyxy':[cc*cw,rr*ch,(cc+1)*cw,(rr+1)*ch],'crosses_nominal_cell':box[0]<cc*cw or box[2]>(cc+1)*cw or box[1]<rr*ch or box[3]>(rr+1)*ch,'kept_full_atlas_component':True}
# plan corrector is two columns; map cells to nominal 362px source cell by uniform 362/cellwidth resolution calibration.
plan=Image.open(planp).convert('RGBA');pw,ph=plan.size; pcw=pw//2; correction={}
for c,v in [(0,'top'),(1,'bottom')]:
 crop=plan.crop((c*pcw,0,(c+1)*pcw,ph));al=np.asarray(crop.getchannel('A'));crop.putalpha(Image.fromarray(np.where(al>=64,255,0).astype('uint8')));box=crop.getchannel('A').getbbox();assert box
 crop=crop.crop(box);factor=cw/pcw; crop=crop.resize((round(crop.width*factor),round(crop.height*factor)),Image.Resampling.NEAREST);correction[v]=crop
# use corrected inner plan only, replacing generated red plan cells
for v in ('top','bottom'):
 club_cells[(1,v)]=correction[v]
# calibration scales: output common scale per row, considering all view crops, same atlas cell units after isotropic correction calibration
assets=[];sets=[]
for rr,o in enumerate(D['objects'][:2]):
 crops=[club_cells[(rr,v)] for v in views];maxdim=max(max(c.width,c.height) for c in crops);scale=200/maxdim
 cv={};qa=[]
 for v,crop in zip(views,crops):
  box=crop.getchannel('A').getbbox();crop=crop.crop(box);nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale));crop=crop.resize((nw,nh),Image.Resampling.NEAREST);out=Image.new('RGBA',(256,256),(0,0,0,0));ox=(256-nw)//2;oy=(256-nh)//2;out.alpha_composite(crop,(ox,oy));name=o['object_id']+'.'+v+'.png';p=BASE+'/images/'+name;out.save(p)
  entry={'asset_id':o['object_id']+'.'+v,'object_id':o['object_id'],'view':v,'candidate_path':'images/'+name,'sha256':sha(p),'width':256,'height':256,'anchor_px':[128,128],'provenance':{'method':'generated','source_image':o['source']['path'].replace('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/',''),'source_sha256':o['source']['sha256'],'generated_atlases':[{'path':'raw/clubs-corners-batch02-approved-candidate-atlas.png','sha256':raws['club-atlas']['sha256']},({'path':'raw/club-inner-plans-charcoal-correction.png','sha256':raws['club-plan-correction']['sha256']} if rr==1 and v in ('top','bottom') else {})],'geometry_guides':[{'path':'references/club-guide-six.jpg','sha256':sha(BASE+'/references/club-guide-six.jpg')},{'path':'references/club-corner-silhouette-guide.png','sha256':sha(BASE+'/references/club-corner-silhouette-guide.png')}],'notes':'Inferred orthographic art, not recovered source pixels.'},'normalization':{'raw_component':cc_qa.get((rr,v),{'plan_correction_cell':v,'uniform_resolution_calibration':cw/pcw,'alpha_bbox_in_plan_cell':list(box)}),'common_isotropic_scale_across_six_views':scale,'resampling':'NEAREST','offset_px':[ox,oy]}}
  assets.append(entry);cv[v]={'asset_id':entry['asset_id'],'path':entry['candidate_path'],'sha256':entry['sha256']};qa.append({'view':v,'candidate_alpha_bbox_256':list(out.getchannel('A').getbbox())})
 sets.append({'object_id':o['object_id'],'affected_views':views,'source':{'path':o['source']['path'].replace('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/',''),'sha256':o['source']['sha256']},'base_current_six':{v:{'path':e['path'].replace('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/',''),'sha256':e['sha256']} for v,e in o['current_six'].items()},'candidate_views':cv,'status':'candidate-only-pending-Page-review','cell_qa':qa,'common_isotropic_scale':scale,'anchor_px':[128,128],'notes':'Top/bottom remain inferred planes. Inner top/bottom use charcoal material correction; do not call underside pixels recovered.'})
cm={'created_at':'2026-10-26','scope':'book-tiles/dungeon-after-dark','assignment':'candidate-only; Page sole reviewer, Dark sole installer','batch':'clubs-corners-final-candidate','raw_manifests':['raw/clubs-corners-batch02-approved-candidate-atlas.json','raw/club-inner-plans-charcoal-correction.json'],'assets':assets,'objects':sets}
open(BASE+'/clubs-corners-final-candidates.json','w').write(json.dumps(cm,indent=2)+'\n')
# record global component qa and cross-cell ownership
open(BASE+'/raw/clubs-corners-global-component-map.json','w').write(json.dumps({'raw_atlas_sha256':raws['club-atlas']['sha256'],'grid':[6,2],'objects':{str(k):v for k,v in cc_qa.items()},'policy':'Full-atlas alpha threshold >=64/255; 4-connected CC; assign component by centroid to nominal cell, crop complete bbox even if it crosses the nominal cell; preserve no neighboring component.'},indent=2)+'\n')
# contact source+candidate six per object
contact=Image.new('RGBA',(7*256,2*300),(246,246,246,255));d=ImageDraw.Draw(contact)
for rr,(o,s) in enumerate(zip(D['objects'][:2],sets)):
 for col,(p,label) in enumerate([(o['source']['path'],'source')]+[(BASE+'/'+s['candidate_views'][v]['path'],v) for v in views]):
  z=Image.open(p).convert('RGBA');z.thumbnail((244,244));contact.alpha_composite(z,(col*256+(256-z.width)//2,rr*300+28+(244-z.height)//2));d.text((col*256+4,rr*300+4),label,fill=(0,0,0,255))
cp=BASE+'/clubs-corners-final-source-candidate-contact.png';contact.save(cp)
print('club raw sha',raws['club-atlas']['sha256'],'contact',sha(cp),'manifest',BASE+'/clubs-corners-final-candidates.json')
for s in sets:
 print(s['object_id'],s['common_isotropic_scale'],[(v,cc_qa.get((D['objects'].index(next(o for o in D['objects'][:2] if o['object_id']==s['object_id'])),v),{}).get('component_bbox_global_xyxy')) for v in views])
