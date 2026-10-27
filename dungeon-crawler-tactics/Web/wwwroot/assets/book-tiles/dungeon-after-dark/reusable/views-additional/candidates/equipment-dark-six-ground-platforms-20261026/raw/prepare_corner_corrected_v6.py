#!/usr/bin/env python3
"""Apply source-axis correction to Over-City curb corner using declared transforms only."""
from PIL import Image,ImageOps,ImageDraw
import json,hashlib,os
PACK='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark';BASE=PACK+'/reusable/views-additional';CAND=BASE+'/candidates/equipment-dark-six-ground-platforms-20261026'
HAND='/workspace/scratch/equipment-dark-six-ground-platforms-handoff-20261026.json';HSHA='322d4973ff94801647c5094eda70c11347a20325b66dd0f61c62c4ccff7eb0d9'
PROOF='/tmp/page-qa-ground-v3-and-ramp-installed-20261026-01.png.json';PSHA='d7ff413fdf458ab8b0229a5801a654bfef331c2d2fc8acbb542f6bf493eed895'
CGUARD='/workspace/scratch/page-equipment-overcity-corner-native-basis-expansion-20261026.json';CGSHA='34ef9b1136c5b0b86ab73778340d8a0df424eff4acdd4f51f7c7bd15bcf15224';CPROOF='/tmp/page-qa-ground-curb-native-basis-current-20261026-01.png.json';CPSHA='ae2dd0fdab399def11e0f16acbec8f80c20cbebd747bd5f1767f1d698f4aee52'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
assert sha(HAND)==HSHA and sha(PROOF)==PSHA and sha(CGUARD)==CGSHA and sha(CPROOF)==CPSHA
hand=json.load(open(HAND));objs={x['object_id']:x for x in hand['objects']};old=json.load(open(CAND+'/candidate-manifest-v5.json'))
manifest=json.loads(json.dumps(old));manifest['candidate_id']='equipment-dark-six-ground-platforms-v6';manifest['normalizer_path']='reusable/views-additional/candidates/equipment-dark-six-ground-platforms-20261026/raw/prepare_corner_corrected_v6.py';manifest['current_source_six_proof_path']=PROOF;manifest['current_source_six_proof_sha256']=PSHA;manifest['corner_source_six_proof_path']=CPROOF;manifest['corner_source_six_proof_sha256']=CPSHA;manifest['corner_expansion_guard_path']=CGUARD;manifest['corner_expansion_guard_sha256']=CGSHA
manifest['held_directions']=[{'object_id':'over-city-venues-civic-stone-tile-corner-transition','view':'front','status':'held-source-adjudication','reason':'Native source zoom contradicts the assumed U-corner layout; prior generated U-front candidate is superseded and not offered for install.'}]
entry=next(s for s in manifest['sets'] if s['object_id']=='over-city-city-cobblestone-corner-transition');o=objs[entry['object_id']]
assert sha(o['source']['path'])==o['source']['sha256']
for v in ('front','top','right','left','bottom','rear'):
 actual=sha(o['views'][v]['path']);expected=o['views'][v]['sha256']; prior=entry['base_current_views'][v]['sha256']
 assert actual==expected==prior,(v,actual,expected,prior)
# plan = canonical source pixels, uniformly calibrated to 160px physical footprint
src=Image.open(o['source']['path']).convert('RGBA');bb=src.getchannel('A').point(lambda a:255 if a>=64 else 0).getbbox();crop=src.crop(bb);scale=160/max(crop.size);size=(round(crop.width*scale),round(crop.height*scale));z=crop.resize(size,Image.Resampling.NEAREST);xy=((256-size[0])//2,(256-size[1])//2);top=Image.new('RGBA',(256,256),(0,0,0,0));top.alpha_composite(z,xy)
top_path=CAND+'/images/over-city-city-cobblestone-corner-transition.top.candidate-v6.png';top.save(top_path,optimize=False)
entry['candidates']['top']={'path':top_path,'sha256':sha(top_path),'method':'canonical-source-plan-uniform-nearest-calibration','donor_path':o['source']['path'],'donor_sha256':sha(o['source']['path']),'alpha64_crop_bbox':list(bb),'normalization':{'filter':'NEAREST','uniform_scale':scale,'resized_dimensions':list(size),'canvas':[256,256],'anchor_px':[128,128],'placement_xy':list(xy)},'notes':'Canonical zoomed native plan shows back+RIGHT curb; replaces prior mis-oriented TOP.'}
# Source-layout is BACK+RIGHT: FRONT endpoint moves right; right camera sees full right curb; left sees back endpoint at right.
oldf=entry['candidates']['front']; oldr=entry['candidates']['right']; oldl=entry['candidates']['left']
front_path=CAND+'/images/over-city-city-cobblestone-corner-transition.front.candidate-v6.png';ImageOps.mirror(Image.open(oldf['path']).convert('RGBA')).save(front_path,optimize=False)
entry['candidates']['front']={'path':front_path,'sha256':sha(front_path),'method':'rigid-horizontal-reflection-of-v5-front','donor_path':oldf['path'],'donor_sha256':oldf['sha256'],'notes':'Cap moved to screen-right to match source BACK+RIGHT plan.'}
right_path=CAND+'/images/over-city-city-cobblestone-corner-transition.right.candidate-v6.png';Image.open(oldl['path']).convert('RGBA').save(right_path,optimize=False)
entry['candidates']['right']={'path':right_path,'sha256':sha(right_path),'method':'same-target-generated-opposite-side-profile-alias','donor_path':oldl['path'],'donor_sha256':oldl['sha256'],'symmetry_note':'Source RIGHT arm is the long raised curb, shown as full bank from RIGHT camera.'}
left_path=CAND+'/images/over-city-city-cobblestone-corner-transition.left.candidate-v6.png';ImageOps.mirror(Image.open(oldr['path']).convert('RGBA')).save(left_path,optimize=False)
entry['candidates']['left']={'path':left_path,'sha256':sha(left_path),'method':'rigid-horizontal-reflection-of-v5-right-profile','donor_path':oldr['path'],'donor_sha256':oldr['sha256'],'notes':'Back curb endpoint occupies screen-right from LEFT camera, matching native plan.'}
for v,p in [('front',front_path),('top',top_path),('right',right_path),('left',left_path)]:
 if v not in entry['affected_views']:entry['affected_views'].append(v)
entry['notes']='Versioned source-first correction: native curb occupies BACK+RIGHT; only four planes updated, REAR/BOTTOM remain preserved.'
# Remove prior Civic candidate from install set pending source-layout adjudication.
civ=next(s for s in manifest['sets'] if s['object_id']=='over-city-venues-civic-stone-tile-corner-transition');civ['candidates']={};civ['affected_views']=[];civ['notes']='No candidate offered: native source layout is under adjudication; previous U-front candidate remains diagnostic only.'
# Contact set displays v6 candidate directions, all other valid base/candidate directions, and unchanged Civic current.
contacts=[]
for s in manifest['sets']:
 oid=s['object_id'];o=objs[oid];ims=[Image.open(o['source']['path']).convert('RGBA')]
 for v in ('front','top','right','left','bottom','rear'):
  p=s['candidates'].get(v,{}).get('path',o['views'][v]['path']);ims.append(Image.open(p).convert('RGBA'))
 contacts.append((oid,ims))
tw=170;th=170;lh=24;pad=8;rh=th+lh+pad;sheet=Image.new('RGBA',(pad+7*(tw+pad),pad+len(contacts)*rh),(34,34,40,255));dr=ImageDraw.Draw(sheet)
for ri,(oid,ims) in enumerate(contacts):
 y=pad+ri*rh;dr.text((pad,y),oid,fill='white');ty=y+lh
 for ci,im in enumerate(ims):
  x=pad+ci*(tw+pad);im.thumbnail((tw,th),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+(tw-im.width)//2,ty+(th-im.height)//2));dr.text((x,ty+th),['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR'][ci],fill='white')
mp=CAND+'/candidate-manifest-v6.json';open(mp,'w').write(json.dumps(manifest,indent=2)+'\n');cp=CAND+'/contacts/source-six-candidate-v6.png';sheet.save(cp)
print(json.dumps({'manifest':mp,'manifest_sha256':sha(mp),'contact':cp,'contact_sha256':sha(cp)},indent=2))
