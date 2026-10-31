from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,os
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[3];oid='bubble-glass-sand-coloured-glass-wall-northeast';HAND=json.loads(Path('/workspace/scratch/inkbook-core-ne-wall-staging-handoff.json').read_text());item=next(x for x in HAND['sets'] if x['object_id']==oid)
cur=item['current_views'];V=PACK/'reusable/views-additional';OUT=HERE/'candidates';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
# Use target's already-retained plain sand block edge profiles; uniform calibration to NW approved common wall Z.
nw=next(x for x in json.loads(Path('/workspace/scratch/view-review-merged.json').read_text())['libraries'] if x['scope']=='book-tiles/ink-and-lanterns'); nwset=next(x for x in nw['sets'] if x['object_id']=='bubble-glass-sand-coloured-glass-wall-northwest')
heights=[]
for v in ('front','rear'):
 im=Image.open(PACK/nwset['views'][v]['path']).convert('RGBA'); b=im.getchannel('A').getbbox();heights.append(b[3]-b[1])
target_z=sum(heights)/len(heights)
rows={}
for target,donor in [('front','right'),('rear','left')]:
 p=PACK/cur[donor]['path']; live=p.read_bytes()
 if sha(live)!=cur[donor]['sha256']:raise SystemExit(f'live donor changed {oid}.{donor}')
 im=Image.open(p).convert('RGBA');b=im.getchannel('A').getbbox(); z=b[3]-b[1]; scale=target_z/z
 w,h=round(im.width*scale),round(im.height*scale);res=im.resize((w,h),Image.Resampling.LANCZOS); canvas=Image.new('RGBA',(256,256),(0,0,0,0));off=(128-w//2,128-h//2);canvas.alpha_composite(res,off)
 out=OUT/f'{oid}.{target}.candidate.png';canvas.save(out,optimize=False)
 rows[target]={'candidate_path':str(out.relative_to(HERE)),'candidate_sha256':sha(out.read_bytes()),'current_source_view':donor,'donor_path':cur[donor]['path'],'donor_sha256':sha(live),'NW_guide':{'object_id':nwset['object_id'],'path':nwset['views'][('front' if target=='front' else 'rear')]['path'],'sha256':nwset['views'][('front' if target=='front' else 'rear')]['sha256'],'status':'passed'},'uniform_scale':scale,'source_bbox_xyxy':list(b),'resized_wh':[w,h],'canvas_offset_xy':list(off),'note':'Target-native plain sandy-glass endcourse/profile reused, uniformly calibrated to passed same-kit common wall Z; no blue gem/window motif introduced.'}
# Update specific NE set staged record; unchanged other staged candidates remain exact.
p=HERE/'staged-wall-candidates.json';report=json.loads(p.read_text());record=next(x for x in report['sets'] if x['object_id']==oid)
for v,row in rows.items():record['candidates'][v]=row
# Contact source + six current + six staged (KEEP preserved directions)
out=Image.new('RGBA',(13*170,340),(44,44,48,255));d=ImageDraw.Draw(out)
source=PACK/item['source']['path'];panels=[('SOURCE',source)]+[('OLD-'+v.upper(),PACK/cur[v]['path']) for v in ['front','top','right','left','bottom','rear']]
for v in ['front','top','right','left','bottom','rear']:
 path=HERE/record['candidates'][v]['candidate_path'] if v in record['candidates'] else PACK/cur[v]['path'];panels.append((('CAND-' if v in record['candidates'] else 'KEEP-')+v.upper(),path))
for col,(label,path) in enumerate(panels):
 im=Image.open(path).convert('RGBA');im.thumbnail((136,280),Image.Resampling.NEAREST);out.alpha_composite(im,(col*170+17+(136-im.width)//2,38+(280-im.height)//2));d.text((col*170+3,20),label,fill='white')
cp=HERE/'ne-wall-bubble-glass-final-candidates.png';out.save(cp);record['contact_path']=str(cp.relative_to(HERE));record['contact_sha256']=sha(cp.read_bytes());report_path=p.with_suffix('.json.tmp');report_path.write_text(json.dumps(report,indent=2)+'\n');os.replace(report_path,p)
print(json.dumps({'object_id':oid,'target_z_px':target_z,'staged_views':rows,'contact':str(cp),'contact_sha256':record['contact_sha256']},indent=2))
