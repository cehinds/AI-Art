from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects
import numpy as np,json,hashlib,struct
from pathlib import Path
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon');OUT=ROOT/'reusable/views-additional/raw/candidates/desert-doorway-plans-rear-v1';ATLAS=OUT/'raw-atlas.png';ids=['bubble-desert-adobe-desert-plaster-closed-doorway','bubble-desert-adobe-desert-plaster-open-doorway'];views=['front','top','right','left','bottom','rear'];xs=[222.5,622.5,948.5,1225.5,1549,1950];ys=[185,530]
h=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rgba=lambda p:(lambda im:hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest())(Image.open(p).convert('RGBA'))
im=Image.open(ATLAS).convert('RGBA');a=np.array(im)[:,:,3];lab,n=label(a>8);comps=[]
for i,s in enumerate(find_objects(lab),1):
 if s:
  y,x=s;area=int((lab[s]==i).sum())
  if area>100:comps.append({'label':i,'bbox':[x.start,y.start,x.stop,y.stop],'area':area,'cx':(x.start+x.stop)/2,'cy':(y.start+y.stop)/2})
assert len(comps)==12,len(comps)
manifest={'batch_id':'desert-doorway-plans-rear-v1-20261026','status':'staged-awaiting-root-review','raw_atlas':{'path':ATLAS.relative_to(ROOT).as_posix(),'sha256':h(ATLAS),'output_binding':'/workspace/generated_images/exec-1da4d7e6-64b3-48b5-a987-7a80aacef968.png'},'prompt_file':(OUT/'prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':h(OUT/'prompt.txt'),'objects':[]}
for ri,oid in enumerate(ids):
 row={}; records=[]; source=ROOT/'bubble-desert/components'/f'{oid}.png'; front=Image.open(ROOT/'reusable/views-additional'/f'{oid}.front.png').convert('RGBA');fb=front.getchannel('A').getbbox();fw,fh=fb[2]-fb[0],fb[3]-fb[1]
 for vi,v in enumerate(views):
  c=min(comps,key=lambda z:abs(z['cx']-xs[vi])+abs(z['cy']-ys[ri]));x0,y0,x1,y1=c['bbox'];crop=im.crop((x0,y0,x1,y1));
  target=ROOT/'reusable/views-additional'/f'{oid}.{v}.png';tb=Image.open(target).convert('RGBA').getchannel('A').getbbox();tw,th=tb[2]-tb[0],tb[3]-tb[1]
  if v not in ('top','bottom','rear'):
   frame=Image.open(target).convert('RGBA');scale=1;size=[frame.width,frame.height]
  else:
   scale=(fh/crop.height if v=='rear' else fw/crop.width);size=[round(crop.width*scale),round(crop.height*scale)];crop=crop.resize(tuple(size),Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop,((256-size[0])//2,248-size[1]))
   candidate=OUT/f'{oid}.{v}.candidate.png';frame.save(candidate,optimize=True)
   records.append({'view':v,'candidate_path':candidate.relative_to(ROOT).as_posix(),'candidate_sha256':h(candidate),'candidate_rgba_sha256':rgba(candidate),'target_path':target.relative_to(ROOT).as_posix(),'target_sha256_before':h(target),'raw_component':c,'scale':scale,'render_size':size,'resampling':'NEAREST','anchor_px':[128,248]})
  row[v]=frame
 row['source']=Image.open(source).convert('RGBA')
 contact=Image.new('RGBA',(7*256,256),(235,235,235,255));draw=ImageDraw.Draw(contact);bg=Image.new('RGBA',(256,256),'white');bg.alpha_composite(row['source']);contact.alpha_composite(bg,(0,0));draw.text((4,4),'source',fill='black')
 for col,v in enumerate(views,1):contact.alpha_composite(row[v],(col*256,0));draw.text((col*256+4,4),v,fill='black')
 cp=OUT/f'{oid}.candidate-source-plus-six.png';contact.convert('RGB').save(cp)
 manifest['objects'].append({'object_id':oid,'source_path':source.relative_to(ROOT).as_posix(),'source_sha256':h(source),'current_root_proof_status':json.load(open('/workspace/scratch/view-qa-root.json'))['reviewed'][f'book-tiles/pocket-dungeon::{oid}']['status'],'current_target_hashes':{v:h(ROOT/'reusable/views-additional'/f'{oid}.{v}.png') for v in views},'candidates':records,'contact_path':cp.relative_to(ROOT).as_posix(),'contact_sha256':h(cp)})
(OUT/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'atlas_sha256':h(ATLAS),'objects':[(x['object_id'],x['contact_path'],x['contact_sha256']) for x in manifest['objects']]},indent=2))
