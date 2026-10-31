#!/usr/bin/env python3
"""Use accepted front/rear as symmetric sides and calibrate both plans to common width."""
from pathlib import Path
import json,hashlib,struct,shutil
from PIL import Image
import numpy as np
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';RAW=VD/'raw';COR=VD/'corrections.json';IDX=VD/'set-index.json'
IDS=['iron-tracks-tunnel-stone-endcap-northwest','iron-tracks-tunnel-stone-endcap-northeast'];views=['front','top','right','left','bottom','rear']
ledger=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed'];idx=json.loads(IDX.read_text());ops=json.loads(COR.read_text())['operations']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
def save_meta(oid,v,md,im):
 p=VD/f'{oid}.{v}.png';mp=VD/f'{oid}.{v}.json';md['image']={'path':f'reusable/views-additional/{oid}.{v}.png','width':256,'height':256,'sha256':sha(p),'rgba_sha256':rgba_sha(im)};mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a['id']==md['id']:a.clear();a.update(md);break
for row,oid in enumerate(IDS):
 r=ledger[f'book-tiles/pocket-dungeon::{oid}']
 if r['status']!='needs-correction' or not {'top','right','left','bottom'}<=set(x.lower() for x in r.get('affected_views',[])):raise SystemExit(f'root review scope changed for {oid}')
 # Verify entire current source+six capture and retained pre-install target snapshots.
 if sha(r['source'])!=r['source_sha256']:raise SystemExit('canonical source changed')
 for v,p in r['view_paths'].items():
  if sha(p)!=r['image_hashes'][v]:raise SystemExit(f'current source+six hash changed: {oid}.{v}')
 hist=r.get('history',[])
 if not hist:raise SystemExit(f'missing prior root capture for {oid}')
 base_hashes=hist[-1]['image_hashes']
 before={}
 for v in ['right','left','bottom']:
  snap=RAW/'targeted-repairs'/f'{oid}.{v}.before-endcaps-v3.png'
  if not snap.is_file() or sha(snap)!=base_hashes[v]:raise SystemExit(f'old pre-repair snapshot does not match prior independent capture {oid}.{v}')
  before[v]=sha(snap)
 # Symmetric view aliases: R <- accepted F, L <- accepted REAR.
 for target,source in [('right','front'),('left','rear')]:
  target_path=VD/f'{oid}.{target}.png';source_path=VD/f'{oid}.{source}.png';target_meta_path=VD/f'{oid}.{target}.json';source_meta=json.loads((VD/f'{oid}.{source}.json').read_text());md=json.loads(target_meta_path.read_text());source_hash=sha(source_path)
  shutil.copyfile(source_path,target_path);md.setdefault('provenance_history',[]).append(md.get('provenance',{}));base=md['provenance_history'][0] if md['provenance_history'] else md.get('provenance',{});target_source=base.get('source_image');target_source_sha=hashlib.sha256((PACK/target_source).read_bytes()).hexdigest() if target_source and (PACK/target_source).is_file() else base.get('source_sha256');input_source=source_meta.get('provenance',{}).get('source_image');input_source_sha=hashlib.sha256((PACK/input_source).read_bytes()).hexdigest() if input_source and (PACK/input_source).is_file() else None
  md['provenance']={**base,'method':'inferred-symmetric-view-copy','source_image':target_source,'source_sha256':target_source_sha,'symmetric_alias_of':source,'symmetric_alias_object_id':oid,'symmetry_reason':'This compact square masonry endcap has symmetric opposite broad faces; reuse the independently accepted FRONT/REAR projections for RIGHT/LEFT to preserve a coherent square footprint and shared Z.','derivation_input':{'asset_id':source_meta['id'],'object_id':oid,'view':source,'image_path':source_meta['image']['path'],'image_sha256':source_hash,'source_image':input_source,'source_sha256':input_source_sha},'notes':'Exact copy of the accepted opposite principal face for a symmetric orthographic endcap; canonical target source provenance retained.'};md['geometry_qa']='pending-review';im=Image.open(target_path).convert('RGBA');save_meta(oid,target,md,im)
  ops.append({'type':'alias','object_id':oid,'target':target,'source':source,'source_object_id':oid,'before_sha256':before[target],'source_sha256':source_hash,'after_sha256':source_hash,'reason':'Square symmetric masonry endcap: reuse its own accepted opposite broad face to achieve matching side footprint and shared Z.'})
 # Uniformly scale TOP to FRONT width.
 top_path=VD/f'{oid}.top.png';front_path=VD/f'{oid}.front.png';md=json.loads((VD/f'{oid}.top.json').read_text());im=Image.open(top_path).convert('RGBA');bbox=im.getchannel('A').getbbox();ref=Image.open(front_path).convert('RGBA').getchannel('A').getbbox();crop=im.crop(bbox);scale=(ref[2]-ref[0])/(bbox[2]-bbox[0]);size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)));crop=crop.resize(size,Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop,((256-size[0])//2,248-size[1]));before_top=sha(top_path);frame.save(top_path,optimize=True);md.setdefault('provenance_history',[]).append(md.get('provenance',{}));md.setdefault('provenance',{})['axis_correction']={'method':'uniform-scale-to-matching-plan-width','reference_view':'front','reference_sha256':sha(front_path),'scale':scale,'source_bbox':list(bbox),'render_size':list(size),'resampling':'NEAREST','notes':'Uniformly calibrate square TOP footprint to accepted broad front width.'};md['geometry_qa']='pending-review';save_meta(oid,'top',md,frame);ops.append({'type':'uniform-scale-to-view-width','object_id':oid,'view':'top','reference_view':'front','before_sha256':before_top,'reference_sha256':sha(front_path),'after_sha256':sha(top_path),'reason':'Uniformly calibrate the square endcap TOP footprint to the accepted FRONT width; preserve aspect and source material.'})
 # Replace BOTTOM from retained full-plan atlas and uniformly scale to FRONT width.
 ap=RAW/'atlases/iron-tracks-endcaps-sides-v1.png';atlas=Image.open(ap).convert('RGBA');aa=np.asarray(atlas.getchannel('A'));# source row bottom component bounded in col 4
 centers=[]
 from scipy import ndimage
 labels,n=ndimage.label(aa>=245,structure=np.ones((3,3),dtype=np.uint8));
 for lab,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is None:continue
  ar=int((labels[sl]==lab).sum());yy,xx=ndimage.center_of_mass(labels==lab);cx=(4.5)*atlas.width/6;cy=(row+.5)*atlas.height/2
  if ar>=500:centers.append((abs(xx-cx)+abs(yy-cy),lab,sl,ar))
 _,lab,sl,area=min(centers);cropbox=(sl[1].start,sl[0].start,sl[1].stop,sl[0].stop);crop=atlas.crop(cropbox);front=Image.open(front_path).convert('RGBA');fb=front.getchannel('A').getbbox();targetw=fb[2]-fb[0];scale=targetw/crop.width;size=(targetw,max(1,round(crop.height*scale)));crop=crop.resize(size,Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop,((256-size[0])//2,248-size[1]));bottom_path=VD/f'{oid}.bottom.png';md=json.loads((VD/f'{oid}.bottom.json').read_text());bottom_before=before['bottom'];atlas_sha=sha(ap);frame.save(bottom_path,optimize=True);original_prov=(md.get('provenance_history') or [md.get('provenance',{})])[0];md['provenance_history']=[original_prov];md['provenance']={'method':'generated','source_image':original_prov.get('source_image'),'source_sha256':hashlib.sha256((PACK/original_prov['source_image']).read_bytes()).hexdigest(),'generated_atlas':'reusable/views-additional/raw/atlases/iron-tracks-endcaps-sides-v1.png','generated_atlas_sha256':atlas_sha,'generation_request':'reusable/views-additional/raw/requests/iron-tracks-endcaps-sides-v1.json','normalization':{'component_policy':'whole-atlas CC selected by source row and BOTTOM column centroid; full bounds retained','component':[lab,area,list(cropbox)],'reference_view':'front','reference_sha256':sha(front_path),'uniform_scale':scale,'render_size':list(size),'resampling':'NEAREST','anchor_px':[128,248]},'notes':'Inferred full-footprint underside plan calibrated uniformly to the accepted front width.'};md['geometry_qa']='pending-review';save_meta(oid,'bottom',md,frame)
 ops.append({'type':'replace-generated-view','object_id':oid,'view':'bottom','before_sha256':bottom_before,'after_sha256':sha(bottom_path),'atlas_path':'raw/atlases/iron-tracks-endcaps-sides-v1.png','atlas_sha256':atlas_sha,'crop_bbox':list(cropbox),'reference_view':'front','reference_sha256':sha(front_path),'scale':scale,'render_size':list(size),'reason':'Use the retained source-matched full-footprint underside plan and uniformly calibrate it to the broad accepted front width.'})
 g=next(x for x in idx['view_sets'] if x['object_id']==oid);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='RIGHT/LEFT derived from accepted symmetric FRONT/REAR; TOP/BOTTOM uniformly calibrated to common footprint; awaiting independent source+six review.'
COR.write_text(json.dumps({'version':json.loads(COR.read_text()).get('version',1),'operations':ops},indent=2)+'\n')
IDX.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps({oid:{v:sha(VD/f'{oid}.{v}.png') for v in ['top','right','left','bottom']} for oid in IDS},indent=2))
