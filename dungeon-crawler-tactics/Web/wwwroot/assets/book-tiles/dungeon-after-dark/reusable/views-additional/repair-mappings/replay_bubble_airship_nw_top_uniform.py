"""Guarded isotropic replay for the airship north-wall TOP view."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;SPEC=json.loads((HERE/'bubble-airship-northwest-top-uniform.json').read_text());INDEX=OUT/'set-index.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
idx=json.loads(INDEX.read_text());asset=next(a for a in idx['assets'] if a['id']==SPEC['asset_id']);out=BOOK/asset['image']['path'];raw=OUT/SPEC['raw_pack_path']
assert sha(BOOK/SPEC['source_image'])==SPEC['source_sha256'],'source changed'
assert sha(raw)==SPEC['raw_atlas_sha256'],'raw atlas changed'
assert sha(OUT/SPEC['prompt_path'].replace('reusable/views-additional/',''))==SPEC['prompt_sha256'],'prompt changed'
assert sha(out) in {SPEC['before_sha256'],SPEC.get('after_sha256')},'unexpected current output; refusing rewrite'
if sha(out)!=SPEC.get('after_sha256'):
 im=Image.open(raw).convert('RGBA');b=SPEC['source_rect']['alpha_bounds'];crop=im.crop((b[0],b[1],b[0]+b[2],b[1]+b[3]));scale=SPEC['uniform_scale'];nw=round(crop.width*scale);nh=round(crop.height*scale);crop=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256));off=((256-nw)//2,(256-nh)//2);canvas.alpha_composite(crop,off);tmp=out.with_suffix('.png.tmp');canvas.save(tmp,format='PNG',optimize=True);os.replace(tmp,out)
 actual=sha(out)
 if SPEC.get('after_sha256') and actual!=SPEC['after_sha256']:raise RuntimeError('output hash differs from the frozen replay spec')
 SPEC['after_sha256']=actual;SPEC['normalization']={'scale':scale,'offset_px':list(off),'size_px':[nw,nh]};(HERE/'bubble-airship-northwest-top-uniform.json').write_text(json.dumps(SPEC,indent=2)+'\n')
im=Image.open(out).convert('RGBA');asset['image']['sha256']=sha(out);asset['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+im.tobytes()).hexdigest()
hist=asset.setdefault('provenance_history',[]);marker='airship-northwest-top-uniform-v1'
if not any(h.get('candidate_id')==marker for h in hist):hist.append({'candidate_id':marker,'previous_image_sha256':SPEC['before_sha256'],'previous_provenance':asset.get('provenance',{})})
asset['provenance']={'method':'generated-orthographic-view-uniform-normalization','source_image':SPEC['source_image'],'source_contact_sheet':SPEC['source_contact_sheet'],'source_contact_sheet_sha256':SPEC['source_contact_sheet_sha256'],'generated_atlas':SPEC['raw_atlas'],'generated_atlas_sha256':SPEC['raw_atlas_sha256'],'prompt_path':SPEC['prompt_path'],'prompt_sha256':SPEC['prompt_sha256'],'source_rect':SPEC['source_rect'],'normalization':{**SPEC.get('normalization',{}),'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; one isotropic factor derived from accepted front world-X extent'},'geometry_basis':'north-wall extends along world X; top plan length matches front world-X span','notes':'Aspect-preserving uniformly normalized orthographic plan. The earlier anisotropic calibration is retained in provenance history; inferred geometry, not calibrated 3D.'}
meta=BOOK/asset['metadata_path'];tmp=meta.with_suffix('.json.tmp');tmp.write_text(json.dumps(asset,indent=2)+'\n');os.replace(tmp,meta)
ss=next(s for s in idx['view_sets'] if s['object_id']==SPEC['object_id']);ss['complete']=False;ss['notes']='TOP reprocessed with one isotropic world-X scale; pending current-hash source+six review.'
tmp=INDEX.with_suffix('.json.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
print(SPEC['after_sha256'])
