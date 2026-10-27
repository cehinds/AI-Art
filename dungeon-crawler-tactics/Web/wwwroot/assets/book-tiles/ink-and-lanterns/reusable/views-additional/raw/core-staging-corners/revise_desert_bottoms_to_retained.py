from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,os
H=Path(__file__).resolve().parent;BASE=H.parents[3];p=H/'staged-corners-batch-01.json';d=json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
for s in d['sets']:
 old=s['candidate_views'].pop('bottom');s['rejected_candidates']={'bottom':{'path':old['candidate_path'],'sha256':old['candidate_sha256'],'reason':'Root prefers the current source-matched stone-backed underside L over a 180-degree copy that repeats top-facing pegs.'}}
 item=next(x for x in json.loads((H/'current-corner-handoff.json').read_text())['sets'] if x['object_id']==s['object_id'])
 cur=Image.open(BASE/item['current_views']['bottom']['path']).convert('RGBA');s['retained_views']={'bottom':{'path':item['current_views']['bottom']['path'],'sha256':item['current_views']['bottom']['sha256'],'size_wh':list(cur.size),'alpha_bbox_xyxy':list(cur.getchannel('A').getbbox()),'reason':'Retain existing stone-backed L underside; no pixel edit or scaling.'}}
 panels=[('SOURCE',BASE/item['source']['path'])]+[('OLD-'+v.upper(),BASE/item['current_views'][v]['path']) for v in ['front','top','right','left','bottom','rear']]
 for v in ['front','top','right','left','bottom','rear']:
  if v in s['candidate_views']:path=H/s['candidate_views'][v]['candidate_path'];label='CAND-'+v.upper()
  else:path=BASE/item['current_views'][v]['path'];label='KEEP-'+v.upper()
  panels.append((label,path))
 contact=Image.new('RGBA',(13*164,340),(42,42,46,255));dr=ImageDraw.Draw(contact)
 for col,(lab,path) in enumerate(panels):
  im=Image.open(path).convert('RGBA');im.thumbnail((128,280),Image.Resampling.NEAREST);contact.alpha_composite(im,(col*164+18+(128-im.width)//2,36+(280-im.height)//2));dr.text((col*164+2,16),lab,fill='white')
 cp=H/f'corner-candidates-{s["object_id"]}.png';contact.save(cp,optimize=False);s['contact_path']=cp.name;s['contact_sha256']=sha(cp.read_bytes())
tmp=p.with_suffix('.json.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n');os.replace(tmp,p)
print(json.dumps([{'id':s['object_id'],'contact':s['contact_path'],'sha256':s['contact_sha256'],'candidate_views':list(s['candidate_views']),'retained_bottom':s['retained_views']['bottom']['alpha_bbox_xyxy']} for s in d['sets']],indent=2))
