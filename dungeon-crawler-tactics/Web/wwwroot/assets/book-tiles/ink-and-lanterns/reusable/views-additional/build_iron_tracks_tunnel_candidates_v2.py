"""Extract three-per-atlas generated tunnel views with a shared isotropic object scale."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];OID='iron-tracks-tunnel-portal-frame';VIEWS=('front','top','right','left','bottom','rear');INDEX=OUT/'set-index.json';SRC=PACK/'iron-tracks/components/iron-tracks-tunnel-portal-frame.png'
ATLAS={'front':'raw/iron-tracks-tunnel-portal-v2-front-top-right-generated.png','top':'raw/iron-tracks-tunnel-portal-v2-front-top-right-generated.png','right':'raw/iron-tracks-tunnel-portal-v2-front-top-right-generated.png','left':'raw/iron-tracks-tunnel-portal-v2-left-bottom-rear-generated.png','bottom':'raw/iron-tracks-tunnel-portal-v2-left-bottom-rear-generated.png','rear':'raw/iron-tracks-tunnel-portal-v2-left-bottom-rear-generated.png'}
CELL={'front':0,'top':1,'right':2,'left':0,'bottom':1,'rear':2};sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 index=json.loads(INDEX.read_text());assets={a['id']:a for a in index['assets']};group=next(g for g in index['view_sets'] if g['object_id']==OID)
 crops={};records={}
 for view in VIEWS:
  path=OUT/ATLAS[view];im=Image.open(path).convert('RGBA');arr=np.asarray(im);assert im.size==(2172,724), (view,im.size);col=CELL[view];x0=col*724;x1=(col+1)*724;local=arr[:,x0:x1];mask=local[:,:,3]>=64;ys,xs=np.where(mask)
  if len(xs)==0:raise RuntimeError('empty requested cell '+view)
  box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
  # Fail closed if image art touches any cell edge; that signals possible clipping/cell collision.
  if box[0]<12 or box[1]<12 or box[2]>712 or box[3]>712:raise RuntimeError(f'cell-boundary collision {view}: {box}')
  crops[view]=Image.fromarray(local).crop(tuple(box));records[view]={'atlas_path':path.relative_to(PACK).as_posix(),'atlas_sha256':sha(path),'atlas_cell_bbox_xyxy':[x0,0,x1,724],'alpha_bbox_xyxy_in_cell':box,'alpha_pixels':int(mask.sum())}
 shared=208/max(max(x.size) for x in crops.values());cand={}
 for view in VIEWS:
  crop=crops[view];sz=(round(crop.width*shared),round(crop.height*shared));res=crop.resize(sz,Image.Resampling.NEAREST);offset=((256-sz[0])//2,(256-sz[1])//2);canvas=Image.new('RGBA',(256,256));canvas.alpha_composite(res,offset);p=OUT/'raw'/f'{OID}.{view}.candidate-v2.png';canvas.save(p);cand[view]={'path':p.relative_to(PACK).as_posix(),'sha256':sha(p),'resized_wh':list(sz),'offset_xy':list(offset),'uniform_scale':shared,'resampler':'NEAREST','alpha_bbox_xyxy_in_cell':records[view]['alpha_bbox_xyxy_in_cell']}
 # Current-source+six contact reads active set-index targets after candidate substitution, but does not mutate them.
 sheet=Image.new('RGB',(7*220,236),(239,235,226));draw=ImageDraw.Draw(sheet);paths=[SRC]
 for view in VIEWS:paths.append(PACK/assets[group['views'][view]]['image']['path'])
 # Replace current held directions only in contact.
 contact_candidates={v:OUT/cand[v]['path'].split('reusable/views-additional/',1)[1] for v in VIEWS}
 for col,(p,label) in enumerate(zip(paths,('source',*VIEWS))):
  draw.text((col*220+4,3),label,fill=(0,0,0));art=Image.open(p).convert('RGBA') if col==0 else Image.open(contact_candidates[VIEWS[col-1]]).convert('RGBA');art.thumbnail((208,208),Image.Resampling.NEAREST);sheet.paste(art,(col*220+(220-art.width)//2,24+(208-art.height)//2),art)
 contact=OUT/'raw/qa-iron-tracks-tunnel-portal-frame-candidate-v2-source-plus-six.png';sheet.save(contact,optimize=True)
 current={v:{'asset_id':group['views'][v],'path':assets[group['views'][v]]['image']['path'],'sha256':sha(PACK/assets[group['views'][v]]['image']['path'])} for v in VIEWS}
 # Persist exact generation-result mapping and v1 rejection reason.
 for name,views in [('v2-front-top-right',['front','top','right']),('v2-left-bottom-rear',['left','bottom','rear'])]:
  q=OUT/'raw'/f'{OID}-{name}.request.json';d=json.loads(q.read_text());p=OUT/d['directions'][0] # unused, keep only request stable
  atlas=OUT/ATLAS[views[0]];d['generation_result']={'output_path':atlas.relative_to(PACK).as_posix(),'output_sha256':sha(atlas),'dimensions':[2172,724],'layout':views,'attribution':'ImageGen result saved immediately to this request mapping'};d['status']='generated; three isolated cells extracted and visually inspected';q.write_text(json.dumps(d,indent=2)+'\n')
 receipt={'schema_version':1,'object_id':OID,'status':'candidate set; Root review required before install','canonical_source':{'path':SRC.relative_to(PACK).as_posix(),'sha256':sha(SRC)},'current_live_views':current,'raw_atlases':{f: {'path':(OUT/f).relative_to(PACK).as_posix(),'sha256':sha(OUT/f)} for f in set(ATLAS.values())},'superseded_atlas':{'path':'reusable/views-additional/raw/iron-tracks-tunnel-portal-focused-views-v1-generated.png','sha256':sha(OUT/'raw/iron-tracks-tunnel-portal-focused-views-v1-generated.png'),'reason':'six images collapsed into three overlapping side-view cell regions; cell-boundary collision prevented valid isolation and output was not used'},'request_paths':['reusable/views-additional/raw/iron-tracks-tunnel-portal-frame-v2-front-top-right.request.json','reusable/views-additional/raw/iron-tracks-tunnel-portal-frame-v2-left-bottom-rear.request.json'],'direction_order':list(VIEWS),'shared_uniform_scale':shared,'views':{v:{**records[v],**cand[v]} for v in VIEWS},'contact_path':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'notes':'Six inferred orthographic views, not recovered pixels or calibrated 3D. Canonical native source remains object identity authority.'}
 out=OUT/'raw/iron-tracks-tunnel-portal-frame-candidates-v2.json';out.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'contact':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'receipt':out.relative_to(PACK).as_posix(),'receipt_sha256':sha(out),'shared_scale':shared,'views':{v:{'size':cand[v]['resized_wh'],'bbox':records[v]['alpha_bbox_xyxy_in_cell']} for v in VIEWS}},indent=2))
if __name__=='__main__':main()
