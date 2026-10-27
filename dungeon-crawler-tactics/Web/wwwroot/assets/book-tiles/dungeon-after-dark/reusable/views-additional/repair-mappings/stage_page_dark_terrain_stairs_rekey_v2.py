"""Re-key the terrain-stair atlases by physical alpha-cell row/column; preserve v1."""
from pathlib import Path
import json,hashlib,copy
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parents[1];PACK=OUT.parent.parent;CDIR=OUT/'candidates/page-dark-next-six-terrain-stairs-v1'
M1=CDIR/'terrain-stairs-candidate-manifest-v1.json';HAND=Path('/workspace/scratch/page-dark-future-six-terrain-stairs-handoff-v2-20261026.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(rel):
 p=(PACK/rel).resolve();p.relative_to(PACK.resolve());return p
def rgba(p):return Image.open(p).convert('RGBA')
def components(p):
 im=rgba(p);a=np.asarray(im)[:,:,3];labels,n=ndimage.label(a>=32);out=[]
 for i in range(1,n+1):
  mask=labels==i;area=int(mask.sum())
  if area<1000:continue
  ys,xs=np.where(mask);bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];out.append({'i':i,'bbox':bbox,'area':area})
 return im,labels,sorted(out,key=lambda x:(x['bbox'][1],x['bbox'][0]))
def crop_component(im,labels,item,halo=2):
 a=np.asarray(im)[:,:,3];mask=ndimage.binary_dilation(labels==item['i'],iterations=halo)&(a>0);ys,xs=np.where(mask);box=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];arr=np.asarray(im).copy();arr[:,:,3]=np.where(mask,a,0).astype(np.uint8);return Image.fromarray(arr,'RGBA').crop(tuple(box)),box
def fit(crop,tw,th):
 w,h=crop.size;s=min(tw/w,th/h);nw=max(1,round(w*s));nh=max(1,round(h*s));im=crop.resize((nw,nh),Image.Resampling.NEAREST);fr=Image.new('RGBA',(256,256),(0,0,0,0));x=(256-nw)//2;y=(256-nh)//2;fr.alpha_composite(im,(x,y));return fr,{'uniform_scale':s,'resized_dimensions_px':[nw,nh],'offset_px':[x,y],'anchor_px':[128,128],'resampling':'nearest'}
def main():
 m1=json.loads(M1.read_text());hand=json.loads(HAND.read_text());objects={o['object_id']:o for o in m1['objects']};c1={(c['object_id'],c['view']):c for c in m1['candidates']}
 for o in hand['objects']:
  assert sha(Path(o['source']['path']))==o['source']['sha256']
  for v,x in o['views'].items():assert sha(Path(x['path']))==x['sha256'],(o['object_id'],v)
 # Build only physically mapped views. Cells are segmented; row key uses top bounding y, then left x.
 style_groups={'battlefield':('battlefield-earth-up-down','right','left','bottom'),'larracos':('larracos-cobble-up-down','bottom',None,None),'cemetery':('cemetery-flagstone-up-down','right','left','bottom')}
 candidates=[];outdirs={}
 for style,(atlasname,*targetviews) in style_groups.items():
  raw=CDIR/'raw'/(atlasname+'.png');im,labs,items=components(raw);assert len(items)==8
  rows=[items[:4],items[4:]]
  ids=[o['object_id'] for o in m1['objects'] if o['object_id'].startswith({'battlefield':'faction-battlefield','larracos':'faction-larracos','cemetery':'ghost-cemetery'}[style])]
  for rownum,oid in enumerate(ids):
   row=rows[rownum];assert len(row)==4
   # Physical columns are identified from measured x: 0/1 are two opposite stair side profiles; 2 is substrate plan; 3 is a duplicate tread-facing plane, unused.
   desired=targetviews
   for col,v in enumerate(desired):
    if v is None:continue
    item=row[col];crop,cropbox=crop_component(im,labs,item)
    idx_asset={a['id']:a for a in json.loads((OUT/'set-index.json').read_text())['assets']}
    front=rgba(PACK/idx_asset[oid+'.front']['image']['path']);fb=front.getchannel('A').getbbox();fh=fb[3]-fb[1]
    top=rgba(PACK/idx_asset[oid+'.top']['image']['path']);tb=top.getchannel('A').getbbox();tw,th=tb[2]-tb[0],tb[3]-tb[1]
    # Side faces share accepted FRONT Z; substrate shares the accepted/native TOP footprint.
    if v in ('right','left'): frame,norm=fit(crop,256,fh)
    else: frame,norm=fit(crop,tw,th)
    path=CDIR/'images'/f'{oid}.{v}.candidate-v2.png';frame.save(path,format='PNG',optimize=False)
    prev=c1[(oid,v)];c=copy.deepcopy(prev);c['candidate_path']=path.relative_to(PACK).as_posix();c['candidate_sha256']=sha(path);c['extraction']['component_index']=item['i'];c['extraction']['component_bbox_xyxy']=item['bbox'];c['extraction']['component_area']=item['area'];c['extraction']['row_column_mapping']={'row':'up' if rownum==0 else 'down','column':col,'measured_order':'top-bounding-y then left-bounding-x','expected_role':'stair-side-profile' if v in ('right','left') else 'opaque-support-substrate'};c['extraction']['crop_bbox_xyxy']=cropbox;c['normalization']=norm;c['notes']+=' Re-keyed from the measured top-row/left-to-right alpha cell; candidate direction fixed after visual mapping check.';c['review_status']='v2 re-keyed candidate; Page review requested'
    candidates.append(c);outdirs[(oid,v)]=c
 # Keep the accepted native plans and separate rear profiles from v1, byte-identical.
 for c in m1['candidates']:
  key=(c['object_id'],c['view'])
  if key in outdirs:continue
  candidates.append(copy.deepcopy(c))
 # Manifest scope exactly 24 directions, same current source/six bindings as v1.
 m2=copy.deepcopy(m1);m2['supersedes_manifest']='reusable/views-additional/candidates/page-dark-next-six-terrain-stairs-v1/terrain-stairs-candidate-manifest-v1.json';m2['supersedes_manifest_sha256']=sha(M1);m2['candidates']=candidates
 # Candidate contact source + all current six + 24 proposed views.
 A={a['id']:a for a in json.loads((OUT/'set-index.json').read_text())['assets']};proofrows=[];contact=Image.new('RGBA',(200*12,220*6),(13,16,21,255))
 for ri,o in enumerate(m2['objects']):
  oid=o['object_id'];ordered=[('SOURCE',o['source'])]+[(v,o['base_six'][v]) for v in ['front','top','right','left','bottom','rear']]+[(c['view'].upper()+' NEW',{'path':c['candidate_path'],'sha256':c['candidate_sha256']}) for c in candidates if c['object_id']==oid];cells=[]
  for ci,(lab,rec) in enumerate(ordered):
   p=safe(rec['path']);assert sha(p)==rec['sha256'],(oid,lab);im2=rgba(p);im2.thumbnail((180,180),Image.Resampling.NEAREST);t=Image.new('RGBA',(200,220),(31,34,39,255));t.alpha_composite(im2,((200-im2.width)//2,8+(180-im2.height)//2));ImageDraw.Draw(t).text((4,195),lab,fill='white');contact.alpha_composite(t,(ci*200,ri*220));cells.append({'label':lab,**rec})
  proofrows.append({'object_id':oid,'cells':cells})
 cp=CDIR/'terrain-stairs-source-six-candidates-v2.png';contact.save(cp);mp=CDIR/'terrain-stairs-candidate-manifest-v2.json';mp.write_text(json.dumps(m2,indent=2)+'\n');proof={'manifest_path':mp.relative_to(PACK).as_posix(),'manifest_sha256':sha(mp),'contact_path':cp.relative_to(PACK).as_posix(),'contact_sha256':sha(cp),'supersedes_manifest_sha256':sha(M1),'rows':proofrows};pf=CDIR/'terrain-stairs-candidate-contact-proof-v2.json';pf.write_text(json.dumps(proof,indent=2)+'\n')
 print(json.dumps({'manifest':proof['manifest_path'],'manifest_sha256':proof['manifest_sha256'],'contact':proof['contact_path'],'contact_sha256':proof['contact_sha256'],'candidate_count':len(candidates)},indent=2))
if __name__=='__main__':main()
