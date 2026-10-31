from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,os
H=Path(__file__).resolve().parent;PACK=H.parents[3];p=H/'staged-wall-candidates.json';d=json.loads(p.read_text()); oid='bubble-airship-riveted-scrap-hull-wall-northeast';s=next(x for x in d['sets'] if x['object_id']==oid)
sha=lambda b:hashlib.sha256(b).hexdigest();left=s['candidates']['left'];src=H/left['candidate_path'];raw=src.read_bytes()
if sha(raw)!=left['candidate_sha256']:raise SystemExit('plain LEFT candidate hash mismatch')
im=Image.open(src).convert('RGBA')
if im.size!=(256,256):raise SystemExit(f'expected 256 square guide, got {im.size}')
out=H/'candidates'/f'{oid}.right.candidate.png';mir=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);mir.save(out,optimize=False)
ref=s['candidates']['right'];s['candidates']['right']={'candidate_path':str(out.relative_to(H)),'candidate_sha256':sha(out.read_bytes()),'candidate_rgba_sha256':hashlib.sha256(mir.tobytes()).hexdigest(),'size':[256,256],'alpha_bbox_xyxy':list(mir.getchannel('A').getbbox()),'derivation':{'method':'declared-opposite-face-symmetry','guide_view':'left','guide_path':left['candidate_path'],'guide_sha256':sha(raw),'transform':'horizontal flip within 256x256 canvas','binding':'target canonical NE source retained; inferred plain riveted face symmetry replaces unsupported porthole; no recovered pixels'},'note':'Plain riveted broad face inferred symmetric to the accepted plain opposite face; porthole omitted because target source does not establish one.'}
# refreshed full contact for this object
item=next(x for x in json.loads(Path('/workspace/scratch/inkbook-core-ne-wall-staging-handoff.json').read_text())['sets'] if x['object_id']==oid)
panels=[('SOURCE',PACK/item['source']['path'])]
for v in ('front','top','right','left','bottom','rear'):panels.append(('OLD-'+v.upper(),PACK/item['current_views'][v]['path']))
for v in ('front','top','right','left','bottom','rear'):
 c=s['candidates'].get(v);panels.append((('CAND-' if c else 'KEEP-')+v.upper(),H/c['candidate_path'] if c else PACK/item['current_views'][v]['path']))
contact=Image.new('RGBA',(len(panels)*170,340),(44,44,48,255));dr=ImageDraw.Draw(contact)
for i,(label,path) in enumerate(panels):
 x=Image.open(path).convert('RGBA');x.thumbnail((136,280),Image.Resampling.NEAREST);contact.alpha_composite(x,(i*170+17+(136-x.width)//2,38+(280-x.height)//2));dr.text((i*170+3,20),label,fill='white')
cp=H/'ne-wall-airship-plain-face-candidates.png';contact.save(cp,optimize=False);s['contact_path']=str(cp.relative_to(H));s['contact_sha256']=sha(cp.read_bytes());t=p.with_suffix('.json.tmp');t.write_text(json.dumps(d,indent=2)+'\n');os.replace(t,p)
print(json.dumps({'object_id':oid,'candidate_right_sha256':s['candidates']['right']['candidate_sha256'],'alpha_bbox':s['candidates']['right']['alpha_bbox_xyxy'],'contact':str(cp),'contact_sha256':s['contact_sha256']},indent=2))
