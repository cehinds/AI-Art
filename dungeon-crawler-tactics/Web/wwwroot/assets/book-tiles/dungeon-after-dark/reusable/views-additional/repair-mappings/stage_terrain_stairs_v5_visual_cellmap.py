"""Terrain stair candidate v4. Cells are grouped by top-origin row first, then X; camera-role verified from raw contact."""
from pathlib import Path
import json, hashlib, copy
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
OUT=Path(__file__).resolve().parents[1]; PACK=OUT.parent.parent
CDIR=OUT/'candidates/page-dark-next-six-terrain-stairs-v1'
M3=CDIR/'terrain-stairs-candidate-manifest-v4.json'
IDX=json.loads((OUT/'set-index.json').read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p): return Image.open(p).convert('RGBA')
def comps(p):
 im=rgba(p); a=np.asarray(im)[:,:,3]; labels,n=ndimage.label(a>=32); rows=[]
 for i in range(1,n+1):
  mask=labels==i
  if int(mask.sum())<1000: continue
  ys,xs=np.where(mask); rows.append({'i':i,'bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'area':int(mask.sum())})
 # Atlas rows are two distinct vertical bands. Never sort cells by top y within a row.
 bands=[sorted([c for c in rows if c['bbox'][1]<300],key=lambda c:c['bbox'][0]),sorted([c for c in rows if c['bbox'][1]>=300],key=lambda c:c['bbox'][0])]
 assert all(len(r)==4 for r in bands),[len(r) for r in bands]
 return im,labels,bands
def crop(im,labels,item):
 a=np.asarray(im)[:,:,3];mask=ndimage.binary_dilation(labels==item['i'],iterations=2)&(a>0);ys,xs=np.where(mask);box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];arr=np.asarray(im).copy();arr[:,:,3]=np.where(mask,a,0).astype(np.uint8);return Image.fromarray(arr,'RGBA').crop(tuple(box)),box
def fit(crop, tw, th):
 w,h=crop.size;s=min(tw/w,th/h);nw=max(1,round(w*s));nh=max(1,round(h*s));im=crop.resize((nw,nh),Image.Resampling.NEAREST);fr=Image.new('RGBA',(256,256),(0,0,0,0));x=(256-nw)//2;y=(256-nh)//2;fr.alpha_composite(im,(x,y));return fr,{'uniform_scale':s,'resized_dimensions_px':[nw,nh],'offset_px':[x,y],'anchor_px':[128,128],'resampling':'nearest'}
def main():
 m=copy.deepcopy(json.loads(M3.read_text())); oldsha=sha(M3); assets={a['id']:a for a in IDX['assets']}; lookup={(c['object_id'],c['view']):c for c in m['candidates']}; revisions=[]
 # Battlefield raw physical cells by explicit visual classification:
 # UP row: profiles, profiles, flat support, tread-facing plan. DOWN row: tread plan, flat support, profiles, profiles.
 bp=CDIR/'raw/battlefield-earth-up-down.png';im,labels,bands=comps(bp)
 choices={
 ('faction-battlefield-churned-battlefield-earth-stairs-up','bottom'):(0,2,'flat opaque substrate'),
 ('faction-battlefield-churned-battlefield-earth-stairs-down','right'):(1,0,'descending stepped profile'),
 ('faction-battlefield-churned-battlefield-earth-stairs-down','left'):(1,1,'ascending stepped profile'),
 ('faction-battlefield-churned-battlefield-earth-stairs-down','bottom'):(1,2,'flat opaque substrate')}
 # Larracos: bottom cells are flat stone planes; UP row col1 is flagstone paving and DOWN row col2 is unornamented backing slab.
 lp=CDIR/'raw/larracos-cobble-up-down.png';lim,llabs,lbands=comps(lp)
 choices.update({
 ('faction-larracos-drained-city-cobblestone-stairs-up','bottom'):(1,2,'flat flagstone support plane'),
 ('faction-larracos-drained-city-cobblestone-stairs-down','bottom'):(1,2,'flat flagstone support plane')})
 for (oid,v),(row,col,role) in choices.items():
  raw=bp if 'battlefield' in oid else lp;src=im if 'battlefield' in oid else lim; labs=labels if 'battlefield' in oid else llabs;item=(bands if 'battlefield' in oid else lbands)[row][col];cr,box=crop(src,labs,item)
  basefront=rgba(PACK/Path(assets[oid+'.front']['image']['path']));fb=basefront.getchannel('A').getbbox();fh=fb[3]-fb[1]
  if v in ('right','left'): tw,th=256,fh
  else:
   top=rgba(PACK/Path(assets[oid+'.top']['image']['path']));tb=top.getchannel('A').getbbox();tw,th=tb[2]-tb[0],tb[3]-tb[1]
  frame,norm=fit(cr,tw,th);path=CDIR/'images'/f'{oid}.{v}.candidate-v5.png';frame.save(path,format='PNG',optimize=False)
  c=lookup[(oid,v)];c['candidate_path']=path.relative_to(PACK).as_posix();c['candidate_sha256']=sha(path);c['extraction']={'source_atlas_path':raw.relative_to(PACK).as_posix(),'source_atlas_sha256':sha(raw),'alpha_threshold':32,'component_index':item['i'],'component_count':8,'component_bbox_xyxy':item['bbox'],'component_area':item['area'],'soft_alpha_halo_px':2,'crop_bbox_xyxy':box,'row_column_mapping':{'row':'up' if row==0 else 'down','column':col,'method':'vertical-band by component bbox top; left-to-right within band','visually_classified_role':role}};c['normalization']=norm;c['review_status']='v5 visual component mapping; Page review requested';c['notes']=f'Corrected from raw atlas after visual cell classification: {role}. Extraction uses full connected alpha component plus 2px soft halo; isotropic nearest-neighbor fit to shared footprint/height.';revisions.append({'object_id':oid,'view':v,'component_bbox':item['bbox'],'role':role,'candidate_path':c['candidate_path'],'candidate_sha256':c['candidate_sha256']})
 m['supersedes_manifest']='reusable/views-additional/candidates/page-dark-next-six-terrain-stairs-v1/terrain-stairs-candidate-manifest-v4.json';m['supersedes_manifest_sha256']=oldsha;m['status']='candidate-only; corrected v5 component mapping submitted for Page review'
 # Refresh per-manifest candidate contact with actual source + six + proposed directions.
 contact=Image.new('RGBA',(200*12,220*6),(13,16,21,255));proofrows=[]
 for ri,o in enumerate(m['objects']):
  oid=o['object_id']; cand=[c for c in m['candidates'] if c['object_id']==oid];ordered=[('SOURCE',o['source'])]+[(v,o['base_six'][v]) for v in ['front','top','right','left','bottom','rear']]+[(c['view'].upper()+' NEW',{'path':c['candidate_path'],'sha256':c['candidate_sha256']}) for c in cand];cells=[]
  for ci,(lab,rec) in enumerate(ordered):
   p=PACK/rec['path'];assert sha(p)==rec['sha256'],(oid,lab,p);pic=rgba(p);pic.thumbnail((180,180),Image.Resampling.NEAREST);tile=Image.new('RGBA',(200,220),(31,34,39,255));tile.alpha_composite(pic,((200-pic.width)//2,8+(180-pic.height)//2));ImageDraw.Draw(tile).text((4,195),lab,fill='white');contact.alpha_composite(tile,(ci*200,ri*220));cells.append({'label':lab,**rec})
  proofrows.append({'object_id':oid,'cells':cells})
 cp=CDIR/'terrain-stairs-source-six-candidates-v5.png';contact.save(cp,format='PNG',optimize=False);m['candidate_contact_path']=cp.relative_to(PACK).as_posix();m['candidate_contact_sha256']=sha(cp)
 mp=CDIR/'terrain-stairs-candidate-manifest-v4.json';mp.write_text(json.dumps(m,indent=2)+'\n');proof={'manifest_path':mp.relative_to(PACK).as_posix(),'manifest_sha256':sha(mp),'contact_path':cp.relative_to(PACK).as_posix(),'contact_sha256':sha(cp),'supersedes_manifest_path':M3.relative_to(PACK).as_posix(),'supersedes_manifest_sha256':oldsha,'rows':proofrows,'revisions':revisions};pf=CDIR/'terrain-stairs-candidate-contact-proof-v5.json';pf.write_text(json.dumps(proof,indent=2)+'\n')
 print(json.dumps({'manifest':mp.relative_to(PACK).as_posix(),'manifest_sha256':sha(mp),'contact':cp.relative_to(PACK).as_posix(),'contact_sha256':sha(cp),'proof':pf.relative_to(PACK).as_posix(),'proof_sha256':sha(pf),'revisions':revisions},indent=2))
if __name__=='__main__':main()
