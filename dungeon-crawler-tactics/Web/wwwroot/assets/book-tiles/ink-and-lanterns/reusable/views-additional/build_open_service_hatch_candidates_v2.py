"""Stage revised hatch FRONT/TOP/BOTTOM with accepted v1 REAR kept unchanged."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];OID='iron-trains-open-service-hatch';VIEWS=('front','top','right','left','bottom','rear');ATLAS=OUT/'raw/iron-trains-open-service-hatch-focused-v2-generated.png';SRC=PACK/'iron-trains/components/iron-trains-open-service-hatch.png';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 im=Image.open(ATLAS).convert('RGBA');a=np.asarray(im);assert im.size==(2172,724);cells={};crops={}
 for i,v in enumerate(('front','top','bottom')):
  local=a[:,i*724:(i+1)*724].copy();mask=local[:,:,3]>=250;y,x=np.where(mask);box=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
  if box[0]<12 or box[1]<12 or box[2]>712 or box[3]>712:raise RuntimeError(f'alpha250 cell contamination {v}: {box}')
  dil=binary_dilation(mask,structure=np.ones((3,3)));local[:,:,3]=np.where(dil,local[:,:,3],0);crop=Image.fromarray(local).crop((max(0,box[0]-2),max(0,box[1]-2),min(724,box[2]+2),min(724,box[3]+2)));crops[v]=crop;cells[v]={'cell_bbox_xyxy_global':[i*724,0,(i+1)*724,724],'alpha250_bbox_xyxy_cell':box,'alpha250_pixels':int(mask.sum())}
 scale=180/max(c.height for c in crops.values());idx=json.loads((OUT/'set-index.json').read_text());assets={a['id']:a for a in idx['assets']};g=next(g for g in idx['view_sets'] if g['object_id']==OID);cand={}
 for v in ('front','top','bottom'):
  c=crops[v];sz=(round(c.width*scale),round(c.height*scale));r=c.resize(sz,Image.Resampling.NEAREST);xy=((256-sz[0])//2,(256-sz[1])//2);can=Image.new('RGBA',(256,256));can.alpha_composite(r,xy);p=OUT/'raw'/f'{OID}.{v}.candidate-v2.png';can.save(p);cand[v]={'path':p.relative_to(PACK).as_posix(),'sha256':sha(p),'resized_wh':list(sz),'offset_xy':list(xy),'shared_uniform_scale':scale,'resampler':'NEAREST','transform':'alpha250 isolated cell crop'}
 rear=OUT/'raw/iron-trains-open-service-hatch.rear.candidate-v1.png';cand['rear']={'path':rear.relative_to(PACK).as_posix(),'sha256':sha(rear),'reuse':'Root-approved v1 REAR unchanged'}
 sheet=Image.new('RGB',(7*220,236),(239,235,226));d=ImageDraw.Draw(sheet);paths=[SRC]+[PACK/assets[g['views'][v]]['image']['path'] for v in VIEWS]
 for col,(p,label) in enumerate(zip(paths,('source',*VIEWS))):
  d.text((col*220+4,2),label,fill=(0,0,0));art=Image.open(PACK/cand[label]['path']).convert('RGBA') if label in cand else Image.open(p).convert('RGBA');art.thumbnail((208,208),Image.Resampling.NEAREST);sheet.paste(art,(col*220+(220-art.width)//2,24+(208-art.height)//2),art)
 contact=OUT/'raw/qa-iron-trains-open-service-hatch-candidate-v2-source-plus-six.png';sheet.save(contact,optimize=True);current={v:{'path':assets[g['views'][v]]['image']['path'],'sha256':sha(PACK/assets[g['views'][v]]['image']['path'])} for v in VIEWS};rec={'schema_version':1,'object_id':OID,'status':'candidate only; Root review required','source':{'path':SRC.relative_to(PACK).as_posix(),'sha256':sha(SRC)},'current_views':current,'raw_atlas':{'path':ATLAS.relative_to(PACK).as_posix(),'sha256':sha(ATLAS)},'request':'reusable/views-additional/raw/iron-trains-open-service-hatch-focused-v2.request.json','directions':cand,'shared_scale':scale,'target_accepted_side_height_px':180,'contact_path':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'notes':'TOP/BOTTOM use strict plan views with foreshortened ladder ends; REAR is the Root-approved v1 candidate unchanged. FRONT ladder visibility remains subject to Root review.'};rp=OUT/'raw/iron-trains-open-service-hatch-candidates-v2.json';rp.write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({'contact':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'receipt':rp.relative_to(PACK).as_posix(),'receipt_sha256':sha(rp),'scale':scale,'sizes':{v:cand[v].get('resized_wh') for v in ('front','top','bottom')}},indent=2))
if __name__=='__main__':main()
