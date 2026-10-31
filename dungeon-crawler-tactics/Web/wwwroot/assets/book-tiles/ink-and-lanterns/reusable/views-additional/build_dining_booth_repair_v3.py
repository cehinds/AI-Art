"""Stage broad booth outer-back side projections and an underside plan."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from scipy.ndimage import binary_dilation
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];OID='safe-services-restaurant-dining-booth';VIEWS=('front','top','right','left','bottom','rear');ATLAS=OUT/'raw/safe-services-restaurant-dining-booth-v3-generated.png';SRC=PACK/'safe-services/components/safe-services-restaurant-dining-booth.png';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cropcell(i,box=None):
 im=Image.open(ATLAS).convert('RGBA');a=np.asarray(im);local=a[:,i*724:(i+1)*724]
 if box is None:
  mask=local[:,:,3]>=245;y,x=np.where(mask);box=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
 else:box=list(box)
 ext=(max(0,box[0]-2),max(0,box[1]-2),min(724,box[2]+2),min(724,box[3]+2));return Image.fromarray(local).crop(ext),box

def canvas(c,scale,view,trans):
 sz=(round(c.width*scale),round(c.height*scale));res=c.resize(sz,Image.Resampling.NEAREST);xy=((256-sz[0])//2,(256-sz[1])//2);o=Image.new('RGBA',(256,256));o.alpha_composite(res,xy);p=OUT/'raw'/f'{OID}.{view}.candidate-v3.png';o.save(p);return {'path':p.relative_to(PACK).as_posix(),'sha256':sha(p),'resized_wh':list(sz),'offset_xy':list(xy),'uniform_scale':scale,'resampler':'NEAREST','transform':trans}
def main():
 # extract panel only from first view: exclude side table/pedestal; keep back cushion, brown uprights and base.
 # Native atlas cell0 panel spans x315..558; transparent margin remains around the whole panel.
 panel,box=cropcell(0,[315,227,554,484]);mask=np.asarray(panel)[:,:,3]>=245;y,x=np.where(mask);panelbox=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)];panel=panel.crop(tuple(panelbox));# scale its Z to current front-view height
 idx=json.loads((OUT/'set-index.json').read_text());assets={a['id']:a for a in idx['assets']};g=next(g for g in idx['view_sets'] if g['object_id']==OID);front=Image.open(PACK/assets[g['views']['front']]['image']['path']).convert('RGBA');f=np.array(front)[:,:,3]>=64;fy,fx=np.where(f);targetz=int(fy.max()+1-fy.min());side_scale=targetz/panel.height
 cand={}
 for v in ('front','top'):
  a=assets[g['views'][v]]['image']['path'];pp=PACK/a;cand[v]={'path':a,'sha256':sha(pp),'reuse':'existing accepted direction unchanged'}
 rear=OUT/'raw/safe-services-restaurant-dining-booth.rear.candidate-v2.png';cand['rear']={'path':rear.relative_to(PACK).as_posix(),'sha256':sha(rear),'reuse':'Root-approved v2 rear candidate unchanged','raw_atlas':'reusable/views-additional/raw/safe-services-restaurant-dining-booth-sides-v2-generated.png'}
 cand['right']=canvas(panel,side_scale,'right','cropped outer booth-back rectangle; table and pedestal excluded');cand['right'].update({'source_atlas_cell':0,'source_crop_bbox_xyxy':[315+panelbox[0],227+panelbox[1],315+panelbox[2],227+panelbox[3]],'target_common_z_px':targetz})
 cand['left']=canvas(ImageOps.mirror(panel),side_scale,'left','horizontal mirror of same-object outer back for opposite side');cand['left'].update({'donor_view':'right','donor_sha256':cand['right']['sha256'],'target_common_z_px':targetz})
 # Bottom: preserve complete generated underside panel, calibrate its maximum X span to accepted TOP width.
 bottom,bb=cropcell(2);top=Image.open(PACK/assets[g['views']['top']]['image']['path']).convert('RGBA');ta=np.array(top)[:,:,3]>=64;ty,tx=np.where(ta);topw=int(tx.max()+1-tx.min());bs=topw/bottom.width
 cand['bottom']=canvas(bottom,bs,'bottom','global component crop and isotropic fit to accepted TOP X span');cand['bottom'].update({'source_atlas_cell':2,'alpha_bbox_xyxy':bb,'target_top_width_px':topw})
 # Contact from canonical source and unchanged current views with proposed targets installed in sheet only.
 sheet=Image.new('RGB',(7*220,236),(239,235,226));dr=ImageDraw.Draw(sheet);paths=[SRC]+[PACK/assets[g['views'][v]]['image']['path'] for v in VIEWS]
 for col,(p,label) in enumerate(zip(paths,('source',*VIEWS))):
  dr.text((col*220+4,2),label,fill=(0,0,0));art=Image.open(PACK/cand[label]['path']).convert('RGBA') if label in cand else Image.open(p).convert('RGBA');art.thumbnail((208,208),Image.Resampling.NEAREST);sheet.paste(art,(col*220+(220-art.width)//2,24+(208-art.height)//2),art)
 contact=OUT/'raw/qa-safe-services-restaurant-dining-booth-candidate-v3-source-plus-six.png';sheet.save(contact,optimize=True);current={v:{'path':assets[g['views'][v]]['image']['path'],'sha256':sha(PACK/assets[g['views'][v]]['image']['path'])} for v in VIEWS};rec={'schema_version':1,'object_id':OID,'status':'candidate only; Root review required','canonical_source':{'path':SRC.relative_to(PACK).as_posix(),'sha256':sha(SRC)},'current_views':current,'raw_atlas':{'path':ATLAS.relative_to(PACK).as_posix(),'sha256':sha(ATLAS)},'request':'reusable/views-additional/raw/safe-services-restaurant-dining-booth-v3.request.json','shared_scale':{'side_z_scale':side_scale,'bottom_width_scale':bs,'target_z_px':targetz,'target_top_x_px':topw},'directions':cand,'contact_path':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'notes':'RIGHT/LEFT are flat outer-back planes with table/pedestal excluded; BOTTOM is inferred plan showing underside seat/table structures. Review image proportions/footprint before installation.'};rp=OUT/'raw/safe-services-restaurant-dining-booth-candidates-v3.json';rp.write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({'contact':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'receipt':rp.relative_to(PACK).as_posix(),'receipt_sha256':sha(rp),'crop_box':cand['right']['source_crop_bbox_xyxy'],'targetZ':targetz,'side_scale':side_scale,'bottom_scale':bs,'sizes':{v:cand[v]['resized_wh'] for v in ('right','left','bottom')}},indent=2))
if __name__=='__main__':main()
