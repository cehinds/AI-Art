from pathlib import Path
from PIL import Image,ImageDraw
from scipy import ndimage
import numpy as np,json,hashlib
D=Path(__file__).resolve().parent;PACK=D.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();V=('front','top','right','left','bottom','rear');handoff=json.loads((D/'current-floor-transition-handoff.json').read_text());rows={x['object_id']:x for x in handoff['objects']}
configs={
 'over-city-venues-civic-stone-tile-corner-transition':{'atlas':'overcity-civic-corner-edges-atlas-v3.png','hash':'2722eb30827a8221306ccea1a0e3e652e33920f3fa1f6ce4f4752bd57468d62a','request':'overcity-civic-corner-edges-v3.request.json','request_id':'exec-640afe5c-4176-4d08-a97a-2a93624f7d1b','target_width':218},
 'safe-services-diner-checker-tile-edge-transition':{'atlas':'safe-diner-checker-edges-atlas.png','hash':'645a68aaca57941cf440bdc14a2d18e52e64ffd19e88fb3ca5746ce84efa4cc4','request':'safe-diner-checker-edges-v2.request.json','request_id':'exec-cc136f4a-3eaf-44c0-b50d-22f53f34002d','target_width':208}}
for oid,C in configs.items():
 row=rows[oid];src=PACK/row['source']['path'];assert sha(src)==row['source']['sha256'];atlas=D/C['atlas'];assert sha(atlas)==C['hash'];reqp=D/C['request'];req=json.loads(reqp.read_text());req['request_id']=C['request_id'];reqp.write_text(json.dumps(req,indent=2)+'\n');raw=Image.open(atlas).convert('RGBA');a=np.array(raw)[:,:,3];labs,n=ndimage.label(a>=16);comps=[]
 for i in range(1,n+1):
  ys,xs=np.where(labs==i)
  if len(xs)>1000:comps.append((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1),int(xs.mean()),int(ys.mean()),len(xs),i))
 comps.sort(key=lambda x:x[4]);assert len(comps)==4,(oid,comps)
 avgw=sum(x[2]-x[0] for x in comps)/4;scale=C['target_width']/avgw
 current=row['live_views'];cur={}
 for v,ref in current.items():
  p=PACK/ref['path'];assert sha(p)==ref['sha256'],(oid,v,'current drift')
  with Image.open(p) as im:cur[v]={**ref,'size_wh':list(im.size),'alpha_bbox_xyxy':list(im.convert('RGBA').getchannel('A').getbbox() or (0,0,0,0))}
 cand={};outdir=D/'candidates'/'overcity-diner-v3';outdir.mkdir(parents=True,exist_ok=True)
 for view,i in zip(('front','right','left','rear'),range(4)):
  x0,y0,x1,y1,cx,cy,area,lab=comps[i];crop=raw.crop((x0,y0,x1,y1));w=round(crop.width*scale);h=round(crop.height*scale);off=((256-w)//2,(256-h)//2);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(crop.resize((w,h),Image.Resampling.NEAREST),off);out=outdir/f'{oid}.{view}.candidate.png';canvas.save(out,optimize=False);bbox=list(canvas.getchannel('A').getbbox());assert 0<bbox[0]<bbox[2]<256 and 0<bbox[1]<bbox[3]<256
  cand[view]={'candidate_path':str(out.relative_to(D)),'candidate_sha256':sha(out),'size_wh':[256,256],'alpha_bbox_xyxy':bbox,'derivation':{'method':'imagegen-orthographic-atlas-component-common-scale','raw_atlas_path':C['atlas'],'raw_atlas_sha256':sha(atlas),'request_id':C['request_id'],'request_file':C['request'],'request_sha256':sha(reqp),'source_path':row['source']['path'],'source_sha256':row['source']['sha256'],'atlas_component_bbox_xyxy':[x0,y0,x1,y1],'atlas_component_centroid_xy':[cx,cy],'atlas_component_area_alpha_ge16':area,'alpha_threshold':16,'cell_index':i,'normalization':'global alpha connected component assignment by centroid, full bounds cropped; one shared NEAREST isotropic scale for all four views; centered on 256 canvas','uniform_scale':scale,'resized_wh':[w,h],'canvas_offset_xy':list(off),'anchor_px':[128,128],'note':'Orthographic floor-edge illustration; unknown hidden construction inferred from source palette and material, not recovered pixels.'}}
 cp=D/f'{oid}.candidate-source-current-six-v3.png';ct=Image.new('RGBA',(13*164,350),(42,42,46,255));draw=ImageDraw.Draw(ct);panels=[('SOURCE',src)]+[(f'CURRENT-{v.upper()}',PACK/current[v]['path']) for v in V]
 for v in V:panels.append((f'CAND-{v.upper()}',D/cand[v]['candidate_path'] if v in cand else PACK/current[v]['path']))
 for j,(label,p) in enumerate(panels):
  q=Image.open(p).convert('RGBA');q.thumbnail((128,280),Image.Resampling.NEAREST);ct.alpha_composite(q,(j*164+18+(128-q.width)//2,42+(280-q.height)//2));draw.text((j*164+2,20),label,fill='white')
 ct.save(cp,optimize=False);rpt={'schema_version':1,'batch':'floor-transitions-overcity-diner-v3','role':'candidate-only','write_scope':'book-tiles/ink-and-lanterns/reusable/views-additional/raw/core-staging-floor-transitions','no_live_writes':True,'object_id':oid,'source':row['source'],'source_actual_sha256':sha(src),'current_views':cur,'preserved_views':{v:cur[v] for v in V if v not in cand},'candidate_views':cand,'raw_atlas_path':C['atlas'],'raw_atlas_sha256':sha(atlas),'request_file':C['request'],'request_sha256':sha(reqp),'request_id':C['request_id'],'contact_path':cp.name,'contact_sha256':sha(cp),'root_review':{'status':'awaiting-root-review','reviewed_contact_sha256':None}}
 (D/f'staged-{oid}-v3.json').write_text(json.dumps(rpt,indent=2)+'\n');print(oid,'common_scale',scale,'contact',cp.name,sha(cp),'views',[(v,c['alpha_bbox_xyxy'],c['candidate_sha256']) for v,c in cand.items()])
