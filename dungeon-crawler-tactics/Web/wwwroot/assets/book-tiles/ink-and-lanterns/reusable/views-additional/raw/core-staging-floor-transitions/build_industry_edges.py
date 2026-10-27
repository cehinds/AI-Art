from pathlib import Path
from PIL import Image,ImageDraw
from scipy import ndimage
import numpy as np, json, hashlib
D=Path(__file__).resolve().parent; PACK=D.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
V=('front','top','right','left','bottom','rear')
H=json.loads((D/'current-floor-transition-handoff.json').read_text())
records={x['object_id']:x for x in H['objects']}
ids=['industry-menagerie-industrial-brick-corner-transition','industry-menagerie-industrial-brick-edge-transition']
layout={
 ids[0]:{'atlas':'industry-corner-edges-v2-atlas.png','raw_hash':'2b27f1aa1ba27a988fd76ccddfeff4eba2b7cbbf13ae1934227115baca258240','request':'industry-corner-edges-v2.request.json','request_id':'exec-eafd3348-f0ff-4c44-9f9a-83496774611e','cell_map':{'front':2,'right':1,'left':2,'rear':3},'target_width':230},
 ids[1]:{'atlas':'industry-edge-edges-v2-atlas.png','raw_hash':'078bbfad2931e5ecd5d8795350ffdf492626fabae9d67a18ec12debbd8741284','request':'industry-edge-edges-v2.request.json','request_id':'exec-14bb196a-e32d-4dc7-8b43-4fd707a201a3','cell_map':{'front':0,'right':1,'left':2,'rear':3},'target_width':230}
}
for oid,L in layout.items():
 reqp=D/L['request']; req=json.loads(reqp.read_text()); req['request_id']=L['request_id']; reqp.write_text(json.dumps(req,indent=2)+'\n')
 atlas=D/L['atlas'];assert sha(atlas)==L['raw_hash'],(oid,'atlas hash');raw=Image.open(atlas).convert('RGBA');a=np.array(raw)[:,:,3];labels,n=ndimage.label(a>=16); objs=[]
 for lab in range(1,n+1):
  ys,xs=np.where(labels==lab)
  if len(xs)>=4000:objs.append((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1),int(xs.sum()/len(xs)),int(ys.sum()/len(ys)),lab,len(xs)))
 objs.sort(key=lambda q:q[4]);assert len(objs)==4,(oid,len(objs),objs)
 source=records[oid]['source'];src=PACK/source['path'];assert sha(src)==source['sha256']
 current=records[oid]['live_views'];curdata={}
 for v,ref in current.items():
  p=PACK/ref['path'];assert sha(p)==ref['sha256'],(oid,v,'current mismatch')
  with Image.open(p) as im:curdata[v]={**ref,'size_wh':list(im.size),'alpha_bbox_xyxy':list(im.convert('RGBA').getchannel('A').getbbox() or (0,0,0,0))}
 outdir=D/'candidates'/'industry-v2';outdir.mkdir(parents=True,exist_ok=True);candidates={}
 for view,cell_i in L['cell_map'].items():
  # The entire global connected component is assigned by its center/centroid to the correct atlas cell.
  x0,y0,x1,y1,cx,cy,lab,area=objs[cell_i]
  crop=raw.crop((x0,y0,x1,y1));cw,ch=crop.size;scale=L['target_width']/cw;w=round(cw*scale);h=round(ch*scale)
  resized=crop.resize((w,h),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));offset=((256-w)//2,(256-h)//2);canvas.alpha_composite(resized,offset)
  out=outdir/f'{oid}.{view}.candidate.png';canvas.save(out,optimize=False);bbox=list(canvas.getchannel('A').getbbox());assert 0<bbox[0]<bbox[2]<256 and 0<bbox[1]<bbox[3]<256
  candidates[view]={'candidate_path':str(out.relative_to(D)),'candidate_sha256':sha(out),'size_wh':[256,256],'alpha_bbox_xyxy':bbox,'derivation':{'method':'imagegen-orthographic-atlas-component-uniform-normalization','raw_atlas_path':L['atlas'],'raw_atlas_sha256':sha(atlas),'request_id':L['request_id'],'request_file':L['request'],'request_sha256':sha(reqp),'source_path':source['path'],'source_sha256':source['sha256'],'atlas_component_bbox_xyxy':[x0,y0,x1,y1],'atlas_component_centroid_xy':[cx,cy],'atlas_component_area_alpha_ge16':area,'alpha_threshold':16,'cell_index':cell_i,'normalization':'complete global alpha component assigned by centroid; exact alpha bounds cropped; NEAREST isotropic scale to 230px common horizontal edge span; centered on 256 canvas','uniform_scale':scale,'resized_wh':[w,h],'canvas_offset_xy':list(offset),'anchor_px':[128,128],'note':'Inferred orthographic edge projection; hidden faces are generated illustrations, not recovered pixels.'}}
 # Corner front and left both have plain orange straight edges, same square-arm length and no curb; a byte-identical profile is defensible.
 if oid==ids[0]:
  v='front'; original=candidates[v]; alias_src=outdir/f'{oid}.left.candidate.png'; alias=outdir/f'{oid}.front.candidate.png'; alias.write_bytes(alias_src.read_bytes());original['candidate_path']=str(alias.relative_to(D));original['candidate_sha256']=sha(alias);original['alpha_bbox_xyxy']=list(Image.open(alias).getchannel('A').getbbox());original['derivation']={'method':'symmetric-unmarked-edge-alias','source_path':source['path'],'source_sha256':source['sha256'],'reference_candidate_path':candidates['left']['candidate_path'],'reference_candidate_sha256':candidates['left']['candidate_sha256'],'transform':'exact pixel alias; no rotation or scaling','justification':'The native square corner tile has matching plain-orange front and left straight edges; both are uncurbed and same length/material. The missing L quadrant affects the TOP/BOTTOM plan only.'}
 # make versioned source + old six + candidate six contact, candidate only for modified views
 cp=D/f'{oid}.candidate-source-current-six-v2.png';contact=Image.new('RGBA',(13*164,350),(42,42,46,255));dr=ImageDraw.Draw(contact)
 panels=[('SOURCE',src)]+[(f'CURRENT-{v.upper()}',PACK/current[v]['path']) for v in V]
 for v in V: panels.append((f'CAND-{v.upper()}',D/candidates[v]['candidate_path'] if v in candidates else PACK/current[v]['path']))
 for j,(label,p) in enumerate(panels):
  q=Image.open(p).convert('RGBA');q.thumbnail((128,280),Image.Resampling.NEAREST);contact.alpha_composite(q,(j*164+18+(128-q.width)//2,42+(280-q.height)//2));dr.text((j*164+2,20),label,fill='white')
 contact.save(cp,optimize=False)
 report={'schema_version':1,'batch':'floor-transitions-industry-v2','role':'candidate-only','write_scope':'book-tiles/ink-and-lanterns/reusable/views-additional/raw/core-staging-floor-transitions','no_live_writes':True,'object_id':oid,'source':source,'source_actual_sha256':sha(src),'current_views':curdata,'preserved_views':{v:curdata[v] for v in V if v not in candidates},'candidate_views':candidates,'raw_atlas_path':L['atlas'],'raw_atlas_sha256':sha(atlas),'request_file':L['request'],'request_sha256':sha(reqp),'request_id':L['request_id'],'contact_path':cp.name,'contact_sha256':sha(cp),'root_review':{'status':'awaiting-root-review','reviewed_contact_sha256':None}}
 (D/f'staged-{oid}-v2.json').write_text(json.dumps(report,indent=2)+'\n')
 print(oid, 'contact',cp.name,sha(cp),'views',[(v,c['alpha_bbox_xyxy'],c['candidate_sha256']) for v,c in candidates.items()])
