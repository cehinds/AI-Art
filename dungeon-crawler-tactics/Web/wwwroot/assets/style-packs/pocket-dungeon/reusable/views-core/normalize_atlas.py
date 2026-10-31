from PIL import Image
import json,hashlib,struct,sys
from pathlib import Path
import numpy as np
from scipy import ndimage
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
atlas_arg=Path(sys.argv[1]);atlas_path=atlas_arg if atlas_arg.is_absolute() else ROOT/atlas_arg
im=Image.open(atlas_path).convert('RGBA');arr=np.asarray(im);mask=arr[:,:,3]>=245
labels,n=ndimage.label(mask,np.ones((3,3),dtype=np.uint8));counts=np.bincount(labels.ravel());H,W=mask.shape
# Assign each whole connected foreground island to its nearest nominal cell center.
centers=[]
for y in range(3):
 for x in range(6): centers.append(((x+.5)*W/6,(y+.5)*H/3))
assign={k:[] for k in range(18)}; props=[]
for k in range(1,n+1):
 if counts[k]<4: continue
 yy,xx=np.where(labels==k);cx=float(xx.mean());cy=float(yy.mean());cell=min(range(18),key=lambda i:((cx-centers[i][0])/(W/6))**2+((cy-centers[i][1])/(H/3))**2)
 assign[cell].append(k);props.append((k,cx,cy,int(counts[k]),[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]))
manifest=json.load(open(ROOT/'manifest.json'));objects=sys.argv[2:5];views=['front','top','right','left','bottom','rear'];assets=[];sets=[];raw_rel=atlas_path.relative_to(ROOT).as_posix();raw_hash=hashlib.sha256(atlas_path.read_bytes()).hexdigest()
for row,oid in enumerate(objects):
 obj=next(a for a in manifest['assets'] if a['id']==oid); parts=[]
 for col,v in enumerate(views):
  cell=row*6+col; labs=assign[cell]
  if not labs: continue
  main=max(labs,key=lambda k:counts[k]); chosen=[k for k in labs if k==main or counts[k]>=counts[main]*.02]
  boxes=[p[4] for p in props if p[0] in chosen]; x0=min(b[0] for b in boxes);y0=min(b[1] for b in boxes);x1=max(b[2] for b in boxes);y1=max(b[3] for b in boxes)
  local=(labels[y0:y1,x0:x1,None]==np.array(chosen)[None,None,:]).any(axis=2) if len(chosen)>1 else labels[y0:y1,x0:x1]==chosen[0]
  crop=im.crop((x0,y0,x1,y1));crop.putalpha(Image.fromarray((local*255).astype('uint8')));parts.append((v,crop,[x0,y0,x1,y1],(row,col),chosen))
 scale=min(208/max(max(p[1].size) for p in parts),1.0); refs={}
 for v,piece,bounds,cell,chosen in parts:
  nw=max(1,round(piece.width*scale));nh=max(1,round(piece.height*scale));piece=piece.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256));xy=(128-nw//2,128-nh//2);canvas.alpha_composite(piece,xy)
  aid=f'{oid}.{v}';rel=f'reusable/views-core/{aid}.png';dst=ROOT/rel;canvas.save(dst,optimize=True);meta=OUT/f'{aid}.json';
  a={'id':aid,'name':obj['label']+' '+v.title(),'kind':'tile' if obj['category']=='terrain' else 'sprite','tags':[obj['category'],v,obj['source']['sheet']],'object_id':oid,'view':v,'image':{'path':rel,'width':256,'height':256,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'rgba_sha256':hashlib.sha256(struct.pack('>II',256,256)+canvas.tobytes()).hexdigest()},'metadata_path':meta.relative_to(ROOT).as_posix(),'anchor_px':[128,128],'provenance':{'method':'generated','source_image':f'components/{oid}.png','notes':'inferred orthographic view, not recovered pixels','source_atlas':raw_rel,'source_atlas_sha256':raw_hash,'crop_bounds_px':{'nominal_cell':{'column':cell[1],'row':cell[0],'bounds':[round(cell[1]*W/6),round(cell[0]*H/3),round((cell[1]+1)*W/6),round((cell[0]+1)*H/3)]},'alpha_bounds_global':bounds,'component_labels':chosen,'resized_bounds_px':[nw,nh],'canvas_offset_px':list(xy),'shared_scale':scale}}}
  meta.write_text(json.dumps(a,indent=2)+'\n');assets.append(a);refs[v]=aid
 sets.append({'object_id':oid,'views':refs,'complete':len(refs)==6,'notes':'Six generated orthographic views; unseen surfaces conservatively inferred from the component source.'})
idx=OUT/'set-index.json';old=json.loads(idx.read_text()) if idx.exists() else {'assets':[],'view_sets':[]};byid={a['id']:a for a in old['assets'] if (ROOT/a['image']['path']).exists()};byid.update({a['id']:a for a in assets});sb={s['object_id']:s for s in old['view_sets']};sb.update({s['object_id']:s for s in sets});idx.write_text(json.dumps({'assets':list(byid.values()),'view_sets':list(sb.values())},indent=2)+'\n')
