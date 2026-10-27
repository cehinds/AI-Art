"""Combine accepted tree-canopy underside with its plain source-backed stone base."""
from pathlib import Path
import json,hashlib,copy
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parents[1];PACK=OUT.parent.parent;CDIR=OUT/'candidates/page-dark-next-six-support6-v1/held-corrections-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):return Image.open(p).convert('RGBA')
idx=json.loads((OUT/'set-index.json').read_text());A={a['id']:a for a in idx['assets']};oid='parade-horribles-white-arena-tree-landmark';view='bottom'
asset=A[oid+'.front'];src=PACK/asset['source']['source_image'];srcsha=asset['source']['source_sha256'];assert sha(src)==srcsha
base={v:{'path':A[oid+'.'+v]['image']['path'],'sha256':A[oid+'.'+v]['image']['sha256']} for v in ['front','top','right','left','bottom','rear']}
for v,e in base.items():assert sha(PACK/e['path'])==e['sha256']
canopy=CDIR/'images/parade-horribles-white-arena-tree-landmark.bottom.candidate-v2.png';base_png=OUT/'candidates/page-dark-next-six-support6-v1/images/parade-horribles-white-arena-tree-landmark.bottom.candidate.png'
assert sha(canopy);assert sha(base_png)
back=rgba(canopy);fore=rgba(base_png);bb=fore.getchannel('A').getbbox();crop=fore.crop(bb);w,h=crop.size;targetw=108;scale=targetw/w;size=(targetw,round(h*scale));crop=crop.resize(size,Image.Resampling.NEAREST)
layer=Image.new('RGBA',(256,256),(0,0,0,0));layer.alpha_composite(crop,((256-size[0])//2,(256-size[1])//2));back.alpha_composite(layer,(0,0))
out=CDIR/'images/parade-horribles-white-arena-tree-landmark.bottom.candidate-v3.png';back.save(out,format='PNG',optimize=False)
manifest={'status':'candidate-only; Root review requested','object_id':oid,'view':view,'source_path':asset['source']['source_image'],'source_sha256':srcsha,'baseline_six':base,'candidate_path':out.relative_to(PACK).as_posix(),'candidate_sha256':sha(out),'dimensions_px':[256,256],'anchor_px':[128,128],'derivation':{'method':'alpha-composite-canopy-and-stone-base','canopy_candidate_path':canopy.relative_to(PACK).as_posix(),'canopy_candidate_sha256':sha(canopy),'base_candidate_path':base_png.relative_to(PACK).as_posix(),'base_candidate_sha256':sha(base_png),'base_alpha_bbox_xyxy':list(bb),'base_crop_dimensions_px':[w,h],'uniform_scale':scale,'resized_base_dimensions_px':list(size),'offset_px':[(256-size[0])//2,(256-size[1])//2],'resampling':'nearest','base_width_ratio_to_canopy':'approximately 2/3','layer_order':'canopy behind; opaque stone base over central trunk'},'notes':'Base has no invented wheels; inferred trunk footing occludes canopy center.'}
mp=CDIR/'tree-bottom-base-occlusion-v3-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
# source + actual current six + v3 output contact
cells=[('SOURCE',src,srcsha)]+[(v,PACK/e['path'],e['sha256']) for v,e in base.items()]+[('BOTTOM V3',out,sha(out))];contact=Image.new('RGBA',(230*8,260),(18,21,26,255));rows=[]
for i,(label,p,hsh) in enumerate(cells):
 assert sha(p)==hsh;im=rgba(p);im.thumbnail((210,210),Image.Resampling.NEAREST);tile=Image.new('RGBA',(230,260),(30,33,39,255));tile.alpha_composite(im,((230-im.width)//2,8+(210-im.height)//2));ImageDraw.Draw(tile).text((5,235),label,fill='white');contact.alpha_composite(tile,(230*i,0));rows.append({'label':label,'path':p.relative_to(PACK).as_posix(),'sha256':hsh})
cp=CDIR/'tree-bottom-base-occlusion-v3-source-six.png';contact.save(cp);proof={'manifest_path':mp.relative_to(PACK).as_posix(),'manifest_sha256':sha(mp),'contact_path':cp.relative_to(PACK).as_posix(),'contact_sha256':sha(cp),'index_sha256':sha(OUT/'set-index.json'),'cells':rows};pf=CDIR/'tree-bottom-base-occlusion-v3-proof.json';pf.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'manifest':manifest['candidate_path'],'candidate_sha256':manifest['candidate_sha256'],'contact':proof['contact_path'],'contact_sha256':proof['contact_sha256'],'base_scale':scale},indent=2))
