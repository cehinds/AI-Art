"""Uniformly recalibrate 12 already-approved plan projections to their preserved side spans."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;PACK=OUT.parent.parent;LEDGER=Path('/workspace/scratch/view-qa-report.json')
IDS=['iron-trains-railcar-metal-floor','iron-trains-worn-railcar-metal-floor','iron-trains-cracked-railcar-metal-floor','iron-trains-wet-railcar-metal-floor','iron-trains-railcar-metal-edge-transition','iron-trains-railcar-metal-corner-transition','over-city-city-cobblestone-floor','over-city-worn-city-cobblestone-floor','over-city-cracked-city-cobblestone-floor','over-city-wet-city-cobblestone-floor','race-circuits-race-asphalt-floor','race-circuits-garage-concrete-floor']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def largest(im):
 lab,n=ndimage.label(np.asarray(im.getchannel('A'))>=32);cs=[]
 for i,s in enumerate(ndimage.find_objects(lab),1):
  if s is None:continue
  y,x=s;area=int(np.count_nonzero(lab[s]==i));
  if area>50:cs.append((area,(x.start,y.start,x.stop,y.stop)))
 cs.sort(reverse=True);assert cs and cs[0][0]>5000,(len(cs),cs[:5]);assert len([c for c in cs if c[0]>5000])==1,(cs[:5]);return cs[0],cs[1:]
def main():
 idx=json.loads((OUT/'set-index.json').read_text());assets={a['id']:a for a in idx['assets']};ledger=json.loads(LEDGER.read_text())['reviewed'];sets=[];audit=[]
 for oid in IDS:
  rec=ledger.get('book-tiles/dungeon-after-dark::'+oid);assert rec and rec['status']=='needs-review',(oid,rec and rec['status']);viewbases={};lateral=[]
  for v in ('front','right','left','rear'):
   a=assets[f'{oid}.{v}'];p=PACK/a['image']['path'];h=sha(p);assert h==rec['image_hashes'][v],(oid,v,'stale');im=Image.open(p).convert('RGBA');box=im.getchannel('A').getbbox();lateral.append(box[2]-box[0]);viewbases[v]=h
  target=round(sum(lateral)/len(lateral));assert target>0
  plans=[]
  for v in ('top','bottom'):
   a=assets[f'{oid}.{v}'];live=PACK/a['image']['path'];snapshot=OUT/'prebuilt/retained-plan-scale-inputs-v1'/f'{oid}.{v}.png';p=snapshot if snapshot.exists() else live;base=sha(p);expected=rec['image_hashes'][v];assert base==expected,(oid,v,'retained input mismatch');im=Image.open(p).convert('RGBA');(area,b),others=largest(im);x0,y0,x1,y1=b;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(im.width,x1+3);y1=min(im.height,y1+3);crop=im.crop((x0,y0,x1,y1));scale=target/max(crop.width,crop.height);nw=round(crop.width*scale);nh=round(crop.height*scale);r=crop.resize((nw,nh),Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(r,((256-nw)//2,(256-nh)//2));dst=OUT/'candidates/retained-plan-scale-v1'/f'{oid}.{v}.png';dst.parent.mkdir(parents=True,exist_ok=True);can.save(dst);plans.append({'view':v,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'base_sha256':expected,'input_view_asset_id':f'{oid}.{v}','retained_input_path':'reusable/views-additional/prebuilt/retained-plan-scale-inputs-v1/'+snapshot.name,'input_raster_sha256':base,'largest_component_bbox_threshold32':list(b),'largest_component_area_threshold32':area,'other_components_area_gt50':[{'area':q[0],'bbox':list(q[1])} for q in others[:10]],'crop_rect_with_padding':[x0,y0,x1,y1],'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128],'target_span_px':target})
  sets.append({'object_id':oid,'lateral_view_widths_px':lateral,'target_span_px':target,'views':plans});audit.append({'object_id':oid,'lateral_view_widths_px':lateral,'plan_changes':[{k:e[k] for k in ('view','base_sha256','largest_component_bbox_threshold32','largest_component_area_threshold32','crop_rect_with_padding','uniform_scale','normalized_size','target_span_px')} for e in plans]})
 spec={'candidate_id':'retained-plan-scale-12-v1','sets':sets,'method':'lossless-raster-content retained and nearest-neighbor resized with one isotropic scale per view; no redraw, color change, or axis-specific calibration. Target span is the average alpha-bounds width of four already-reviewed lateral views.'};p=OUT/'candidates/retained-plan-scale-12-v1.json';p.write_text(json.dumps(spec,indent=2)+'\n');(OUT/'repair-mappings/retained-plan-scale-12-v1-audit.json').write_text(json.dumps({'source_ledger':str(LEDGER),'sets':audit},indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
