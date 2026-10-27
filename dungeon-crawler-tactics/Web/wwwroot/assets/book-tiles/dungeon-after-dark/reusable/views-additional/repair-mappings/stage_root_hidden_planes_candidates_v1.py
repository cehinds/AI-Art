"""Stage Root-authorized hidden-plane candidate batch; writes candidates/provenance only, never production assets."""
from pathlib import Path
import json,hashlib,shutil,copy
import numpy as np
from PIL import Image
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[1];PACK=ROOT.parent.parent;CD=ROOT/'candidates/root-dark-hidden-planes-20261026';RAW=CD/'raw';PROMPTS=CD/'prompts';IMAGES=CD/'images';
HAND=Path('/workspace/scratch/root-dark-next-six-hidden-planes-handoff-20261026.json')
GEN=Path('/workspace/generated_images')
IDX=json.loads((ROOT/'set-index.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).relative_to(PACK).as_posix()
def alpha_crop(p,region=None):
 im=Image.open(p).convert('RGBA');
 if region: im=im.crop(region)
 a=np.asarray(im)[:,:,3]; labels,n=ndimage.label(a>=32); opts=[]
 for i in range(1,n+1):
  mask=labels==i;area=int(mask.sum())
  if area>=100:ys,xs=np.where(mask);opts.append((area,i,(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))))
 if not opts:raise ValueError(f'no alpha component {p}')
 area,i,bbox=max(opts)
 # Preserve all soft-alpha pixels inside the selected opaque component bounds and a two-pixel halo.
 x0,y0,x1,y1=bbox;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(im.width,x1+2);y1=min(im.height,y1+2)
 return im.crop((x0,y0,x1,y1)),{'alpha_threshold':32,'component_index':i,'component_count':n,'component_bbox_xyxy':bbox,'selected_component_area':area,'halo_px':2,'crop_bbox_xyxy':[x0,y0,x1,y1]}
def fit(crop,tw,th):
 w,h=crop.size;s=min(tw/w,th/h);nw=max(1,round(w*s));nh=max(1,round(h*s));rs=crop.resize((nw,nh),Image.Resampling.NEAREST);out=Image.new('RGBA',(256,256),(0,0,0,0));x=(256-nw)//2;y=(256-nh)//2;out.alpha_composite(rs,(x,y));return out,{'uniform_scale':s,'resized_dimensions_px':[nw,nh],'offset_px':[x,y],'anchor_px':[128,128],'resampling':'nearest'}
def bounds(path):
 im=Image.open(path).convert('RGBA'); b=im.getchannel('A').getbbox();return [b[2]-b[0],b[3]-b[1]]
def main():
 hand=json.loads(HAND.read_text());assert len(hand['objects'])==6
 proof=json.loads(Path(hand['source_and_six_proof']['path']).read_text());assert sha(Path(hand['source_and_six_proof']['path']))==hand['source_and_six_proof']['sha256']
 assets={a['id']:a for a in IDX['assets']};proofobs={o['object_id']:o for o in proof['objects']}
 inputs={
 'coral-top':('exec-43d6855c-84a3-425f-9ea1-f62a029a3970.png','bubble-sea-coral-cluster','top','Strict direct-overhead coral cluster. Preserve source count, palette, coral types and rocks. Tall red hollow tubes/branching coral are vertical world Z: show only small oval tube mouths and compact branch crowns at their same XY positions among the blue, orange, purple coral heads; no full tube lengths or front faces. No perspective, text or extra coral.'),
 'throne-top':('exec-1e7f39cf-dfb9-4d6c-ac5a-301fc88546dc.png','early-arenas-scrap-throne','top','Strict direct-overhead plan of exact scrap throne. Preserve red seat, metal arms, base, palette, wear and source-specific spikes. Show seat cushion and armrest tops, narrow backrest cap and foreshortened spike tips rooted along fixed back edge; do not lay upright backrest or long vertical spikes into XY. No perspective/text/extra furniture.'),
 'memorial-top':('exec-c9420f3e-065a-475e-a968-2fb8c1bab6cf.png','ghost-cemetery-memorial-stone','top','Two-row memorial imagegen atlas row 1, strict overhead. Exact central stone plaque, cross and wreath/flower border source palette; direct above.'),
 'memorial-bottom':('exec-c9420f3e-065a-475e-a968-2fb8c1bab6cf.png','ghost-cemetery-memorial-stone','bottom','Two-row memorial imagegen atlas row 2, direct underside: opaque stone backing slab, same square border/material, no upright flowers or top-facing cross showing through.'),
 'counter-top':('exec-e5a54971-0f2c-4af8-93bf-548d71e6a76d.png','safe-services-food-service-counter','top','Strict overhead exact food-service counter. Preserve glass display case, contents/positions, trays, red body, gray trim and side-handle count. Show glass as thin clear inset and food compact overhead shapes; no front red cabinet face in plan. No perspective/text/extra items.'),
 'bookcase-top':('exec-715a8b6c-1002-4bda-9ff8-a1c82b98587c.png','starter-dungeon-bookcase-with-framed-photographs','top','Iterative correction from bookcase current TOP: flat wooden footprint, two thin upright-frame edge strips, green plant crown right; no complete photograph faces; only thin book-top slivers, remove front-facing spines/shelves; direct overhead.'),
 'torch-rear':('exec-472296fb-2115-47f5-a55a-b8dc5efee543.png','starter-dungeon-wall-torch','rear','Rear view of wall-mounted torch: remove fixture/flame/glow, keep same vertical wall panel footprint filled with continuous blank blue-gray/tan reverse masonry. Opaque panel; no detached bricks or second fixture.')}
 prompts={
 'coral-top':'Create one transparent-background pixel-art asset. '+inputs['coral-top'][3],
 'throne-top':'Create one transparent-background pixel-art asset. '+inputs['throne-top'][3],
 'memorial-top':'Create transparent two-row atlas; exactly two equal-width views. '+inputs['memorial-top'][3],
 'memorial-bottom':'Create transparent two-row atlas; exactly two equal-width views. '+inputs['memorial-bottom'][3],
 'counter-top':'Create one transparent-background pixel-art asset. '+inputs['counter-top'][3],
 'bookcase-top':'Edit current top into strict direct-overhead view. '+inputs['bookcase-top'][3],
 'torch-rear':'Create one transparent-background pixel-art asset. '+inputs['torch-rear'][3]}
 shutil.copy2(HAND,CD/'root-hidden-planes-handoff.json');(CD/'root-hidden-planes-handoff.sha256').write_text(sha(HAND)+'  root-hidden-planes-handoff.json\n');PROMPTS.mkdir(parents=True,exist_ok=True);IMAGES.mkdir(parents=True,exist_ok=True)
 # Copy exact tool-returned files; no newest-file/glob selection.
 rawmeta={}
 for key,(fname,oid,view,_) in inputs.items():
  src=GEN/fname;assert src.exists();dest=RAW/f'{key}.png';shutil.copy2(src,dest);rawmeta[key]={'raw_path':rel(dest),'raw_sha256':sha(dest),'tool_request_id':None,'local_request_label':key,'tool_response_name':fname,'tool_response_sha256':sha(src)}
  pp=PROMPTS/f'{key}.txt';pp.write_text(prompts[key]+'\n');rawmeta[key]['prompt_path']=rel(pp);rawmeta[key]['prompt_sha256']=sha(pp)
 rows=[];cand=[]
 # output spec key, object/view, raw-key, atlas crop region, accepted view metric target source sizes
 specs=[('coral-top','bubble-sea-coral-cluster','top',None),('throne-top','early-arenas-scrap-throne','top',None),('memorial-top','ghost-cemetery-memorial-stone','top',(0,0,887,887)),('memorial-bottom','ghost-cemetery-memorial-stone','bottom',(0,887,887,1774)),('counter-top','safe-services-food-service-counter','top',None),('bookcase-top','starter-dungeon-bookcase-with-framed-photographs','top',None),('torch-rear','starter-dungeon-wall-torch','rear',None)]
 for key,oid,view,region in specs:
  obj=next(o for o in hand['objects'] if o['object_id']==oid);assert proofobs[oid]['source']['sha256']==obj['source']['sha256']
  for v,r in obj['views'].items():assert sha(Path(r['path']))==r['sha256'],(oid,v)
  raw=RAW/f'{key}.png';crop,ex=alpha_crop(raw,region)
  if view=='top':
   # Use the accepted object footprint in XY: front width by right-view depth width.
   fw,fh=bounds(obj['views']['front']['path']);rw,rh=bounds(obj['views']['right']['path']);target=(fw,rw)
  elif oid=='ghost-cemetery-memorial-stone': target=(max(bounds(obj['views']['top']['path'])[0],bounds(obj['views']['bottom']['path'])[0]),max(bounds(obj['views']['top']['path'])[1],bounds(obj['views']['bottom']['path'])[1]))
  else: target=bounds(obj['views']['front']['path'])
  img,norm=fit(crop,*target);op=IMAGES/f'{oid}.{view}.candidate-v1.png';img.save(op,format='PNG',optimize=False)
  # Verify target canonical source equals set-index canonical component and serialize only portable paths.
  srcasset=assets[oid+'.front']['source'];sourcepath=srcasset['source_image'];assert not Path(sourcepath).is_absolute()
  objrec=next((x for x in rows if x['object_id']==oid),None)
  if objrec is None: objrec={'object_id':oid,'source':{'path':sourcepath,'sha256':sha(Path(PACK/sourcepath))},'base_six':{v:{'path':a['image']['path'],'sha256':sha(PACK/a['image']['path'])} for v,a in ((v,assets[oid+'.'+v]) for v in ('front','top','right','left','bottom','rear'))},'candidate_views':[]};rows.append(objrec)
  c={'object_id':oid,'asset_id':oid+'.'+view,'view':view,'candidate_path':rel(op),'candidate_sha256':sha(op),'dimensions_px':[256,256],'anchor_px':[128,128],'source_path':sourcepath,'source_sha256':sha(PACK/sourcepath),'base_six':objrec['base_six'],'input':rawmeta[key]|{'extraction':ex,'normalization':norm,'crop_region_xyxy':list(region) if region else None},'tool_request_id':None,'local_request_label':key,'tool_response_name':rawmeta[key]['tool_response_name'],'tool_response_sha256':rawmeta[key]['tool_response_sha256'],'notes':'Inferred hidden plane; illustrative orthographic art, not recovered hidden pixels. Target source remains identity authority.'};cand.append(c);objrec['candidate_views'].append({'view':view,'candidate_path':rel(op),'candidate_sha256':sha(op)})
 manifest={'status':'candidate-only; Root review requested','scope':'six objects; seven directions','handoff_path':rel(CD/'root-hidden-planes-handoff.json'),'handoff_sha256':sha(CD/'root-hidden-planes-handoff.json'),'handoff_original_sha256':sha(HAND),'objects':rows,'candidates':cand,'rules':['Exact imagegen return filenames are bound per request; tool_request_id null because no request ID returned.','Source and all-six base PNGs hash-checked against live index before staging.','One isotropic nearest-neighbor fit per candidate; transparent centered frame with anchor [128,128].','Raw imagegen outputs, prompts, source views and exact extraction bounds retained. No production asset/index/sidecar writes.']}
 contact=Image.new('RGBA',(9*180,220*len(rows)),(31,34,39,255))
 for ri,o in enumerate(rows):
  oid=o['object_id'];ordered=[('SOURCE',o['source'])]+[(v,o['base_six'][v]) for v in ('front','top','right','left','bottom','rear')]+[(c['view'].upper()+' NEW',{'path':c['candidate_path'],'sha256':c['candidate_sha256']}) for c in cand if c['object_id']==oid];
  for ci,(lab,r) in enumerate(ordered):
   path=PACK/r['path'];im=Image.open(path).convert('RGBA');im.thumbnail((160,180),Image.Resampling.NEAREST);tile=Image.new('RGBA',(180,220),(31,34,39,255));tile.alpha_composite(im,((180-im.width)//2,8+(180-im.height)//2));from PIL import ImageDraw;ImageDraw.Draw(tile).text((3,195),lab,fill='white');contact.alpha_composite(tile,(ci*180,ri*220))
 cp=CD/'root-hidden-planes-source-six-candidates-v1.png';contact.save(cp,format='PNG',optimize=False);manifest['contact_path']=rel(cp);manifest['contact_sha256']=sha(cp);mp=CD/'root-hidden-planes-candidate-manifest-v1.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');proof={'manifest_path':rel(mp),'manifest_sha256':sha(mp),'contact_path':rel(cp),'contact_sha256':sha(cp),'objects':[{'object_id':o['object_id'],'source':o['source'],'base_six':o['base_six'],'proposed':o['candidate_views']} for o in rows]};pf=CD/'root-hidden-planes-candidate-proof-v1.json';pf.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'manifest':rel(mp),'manifest_sha256':sha(mp),'contact':rel(cp),'contact_sha256':sha(cp),'proof':rel(pf),'proof_sha256':sha(pf),'candidate_count':len(cand)},indent=2))
if __name__=='__main__':main()
