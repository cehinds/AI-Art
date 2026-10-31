#!/usr/bin/env python3
"""Replace generated ground TOPs with their canonical source top plan, preserving exact pixels where 256x256."""
from pathlib import Path
from PIL import Image
import json,hashlib,struct,shutil
WORK=Path(__file__).resolve().parent;PACK=WORK.parents[1]
planp=WORK/'replay-plan.json'
if not planp.is_file(): raise SystemExit('missing frozen replay-plan.json; source TOP reuse selection must precede base index replacement')
TARGETS=json.loads(planp.read_text()).get('source_top_reuse_active_ids',[])
print('source TOP reuse active targets',len(TARGETS))
ixp=WORK/'set-index.json';ix=json.loads(ixp.read_text());assets={}
for row in ix['assets']:
 if row.get('id'): assets[row['id']]=row
for vs in ix['view_sets']:
 for aid in vs.get('views',{}).values():
  if aid not in assets: assets[aid]=json.loads((WORK/(aid+'.json')).read_text())

def file_sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):
 im=im.convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
manifests={}
for mp in PACK.glob('*/manifest.json'):
 try: manifests[mp.parent.name]=json.loads(mp.read_text())
 except Exception: pass
for oid in TARGETS:
 found=[(kit,m) for kit,m in manifests.items() if any(a.get('id')==oid for a in m.get('assets',[]))]
 if len(found)!=1: raise RuntimeError(f'{oid}: expected one kit manifest, found {len(found)}')
 kit,manifest=found[0];source=next(a for a in manifest['assets'] if a['id']==oid)
 src=PACK/kit/source['file'];aid=oid+'.top';meta=assets[aid];dst=PACK/meta['image']['path'];im=Image.open(src).convert('RGBA')
 if im.size!=(256,256):
  scale=220/max(im.size);size=(max(1,round(im.width*scale)),max(1,round(im.height*scale)))
  norm=Image.new('RGBA',(256,256),(0,0,0,0));small=im.resize(size,Image.Resampling.NEAREST);norm.alpha_composite(small,((256-size[0])//2,(256-size[1])//2));norm.save(dst);mode='isotropic-nearest-fit-220'
 else:
  shutil.copyfile(src,dst);norm=Image.open(dst).convert('RGBA');mode='exact-source-png-reuse'
 meta['image']['width'],meta['image']['height']=norm.size;meta['image']['sha256']=file_sha(dst);meta['image']['rgba_sha256']=rgba_sha(norm)
 prov=meta['provenance'];prov['method']='source-art-reused';prov['source_image']=src.relative_to(PACK).as_posix();prov['source_top_reuse']={'source_sha256':file_sha(src),'source_size':list(im.size),'resampling':'NEAREST','normalization':mode,'render_size':list(norm.size)};prov['notes']=prov.get('notes','')+' TOP plan reused from the canonical source component without redrawing; hidden views are generated/inferred.'
 status='pending-review';meta['geometry_qa']=status;Path(PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n')
 assets[aid]=meta
 s=next(x for x in ix['view_sets'] if x['object_id']==oid);s['complete']=False;s['geometry_qa']=status;s['notes']=s.get('notes','')+' Canonical TOP plan preserved from source; awaiting independent current-hash QA.'
ix['assets']=[assets[aid] for vs in ix['view_sets'] for aid in vs.get('views',{}).values()]
ixp.write_text(json.dumps(ix,indent=2)+'\n')
print('source TOPs reused',len(TARGETS))
