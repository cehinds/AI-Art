from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage
import numpy as np, json,hashlib
BASE=Path(__file__).resolve().parents[4]
OUT=BASE/'reusable/views-additional/candidates/root-dark-worktops-unblocked-20261026-v3'
RAW=BASE/'reusable/views-additional/raw/root-dark-worktops6-20261026'
IDX=json.loads((BASE/'reusable/views-additional/set-index.json').read_text())
ASSETS={a['id']:a for a in IDX['assets'] if a.get('kind')=='sprite'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def component(im):
 m=np.asarray(im.getchannel('A'))>=64; labels,n=ndimage.label(m,structure=ndimage.generate_binary_structure(2,2));counts=np.bincount(labels.ravel());counts[0]=0;lab=int(counts.argmax());ys,xs=np.where(labels==lab);return [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],int(counts[lab])
def fit(rawp,target,dest):
 im=Image.open(rawp).convert('RGBA');box,count=component(im);crop=im.crop(box);scale=min(target[0]/crop.width,target[1]/crop.height);size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)));crop=crop.resize(size,Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(256,256),(0,0,0,0));xy=(128-size[0]//2,128-size[1]//2);canvas.alpha_composite(crop,xy);dest.parent.mkdir(parents=True,exist_ok=True);canvas.save(dest);return box,count,scale,size
items=[
('great-race-transition-selection-chamber-console','front','console-front-v9.png',(198,134)),
('great-race-transition-selection-chamber-console','rear','console-rear-v6.png',(204,139)),
('industry-menagerie-pipe-valve-cluster','bottom','industry-menagerie-pipe-valve-cluster.bottom.unblocked-v3.png',(195,181))]
rows=[]
for oid,view,rawname,target in items:
 aid=f'{oid}.{view}';ap=ASSETS[aid];src=BASE/ap['source']['source_image'];live=BASE/ap['image']['path'];rawp=RAW/rawname;dest=OUT/'candidates'/f'{aid}.png';box,count,scale,size=fit(rawp,target,dest)
 resultp=RAW/({'console-front-v9.png':'console-front-v9.result.json','console-rear-v6.png':'console-rear-v6.result.json'}.get(rawname,'pipe-bottom-v3.result.json'))
 promptp=RAW/({'console-front-v9.png':'console-front-v9.prompt.txt','console-rear-v6.png':'console-rear-v6.prompt.txt'}.get(rawname,'pipe-bottom-v3.prompt.txt'))
 rows.append({'object_id':oid,'view':view,'source_path':ap['source']['source_image'],'source_sha256':sha(src),'current_path':ap['image']['path'],'current_sha256':sha(live),'raw_path':f'reusable/views-additional/raw/root-dark-worktops6-20261026/{rawname}','raw_sha256':sha(rawp),'result_path':f'reusable/views-additional/raw/root-dark-worktops6-20261026/{resultp.name}','result_sha256':sha(resultp),'prompt_path':f'reusable/views-additional/raw/root-dark-worktops6-20261026/{promptp.name}','prompt_sha256':sha(promptp),'candidate_path':f'reusable/views-additional/candidates/root-dark-worktops-unblocked-20261026-v3/candidates/{dest.name}','candidate_sha256':sha(dest),'component_alpha64_bbox_xyxy':box,'component_pixels':count,'target_bbox_size':target,'output_bbox_size':size,'uniform_scale':scale,'anchor':[128,128],'connectivity':8,'alpha_threshold':64,'resample':'LANCZOS','tool_request_id':None,'request_label':resultp.stem,'method':'single-largest-8-connected-alpha64-component-fit-uniform'})
 print(aid,box,size,round(scale,5),sha(dest))

def contact(oid,filename,records):
 # 8 cells: source, six current/proposed views substituted, and candidates area labeled as selected current slot.
 ids=[f'{oid}.{v}' for v in ['front','top','right','left','bottom','rear']]
 srcpath=BASE/ASSETS[ids[0]]['source']['source_image'];mapping={r['view']:BASE/r['candidate_path'] for r in records}
 ims=[Image.open(srcpath).convert('RGBA')]
 for aid in ids:
  v=aid.rsplit('.',1)[1];ims.append(Image.open(mapping.get(v,BASE/ASSETS[aid]['image']['path'])).convert('RGBA'))
 names=['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR']
 W,H=256,292; sheet=Image.new('RGB',(4*W,2*H),(30,32,36));d=ImageDraw.Draw(sheet)
 try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
 except:font=None
 for i,(im,name) in enumerate(zip(ims,names)):
  col=i%4;row=i//4; x=col*W;y=row*H; d.text((x+5,y+4),name,font=font,fill='white')
  tile=Image.new('RGBA',(W,H-32),(24,25,28,255)); im.thumbnail((W-12,H-44),Image.Resampling.NEAREST);tile.alpha_composite(im,((W-im.width)//2,(H-32-im.height)//2));sheet.paste(tile.convert('RGB'),(x,y+32))
 cp=OUT/'contacts'/filename;cp.parent.mkdir(parents=True,exist_ok=True);sheet.save(cp);return cp
man={'schema_version':1,'candidate_id':'root-dark-worktops-v3-held-three','status':'candidate-review-pending','installer':'views_dark_books','reviewer':'root','normalization':'largest 8-connected alpha>=64 component, crop and isotropically fit to target bounding size, centered on 256 canvas; no anisotropic scaling','candidates':rows,'contacts':{}}
for oid,filename in [('great-race-transition-selection-chamber-console','console-v3-source-six.png'),('industry-menagerie-pipe-valve-cluster','pipe-v3-source-six.png')]:
 rr=[r for r in rows if r['object_id']==oid];cp=contact(oid,filename,rr);man['contacts'][oid]={'path':f'reusable/views-additional/candidates/root-dark-worktops-unblocked-20261026-v3/contacts/{cp.name}','sha256':sha(cp),'included_views':['canonical source','front','top','right','left','bottom','rear'],'candidate_substitutions':[r['view'] for r in rr]}
mp=OUT/'candidate-manifest-v3.json';mp.write_text(json.dumps(man,indent=2)+'\n');print('manifest',sha(mp));print(json.dumps(man['contacts'],indent=2))
