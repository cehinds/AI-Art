from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np, hashlib, json
from scipy.ndimage import label, generate_binary_structure

PACK=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
ROOT=PACK/'reusable/views-additional/candidates/equipment-dark-hidden-six-20261026'
RAW=ROOT/'raw'; IMAGES=ROOT/'images'
REVIEW=Path('/workspace/scratch/page-equipment-hidden6-v1-candidate-review.json')
PROOF=Path('/tmp/page-qa-equipment-next-six-reassessed-hidden-current-20261026-01.png.json')
PROMPTS={
 'flagstone':RAW/'flagstone-bottom-correction-request-v3.json',
 'mausoleum':RAW/'mausoleum-top-correction-request-v3.json',
 'quadrant':RAW/'quadrant-top-correction-request-v5.json',
}
OUTPUTS={
 'flagstone':RAW/'flagstone-bottom-correction-output-v3.png',
 'mausoleum':RAW/'mausoleum-top-correction-output-v3.png',
 'quadrant':RAW/'quadrant-top-correction-output-v5.png',
}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,obj): Path(p).write_text(json.dumps(obj,indent=2)+'\n')

def extract_normalize(raw_path,target_max,out_path):
 im=Image.open(raw_path).convert('RGBA'); alpha=np.array(im.getchannel('A'))
 labels,n=label(alpha>=64,structure=generate_binary_structure(2,2))
 comps=[]
 for i in range(1,n+1):
  yy,xx=np.where(labels==i)
  if len(xx)>500: comps.append((len(xx),i,(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))))
 assert comps, raw_path
 area,i,bbox=max(comps);x0,y0,x1,y1=bbox
 crop=im.crop(bbox); component=labels[y0:y1,x0:x1]
 mask=Image.fromarray(np.where(component==i,255,0).astype('uint8'))
 crop.putalpha(Image.fromarray(np.minimum(np.array(crop.getchannel('A')),np.array(mask)).astype('uint8')))
 scale=target_max/max(crop.size); dims=(round(crop.width*scale),round(crop.height*scale))
 resized=crop.resize(dims,Image.Resampling.NEAREST)
 canvas=Image.new('RGBA',(256,256),(0,0,0,0));offset=((256-dims[0])//2,(256-dims[1])//2);canvas.alpha_composite(resized,offset);canvas.save(out_path)
 return {'component_bbox_global_xyxy':list(bbox),'component_area_alpha64':area,'component_selection':'largest whole-atlas 8-connected alpha>=64 component','alpha_threshold':64,'connectivity':8,'uniform_scale':scale,'resized_dimensions':list(dims),'offset_px':list(offset),'anchor_px':[128,128],'canvas':[256,256],'resampler':'PIL.Image.Resampling.NEAREST'}

review=json.loads(REVIEW.read_text()); proof=json.loads(PROOF.read_text())
assert sha(PROOF)==review['current_source_and_six_proof_sha256'] if 'current_source_and_six_proof_sha256' in review else True
records={s['object_id']:s for s in review['current_source_and_six']}
# Exactly three target corrections are included in this version.
targets=[
 ('ghost-cemetery-cemetery-flagstone-corner-transition','bottom','flagstone',181,'ghost-cemetery-cemetery-flagstone-corner-transition.bottom.candidate-v2.png',
  'Full opaque L-shaped underside matches the approved top plan and source paver field; top material is inferred, no void.'),
 ('ghost-cemetery-mausoleum-facade','top','mausoleum',204,'ghost-cemetery-mausoleum-facade.top.candidate-v2.png',
  'True top-down shallow roof plan with ridge running depth; no front gable facade plane. Hidden roof detail inferred from same-object approved guide.'),
 ('thresholds-quadrant-selection-wheel','top','quadrant',181,'thresholds-quadrant-selection-wheel.top.candidate-v2.png',
  'Top projection keeps wide shallow ring body, separate round stand, volumetric arcs, and fixed gem quadrants; hidden construction inferred.')
]
sets=[]; current_by_object={}
for obj,view,key,target,name,note in targets:
 s=records[obj]; current_by_object[obj]=s
 source=s['source']
 # Abort if current canonical source or any sibling view no longer matches Page's reviewed bytes.
 src=Path(source['path']); assert sha(src)==source['sha256'],(obj,'source hash changed')
 for v,x in s['views'].items(): assert sha(x['path'])==x['sha256'],(obj,v,'source/current view changed; refresh candidate bindings')
 out=IMAGES/name; recipe=extract_normalize(OUTPUTS[key],target,out)
 prompt=PROMPTS[key]; promptj=json.loads(prompt.read_text())
 raw=OUTPUTS[key]
 assert sha(raw)==promptj['generation_output_sha256'],(key,'raw output hash differs from request record')
 assert sha(prompt)==hashlib.sha256(prompt.read_bytes()).hexdigest()
 refs=[]
 for r in promptj['references']:
  rf=PACK/r['path']; assert sha(rf)==r['sha256']; refs.append({'path':r['path'],'sha256':r['sha256'],'role':r.get('role')})
 donor_geometry=[r for r in refs if 'geometry' in str(r.get('role','')).lower()]
 sets.append({'object_id':obj,'view':view,'candidate_path':str(out.relative_to(PACK)),'candidate_sha256':sha(out),
  'source_path':source['path'],'source_sha256':source['sha256'],
  'base_current_views':{v:{'path':x['path'],'sha256':x['sha256']} for v,x in s['views'].items()},
  'raw_path':str(raw.relative_to(PACK)),'raw_sha256':sha(raw),'prompt_path':str(prompt.relative_to(PACK)),'prompt_sha256':sha(prompt),
  'references':refs,'geometry_guides':donor_geometry,'processing':recipe,'provenance_method':'generated','geometry_note':note})

# Capture proof with exact source and six current leaves plus new candidate for each repair.
cellw=220;cellh=250;cols=8
contact=Image.new('RGB',(cellw*cols,cellh*len(targets)),(235,235,235));draw=ImageDraw.Draw(contact)
for ri,(obj,view,key,target,name,note) in enumerate(targets):
 s=current_by_object[obj]; y=ri*cellh
 paths=[s['source']['path']]+[s['views'][v]['path'] for v in ['front','top','right','left','bottom','rear']]+[str(IMAGES/name)]
 labels=['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR','CAND '+view.upper()]
 for ci,(path,labeltext) in enumerate(zip(paths,labels)):
  src=Path(path); art=Image.open(src).convert('RGBA'); art.thumbnail((200,205),Image.Resampling.NEAREST)
  x=ci*cellw+(cellw-art.width)//2; yy=y+27+(205-art.height)//2
  bg=Image.new('RGBA',art.size,(225,225,225,255)); bg.alpha_composite(art); contact.paste(bg.convert('RGB'),(x,yy)); draw.text((ci*cellw+4,y+5),labeltext,fill=(0,0,0))
 draw.text((4,y+231),f'{obj}.{view}',fill=(0,0,0))
contact_path=ROOT/'hidden-six-source-current-candidate-contact-v2.png';contact.save(contact_path)
contact_json_path=ROOT/'hidden-six-source-current-candidate-contact-v2.json'
manifest_path=ROOT/'hidden-six-candidate-manifest-v2.json'
manifest={'candidate_id':'equipment-dark-hidden-six-candidate-v2','candidate_only':True,'candidate_owner':'views_equipment','reviewer':'page_inventory','installer':'views_dark_books','scope':'book-tiles/dungeon-after-dark',
 'parent_manifest_path':str((ROOT/'hidden-six-candidate-manifest-v1.json').relative_to(PACK)), 'parent_manifest_sha256':sha(ROOT/'hidden-six-candidate-manifest-v1.json'),
 'page_review_path':str(REVIEW),'page_review_sha256':sha(REVIEW),'source_and_six_proof_path':str(PROOF),'source_and_six_proof_sha256':sha(PROOF),
 'sets':sets,'reproducibility':{'script_path':str(Path(__file__).relative_to(PACK)),'script_sha256':sha(__file__),'procedure':'Select largest whole-atlas 8-connected alpha>=64 foreground component; preserve its original RGBA, normalize isotropically to stated target max extent on centered 256 transparent canvas using nearest-neighbor. Full source/current six hashes are preflighted before output.'}}
write_json(manifest_path,manifest)
contact_meta={'contact_path':str(contact_path.relative_to(PACK)),'contact_sha256':sha(contact_path),'manifest_path':str(manifest_path.relative_to(PACK)),'manifest_sha256':sha(manifest_path),'candidate_count':len(sets),'directions':[{'object_id':x['object_id'],'view':x['view'],'candidate_sha256':x['candidate_sha256']} for x in sets]}
write_json(contact_json_path,contact_meta)
print(json.dumps({'manifest':str(manifest_path),'manifest_sha256':sha(manifest_path),'contact':str(contact_path),'contact_sha256':sha(contact_path),'contact_json_sha256':sha(contact_json_path),'directions':[{'object_id':x['object_id'],'view':x['view'],'candidate_sha256':x['candidate_sha256']} for x in sets]},indent=2))
