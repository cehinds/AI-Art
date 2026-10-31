from pathlib import Path
import json,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;PACK=D.parents[3];sha=lambda p:hashlib.sha256(p if isinstance(p,bytes) else p.read_bytes()).hexdigest()
r=json.loads((D/'staged-floor-transitions-batch-02-zockau-v2.json').read_text());s=r['sets'][0];oid=s['object_id']
source=PACK/s['source']['path'];assert sha(source)==s['source']['sha256']
current={}
for v,ref in s['current_views'].items():
 p=PACK/ref['path'];assert sha(p)==ref['sha256'],(v,'current')
 with Image.open(p) as im:current[v]={**ref,'size_wh':list(im.size),'alpha_bbox_xyxy':list(im.convert('RGBA').getchannel('A').getbbox() or (0,0,0,0))}
candidates={}
for v,ref in s['candidate_views'].items():
 p=D/ref['candidate_path'];assert sha(p)==ref['candidate_sha256'],(v,'candidate')
 with Image.open(p) as im:assert im.size==(256,256);bbox=list(im.convert('RGBA').getchannel('A').getbbox() or (0,0,0,0))
 assert bbox==ref['alpha_bbox_xyxy']
 candidates[v]=ref
cp=D/s['contact_path'];assert sha(cp)==s['contact_sha256']
out=D/f'installer-handoff--{oid}.json'
h={'schema_version':1,'object_id':oid,'role':'staging-only-installer-handoff','status':'root-approved-candidate-directions-pending-live-install','write_scope':'book-tiles/ink-and-lanterns/reusable/views-additional/raw/core-staging-floor-transitions','installer':'views_ink_books','reviewer':'root','source':{**s['source'],'rgba_sha256':None},'source_actual_sha256':sha(source),'current_views':current,'candidate_views':candidates,'contact_path':s['contact_path'],'contact_sha256':sha(cp),'approval':'Root scoped-approved all five requested candidates from this exact source/current/candidate contact. Preserve current BOTTOM unchanged. Candidate TOP is the canonical source crop uniformly enlarged and centered to match the edge XY footprint; generated lateral profiles retain the source left-only curb relation. Recheck canonical source, all six current view hashes, each candidate hash and this contact before install.','canvas_contract':{'size_wh':[256,256],'anchor_px':[128,128]}}
out.write_text(json.dumps(h,indent=2)+'\n');print(out,sha(out.read_bytes()),'candidates',list(candidates))
