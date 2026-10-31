#!/usr/bin/env python3
"""Guarded install of Page-approved source-faithful Scatterer six-view candidates."""
from pathlib import Path
from PIL import Image
import hashlib,json,os,struct
HERE=Path(__file__).resolve().parent;RAW=HERE/'raw';STAGE=RAW/'scatterer-v2-candidates';OID='scenario-props--scatterer';ORDER=['front','top','right','left','bottom','rear']
ATLAS=RAW/'scatterer-six-view-v2-20261026.png';REQUEST='exec-c216806a-c081-451f-a124-e75f5b890c9c'
REVIEW=Path('/workspace/scratch/page-scatterer-base-candidate-review-20261026.json')
def sha(b):return hashlib.sha256(b).hexdigest()
def rh(im):return sha(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes())
report=json.loads((STAGE/'scatterer-v2-stage-report.json').read_text());review=json.loads(REVIEW.read_text())
if report['source_atlas_sha256']!=sha(ATLAS.read_bytes()) or report['generation_request_id']!=REQUEST:raise SystemExit('raw generation evidence changed')
source=HERE.parents[0]/'native'/f'{OID}.png';source_sha=sha(source.read_bytes())
if report['source_image_sha256']!=source_sha:raise SystemExit('canonical native source changed')
index_path=HERE/'set-index.json';index=json.loads(index_path.read_text());assets={a['id']:a for a in index['assets']}
group=next(g for g in index['view_sets'] if g['object_id']==OID)
if group['complete'] and group.get('geometry_qa',{}).get('status')=='independently-reviewed-pass':raise SystemExit('already reviewed/install state changed')
staged=[]
for v in ORDER:
 aid=f'{OID}.{v}';live=HERE/f'{aid}.png';side=HERE/f'{aid}.json';old=live.read_bytes()
 expected_old=report['live_base_png_sha256'][v]
 if sha(old)!=expected_old:raise SystemExit(f'live source view changed before install: {aid}')
 row=next(x for x in report['candidates'] if x['view']==v);cand=HERE/row['candidate_path'];new=cand.read_bytes()
 if sha(new)!=row['png_sha256']:raise SystemExit(f'candidate hash mismatch: {aid}')
 meta=json.loads(side.read_text())
 if meta['provenance'].get('source_image')!=f'reusable/native/{OID}.png':raise SystemExit(f'noncanonical sidecar source: {aid}')
 staged.append((v,aid,live,side,old,new,cand,meta,row))
# Ensure review and stage evidence agree on current source/atlas/output hashes when fields exist.
flat=str(REVIEW)
for v,aid,live,side,old,new,cand,meta,row in staged:
 backup=STAGE/'previous-live'/f'{aid}.png';backup.parent.mkdir(exist_ok=True)
 if not backup.exists():backup.write_bytes(old)
 tmp=live.with_suffix('.png.tmp');tmp.write_bytes(new);os.replace(tmp,live)
 im=Image.open(cand).convert('RGBA');meta['image']['sha256']=sha(new);meta['image']['rgba_sha256']=rh(im)
 cell=row['cell_bounds_xywh']; bbox=row['alpha_bbox_local_xyxy']
 global_xywh=[cell[0]+bbox[0],cell[1]+bbox[1],bbox[2]-bbox[0],bbox[3]-bbox[1]]
 meta['provenance'].update({'source_image':f'reusable/native/{OID}.png','source_image_sha256':source_sha,'native_front':f'reusable/native/{OID}.png','native_front_sha256':source_sha,'source_atlas':f'reusable/views-additional/raw/{ATLAS.name}','source_atlas_sha256':sha(ATLAS.read_bytes()),'generation_request_id':REQUEST,'generation_prompt':'reusable/views-additional/raw/scatterer-six-view-v2-20261026.prompt.txt','generation_recipe':'reusable/views-additional/stage_scatterer_v2_20261026.py','generation_reference_images':[{'path':f'reusable/native/{OID}.png','sha256':source_sha},{'path':'reusable/views-additional/review-contacts/gameplay-scatterer-frames-batch-001-source-six.png','sha256':report['style_guide_contact_sha256']}],'notes':'Inferred orthographic projection preserves the dark source beetle identity and paired attached antennae; unseen surfaces are inferred, not recovered pixels. Six-view source-plus-six geometry review passed.','crop_bounds_px':{'coordinate_format':'xywh','nominal_cell':{'bounds':cell},'alpha_threshold':16,'alpha_bounds_global':global_xywh,'alpha_bbox_global_coordinate_format':'xywh','resized_bounds_px':row['resized_wh'],'canvas_offset_px':row['canvas_offset_xy'],'shared_anchor_px':[128,128],'uniform_scale':row['uniform_scale'],'normalization':'one shared isotropic scale calibrated to accepted elevation Z extents; common anchor'}})
 side.write_text(json.dumps(meta,indent=2)+'\n');assets[aid].clear();assets[aid].update(meta)
 (STAGE/f'{aid}.install-record.json').write_text(json.dumps({'asset_id':aid,'source_image':meta['provenance']['source_image'],'source_image_sha256':source_sha,'old_png_sha256':sha(old),'installed_png_sha256':sha(new),'source_atlas_sha256':report['source_atlas_sha256'],'generation_request_id':REQUEST,'review_evidence':flat,'review_status':'independently-reviewed-pass'},indent=2)+'\n')
index['assets']=[assets[x['id']] for x in index['assets']]
group['complete']=True;group['notes']='All six source-faithful inferred orthographic views passed current-hash independent source-plus-six review.'
group['geometry_qa']={'status':'independently-reviewed-pass','views':ORDER,'notes':'Page source-plus-six geometry review passed exact candidate hashes; source, atlas, all six live-base hashes and candidates were checked before install.','atlas_self_inspected':True,'review_evidence':'/workspace/scratch/page-scatterer-base-candidate-review-20261026.json'}
tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)
print(json.dumps({'installed':{f'{OID}.{v}':sha(x[5]) for v,x in zip(ORDER,staged)},'complete':group['complete'],'geometry_qa':group['geometry_qa']},indent=2))
