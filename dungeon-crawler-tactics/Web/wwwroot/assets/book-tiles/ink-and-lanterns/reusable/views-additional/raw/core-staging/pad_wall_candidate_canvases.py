from pathlib import Path
from PIL import Image
import json,hashlib,os,shutil
H=Path(__file__).resolve().parent; REPORT=H/'staged-wall-candidates.json'; OUT=H/'candidates'; PAD=H/'canvas-padding-manifest.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads(REPORT.read_text()); padlog=[]
for s in r['sets']:
 for view,c in s['candidates'].items():
  p=H/c['candidate_path']; im=Image.open(p).convert('RGBA')
  if im.size==(256,256): continue
  old_sha=sha(p); old_size=list(im.size); old_bbox=list(im.getchannel('A').getbbox())
  if im.width>256 or im.height>256: raise SystemExit(f'candidate exceeds 256 canvas: {s["object_id"]}.{view} {im.size}')
  ox=(256-im.width)//2; oy=(256-im.height)//2
  canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(im,(ox,oy))
  # Preserve the unpadded candidate as raw staging evidence, never as an installable candidate.
  archival=H/'candidates'/'prepad'; archival.mkdir(parents=True,exist_ok=True)
  archive=archival/f'{s["object_id"]}.{view}.prepad.png'
  if not archive.exists(): shutil.copy2(p,archive)
  canvas.save(p,optimize=False); new_sha=sha(p); bbox=list(canvas.getchannel('A').getbbox())
  c['candidate_sha256']=new_sha; c['candidate_rgba_sha256']=hashlib.sha256(canvas.tobytes()).hexdigest(); c['size']=[256,256];c['alpha_bbox_xyxy']=bbox
  c['derivation']=c.get('derivation',{})
  c['derivation']['canvas_padding']={'method':'transparent-center-pad-no-rescale','old_size_wh':old_size,'old_file_sha256':old_sha,'old_candidate_path':str(archive.relative_to(H)),'offset_xy':[ox,oy],'new_size_wh':[256,256],'anchor_px':[128,128]}
  padlog.append({'object_id':s['object_id'],'view':view,'old_path':c['candidate_path'],'old_sha256':old_sha,'old_size_wh':old_size,'old_alpha_bbox_xyxy':old_bbox,'archived_prepad_path':str(archive.relative_to(H)),'offset_xy':[ox,oy],'new_candidate_path':c['candidate_path'],'new_sha256':new_sha,'new_size_wh':[256,256],'new_alpha_bbox_xyxy':bbox})
# Rebuild source+old six+candidate/kept six contacts per affected set, and update hashes.
from PIL import ImageDraw
for s in r['sets']:
 if not any(x['object_id']==s['object_id'] for x in padlog): continue
 panels=[('SOURCE',H.parents[3]/s['source']['path'])]
 for v in ['front','top','right','left','bottom','rear']: panels.append(('OLD-'+v.upper(),H.parents[3]/s['current_views'][v]['path']))
 for v in ['front','top','right','left','bottom','rear']:
  c=s['candidates'].get(v); panels.append((('CAND-' if c else 'KEEP-')+v.upper(),H/c['candidate_path'] if c else H.parents[3]/s['current_views'][v]['path']))
 contact=Image.new('RGBA',(len(panels)*170,340),(44,44,48,255));d=ImageDraw.Draw(contact)
 for i,(label,path) in enumerate(panels):
  im=Image.open(path).convert('RGBA');im.thumbnail((136,280),Image.Resampling.NEAREST);contact.alpha_composite(im,(i*170+17+(136-im.width)//2,38+(280-im.height)//2));d.text((i*170+3,20),label,fill='white')
 out=H/f'ne-wall-{s["object_id"]}-padded-candidates.png';contact.save(out,optimize=False);s['contact_path']=str(out.relative_to(H));s['contact_sha256']=sha(out)
tmp=REPORT.with_suffix('.json.tmp');tmp.write_text(json.dumps(r,indent=2)+'\n');os.replace(tmp,REPORT)
PAD.write_text(json.dumps({'method':'deterministic center-pad onto 256x256 transparent RGBA canvas; no resizing, rotation or alpha editing','records':padlog},indent=2)+'\n')
print(json.dumps({'padded':padlog,'padding_manifest':str(PAD)},indent=2))
