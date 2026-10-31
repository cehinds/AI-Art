"""Extract the isolated three-panel booth side/rear atlas at shared object scale."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];OID='safe-services-restaurant-dining-booth';VIEWS=('right','left','rear');ATLAS=OUT/'raw/safe-services-restaurant-dining-booth-sides-v2-generated.png';SRC=PACK/'safe-services/components/safe-services-restaurant-dining-booth.png';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 im=Image.open(ATLAS).convert('RGBA');a=np.asarray(im);assert im.size==(2172,724);crops={};boxes={}
 for i,v in enumerate(VIEWS):
  local=a[:,i*724:(i+1)*724];mask=local[:,:,3]>=245;ys,xs=np.where(mask);box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
  if box[0]<12 or box[1]<12 or box[2]>712 or box[3]>712:raise RuntimeError(f'cell contamination/crop {v}: {box}')
  dil=binary_dilation(mask,structure=np.ones((3,3)));local=local.copy();local[:,:,3]=np.where(dil,local[:,:,3],0);crop=Image.fromarray(local).crop((max(0,box[0]-2),max(0,box[1]-2),min(724,box[2]+2),min(724,box[3]+2)));crops[v]=crop;boxes[v]=box
 scale=208/max(max(c.width,c.height) for c in crops.values());idx=json.loads((OUT/'set-index.json').read_text());assets={a['id']:a for a in idx['assets']};g=next(g for g in idx['view_sets'] if g['object_id']==OID);cand={}
 for v in VIEWS:
  c=crops[v];sz=(round(c.width*scale),round(c.height*scale));res=c.resize(sz,Image.Resampling.NEAREST);xy=((256-sz[0])//2,(256-sz[1])//2);can=Image.new('RGBA',(256,256));can.alpha_composite(res,xy);p=OUT/'raw'/f'{OID}.{v}.candidate-v2.png';can.save(p);cand[v]={'path':p.relative_to(PACK).as_posix(),'sha256':sha(p),'alpha245_bbox_xyxy_cell':boxes[v],'resized_wh':list(sz),'offset_xy':list(xy),'uniform_shared_scale':scale,'resampler':'NEAREST'}
 sheet=Image.new('RGB',(7*220,236),(239,235,226));dr=ImageDraw.Draw(sheet);paths=[SRC]+[PACK/assets[g['views'][v]]['image']['path'] for v in ('front','top','right','left','bottom','rear')]
 for col,(p,label) in enumerate(zip(paths,('source','front','top','right','left','bottom','rear'))):
  dr.text((col*220+4,2),label,fill=(0,0,0));art=Image.open(PACK/cand[label]['path']).convert('RGBA') if label in cand else Image.open(p).convert('RGBA');art.thumbnail((208,208),Image.Resampling.NEAREST);sheet.paste(art,(col*220+(220-art.width)//2,24+(208-art.height)//2),art)
 contact=OUT/'raw/qa-safe-services-restaurant-dining-booth-candidate-v2-source-plus-six.png';sheet.save(contact,optimize=True);current={v:{'path':assets[g['views'][v]]['image']['path'],'sha256':sha(PACK/assets[g['views'][v]]['image']['path'])} for v in ('front','top','right','left','bottom','rear')};rec={'schema_version':1,'object_id':OID,'status':'candidate only; Root scoped review required','canonical_source':{'path':SRC.relative_to(PACK).as_posix(),'sha256':sha(SRC)},'current_views':current,'raw_atlas':{'path':ATLAS.relative_to(PACK).as_posix(),'sha256':sha(ATLAS)},'request_path':'reusable/views-additional/raw/safe-services-restaurant-dining-booth-sides-v2.request.json','direction_order':list(VIEWS),'shared_scale':scale,'cell_alpha_bboxes':boxes,'candidates':cand,'contact_path':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'notes':'Source identity/seat count preserved. These are inferred axis-aligned side/rear views, not recovered pixels.'};rp=OUT/'raw/safe-services-restaurant-dining-booth-candidates-v2.json';rp.write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({'contact':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'receipt':rp.relative_to(PACK).as_posix(),'receipt_sha256':sha(rp),'shared_scale':scale,'sizes':{v:cand[v]['resized_wh'] for v in VIEWS}},indent=2))
if __name__=='__main__':main()
