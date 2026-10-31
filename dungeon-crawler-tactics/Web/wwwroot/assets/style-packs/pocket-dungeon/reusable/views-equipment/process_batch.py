from PIL import Image
import json,hashlib,struct,math,shutil
from pathlib import Path
ROOT=Path('/workspace/dungeon-crawler-tactics/Web/wwwroot/assets/style-packs/pocket-dungeon')
OUT=ROOT/'reusable/views-equipment'
raw=Path('/workspace/generated_images/exec-a78e2798-9b6d-4571-aed3-5c2007c11c10.png')
shutil.copy2(raw,OUT/'raw/arsenal-dagger-rapier-longsword.png')
im=Image.open(raw).convert('RGBA')
w,h=im.size
cols=['front','top','right','left','bottom','rear']
objects=[('arsenal-dagger','Dagger','arsenal'),('arsenal-rapier','Rapier','arsenal'),('arsenal-longsword','Longsword','arsenal')]
assets=[]; sets=[]
for ri,(oid,name,kind) in enumerate(objects):
  # common square frame for all six views; common scale based on tallest/widest observed silhouette
  boxes=[]; crops=[]
  for ci in range(6):
    x0=round(ci*w/6); x1=round((ci+1)*w/6); y0=round(ri*h/3); y1=round((ri+1)*h/3)
    cell=im.crop((x0,y0,x1,y1)); alpha=cell.getchannel('A'); box=alpha.getbbox()
    if not box: raise ValueError((oid,ci,'empty'))
    crops.append(cell.crop(box)); boxes.append(box)
  maxdim=max(max(c.size) for c in crops); scale=204/maxdim
  refs={}
  for view,crop in zip(cols,crops):
    nw=max(1,round(crop.width*scale)); nh=max(1,round(crop.height*scale))
    crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(256,256),(0,0,0,0)); px=(256-nw)//2; py=(256-nh)//2
    canvas.alpha_composite(crop,(px,py))
    aid=oid+'.'+view
    ip=OUT/'images'/f'{aid}.png'; mp=ip.with_suffix('.json')
    canvas.save(ip,optimize=True)
    data=ip.read_bytes(); rgba=canvas.tobytes(); ih=hashlib.sha256(data).hexdigest(); rh=hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest()
    meta={'id':aid,'name':name+' '+view.replace('-',' ').title(),'kind':kind,'tags':['pocket-dungeon','six-view','orthographic',kind],'image':{'path':str(ip.relative_to(ROOT)),'width':256,'height':256,'sha256':ih,'rgba_sha256':rh},'object_id':oid,'view':view,'provenance':{'method':'generated','source_image':f'components/{oid}.png','notes':'Generated orthographic view; unseen surfaces conservatively inferred, not recovered pixels.'},'anchor_px':{'x':128,'y':128}}
    mp.write_text(json.dumps(meta,indent=2)+'\n')
    meta['metadata_path']=str(mp.relative_to(ROOT)); assets.append(meta);refs[view]=aid
  sets.append({'object_id':oid,'views':refs,'complete':True,'notes':'Generated six-view orthographic set; inferred hidden surfaces.'})
index=OUT/'set-index.json';index.write_text(json.dumps({'assets':assets,'view_sets':sets},indent=2)+'\n')
