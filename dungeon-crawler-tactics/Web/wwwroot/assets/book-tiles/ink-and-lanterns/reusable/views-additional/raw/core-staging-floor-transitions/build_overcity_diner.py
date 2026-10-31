from pathlib import Path
from PIL import Image,ImageDraw
from scipy import ndimage
import numpy as np,json,hashlib
D=Path(__file__).resolve().parent;PACK=D.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();V=('front','top','right','left','bottom','rear')
H=json.loads((D/'current-floor-transition-handoff.json').read_text());rows={x['object_id']:x for x in H['objects']}
configs={
 'over-city-venues-civic-stone-tile-corner-transition':{'atlas':'overcity-civic-corner-edges-atlas.png','hash':'d5b2dfa05acaf7d076867ee6a09fc0e03b672a2e2ab11f84f222a11bcafd89d1','request':'overcity-civic-corner-edges.request.json','request_id':'exec-98fbabbd-577b-427f-8ed0-c498f554c7a1','target':{'front':222,'right':214,'left':214,'rear':222}},
 'safe-services-diner-checker-tile-edge-transition':{'atlas':'safe-diner-checker-edges-atlas.png','hash':'645a68aaca57941cf440bdc14a2d18e52e64ffd19e88fb3ca5746ce84efa4cc4','request':'safe-diner-checker-edges-v2.request.json','request_id':'exec-cc136f4a-3eaf-44c0-b50d-22f53f34002d','target':{'front':208,'right':208,'left':208,'rear':208}}
}
for oid,C in configs.items():
 row=rows[oid]; src=PACK/row['source']['path']; assert sha(src)==row['source']['sha256'];atlas=D/C['atlas']; assert sha(atlas)==C['hash']; reqp=D/C['request'];req=json.loads(reqp.read_text());req['request_id']=C['request_id'];reqp.write_text(json.dumps(req,indent=2)+'\n')
 raw=Image.open(atlas).convert('RGBA'); a=np.array(raw)[:,:,3]; labs,n=ndimage.label(a>=16); components=[]
 for lab in range(1,n+1):
  ys,xs=np.where(labs==lab)
  if len(xs)>1000: components.append((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1),int(xs.mean()),int(ys.mean()),len(xs),lab))
 components.sort(key=lambda x:x[4]); assert len(components)==4,(oid,components)
 current=row['live_views'];cur={}
 for v,ref in current.items():
  p=PACK/ref['path'];assert sha(p)==ref['sha256'],(oid,v,'current drift')
  with Image.open(p) as im:cur[v]={**ref,'size_wh':list(im.size),'alpha_bbox_xyxy':list(im.convert('RGBA').getchannel('A').getbbox() or (0,0,0,0))}
 outdir=D/'candidates'/'overcity-diner-v2';outdir.mkdir(parents=True,exist_ok=True);candidates={}
 for view,i in zip(('front','right','left','rear'),range(4)):
  x0,y0,x1,y1,cx,cy,area,lab=components[i];crop=raw.crop((x0,y0,x1,y1));scale=C['target'][view]/crop.width;w=round(crop.width*scale);h=round(crop.height*scale);offset=((256-w)//2,(256-h)//2);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(crop.resize((w,h),Image.Resampling.NEAREST),offset);out=outdir/f'{oid}.{view}.candidate.png';canvas.save(out,optimize=False);bbox=list(canvas.getchannel('A').getbbox());assert bbox[0]>0 and bbox[1]>0 and bbox[2]<256 and bbox[3]<256
  candidates[view]={'candidate_path':str(out.relative_to(D)),'candidate_sha256':sha(out),'size_wh':[256,256],'alpha_bbox_xyxy':bbox,'derivation':{'method':'imagegen-orthographic-atlas-component-uniform-normalization','raw_atlas_path':C['atlas'],'raw_atlas_sha256':sha(atlas),'request_id':C['request_id'],'request_file':C['request'],'request_sha256':sha(reqp),'source_path':row['source']['path'],'source_sha256':row['source']['sha256'],'atlas_component_bbox_xyxy':[x0,y0,x1,y1],'atlas_component_centroid_xy':[cx,cy],'atlas_component_area_alpha_ge16':area,'alpha_threshold':16,'cell_index':i,'normalization':'global alpha connected component assigned by centroid, fullbounds cropped, NEAREST isotropic scale to target top-plan edge span; centered on 256 canvas','uniform_scale':scale,'resized_wh':[w,h],'canvas_offset_xy':list(offset),'anchor_px':[128,128],'note':'Illustrated inferred principal edge profile; hidden details are not recovered source pixels.'}}
 cp=D/f'{oid}.candidate-source-current-six-v2.png';contact=Image.new('RGBA',(13*164,350),(42,42,46,255));draw=ImageDraw.Draw(contact);panels=[('SOURCE',src)]+[(f'CURRENT-{v.upper()}',PACK/current[v]['path']) for v in V]
 for v in V:panels.append((f'CAND-{v.upper()}',D/candidates[v]['candidate_path'] if v in candidates else PACK/current[v]['path']))
 for j,(label,p) in enumerate(panels):
  q=Image.open(p).convert('RGBA');q.thumbnail((128,280),Image.Resampling.NEAREST);contact.alpha_composite(q,(j*164+18+(128-q.width)//2,42+(280-q.height)//2));draw.text((j*164+2,20),label,fill='white')
 contact.save(cp,optimize=False)
 rpt={'schema_version':1,'batch':'floor-transitions-overcity-diner-v2','role':'candidate-only','write_scope':'book-tiles/ink-and-lanterns/reusable/views-additional/raw/core-staging-floor-transitions','no_live_writes':True,'object_id':oid,'source':row['source'],'source_actual_sha256':sha(src),'current_views':cur,'preserved_views':{v:cur[v] for v in V if v not in candidates},'candidate_views':candidates,'raw_atlas_path':C['atlas'],'raw_atlas_sha256':sha(atlas),'request_file':C['request'],'request_sha256':sha(reqp),'request_id':C['request_id'],'contact_path':cp.name,'contact_sha256':sha(cp),'root_review':{'status':'awaiting-root-review','reviewed_contact_sha256':None}}
 (D/f'staged-{oid}-v2.json').write_text(json.dumps(rpt,indent=2)+'\n');print(oid,cp.name,sha(cp),[(v,c['alpha_bbox_xyxy'],c['candidate_sha256']) for v,c in candidates.items()])
