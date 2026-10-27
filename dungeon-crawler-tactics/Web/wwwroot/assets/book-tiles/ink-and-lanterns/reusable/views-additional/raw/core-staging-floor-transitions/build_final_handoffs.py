from pathlib import Path
from PIL import Image
import json,hashlib
D=Path(__file__).resolve().parent;PACK=D.parents[3];sha=lambda p:hashlib.sha256(p if isinstance(p,bytes) else p.read_bytes()).hexdigest()
items=[('over-city-venues-civic-stone-tile-corner-transition','v3','Root scoped-accepted the four broad low civic-stone lateral profiles. Preserve TOP and BOTTOM.'),('safe-services-diner-checker-tile-edge-transition','v3','Root scoped-accepted the four shallow orthographic diner-tile edge profiles. Preserve TOP and BOTTOM.'),('safe-services-cream-service-tile-endcap-northeast','v2','Root scoped-accepted RIGHT and LEFT after uniform scale brought side Z height to FRONT/REAR. Preserve FRONT, TOP, BOTTOM and REAR.')]
for oid,ver,approval in items:
 r=json.loads((D/f'staged-{oid}-{ver}.json').read_text());src=PACK/r['source']['path'];assert sha(src)==r['source_actual_sha256'],(oid,'source')
 current={}
 for v,ref in r['current_views'].items():
  p=PACK/ref['path'];assert sha(p)==ref['sha256'],(oid,v,'current')
  with Image.open(p) as im:current[v]={**ref,'size_wh':list(im.size),'alpha_bbox_xyxy':list(im.convert('RGBA').getchannel('A').getbbox() or (0,0,0,0))}
 cand={}
 for v,ref in r['candidate_views'].items():
  p=D/ref['candidate_path'];assert sha(p)==ref['candidate_sha256'],(oid,v,'candidate')
  with Image.open(p) as im:assert im.size==(256,256) and list(im.getchannel('A').getbbox())==ref['alpha_bbox_xyxy']
  cand[v]=ref
 cp=D/r['contact_path'];assert sha(cp)==r['contact_sha256']
 h={'schema_version':1,'object_id':oid,'role':'staging-only-installer-handoff','status':'root-approved-candidate-directions-pending-live-install','write_scope':'book-tiles/ink-and-lanterns/reusable/views-additional/raw/core-staging-floor-transitions','installer':'views_ink_books','reviewer':'root','source':{'path':r['source']['path'],'sha256':r['source_actual_sha256'],'rgba_sha256':None},'source_actual_sha256':r['source_actual_sha256'],'current_views':current,'candidate_views':cand,'contact_path':r['contact_path'],'contact_sha256':r['contact_sha256'],'approval':approval+' Directions absent from candidate_views remain unchanged. Recheck canonical source, all six current view hashes, every candidate hash, and this contact before install. Staging worker made no live edits.','canvas_contract':{'size_wh':[256,256],'anchor_px':[128,128]}}
 out=D/f'installer-handoff--{oid}.json';out.write_text(json.dumps(h,indent=2)+'\n');print(out,sha(out.read_bytes()),list(cand))
