from PIL import Image
import json,hashlib,struct
from pathlib import Path
import numpy as np
from scipy import ndimage
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
COLS=['front','top','right','left','bottom','rear']
def process(raw_rel,objects,kind='caverns'):
 raw=OUT/raw_rel;im=Image.open(raw).convert('RGBA');arr=np.asarray(im);h,w=arr.shape[:2];labels,n=ndimage.label(arr[:,:,3]>16);slices=ndimage.find_objects(labels);components=[]
 for lab,sl in enumerate(slices,1):
  if sl is None:continue
  ys,xs=sl;area=int(np.count_nonzero(labels[sl]==lab))
  if area<24:continue
  components.append({'label':lab,'area':area,'cx':(xs.start+xs.stop)/2,'cy':(ys.start+ys.stop)/2,'box':(xs.start,ys.start,xs.stop,ys.stop)})
 atlas_sha=hashlib.sha256(raw.read_bytes()).hexdigest();idx=json.loads((OUT/'set-index.json').read_text()) if (OUT/'set-index.json').exists() else {'assets':[],'view_sets':[]}
 for ri,(oid,name) in enumerate(objects):
  crops=[];rects=[]
  for ci in range(6):
   x0=round(ci*w/6);x1=round((ci+1)*w/6);y0=round(ri*h/len(objects));y1=round((ri+1)*h/len(objects));selected=[c for c in components if x0<=c['cx']<x1 and y0<=c['cy']<y1]
   if not selected:raise ValueError(f'{oid}/{COLS[ci]}: no alpha components assigned')
   xlo=min(c['box'][0] for c in selected);ylo=min(c['box'][1] for c in selected);xhi=max(c['box'][2] for c in selected);yhi=max(c['box'][3] for c in selected)
   core=np.isin(labels,[c['label'] for c in selected]);expanded=ndimage.binary_dilation(core,iterations=2)&(arr[:,:,3]>0);masked=np.zeros_like(arr);masked[expanded]=arr[expanded];crop=Image.fromarray(masked,'RGBA').crop((xlo,ylo,xhi,yhi));crops.append(crop)
   rects.append({'cell':[x0,y0,x1-x0,y1-y0],'alpha_bounds':[xlo,ylo,xhi-xlo,yhi-ylo],'component_count':len(selected),'component_areas':[c['area'] for c in selected],'components_outside_cell':[c['label'] for c in selected if c['box'][0]<x0 or c['box'][1]<y0 or c['box'][2]>x1 or c['box'][3]>y1]})
  scale=204/max(max(c.size) for c in crops);refs={}
  for ci,(view,crop) in enumerate(zip(COLS,crops)):
   nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale));crop=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));ox=(256-nw)//2;oy=(256-nh)//2;canvas.alpha_composite(crop,(ox,oy));aid=oid+'.'+view;ip=OUT/'images'/f'{aid}.png';mp=ip.with_suffix('.json');canvas.save(ip,optimize=True);rgba=canvas.tobytes();meta={'id':aid,'name':name+' '+view.title(),'kind':kind,'tags':['pocket-dungeon','six-view','orthographic',kind],'image':{'path':str(ip.relative_to(ROOT)),'width':256,'height':256,'sha256':hashlib.sha256(ip.read_bytes()).hexdigest(),'rgba_sha256':hashlib.sha256(struct.pack('>II',256,256)+rgba).hexdigest()},'object_id':oid,'view':view,'provenance':{'method':'generated','source_image':f'components/{oid}.png','generated_atlas':str(raw.relative_to(ROOT)),'generated_atlas_sha256':atlas_sha,'source_rect':rects[ci],'normalization':{'scale':scale,'offset_px':[ox,oy],'resampling':'nearest','frame_size':[256,256]},'rebuild_command':'python3 reusable/views-caverns/build_all.py','notes':'Generated orthographic view; unseen surfaces conservatively inferred, not recovered pixels.'},'anchor_px':[128,128]};meta['metadata_path']=str(mp.relative_to(ROOT));mp.write_text(json.dumps(meta,indent=2)+'\n');idx['assets']=[a for a in idx['assets'] if a['id']!=aid];idx['assets'].append(meta);refs[view]=aid
  idx['view_sets']=[s for s in idx['view_sets'] if s['object_id']!=oid];idx['view_sets'].append({'object_id':oid,'views':refs,'complete':True,'notes':'Reviewed six orthographic views, full alpha-island bounds and transparent background; hidden surfaces inferred.'})
 (OUT/'set-index.json').write_text(json.dumps(idx,indent=2)+'\n')
