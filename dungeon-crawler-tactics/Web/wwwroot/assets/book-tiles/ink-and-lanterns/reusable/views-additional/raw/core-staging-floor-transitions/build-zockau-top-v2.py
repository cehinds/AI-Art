from pathlib import Path
from PIL import Image, ImageDraw
import hashlib,json
D=Path(__file__).resolve().parent; PACK=D.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((D/'staged-floor-transitions-batch-02-zockau.json').read_text());s=r['sets'][0];oid=s['object_id']
source=PACK/s['source']['path']; assert sha(source)==s['source']['sha256']
# Verify all six live bases still match captured request before producing the candidate.
for v,ref in s['current_views'].items(): assert sha(PACK/ref['path'])==ref['sha256'],(v,'current hash drift')
orig=D/s['candidate_views']['top']['candidate_path']; assert sha(orig)==s['candidate_views']['top']['candidate_sha256']
im=Image.open(orig).convert('RGBA'); bbox=im.getchannel('A').getbbox(); assert bbox==(64,128,192,256),bbox
crop=im.crop(bbox); target=210; scale=target/crop.width; side=round(crop.width*scale); assert side==210
res=crop.resize((side,side),Image.Resampling.NEAREST); can=Image.new('RGBA',(256,256),(0,0,0,0)); offset=((256-side)//2,(256-side)//2); can.alpha_composite(res,offset)
outdir=D/'candidates'/'zockau-edge-v2';outdir.mkdir(parents=True,exist_ok=True);out=outdir/f'{oid}.top.candidate.png';can.save(out,optimize=False)
# Compose source + unchanged current six + proposed six, with only TOP revised.
contact=Image.new('RGBA',(13*164,340),(42,42,46,255));draw=ImageDraw.Draw(contact);paths=[('SOURCE',source)]+[(f'OLD-{v.upper()}',PACK/ref['path']) for v,ref in s['current_views'].items()]
for v in ('front','top','right','left','bottom','rear'):
 p=out if v=='top' else (D/s['candidate_views'][v]['candidate_path'] if v in s['candidate_views'] else PACK/s['current_views'][v]['path']); paths.append((f'CAND-{v.upper()}',p))
for j,(label,p) in enumerate(paths):
 q=Image.open(p).convert('RGBA');q.thumbnail((128,280),Image.Resampling.NEAREST);contact.alpha_composite(q,(j*164+18+(128-q.width)//2,36+(280-q.height)//2));draw.text((j*164+2,16),label,fill='white')
cp=D/f'{oid}.candidate-source-current-six-v2.png';contact.save(cp,optimize=False)
rr={**r,'batch':'floor-transitions-02-zockau-top-v2','sets':[dict(s)]};rr['sets'][0]['candidate_views']=dict(s['candidate_views']);rr['sets'][0]['candidate_views']['top']={'candidate_path':str(out.relative_to(D)),'candidate_sha256':sha(out),'size_wh':[256,256],'alpha_bbox_xyxy':list(can.getchannel('A').getbbox()),'derivation':{'method':'native-source-top-uniform-reframe','source_path':s['source']['path'],'source_sha256':s['source']['sha256'],'source_alpha_bbox_xyxy':list(bbox),'crop_xyxy':list(bbox),'uniform_scale':scale,'resized_wh':[side,side],'offset_xy':list(offset),'anchor_px':[128,128],'raw_candidate_path':str(orig.relative_to(D)),'raw_candidate_sha256':sha(orig),'note':'Exact canonical native TOP pixels cropped to their alpha bounds and uniformly nearest-neighbor scaled to match 210px lateral XY span; no perspective or anisotropic deformation.'}}
rr['sets'][0]['contact_path']=cp.name;rr['sets'][0]['contact_sha256']=sha(cp);rr['sets'][0]['note']='TOP size correction only; all other candidates and accepted current siblings unchanged.'
report=D/'staged-floor-transitions-batch-02-zockau-v2.json';report.write_text(json.dumps(rr,indent=2)+'\n')
print(json.dumps({'object_id':oid,'candidate':str(out),'candidate_sha256':sha(out),'bbox':list(can.getchannel('A').getbbox()),'contact':str(cp),'contact_sha256':sha(cp),'report':str(report)},indent=2))
