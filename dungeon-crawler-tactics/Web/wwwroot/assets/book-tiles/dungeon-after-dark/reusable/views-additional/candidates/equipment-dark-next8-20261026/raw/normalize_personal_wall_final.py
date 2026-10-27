#!/usr/bin/env python3
"""Rebuild all six staged NE wall views from scoped v1/v2 candidates.
R/L keep broad faces; TOP/BOTTOM rigidly rotate to world-Y; F/REAR scale isotropically to shared Z and centered groundline.
"""
from PIL import Image
import hashlib,json,os
BASE='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark';C=BASE+'/reusable/views-additional/candidates/equipment-dark-next8-20261026';OID='personal-space-plaster-and-timber-wall-northeast';V=['front','top','right','left','bottom','rear'];H=json.load(open('/workspace/scratch/equipment-dark-next8-candidate-handoff-20261026.json'));obj=next(o for o in H['objects'] if o['object_id']==OID)
def sha(p):return hashlib.sha256(open(p,'rb').read()).hexdigest()
def bbox(p):return Image.open(p).convert('RGBA').getchannel('A').point(lambda x:255 if x>=64 else 0).getbbox()
# Current broad elevation Z extent is the target height for end views.
target_z=min(bbox(f'{C}/images/{OID}.right.png')[3]-bbox(f'{C}/images/{OID}.right.png')[1],bbox(f'{C}/images/{OID}.left.png')[3]-bbox(f'{C}/images/{OID}.left.png')[1])
assets=[];records=[]
for view in V:
 if view in ('right','left'):
  srcp=f'{C}/images/{OID}.{view}.png'; im=Image.open(srcp).convert('RGBA');operation='preserve accepted broad-face candidate byte-for-byte'
 elif view in ('top','bottom'):
  srcp=f'{C}/images/{OID}.{view}.png'; im=Image.open(srcp).convert('RGBA').rotate(-90,resample=Image.Resampling.NEAREST,expand=False);operation='rigid 90-degree clockwise rotation in-place to world-Y plan axis'
 else:
  srcp=f'{C}/images/{OID}.{view}.png'; orig=Image.open(srcp).convert('RGBA'); b=orig.getchannel('A').point(lambda x:255 if x>=64 else 0).getbbox(); part=orig.crop(b); scale=target_z/part.height; sz=(max(1,round(part.width*scale)),target_z); part=part.resize(sz,Image.Resampling.NEAREST); im=Image.new('RGBA',(256,256),(0,0,0,0)); im.alpha_composite(part,((256-sz[0])//2,(256-sz[1])//2));operation=f'isotropic rescale of accepted source-faithful end face to shared elevation height {target_z}px'
 out=f'{C}/images/{OID}.{view}.v3.png';im.save(out);assets.append({'asset_id':OID+'.'+view,'object_id':OID,'view':view,'candidate_path':'images/'+OID+'.'+view+'.v3.png','sha256':sha(out),'width':256,'height':256,'anchor_px':[128,128],'provenance':{'method':'reused','source_image':os.path.relpath(obj['source']['path'],BASE),'source_sha256':obj['source']['sha256'],'generated_atlas_path':'raw/personal-wall-longY-atlas-v2.png','generated_atlas_sha256':sha(C+'/raw/personal-wall-longY-atlas-v2.png'),'geometry_guide':{'path':'personal-space/components/personal-space-plaster-and-timber-wall-northwest.png','sha256':sha(BASE+'/personal-space/components/personal-space-plaster-and-timber-wall-northwest.png'),'role':'same-kit geometry/material guide'},'notes':operation+'; no anisotropic distortion. Reverse/hidden construction remains inferred.'},'transform_recipe':{'input':os.path.relpath(srcp,C),'operation':operation,'source_alpha_bbox':list(bbox(srcp)) if view in ('right','left') else None,'target_z_px':target_z if view in ('front','rear') else None,'resampling':'NEAREST'}});records.append({'view':view,'source_candidate':os.path.relpath(srcp,C),'operation':operation,'alpha_bbox':[list(bbox(out)) if bbox(out) else None][0],'sha256':assets[-1]['sha256']})
# Bind against current production originals at staging time (Dark installed the already accepted end faces).
current={}
for view,x in obj['views'].items():
 p=x['path'];current[view]={'path':p,'sha256':sha(p)}
src={'path':obj['source']['path'],'sha256':sha(obj['source']['path'])}
man={'created_at':'2026-10-26','scope':'book-tiles/dungeon-after-dark','assignment':'candidate-only; Page sole reviewer, Dark sole installer','batch':'equipment-dark-next8-personal-wall-final-v3','raw_manifest':'raw/personal-wall-longY-request-v2.json','assets':assets,'normalization_records':records,'source_bindings':{OID:{'source':src,'current_base_views':current,'original_handoff_source':obj['source'],'original_handoff_base_views':obj['views']}}};mp=C+'/personal-wall-final-v3-candidate.json';json.dump(man,open(mp,'w'),indent=2);print(mp,sha(mp),'z',target_z)
