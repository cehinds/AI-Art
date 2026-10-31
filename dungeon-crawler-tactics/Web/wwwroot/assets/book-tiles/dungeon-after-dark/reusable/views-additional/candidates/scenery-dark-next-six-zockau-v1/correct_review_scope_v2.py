#!/usr/bin/env python3
"""Correct Zockau review/install split from Root's explicit current-scope decisions."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
BASE=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/reusable/views-additional');PACK=BASE.parent.parent;C=BASE/'candidates/scenery-dark-next-six-zockau-v1'
HAND=Path('/workspace/scratch/scenery-dark-next-six-zockau-handoff-20261026.json');PROOF=Path('/tmp/root148-dark-zockau6.png.json');VIEWS=['front','top','right','left','bottom','rear']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
h=json.loads(HAND.read_text());objs={x['object_id']:x for x in h['objects']};old=json.loads((C/'candidate-manifest.json').read_text());oldsets={s['object_id']:s for s in old['sets']}
# Immediately reconfirm source and six canonical leaves against the frozen handoff.
assert sha(HAND)==old['handoff_sha256'];assert sha(PROOF)==h['source_and_six_proof']['sha256']
for o in h['objects']:
 assert sha(o['source']['path'])==o['source']['sha256']
 for v,x in o['views'].items():assert sha(x['path'])==x['sha256'],(o['object_id'],v)
accepted_directions={
 'hunting-jungle-vine-covered-ruin-stone-endcap-northwest':['top','bottom'],
 'hunting-zockau-bear-head-square-statue':['bottom'],
 'hunting-zockau-painted-town-brick-endcap-northeast':VIEWS,
 'hunting-zockau-painted-town-brick-endcap-northwest':['top','right','left','bottom'],
 'hunting-zockau-painted-town-brick-wall-northeast':['front','right','left','rear'],
 'hunting-zockau-painted-town-brick-wall-northwest':['top','bottom'],
}
held_directions={
 'hunting-zockau-painted-town-brick-wall-northeast':['top','bottom'],
 'hunting-zockau-painted-town-brick-wall-northwest':['front','right','left','rear'],
}
# Build approved NE plans from the exact approved v1 atlas-derived plan candidates, not live canonical plans.
ne='hunting-zockau-painted-town-brick-wall-northeast';neobj=objs[ne];neold=oldsets[ne];newrot={}
for v in ('top','bottom'):
 prior=neold['candidates'][v];priorpath=BASE/prior['candidate_path'];assert sha(priorpath)==prior['candidate_sha256']
 im=Image.open(priorpath).convert('RGBA');rot=im.rotate(90,resample=Image.Resampling.NEAREST,expand=True);p=C/'images'/f'{ne}.{v}.candidate-v3.png';rot.save(p,optimize=False)
 recipe={'operation':'rigid-90-degree-rotation-of-approved-v1-plan-candidate','object_id':ne,'view':v,'donor_path':prior['candidate_path'],'donor_sha256':prior['candidate_sha256'],'source_atlas_path':prior['raw_path'],'source_atlas_sha256':prior['raw_sha256'],'prior_request_path':prior['request_path'],'prior_request_sha256':prior['request_sha256'],'rotation_degrees_ccw':90,'filter':'NEAREST','canvas':[256,256],'notes':'The approved v1 plan candidate is long-X. Rotate that accepted candidate by 90 degrees to place its long dimension along this NE wall long-Y. Do not rotate the old canonical PNG.'};rp=C/f'{ne}.{v}.approved-v1-rotated-recipe.json';rp.write_text(json.dumps(recipe,indent=2)+'\n')
 newrot[v]={'candidate_path':str(p.relative_to(BASE)),'candidate_sha256':sha(p),'raw_path':prior['raw_path'],'raw_sha256':prior['raw_sha256'],'request_path':prior['request_path'],'request_sha256':prior['request_sha256'],'base_sha256':neobj['views'][v]['sha256'],'source_path':neobj['source']['path'].replace(str(PACK)+'/',''),'source_sha256':neobj['source']['sha256'],'method':'rigid-90-degree-rotation-of-approved-v1-plan-candidate','derived_from_candidate_path':prior['candidate_path'],'derived_from_candidate_sha256':prior['candidate_sha256'],'recipe_path':str(rp.relative_to(BASE)),'recipe_sha256':sha(rp),'resized_dimensions':[rot.width,rot.height],'filter':'NEAREST'}
# Accepted manifest: 19 actual changed leaves. Existing generated leaves plus NW cap plans from v1.
accepted={'candidate_id':'scenery-dark-zockau-approved-subset-v2','scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_scenery','reviewer':'root','installer':'views_dark_books','candidate_only':True,'handoff_path':str(HAND),'handoff_sha256':sha(HAND),'source_six_proof_path':str(PROOF),'source_six_proof_sha256':sha(PROOF),'sets':[],'held_directions':[f'{oid}.{v}' for oid,vs in held_directions.items() for v in vs]}
for oid,vs in accepted_directions.items():
 o=objs[oid];s=oldsets[oid]
 for v in vs:
  if oid==ne and v in newrot:c=newrot[v].copy()
  else:
   # This includes the two accepted NW wall plan candidates, sourced from v1, not unchanged canonical values.
   c=s['candidates'][v].copy()
  c.update({'object_id':oid,'view':v,'base_path':o['views'][v]['path'].replace(str(PACK)+'/',''),'base_sha256':o['views'][v]['sha256'],'source_path':o['source']['path'].replace(str(PACK)+'/',''),'source_sha256':o['source']['sha256']})
  accepted['sets'].append(c)
ap=C/'accepted-subset-manifest-v2.json';ap.write_text(json.dumps(accepted,indent=2)+'\n')
# Remaining six manifest uses NE rotated v3 and NW source-based four candidates v2 from prior staging.
remaining={'candidate_id':'scenery-dark-zockau-held-six-v2','scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_scenery','reviewer':'root','installer':'views_dark_books','candidate_only':True,'handoff_path':str(HAND),'handoff_sha256':sha(HAND),'source_six_proof_path':str(PROOF),'source_six_proof_sha256':sha(PROOF),'sets':[]}
opsold=json.loads((C/'remaining-six-manifest.json').read_text());nw='hunting-zockau-painted-town-brick-wall-northwest';nwobj=objs[nw]
for v in ('top','bottom'):
 c=newrot[v].copy();c.update({'object_id':ne,'view':v});remaining['sets'].append(c)
for v in ('front','right','left','rear'):
 c=next(x for x in opsold['sets'] if x['object_id']==nw and x['view']==v).copy();
 # NW TOP/BOTTOM are approved v1 changed leaves and must be used in the combined contact.
 c.update({'object_id':nw,'view':v});remaining['sets'].append(c)
rp=C/'remaining-six-manifest-v2.json';rp.write_text(json.dumps(remaining,indent=2)+'\n')
# Both contacts use explicit path selection map, one accepted-only and one accepted+pending.
def compose(path,include_pending):
 accepted_map={(x['object_id'],x['view']):BASE/x['candidate_path'] for x in accepted['sets']}
 pending_map={(x['object_id'],x['view']):BASE/x['candidate_path'] for x in remaining['sets']}
 selections=[];records=[]
 for o in h['objects']:
  ims=[Image.open(o['source']['path']).convert('RGBA')];sels=[]
  for v in VIEWS:
   key=(o['object_id'],v);selected=None;status='canonical-current-retained'
   if key in accepted_map:selected=accepted_map[key];status='root-accepted-candidate'
   elif include_pending and key in pending_map:selected=pending_map[key];status='pending-root-review-candidate'
   else:selected=Path(o['views'][v]['path'])
   im=Image.open(selected).convert('RGBA');ims.append(im);sels.append({'view':v,'status':status,'selected_path':str(selected),'selected_sha256':sha(selected),'canonical_base_path':o['views'][v]['path'],'canonical_base_sha256':o['views'][v]['sha256']})
  records.append((o['object_id'],ims));selections.append({'object_id':o['object_id'],'source_path':o['source']['path'],'source_sha256':o['source']['sha256'],'views':sels})
 W=160;HH=160;lh=24;pad=8;rowh=HH+lh+pad;sheet=Image.new('RGBA',(pad+7*(W+pad),pad+len(records)*rowh),(35,35,40,255));draw=ImageDraw.Draw(sheet)
 for ri,(oid,ims) in enumerate(records):
  y=pad+ri*rowh;draw.text((pad,y),oid,fill='white');y+=lh
  for ci,im in enumerate(ims):
   x=pad+ci*(W+pad);im.thumbnail((W,HH),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+(W-im.width)//2,y+(HH-im.height)//2));draw.text((x,y+HH+2),['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR'][ci],fill='white')
 sheet.save(path,optimize=False);return selections
accepted_contact=C/'accepted-subset-source-plus-six-v2.png';accepted_selection=compose(accepted_contact,False);asha=sha(accepted_contact)
combined=C/'combined-proposed-source-plus-six-v2.png';combined_selection=compose(combined,True);csha=sha(combined)
selection={'schema_version':1,'candidate_id':'scenery-dark-zockau-combined-review-v2','handoff_path':str(HAND),'handoff_sha256':sha(HAND),'accepted_subset_manifest_path':str(ap.relative_to(BASE)),'accepted_subset_manifest_sha256':sha(ap),'remaining_manifest_path':str(rp.relative_to(BASE)),'remaining_manifest_sha256':sha(rp),'accepted_contact_path':str(accepted_contact.relative_to(BASE)),'accepted_contact_sha256':asha,'combined_contact_path':str(combined.relative_to(BASE)),'combined_contact_sha256':csha,'rows':combined_selection,'selection_rule':'Candidate path for each reviewed/held direction; otherwise canonical current path. Every selected path and SHA is explicit.'};sp=C/'combined-contact-selection-v2.json';sp.write_text(json.dumps(selection,indent=2)+'\n')
preflight=[]
for o in h['objects']:preflight.append({'object_id':o['object_id'],'source':{'path':o['source']['path'].replace(str(PACK)+'/',''),'sha256':o['source']['sha256']},'views':{v:{'path':x['path'].replace(str(PACK)+'/',''),'sha256':x['sha256']} for v,x in o['views'].items()}})
packet={'schema_version':1,'packet_id':'scenery-dark-zockau-approved19-install-packet-v2','status':'authorized scoped install of 19 root-accepted candidate leaves; six held candidate directions excluded','installer':'views_dark_books','reviewer':'root','accepted_subset_manifest_path':str(ap.relative_to(BASE)),'accepted_subset_manifest_sha256':sha(ap),'accepted_direction_count':19,'preflight_source_and_six_guards':preflight,'held_candidates_excluded':[f'{o}.{v}' for o,vs in held_directions.items() for v in vs],'contact_path':str(accepted_contact.relative_to(BASE)),'contact_sha256':asha,'install_rule':'Install exactly listed accepted candidate_path leaves after all source and six base hashes match. Do not install held candidates or replace current PNGs directly.'};pp=C/'accepted-subset-install-packet-v2.json';pp.write_text(json.dumps(packet,indent=2)+'\n')
print(json.dumps({'accepted_candidates':len(accepted['sets']),'accepted_manifest_sha256':sha(ap),'accepted_packet_sha256':sha(pp),'accepted_contact_sha256':asha,'remaining':len(remaining['sets']),'remaining_manifest_sha256':sha(rp),'combined_contact_sha256':csha,'selection_json_sha256':sha(sp),'NE_rotations':{v:{'candidate':newrot[v]['candidate_path'],'hash':newrot[v]['candidate_sha256'],'donor':newrot[v]['derived_from_candidate_path'],'donor_hash':newrot[v]['derived_from_candidate_sha256']} for v in ('top','bottom')},'NW_plan_candidates':{v:next(x for x in accepted['sets'] if x['object_id']==nw and x['view']==v)['candidate_path'] for v in ('top','bottom')}},indent=2))
