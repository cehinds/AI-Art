"""Extract the six isolated atlas cells into a shared-scale orthographic candidate set."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];OID='iron-tracks-tunnel-portal-frame';VIEWS=('front','top','right','left','bottom','rear')
ATLAS=OUT/'raw/iron-tracks-tunnel-portal-focused-views-v1-generated.png';SRC=PACK/'iron-tracks/components/iron-tracks-tunnel-portal-frame.png';INDEX=OUT/'set-index.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 im=Image.open(ATLAS).convert('RGBA');a=np.asarray(im);h,w=a.shape[:2];assert w%6==0 and h==724;cw=w//6
 lab,n=label(a[:,:,3]>=64,np.ones((3,3)));objects=[]
 # Each cell has one principal connected artwork; collect all alpha pixels within exact cell and retain complete bounds.
 cellrecords=[];crops=[]
 for col,view in enumerate(VIEWS):
  x0,x1=col*cw,(col+1)*cw;local=a[:,x0:x1];mask=local[:,:,3]>=64
  ys,xs=np.where(mask)
  if len(xs)==0:raise RuntimeError(f'empty view cell {view}')
  box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
  crop=Image.fromarray(local).crop(tuple(box));crops.append(crop);cellrecords.append({'view':view,'cell_bbox_xyxy_global':[x0,0,x1,h],'alpha_bbox_xyxy_cell':box,'alpha_pixels':int(mask.sum())})
 shared=208/max(max(c.size) for c in crops);candrows=[]
 for view,crop,record in zip(VIEWS,crops,cellrecords):
  sz=(round(crop.width*shared),round(crop.height*shared));res=crop.resize(sz,Image.Resampling.NEAREST);offset=((256-sz[0])//2,(256-sz[1])//2);canvas=Image.new('RGBA',(256,256));canvas.alpha_composite(res,offset)
  dest=OUT/'raw'/f'iron-tracks-tunnel-portal-frame.{view}.candidate-v1.png';canvas.save(dest)
  candrows.append({'view':view,'candidate_path':dest.relative_to(PACK).as_posix(),'candidate_sha256':sha(dest),'alpha_crop_bbox_xyxy_cell':record['alpha_bbox_xyxy_cell'],'cell_bbox_xyxy_global':record['cell_bbox_xyxy_global'],'resized_wh':list(sz),'offset_xy':list(offset),'shared_uniform_scale':shared,'resampler':'NEAREST'})
 index=json.loads(INDEX.read_text());assets={a['id']:a for a in index['assets']};group=next(g for g in index['view_sets'] if g['object_id']==OID)
 sheet=Image.new('RGB',(7*220,236),(239,235,226));draw=ImageDraw.Draw(sheet);paths=[SRC]+[PACK/assets[group['views'][v]]['image']['path'] for v in VIEWS]
 for col,(p,labeltxt) in enumerate(zip(paths,('source',*VIEWS))):
  draw.text((col*220+4,2),labeltxt,fill=(0,0,0)); art=Image.open(p).convert('RGBA')
  if col>0: art=Image.open(PACK/candrows[col-1]['candidate_path']).convert('RGBA')
  art.thumbnail((208,208),Image.Resampling.NEAREST);sheet.paste(art,(col*220+(220-art.width)//2,24+(208-art.height)//2),art)
 contact=OUT/'raw/qa-iron-tracks-tunnel-portal-frame-candidate-source-plus-six-v1.png';sheet.save(contact,optimize=True)
 current={v:{'path':assets[group['views'][v]]['image']['path'],'sha256':sha(PACK/assets[group['views'][v]]['image']['path'])} for v in VIEWS}
 receipt={'schema_version':1,'object_id':OID,'status':'candidate awaiting Root scoped approval','canonical_source':{'path':SRC.relative_to(PACK).as_posix(),'sha256':sha(SRC)},'current_views':current,'raw_atlas':{'path':ATLAS.relative_to(PACK).as_posix(),'sha256':sha(ATLAS)},'request_path':'reusable/views-additional/raw/iron-tracks-tunnel-portal-frame-focused-views-v1.request.json','layout':list(VIEWS),'shared_scale':shared,'cells':cellrecords,'candidates':candrows,'contact_path':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'notes':'All six are inferred axis-aligned views; source identity remains canonical. Not recovered pixels or calibrated 3D.'}
 rp=OUT/'raw/iron-tracks-tunnel-portal-frame-candidates-v1.json';rp.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'contact':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'receipt':rp.relative_to(PACK).as_posix(),'receipt_sha256':sha(rp),'scale':shared,'views':candrows},indent=2))
if __name__=='__main__':main()
