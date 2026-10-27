"""Extract and calibrate the three isolated open-service-hatch views."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];OID='iron-trains-open-service-hatch';VIEWS=('front','top','rear');ATLAS=OUT/'raw/iron-trains-open-service-hatch-focused-v1-generated.png';SRC=PACK/'iron-trains/components/iron-trains-open-service-hatch.png';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 img=Image.open(ATLAS).convert('RGBA');a=np.asarray(img);assert img.size==(2172,724);crops={};cells={}
 for i,v in enumerate(VIEWS):
  local=a[:,i*724:(i+1)*724];mask=local[:,:,3]>=245;ys,xs=np.where(mask)
  box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
  if box[0]<12 or box[1]<12 or box[2]>712 or box[3]>712:raise RuntimeError(f'edge contamination for {v}: {box}')
  soft=binary_dilation(mask,structure=np.ones((3,3)));full=local.copy();full[:,:,3]=np.where(soft,full[:,:,3],0);crop=Image.fromarray(full).crop(tuple([max(0,box[0]-2),max(0,box[1]-2),min(724,box[2]+2),min(724,box[3]+2)]));crops[v]=crop;cells[v]={'cell_bbox_xyxy_global':[i*724,0,(i+1)*724,724],'alpha245_bbox_xyxy_cell':box,'alpha245_pixels':int(mask.sum())}
 # Keep lid elevation at common Z with current accepted broad sides (180px alpha extent).
 raw_scale=180/max(c.height for c in crops.values());index=json.loads((OUT/'set-index.json').read_text());assets={x['id']:x for x in index['assets']};group=next(g for g in index['view_sets'] if g['object_id']==OID);cand={}
 for v in VIEWS:
  c=crops[v];sz=(round(c.width*raw_scale),round(c.height*raw_scale));r=c.resize(sz,Image.Resampling.NEAREST);xy=((256-sz[0])//2,(256-sz[1])//2);can=Image.new('RGBA',(256,256));can.alpha_composite(r,xy);p=OUT/'raw'/f'{OID}.{v}.candidate-v1.png';can.save(p);cand[v]={'path':p.relative_to(PACK).as_posix(),'sha256':sha(p),'crop_bbox_cell':cells[v]['alpha245_bbox_xyxy_cell'],'resized_wh':list(sz),'offset_xy':list(xy),'uniform_shared_scale':raw_scale,'resampler':'NEAREST'}
 sheet=Image.new('RGB',(7*220,236),(239,235,226));d=ImageDraw.Draw(sheet);paths=[SRC]+[PACK/assets[group['views'][v]]['image']['path'] for v in ('front','top','right','left','bottom','rear')]
 for col,(p,label) in enumerate(zip(paths,('source','front','top','right','left','bottom','rear'))):
  d.text((col*220+4,2),label,fill=(0,0,0));art=Image.open(p).convert('RGBA') if col==0 else (Image.open(PACK/cand[{1:'front',2:'top',6:'rear'}[col]]['path']).convert('RGBA') if col in (1,2,6) else Image.open(p).convert('RGBA'));art.thumbnail((208,208),Image.Resampling.NEAREST);sheet.paste(art,(col*220+(220-art.width)//2,24+(208-art.height)//2),art)
 contact=OUT/'raw/qa-iron-trains-open-service-hatch-candidate-v1-source-plus-six.png';sheet.save(contact,optimize=True);current={v:{'path':assets[group['views'][v]]['image']['path'],'sha256':sha(PACK/assets[group['views'][v]]['image']['path'])} for v in ('front','top','right','left','bottom','rear')};rec={'schema_version':1,'object_id':OID,'status':'candidate only, Root review required','canonical_source':{'path':SRC.relative_to(PACK).as_posix(),'sha256':sha(SRC)},'current_views':current,'raw_atlas':{'path':ATLAS.relative_to(PACK).as_posix(),'sha256':sha(ATLAS)},'request_path':'reusable/views-additional/raw/iron-trains-open-service-hatch-focused-v1.request.json','shared_scale':raw_scale,'source_height_reference_px':180,'cell_records':cells,'candidates':cand,'contact_path':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'notes':'Inferred principal views; open lid state retained; not recovered pixels or calibrated 3D.'};rp=OUT/'raw/iron-trains-open-service-hatch-candidates-v1.json';rp.write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({'contact':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'receipt':rp.relative_to(PACK).as_posix(),'receipt_sha256':sha(rp),'scale':raw_scale,'sizes':{v:cand[v]['resized_wh'] for v in VIEWS}},indent=2))
if __name__=='__main__':main()
