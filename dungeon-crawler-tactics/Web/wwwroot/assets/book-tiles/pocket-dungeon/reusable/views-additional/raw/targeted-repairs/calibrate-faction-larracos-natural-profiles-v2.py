#!/usr/bin/env python3
"""Calibrate dry ground profiles and use them as dry transition donors, hash guarded."""
import hashlib,importlib.util,json
from pathlib import Path
from PIL import Image
OUT=Path(__file__).resolve().parents[2];BOOK=OUT.parents[1];QA=Path('/workspace/scratch/view-qa-root.json')
FIRST=['faction-larracos-drained-city-cobblestone-floor','faction-larracos-worn-drained-city-cobblestone-floor','faction-larracos-cracked-drained-city-cobblestone-floor','faction-larracos-wet-drained-city-cobblestone-floor'];EDGE='faction-larracos-drained-city-cobblestone-edge-transition';VIEWS=['front','right','left','bottom','rear']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 idxp=OUT/'set-index.json';index=json.loads(idxp.read_text());sets={s['object_id']:s for s in index['view_sets']};assets={a['id']:a for a in index['assets']};rootq=json.loads(QA.read_text())['reviewed']; allids=FIRST+[EDGE]
 for oid in allids:
  q=rootq.get('book-tiles/pocket-dungeon::'+oid)
  if not q or q.get('status')=='pass':raise RuntimeError(f'{oid} no longer current unresolved hold')
  for view,h in q.get('image_hashes',{}).items():
   p=BOOK/assets[sets[oid]['views'][view]]['image']['path']
   if sha(BOOK/p)!=h:raise RuntimeError(f'{oid}.{view} stale review hashes; do not edit')
 recipe=OUT/'corrections.json';spec=json.loads(recipe.read_text());ops=[];backup=OUT/'raw/targeted-repairs'/'larracos-natural-profile-scale-v2';backup.mkdir(parents=True,exist_ok=True)
 # First four variants retain their generated material and side profiles; calibrate broad front/rear and plan width to accepted TOP.
 for oid in FIRST:
  refp=OUT/f'{oid}.top.png';ref=Image.open(refp).convert('RGBA').getchannel('A').getbbox();targetw=ref[2]-ref[0];refsha=sha(refp)
  for view in ['front','bottom','rear']:
   p=OUT/f'{oid}.{view}.png';before=sha(p);im=Image.open(p).convert('RGBA');bbox=im.getchannel('A').getbbox();crop=im.crop(bbox);scale=targetw/(bbox[2]-bbox[0]);size=(targetw,max(1,round(crop.height*scale)));frame=Image.new('RGBA',(256,256),(0,0,0,0));crop.resize(size,Image.Resampling.NEAREST);res=crop.resize(size,Image.Resampling.NEAREST);frame.alpha_composite(res,((256-size[0])//2,248-size[1]));cand=backup/f'{oid}.{view}.candidate.png';frame.save(cand,optimize=True)
   ops.append({'type':'uniform-scale-to-view-width','object_id':oid,'view':view,'reference_view':'top','before_sha256':before,'reference_sha256':refsha,'after_sha256':sha(cand),'reason':'Uniformly calibrate this shallow floor edge or underside to the accepted square TOP footprint width; preserve aspect ratio and source-specific dry/worn/cracked/wet stone material.'})
 # Edge-transition surfaces were generated with an incorrect wet-blue surface despite the canonical dry-cobble TOP.
 # Copy same-family dry source floor views as explicit inferred material/geometry donors; keep canonical target source provenance.
 donor=FIRST[0]
 for view in VIEWS:
  target=OUT/f'{EDGE}.{view}.png';source=OUT/f'{donor}.{view}.png';ops.append({'type':'alias','object_id':EDGE,'target':view,'source':view,'source_object_id':donor,'before_sha256':sha(target),'after_sha256':sha(source),'source_sha256':sha(source),'reason':'The canonical transition tile TOP is dry cobblestone with an earth curb. Its prior generated views introduced a wet-blue material absent from the source; use the matching same-family dry stone/earth projection donor while retaining canonical target source lineage and disclosing the derivation.'})
 spec['operations'].extend(ops);recipe.write_text(json.dumps(spec,indent=2)+'\n')
 hpath=OUT/'apply_deterministic_view_fixes.py';sp=importlib.util.spec_from_file_location('viewfix',hpath);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);results=[m.apply(op,index,backup) for op in ops];idxp.write_text(json.dumps(index,indent=2)+'\n');(backup/'result.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
