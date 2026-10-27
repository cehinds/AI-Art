"""Prepare a six-object camera-axis batch while retaining all unflagged directions."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;PACK=OUT.parent.parent
BATCHES=[
 ('surface','corner-batch-surface-urban-v2-atlas.png','corner-batch-surface-urban-v2.txt',['surface-entry-urban-brick-inner-corner','surface-entry-urban-brick-outer-corner'],['front','rear'],['right','left']),
 ('masquerade','corner-batch-masquerade-v1-atlas.png','corner-batch-masquerade-v1.txt',['masquerade-smooth-white-cubic-castle-inner-corner','masquerade-smooth-white-cubic-castle-outer-corner'],['front','rear'],['right','left']),
 ('zockau','corner-batch-zockau-v2-atlas.png','corner-batch-zockau-v2.txt',['hunting-zockau-painted-town-brick-inner-corner','hunting-zockau-painted-town-brick-outer-corner'],['right','left'],['front','rear'])]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def comps(im):
 lab,n=ndimage.label(np.asarray(im.getchannel('A'))>=32);r=[]
 for i,s in enumerate(ndimage.find_objects(lab),1):
  if s is None:continue
  y,x=s;area=int(np.count_nonzero(lab[s]==i))
  if area>1000:r.append((area,(x.start,y.start,x.stop,y.stop)))
 r.sort(key=lambda z:(z[1][1],z[1][0]));return r
def main():
 idx=json.loads((OUT/'set-index.json').read_text());assets={a['id']:a for a in idx['assets']};batches=[]
 for key,rawn,promptn,oids,newviews,calviews in BATCHES:
  raw=OUT/'raw'/rawn;im=Image.open(raw).convert('RGBA');cc=comps(im);assert len(cc)==4,(key,len(cc));reqname={'surface':'corner-batch-surface-urban-v2-request-result.json','masquerade':'corner-batch-masquerade-v1-request-result.json','zockau':'corner-batch-zockau-v2-request-result.json'}[key];req=json.loads((OUT/'prompts'/reqname).read_text());promptrel='reusable/views-additional/prompts/'+promptn;rawrel='reusable/views-additional/raw/'+rawn;sets=[]
  for ri,oid in enumerate(oids):
   target=[]
   for v in calviews:
    box=Image.open(PACK/assets[oid+'.'+v]['image']['path']).convert('RGBA').getchannel('A').getbbox();target.append(box[3]-box[1])
   targetheight=round(sum(target)/len(target));objs=cc[ri*2:(ri+1)*2];maxh=max(b[3]-b[1] for _,b in objs);scale=targetheight/maxh;views=[]
   for v,(area,b) in zip(newviews,objs):
    x0,y0,x1,y1=b;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(im.width,x1+3);y1=min(im.height,y1+3);crop=im.crop((x0,y0,x1,y1));nw=round(crop.width*scale);nh=round(crop.height*scale);r=crop.resize((nw,nh),Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(r,((256-nw)//2,(256-nh)//2));dst=OUT/'candidates/corner-batch-six-camera-v1'/f'{oid}.{v}.png';dst.parent.mkdir(parents=True,exist_ok=True);can.save(dst);a=assets[f'{oid}.{v}'];views.append({'object_id':oid,'view':v,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'base_sha256':sha(PACK/a['image']['path']),'raw_atlas':rawrel,'raw_atlas_sha256':sha(raw),'prompt_path':promptrel,'prompt_sha256':sha(OUT/'prompts'/promptn),'reference_paths':req['reference_paths'],'reference_sha256':req['reference_sha256'],'component_bbox_threshold32':list(b),'component_area_threshold32':area,'crop_rect_with_padding':[x0,y0,x1,y1],'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128],'calibration_target_height_px':targetheight})
   sets.append({'object_id':oid,'calibration_views':calviews,'target_height_px':targetheight,'views':views})
  batches.append({'batch_id':key,'sets':sets})
 spec={'candidate_id':'corner-batch-six-camera-v1','batches':batches,'normalization':'one shared isotropic scale per object across its repaired directions; accepted unflagged directions preserved'};p=OUT/'candidates/corner-batch-six-camera-v1.json';p.write_text(json.dumps(spec,indent=2)+'\n');print(p)
if __name__=='__main__':main()
