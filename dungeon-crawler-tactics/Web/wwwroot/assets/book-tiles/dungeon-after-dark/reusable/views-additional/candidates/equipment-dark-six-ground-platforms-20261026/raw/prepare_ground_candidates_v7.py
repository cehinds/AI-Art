from PIL import Image,ImageDraw
from pathlib import Path
import json, hashlib, copy
PACK=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
BASE=PACK/'reusable/views-additional'
CAND=BASE/'candidates/equipment-dark-six-ground-platforms-20261026'
PROOF=Path('/tmp/page-qa-ground-curb-native-basis-current-20261026-01.png.json')
GUARD=Path('/workspace/scratch/page-equipment-civic-native-four-border-expansion-20261026.json')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
proof=json.loads(PROOF.read_text()); guard=json.loads(GUARD.read_text())
assert sha(PROOF)==guard['proof_sha256']
old=json.loads((CAND/'candidate-manifest-v6.json').read_text())
manifest=copy.deepcopy(old)
manifest['candidate_id']='equipment-dark-six-ground-platforms-v7'
script_rel='reusable/views-additional/candidates/equipment-dark-six-ground-platforms-20261026/raw/prepare_ground_candidates_v7.py'
manifest['normalizer_path']=script_rel
manifest['normalizer_sha256']=sha(__file__)
manifest['civic_source_six_proof_path']=str(PROOF); manifest['civic_source_six_proof_sha256']=sha(PROOF)
manifest['civic_native_plan_guard_path']=str(GUARD); manifest['civic_native_plan_guard_sha256']=sha(GUARD)
manifest['held_directions']=[h for h in manifest.get('held_directions',[]) if h.get('object_id')!='over-city-venues-civic-stone-tile-corner-transition']
# Rebind the candidate base to the latest immutable source/current-six proof.
setby={s['object_id']:s for s in manifest['sets']}
for obj in proof['objects']:
    s=setby.get(obj['object_id'])
    if not s: continue
    s['source']={'path':obj['source']['path'],'sha256':obj['source']['sha256']}
    s['base_current_views']={v:{'path':a['path'],'sha256':a['sha256']} for v,a in obj['views'].items()}
    s['base_proof_path']=str(PROOF); s['base_proof_sha256']=sha(PROOF)
# Source-derived top-down plan, alpha64 bbox, isotropic nearest-neighbor scale to 168px footprint.
oid='over-city-venues-civic-stone-tile-corner-transition'; entry=setby[oid]
source=Path(guard['object']['source']['path']); assert sha(source)==guard['object']['source']['sha256']
actual=next(o for o in proof['objects'] if o['object_id']==oid)
assert actual['source']['sha256']==sha(source)
for v,a in guard['object']['views'].items():
    p=Path(a['path']); assert sha(p)==a['sha256']==actual['views'][v]['sha256'],(v,sha(p),a['sha256'],actual['views'][v]['sha256'])
im=Image.open(source).convert('RGBA'); alpha=im.getchannel('A')
mask=alpha.point(lambda a:255 if a>=64 else 0); bbox=mask.getbbox(); assert bbox
crop=im.crop(bbox); scale=168/max(crop.size); dims=(round(crop.width*scale),round(crop.height*scale))
resized=crop.resize(dims,Image.Resampling.NEAREST); xy=((256-dims[0])//2,(256-dims[1])//2)
out=Image.new('RGBA',(256,256),(0,0,0,0)); out.alpha_composite(resized,xy)
imgpath=CAND/'images'/f'{oid}.top.candidate-v7.png'; out.save(imgpath,optimize=False)
entry['candidates']['top']={'path':str(imgpath),'sha256':sha(imgpath),'method':'canonical-source-native-plan-uniform-nearest-calibration','donor_path':str(source),'donor_sha256':sha(source),'alpha_threshold':64,'alpha_crop_bbox_xyxy':list(bbox),'normalization':{'filter':'NEAREST','uniform_scale':scale,'resized_dimensions':list(dims),'canvas':[256,256],'anchor_px':[128,128],'placement_xy':list(xy)},'notes':'Native source plan has four blue border edges and four gold corner caps; inferred overhead projection is a uniformly calibrated source copy.'}
entry['affected_views']=['top']; entry['notes']='TOP-only native source calibration. Preserve full-bank FRONT/RIGHT/LEFT/REAR and opaque BOTTOM; do not use superseded low/open-front candidate.'
# Build fresh diagnostic contact: source + all six views for the three held objects.
contact=Image.new('RGBA',(7*186+16,3*204+16),(35,35,40,255)); draw=ImageDraw.Draw(contact)
labels=['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR']; ids=['over-city-city-cobblestone-corner-transition','over-city-city-cobblestone-edge-transition',oid]
for ri,xid in enumerate(ids):
    o=next(a for a in proof['objects'] if a['object_id']==xid); s=setby[xid]
    rowims=[Image.open(o['source']['path']).convert('RGBA')]
    for v in ('front','top','right','left','bottom','rear'):
        cp=s.get('candidates',{}).get(v,{}).get('path')
        rowims.append(Image.open(cp).convert('RGBA') if cp else Image.open(o['views'][v]['path']).convert('RGBA'))
    y=8+ri*204; draw.text((8,y),xid,fill='white')
    for ci,viewim in enumerate(rowims):
        x=8+ci*186; yv=y+22; viewim.thumbnail((170,170),Image.Resampling.NEAREST)
        contact.alpha_composite(viewim,(x+(170-viewim.width)//2,yv+(170-viewim.height)//2)); draw.text((x,yv+172),labels[ci],fill='white')
mp=CAND/'candidate-manifest-v7.json'; mp.write_text(json.dumps(manifest,indent=2)+'\n')
cp=CAND/'contacts/source-six-candidate-v7.png'; contact.save(cp)
print(json.dumps({'manifest':str(mp),'manifest_sha256':sha(mp),'contact':str(cp),'contact_sha256':sha(cp),'top':str(imgpath),'top_sha256':sha(imgpath),'bbox':bbox,'scale':scale,'dimensions':dims,'offset':xy},indent=2))
