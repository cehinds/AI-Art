#!/usr/bin/env python3
"""Reuse accepted broad endcap faces as symmetric R/L projections for two square caps."""
from pathlib import Path
import json,hashlib,struct,shutil
from PIL import Image
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';IDX=VD/'set-index.json';COR=VD/'corrections.json';ids=['ghost-cemetery-white-mausoleum-masonry-north-cap','ghost-cemetery-white-mausoleum-masonry-west-cap'];ledger=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed'];idx=json.loads(IDX.read_text());spec=json.loads(COR.read_text());ops=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rsha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
for oid in ids:
 r=ledger['book-tiles/pocket-dungeon::'+oid]
 if r['status']!='needs-correction' or set(x.lower() for x in r['affected_views'])!={'right','left'}:raise SystemExit(f'root scope changed: {oid}')
 if sha(r['source'])!=r['source_sha256']:raise SystemExit(f'source changed: {oid}')
 for v,p in r['view_paths'].items():
  if sha(p)!=r['image_hashes'][v]:raise SystemExit(f'current hash changed: {oid}.{v}')
 g=next(x for x in idx['view_sets'] if x['object_id']==oid)
 for target,source in [('right','front'),('left','rear')]:
  tp=VD/f'{oid}.{target}.png';sp=VD/f'{oid}.{source}.png';mp=VD/f'{oid}.{target}.json';md=json.loads(mp.read_text());sm=json.loads((VD/f'{oid}.{source}.json').read_text());before=r['image_hashes'][target];source_hash=r['image_hashes'][source];base=md.get('provenance',{});canonical=base.get('source_image');canonical_sha=hashlib.sha256((PACK/canonical).read_bytes()).hexdigest() if canonical and (PACK/canonical).is_file() else r['source_sha256'];input_source=sm.get('provenance',{}).get('source_image');input_source_sha=hashlib.sha256((PACK/input_source).read_bytes()).hexdigest() if input_source and (PACK/input_source).is_file() else None
  shutil.copyfile(sp,tp);im=Image.open(tp).convert('RGBA');md.setdefault('provenance_history',[]).append(md.get('provenance',{}));md['provenance']={**base,'method':'inferred-symmetric-view-copy','source_image':canonical,'source_sha256':canonical_sha,'symmetric_alias_of':source,'symmetric_alias_object_id':oid,'symmetry_reason':'Square masonry cap with symmetric opposite broad faces; alias accepted FRONT/REAR to RIGHT/LEFT for coherent full-footprint cap geometry.','derivation_input':{'asset_id':sm['id'],'object_id':oid,'view':source,'image_path':sm['image']['path'],'image_sha256':source_hash,'source_image':input_source,'source_sha256':input_source_sha},'notes':'Exact accepted opposite face reused as a symmetric orthographic projection; target canonical source and material retained.'};md['geometry_qa']='pending-review';md['image'].update({'sha256':sha(tp),'rgba_sha256':rsha(im)});mp.write_text(json.dumps(md,indent=2)+'\n')
  for a in idx['assets']:
   if a['id']==md['id']:a.clear();a.update(md);break
  ops.append({'type':'alias','object_id':oid,'target':target,'source':source,'source_object_id':oid,'before_sha256':before,'source_sha256':source_hash,'after_sha256':source_hash,'reason':'Square endcap sides reuse its own accepted broad orthographic faces to match the full square cap footprint and common Z.'})
 g['complete']=False;g['geometry_qa']='pending-review';g['notes']='Guide cleanup accepted; RIGHT/LEFT alias from own accepted FRONT/REAR to match square footprint; pending independent whole-set review.'
spec['operations'].extend(ops);COR.write_text(json.dumps(spec,indent=2)+'\n');IDX.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps(ops,indent=2))
