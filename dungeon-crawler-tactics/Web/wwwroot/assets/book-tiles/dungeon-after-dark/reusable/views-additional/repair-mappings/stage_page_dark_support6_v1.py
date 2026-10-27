"""Rebuild the source-bound support/underside candidate contact deterministically."""
from pathlib import Path
import hashlib,json,math
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage

HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
CDIR=OUT/'candidates/page-dark-next-six-support6-v1'
HANDOFF=CDIR/'support6-handoff.json';MAPPING=CDIR/'request-result-mapping.json'
MANIFEST=CDIR/'candidate-manifest.json';CONTACT=CDIR/'support6-source-six-candidates.png'
DIRS=('front','top','right','left','bottom','rear')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def rel_book(path):return Path(path).resolve().relative_to(BOOK.resolve()).as_posix()
def bounds_and_components(im,threshold=16,min_area=4):
 a=np.asarray(im.convert('RGBA'))[:,:,3]>=threshold
 lab,n=ndimage.label(a,np.ones((3,3),dtype=np.uint8))
 counts=np.bincount(lab.ravel());keep=np.where(counts>=min_area)[0];keep=keep[keep!=0]
 chosen=np.isin(lab,keep)
 ys,xs=np.where(chosen)
 if not len(xs):raise ValueError('candidate image has no usable alpha components')
 return (int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)),int(chosen.sum()),len(keep),chosen
def normalize(raw,target_max,dst):
 im=Image.open(raw).convert('RGBA');box,pixels,ncomp,mask=bounds_and_components(im)
 crop=im.crop(box);w,h=crop.size;scale=target_max/max(w,h)
 nw=max(1,round(w*scale));nh=max(1,round(h*scale))
 crop=crop.resize((nw,nh),Image.Resampling.NEAREST)
 canvas=Image.new('RGBA',(256,256),(0,0,0,0));offset=((256-nw)//2,(256-nh)//2);canvas.alpha_composite(crop,offset)
 dst.parent.mkdir(parents=True,exist_ok=True);canvas.save(dst)
 return {'alpha_threshold':16,'component_connectivity':8,'component_min_area':4,'component_count':ncomp,
   'selected_component_pixels':pixels,'crop_bounds_xyxy_px':list(box),'raw_dimensions_px':list(im.size),
   'uniform_scale':scale,'resized_dimensions_px':[nw,nh],'offset_px':list(offset),'canvas_px':[256,256],
   'anchor_px':[128,128],'resampling':'nearest-neighbor'}

def main():
 h=json.loads(HANDOFF.read_text());mapping=json.loads(MAPPING.read_text());assert len(h['objects'])==6
 reqs={r['target']:r for r in mapping['requests']}
 # Root separately re-opened the ladder BOTTOM hold after building6 and assigned a current guarded target.
 ladder_id='over-city-roof-access-ladder'
 ids={o['object_id']:o for o in h['objects']}
 # Add the Page handoff's roof ladder base-binding from the same immutable Page capture.
 pagebase=CDIR/'root74-current-base-proof.json'
 base=json.loads(pagebase.read_text())
 record=base['records']['book-tiles/dungeon-after-dark::'+ladder_id]
 ladder={'object_id':ladder_id,'source_path':rel_book(Path(record['source'])),'source_sha256':record['source_sha256'],
  'base_six':{v:{'path':rel_book(Path(record['view_paths'][v])),'sha256':record['image_hashes'][v]} for v in DIRS}}
 objects=list(h['objects'])+[ladder]
 image_sources={
  'parade-horribles-white-arena-tree-landmark.bottom':('tree-bottom-v2',124),
  'parade-horribles-parade-staging-platform.bottom':('staging-bottom',215),
  'parade-horribles-jumbotron-display-frame.top':('jumbotron-top',210),
  'masquerade-banquet-table.bottom':('banquet-bottom',195),
  'masquerade-formal-ballroom-dais.bottom':('dais-bottom',209),
  'masquerade-formal-ballroom-dais.rear':('dais-rear',178),
  'parade-horribles-empty-spectator-bleachers.rear':('bleachers-rear',210),
  'over-city-roof-access-ladder.bottom':('roof-ladder-bottom','match-top')}
 idx=json.loads((OUT/'set-index.json').read_text());assetidx={a['id']:a for a in idx['assets']}
 manifest={'created_at':'2026-10-26','status':'candidate-only; Root review requested','scope':'Page support6 plus Root roof ladder BOTTOM','handoff_path':'reusable/views-additional/candidates/page-dark-next-six-support6-v1/support6-handoff.json',
  'handoff_sha256':sha(HANDOFF),'request_result_mapping_path':'reusable/views-additional/candidates/page-dark-next-six-support6-v1/request-result-mapping.json','request_result_mapping_sha256':sha(MAPPING),
  'root_ladder_current_base_proof':'reusable/views-additional/candidates/page-dark-next-six-support6-v1/root74-current-base-proof.json',
  'root_ladder_current_base_proof_sha256':sha(CDIR/'root74-current-base-proof.json'),
  'objects':[],'candidates':[],'candidate_only':True}
 for obj in objects:
  oid=obj['object_id']
  if oid==ladder_id:srcrel=obj['source_path'];srcsha=obj['source_sha256'];bases=obj['base_six']
  else:
   srcabs=Path(obj['source']['path']);srcrel=rel_book(srcabs);srcsha=obj['source']['sha256']
   bases={v:{'path':rel_book(Path(b['path'])),'sha256':b['sha256']} for v,b in obj['views'].items()}
  src=safe(BOOK,srcrel);assert sha(src)==srcsha
  for v,b in bases.items():assert sha(safe(BOOK,b['path']))==b['sha256'],f'{oid}.{v} baseline changed'
  manifest['objects'].append({'object_id':oid,'source_path':srcrel,'source_sha256':srcsha,'base_six':bases})
 for aid,(target,target_max) in image_sources.items():
  oid,view=aid.rsplit('.',1);obj=next(o for o in objects if o['object_id']==oid)
  srcrel=rel_book(Path(obj['source']['path'])) if oid!=ladder_id else obj['source_path']
  srcsha=obj['source']['sha256'] if oid!=ladder_id else obj['source_sha256']
  req=reqs[target];raw=safe(OUT,req['raw_path']);assert sha(raw)==req['raw_sha256']
  if target_max=='match-top':
   top=Image.open(safe(BOOK,bases['top']['path'])).convert('RGBA');box,_,_,_=bounds_and_components(top);target_max=max(box[2]-box[0],box[3]-box[1])
  cpath=CDIR/'images'/f'{aid}.candidate.png'
  if aid=='parade-horribles-jumbotron-display-frame.bottom':
   raise AssertionError('unreachable')
  norm=normalize(raw,target_max,cpath)
  # Bottom jumbotron shares the accepted generated plan's fixed symmetric footprint, rotated 180 degrees.
  candrel=rel_book(cpath);candsha=sha(cpath)
  base_six=obj['views'] if oid!=ladder_id else obj['base_six']
  refs={}
  selected={'parade-horribles-white-arena-tree-landmark':['front','right'],
    'parade-horribles-parade-staging-platform':['front','top'],'parade-horribles-jumbotron-display-frame':['front','right'],
    'masquerade-banquet-table':['front','top'],'masquerade-formal-ballroom-dais':['front','right','top'],
    'parade-horribles-empty-spectator-bleachers':['front','right','top'],'over-city-roof-access-ladder':['front','top']}[oid]
  for v in selected:
   b=base_six[v];rpath=rel_book(Path(b['path'])) if Path(b['path']).is_absolute() else b['path'];rp=safe(BOOK,rpath);assert sha(rp)==b['sha256'];refs[v]={'path':rpath,'sha256':b['sha256']}
  cand={'object_id':oid,'asset_id':aid,'view':view,'candidate_path':candrel,'candidate_sha256':candsha,'dimensions_px':[256,256],'anchor_px':[128,128],
   'source_path':srcrel,'source_sha256':srcsha,'baseline_six':bases,'raw_path':rel_book(raw),'raw_sha256':sha(raw),'request_id':req['request_id'],
   'prompt_path':'reusable/views-additional/'+req['prompt_path'],'prompt_sha256':req['prompt_sha256'],'references':refs,'normalization':norm,
   'notes':'Hidden underside/support details are inferred; source materials and accepted siblings are retained.'}
  manifest['candidates'].append(cand)
 # A rotational symmetry alias for the other orthographic end of the same rigid frame.
 top=next(c for c in manifest['candidates'] if c['asset_id']=='parade-horribles-jumbotron-display-frame.top')
 topimg=Image.open(safe(BOOK,top['candidate_path'])).convert('RGBA').transpose(Image.Transpose.ROTATE_180)
 bottomid='parade-horribles-jumbotron-display-frame.bottom';bottompath=CDIR/'images'/f'{bottomid}.candidate.png';topimg.save(bottompath)
 bo=next(o for o in objects if o['object_id']=='parade-horribles-jumbotron-display-frame')
 manifest['candidates'].append({'object_id':bo['object_id'],'asset_id':bottomid,'view':'bottom','candidate_path':rel_book(bottompath),'candidate_sha256':sha(bottompath),
   'dimensions_px':[256,256],'anchor_px':[128,128],'source_path':top['source_path'],'source_sha256':top['source_sha256'],'baseline_six':bo['views'],
   'derived_from_candidate':top['candidate_path'],'derived_from_candidate_sha256':top['candidate_sha256'],'transformation':'rigid 180-degree rotation; inferred top/bottom plan symmetry of fixed rectangular support frame',
   'normalization':{'method':'alias from accepted candidate plan; 180-degree rigid rotation only','uniform_scale':1.0,'resampling':'none','anchor_px':[128,128]},'notes':'Same symmetric fixed support footprint inferred from above and below; no screen face.'})
 # Build source-plus-six candidate contact from current canonical sources and proposed cells.
 candmap={c['asset_id']:c for c in manifest['candidates']};ids=[o['object_id'] for o in objects];cell,label,gap=210,24,6
 contact=Image.new('RGB',(7*(cell+gap)+gap,len(ids)*(cell+label+gap)+gap),(55,55,62));draw=ImageDraw.Draw(contact)
 proof=[]
 for ri,oid in enumerate(ids):
  source=next(o for o in manifest['objects'] if o['object_id']==oid)['source_path'];cells=[]
  paths=[('SOURCE',safe(BOOK,source))]
  for v in DIRS:
   a_id=f'{oid}.{v}';c=candmap.get(a_id)
   p=safe(BOOK,c['candidate_path']) if c else safe(BOOK,assetidx[a_id]['image']['path']);paths.append((v,p))
  for ci,(labeltxt,p) in enumerate(paths):
   im=Image.open(p).convert('RGBA');im.thumbnail((cell-8,cell-8),Image.Resampling.NEAREST)
   x=gap+ci*(cell+gap);y=gap+ri*(cell+label+gap);draw.rectangle((x,y,x+cell,y+cell),fill=(26,27,31));contact.paste(im,(x+(cell-im.width)//2,y+(cell-im.height)//2),im);draw.text((x+2,y+cell+2),labeltxt,fill='white')
   cells.append({'label':labeltxt,'path':rel_book(p),'sha256':sha(p)})
  proof.append({'object_id':oid,'cells':cells})
 CONTACT.parent.mkdir(parents=True,exist_ok=True);contact.save(CONTACT)
 manifest['contact_path']=CONTACT.relative_to(OUT).as_posix();manifest['contact_sha256']=sha(CONTACT);manifest['candidate_count']=len(manifest['candidates'])
 MANIFEST.parent.mkdir(parents=True,exist_ok=True);MANIFEST.write_text(json.dumps(manifest,indent=2)+'\n')
 proofpath=CDIR/'source-six-contact-proof.json';proofpath.write_text(json.dumps({'contact_path':manifest['contact_path'],'contact_sha256':manifest['contact_sha256'],'manifest_path':MANIFEST.relative_to(OUT).as_posix(),'manifest_sha256':sha(MANIFEST),'rows':proof},indent=2)+'\n')
 print(json.dumps({'manifest':MANIFEST.relative_to(OUT).as_posix(),'manifest_sha256':sha(MANIFEST),'contact':manifest['contact_path'],'contact_sha256':sha(CONTACT),'candidates':len(manifest['candidates'])},indent=2))
if __name__=='__main__':main()
