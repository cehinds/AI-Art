from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib, os, math
HERE=Path(__file__).resolve().parent
PACK=HERE.parents[3]
OID='surface-entry-urban-brick-wall-northeast'
REPORT=HERE/'staged-wall-candidates.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
report=json.loads(REPORT.read_text())
record=next(s for s in report['sets'] if s['object_id']==OID)
# Verify the handoff source and all live views before creating staged candidates.
HAND=json.loads(Path('/workspace/scratch/inkbook-core-ne-wall-staging-handoff.json').read_text())
item=next(s for s in HAND['sets'] if s['object_id']==OID)
for view,ref in record['current_views'].items():
    live=(PACK/ref['path']).read_bytes()
    if sha(live)!=ref['sha256']:
        raise SystemExit(f'current view changed: {OID}.{view}')
if sha((PACK/item['source']['path']).read_bytes())!=item['source']['sha256']:
    raise SystemExit('canonical source changed')
# RIGHT/LEFT shared wall Z calibrates the two narrow end elevations.
side_heights=[]
for v in ('right','left'):
    im=Image.open(PACK/record['current_views'][v]['path']).convert('RGBA')
    b=im.getchannel('A').getbbox(); side_heights.append(b[3]-b[1])
target_z=sum(side_heights)/len(side_heights)
for v in ('front','rear'):
    ref=record['current_views'][v]
    path=PACK/ref['path']; raw=path.read_bytes(); im=Image.open(path).convert('RGBA')
    if sha(raw)!=ref['sha256']: raise SystemExit(f'donor changed: {OID}.{v}')
    bbox=im.getchannel('A').getbbox(); old_z=bbox[3]-bbox[1]
    scale=target_z/old_z
    # Scale uniformly around shared canvas anchor [128,128], retaining pixel art with nearest-neighbor.
    nw=max(1,round(im.width*scale)); nh=max(1,round(im.height*scale))
    scaled=im.resize((nw,nh),Image.Resampling.NEAREST)
    canvas=Image.new('RGBA',(256,256),(0,0,0,0))
    offset=(128-nw//2,128-nh//2)
    canvas.alpha_composite(scaled,offset)
    out=HERE/'candidates'/f'{OID}.{v}.candidate.png'; canvas.save(out,optimize=False)
    ab=canvas.getchannel('A').getbbox()
    record['candidates'][v]={
      'candidate_path':str(out.relative_to(HERE)), 'candidate_sha256':sha(out.read_bytes()),
      'candidate_rgba_sha256':hashlib.sha256(canvas.tobytes()).hexdigest(), 'size':[256,256],
      'alpha_bbox_xyxy':list(ab), 'current_source_view':v, 'donor_path':ref['path'], 'donor_sha256':sha(raw),
      'uniform_scale':scale, 'anchor_px':[128,128], 'resized_canvas_wh':[nw,nh], 'canvas_offset_xy':list(offset),
      'derivation':{'method':'uniform-rescale-existing-view','transform':'uniform nearest-neighbor scale about shared anchor [128,128]',
        'target_common_z_px':target_z,'source_alpha_bbox_xyxy':list(bbox),'source_z_px':old_z,
        'binding':'same target NE source view; deterministic calibration only, no new geometry or material'},
      'note':'Uniformly calibrated narrow end elevation to the mean retained RIGHT/LEFT wall Z; endcap proportions preserved.'}
# Existing TOP/BOTTOM candidate long spans are preserved because their 208px long axis matches the retained 207-208px RIGHT/LEFT broad-face width.
# Fresh compact source+old six+candidate six contact.
panels=[('SOURCE',PACK/item['source']['path'])]
for v in ('front','top','right','left','bottom','rear'):
    panels.append(('OLD-'+v.upper(),PACK/record['current_views'][v]['path']))
for v in ('front','top','right','left','bottom','rear'):
    cand=record['candidates'].get(v)
    panels.append((('CAND-' if cand else 'KEEP-')+v.upper(),HERE/cand['candidate_path'] if cand else PACK/record['current_views'][v]['path']))
contact=Image.new('RGBA',(len(panels)*170,340),(44,44,48,255)); draw=ImageDraw.Draw(contact)
for i,(label,path) in enumerate(panels):
    im=Image.open(path).convert('RGBA'); im.thumbnail((136,280),Image.Resampling.NEAREST)
    contact.alpha_composite(im,(i*170+17+(136-im.width)//2,38+(280-im.height)//2)); draw.text((i*170+3,20),label,fill='white')
out=HERE/'ne-wall-surface-entry-calibrated-candidates.png'; contact.save(out,optimize=False)
record['contact_path']=str(out.relative_to(HERE)); record['contact_sha256']=sha(out.read_bytes())
tmp=REPORT.with_suffix('.json.tmp'); tmp.write_text(json.dumps(report,indent=2)+'\n'); os.replace(tmp,REPORT)
print(json.dumps({'object_id':OID,'mean_side_z_px':target_z,'candidate_views':{v:{'sha256':record['candidates'][v]['candidate_sha256'],'alpha_bbox_xyxy':record['candidates'][v]['alpha_bbox_xyxy'],'scale':record['candidates'][v]['uniform_scale']} for v in ('front','rear')},'preserved_plan_longspan_px':208,'retained_face_width_px':side_heights,'contact':str(out),'contact_sha256':record['contact_sha256']},indent=2))
