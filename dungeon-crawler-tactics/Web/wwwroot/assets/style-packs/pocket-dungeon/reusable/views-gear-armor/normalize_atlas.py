#!/usr/bin/env python3
"""Split a generated 6xN transparent atlas by global alpha components and centroid."""
from PIL import Image
import argparse,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'reusable/views-gear-armor'; VIEWS=['front','top','right','left','bottom','rear']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def components(im,rows):
 w,h=im.size; pix=im.getchannel('A').load(); seen=bytearray(w*h); groups={(r,c):[] for r in range(rows) for c in range(6)}
 for y in range(h):
  for x in range(w):
   k=y*w+x
   if seen[k] or pix[x,y]<64: continue
   seen[k]=1; stack=[k]; comp=[]; sx=sy=0
   while stack:
    z=stack.pop(); comp.append(z); xx=z%w; yy=z//w; sx+=xx; sy+=yy
    for ny in range(max(0,yy-1),min(h,yy+2)):
     for nx in range(max(0,xx-1),min(w,xx+2)):
      nz=ny*w+nx
      if not seen[nz] and pix[nx,ny]>=64: seen[nz]=1; stack.append(nz)
   if len(comp)<8: continue
   cx=sx/len(comp); cy=sy/len(comp); col=min(5,int(cx/(w/6))); row=min(rows-1,int(cy/(h/rows)))
   groups[row,col].extend(comp)
 return groups
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('atlas',type=Path); ap.add_argument('--batch',required=True); ap.add_argument('--objects',required=True,help='id|name|kind tuples separated by comma')
 a=ap.parse_args(); atlas=a.atlas.resolve(); im=Image.open(atlas).convert('RGBA'); w,h=im.size; objs=[x.split('|') for x in a.objects.split(',')]
 if len(objs) not in (2,3,4) or any(len(x)!=3 for x in objs): raise ValueError('requires 2, 3, or 4 id|name|kind rows')
 expected_ratio=6/len(objs)
 if w<1200 or h<400 or abs((w/h)-expected_ratio)>0.3: raise ValueError(f'unexpected atlas geometry {im.size}')
 raw=OUT/'raw'/f'{a.batch}.png'; raw.write_bytes(atlas.read_bytes()); rawsha=sha(raw); groups=components(im,len(objs)); sourcepix=im.load(); cells=[]
 for ri,obj in enumerate(objs):
  for ci,view in enumerate(VIEWS):
   ids=groups[(ri,ci)]
   if not ids: raise ValueError(f'empty centroid slot {ri},{ci} {obj[0]} {view}')
   xs=[z%w for z in ids]; ys=[z//w for z in ids]; bb=(max(0,min(xs)-2),max(0,min(ys)-2),min(w,max(xs)+3),min(h,max(ys)+3))
   crop=Image.new('RGBA',(bb[2]-bb[0],bb[3]-bb[1]),(0,0,0,0)); cp=crop.load()
   for z in ids: cp[z%w-bb[0],z//w-bb[1]]=sourcepix[z%w,z//w]
   slot=(round(ci*w/6),round(ri*h/len(objs)),round((ci+1)*w/6),round((ri+1)*h/len(objs)))
   cells.append((ri,ci,obj,view,slot,bb,crop))
 assets=[]; sets=[]; recipes={}
 for ri,obj in enumerate(objs):
  oid,name,kind=obj; group=[c for c in cells if c[0]==ri]; maxdim=max(max(c[6].size) for c in group); scale=204/maxdim; refs={}; recipes[oid]={'scale':scale,'max_source_dimension':maxdim}
  for _,ci,_,view,slot,bb,crop in group:
   nw=max(1,round(crop.width*scale)); nh=max(1,round(crop.height*scale)); crop=crop.resize((nw,nh),Image.Resampling.NEAREST); canvas=Image.new('RGBA',(256,256),(0,0,0,0)); ox=(256-nw)//2; oy=(256-nh)//2; canvas.alpha_composite(crop,(ox,oy))
   aid=oid+'.'+view; ip=OUT/'images'/f'{aid}.png'; mp=ip.with_suffix('.json'); canvas.save(ip,optimize=True); sha_png=sha(ip); sha_rgba=hashlib.sha256(struct.pack('>II',256,256)+canvas.tobytes()).hexdigest(); source=f'components/{oid}.png'
   m={'id':aid,'name':name+' '+view.title(),'kind':'sprite','tags':['pocket-dungeon','six-view','orthographic',kind],'image':{'path':str(ip.relative_to(ROOT)),'width':256,'height':256,'sha256':sha_png,'rgba_sha256':sha_rgba},'object_id':oid,'view':view,'provenance':{'method':'generated','source_image':source,'source_sha256':sha(ROOT/source),'generated_atlas':str(raw.relative_to(ROOT)),'generated_atlas_sha256':rawsha,'source_rect':{'cell_px':list(slot),'alpha_component_bounds_atlas_px':list(bb)},'normalization':{'scale':scale,'offset_px':[ox,oy],'resampling':'nearest','frame_size':[256,256]},'notes':'Generated orthographic view; unseen surfaces conservatively inferred, not recovered pixels.'},'anchor_px':[128,128],'metadata_path':str(mp.relative_to(ROOT))}
   mp.write_text(json.dumps(m,indent=2)+'\n'); assets.append(m); refs[view]=aid
  sets.append({'object_id':oid,'views':refs,'complete':True,'notes':'Generated six-view orthographic set; inferred hidden surfaces.'})
 idx=OUT/'set-index.json'; data=json.loads(idx.read_text()) if idx.exists() else {'assets':[],'view_sets':[]}; merged_assets={m['id']:m for m in data['assets']}; merged_assets.update({m['id']:m for m in assets}); data['assets']=list(merged_assets.values()); merged={s['object_id']:s for s in data['view_sets']}; merged.update({s['object_id']:s for s in sets}); data['view_sets']=list(merged.values()); tmp=idx.with_suffix('.json.tmp'); tmp.write_text(json.dumps(data,indent=2)+'\n'); tmp.replace(idx)
 print(json.dumps({'objects':[o[0] for o in objs],'views':len(assets),'atlas_sha256':rawsha,'scales':recipes}))
 from apply_targeted_repairs import apply_all
 apply_all()
if __name__=='__main__': main()
