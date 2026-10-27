#!/usr/bin/env python3
"""Replay candidate views from retained image-generation outputs.
For each full transparent atlas cell, isolate the robust object alpha (>=64),
retain its RGBA pixels, apply one isotropic scale to the approved common-X
span using NEAREST resampling, and center on a 256 square transparent canvas.
No drawing, reflection, or anisotropic distortion is performed.
"""
from PIL import Image
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/'raw'; OUT=ROOT/'images'
JOBS=[
 ('havana-sign-bottom-output-v1.png','ghost-havana-blank-street-sign.bottom.candidate-v1.png',204),
 ('station-bottom-output-v1.png','iron-stations-blank-station-signboard.bottom.candidate-v1.png',204),
 ('transfer-bottom-output-v1.png','iron-stations-transfer-direction-board.bottom.candidate-v1.png',204),
 ('starter-top-output-v1.png','starter-dungeon-dark-stone-block-closed-doorway.top.candidate-v1.png',163),
 ('jungle-open-top-output-v1.png','hunting-jungle-vine-covered-ruin-stone-open-doorway.top.candidate-v1.png',202),
 ('jungle-open-bottom-output-v1.png','hunting-jungle-vine-covered-ruin-stone-open-doorway.bottom.candidate-v1.png',202),
 ('jungle-closed-top-output-v1.png','hunting-jungle-vine-covered-ruin-stone-closed-doorway.top.candidate-v1.png',204),
 ('jungle-closed-bottom-output-v1.png','hunting-jungle-vine-covered-ruin-stone-closed-doorway.bottom.candidate-v1.png',204),
 ('larracos-gate-top-output-v1.png','faction-larracos-larracos-castle-gate.top.candidate-v1.png',173),
 ('larracos-college-top-output-v1.png','faction-larracos-larracos-college-of-magic-entrance.top.candidate-v1.png',183),
]
records=[]
for rawname,outname,targetw in JOBS:
 im=Image.open(RAW/rawname).convert('RGBA'); alpha=im.getchannel('A')
 box=alpha.point(lambda a:255 if a>=64 else 0).getbbox()
 if box is None: raise RuntimeError(f'empty alpha: {rawname}')
 crop=im.crop(box); scale=targetw/crop.width; wh=(targetw,max(1,round(crop.height*scale)))
 resized=crop.resize(wh,Image.Resampling.NEAREST)
 offset=((256-wh[0])//2,(256-wh[1])//2)
 canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(resized,offset)
 out=OUT/outname;out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,optimize=False)
 records.append({'raw_path':'raw/'+rawname,'raw_sha256':hashlib.sha256((RAW/rawname).read_bytes()).hexdigest(),'raw_alpha_threshold':64,'raw_alpha_bbox_xyxy':list(box),'resampling':'PIL.Image.Resampling.NEAREST','scale_isotropic':scale,'resized_wh':list(wh),'offset_xy':list(offset),'candidate_path':'images/'+outname,'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
report={'recipe':'build_sign_doorway_candidates_v1.py','recipe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'outputs':records}
(OUT.parent/'sign-doorway-normalization-v1.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
