"""Install only the five explicitly accepted batch01 facade leaves."""
from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent; OUT=HERE.parent; BOOK=OUT.parent.parent
INDEX=OUT/'set-index.json'; RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
MANIFEST=OUT/'candidates/equipment-dark-six-cemetery-havana-facades-20261026/candidate-manifest-batch01-v1.json'
REVIEW=Path('/workspace/scratch/page-equipment-facades-batch01-v1-candidate-review.json')
REVIEW_LOCAL=OUT/'qa/page-equipment-facades-batch01-v1-candidate-review.json'
BEFORE=OUT/'prebuilt/equipment-facades-batch01-v1-before'; SNAP=OUT/'prebuilt/replay-sidecars-final-v1'
CID='equipment-dark-facades-batch01-page-approved-v1'
APPROVED={('ghost-cemetery-burial-niche-wall','top'),('ghost-cemetery-burial-niche-wall','bottom'),('ghost-cemetery-la-iglesia-de-los-olvidados-entrance','top'),('ghost-cemetery-la-iglesia-de-los-olvidados-entrance','bottom'),('ghost-cemetery-spirit-box-trap','top')}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA'); return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,p):
 q=(root/p).resolve(); q.relative_to(root.resolve()); return q
def rel(p): return Path(p).resolve().relative_to(BOOK.resolve()).as_posix()
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 man=json.loads(MANIFEST.read_text()); rv=json.loads(REVIEW.read_text())
 assert sha(MANIFEST)==rv['candidate_manifest']['sha256']
 assert rv['install_authorized_for_accepted_directions'] is True
 assert REVIEW_LOCAL.exists() is False or sha(REVIEW_LOCAL)==sha(REVIEW)
 if not REVIEW_LOCAL.exists(): atomic(REVIEW_LOCAL,REVIEW.read_bytes())
 idx=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text())
 assets={a['id']:copy.deepcopy(a) for a in idx['assets']};sets={s['object_id']:copy.deepcopy(s) for s in idx['view_sets']}; entries=recipe['entries'];emap={e['asset_id']:e for e in entries}
 review={(x['object_id'],x['view']):x for x in rv['sets']}
 rows=[]
 for obj in man['sets']:
  oid=obj['object_id']; src=obj['source']; sp=safe(BOOK,src['path']); assert sha(sp)==src['sha256']
  for v,b in obj['base_current_views'].items(): assert sha(safe(BOOK,b['path']))==b['sha256'],(oid,v,'base')
  for v,c in obj['candidates'].items():
   if (oid,v) not in APPROVED: continue
   r=review[(oid,v)]; assert r['decision']=='accepted' and r['candidate_sha256']==c['sha256']
   cp=safe(BOOK,c['path']); assert sha(cp)==c['sha256']
   aid=f'{oid}.{v}'; a=assets[aid]; dst=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path']);base=obj['base_current_views'][v]['sha256']
   assert sha(dst) in (base,c['sha256']);old=json.loads(md.read_text());assert old['image']['sha256'] in (base,c['sha256'])
   new=copy.deepcopy(old);im=Image.open(cp).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=c['sha256'],rgba_sha256=rgba(cp));new.setdefault('provenance_history',[]).append({'candidate_id':CID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
   req=safe(BOOK,man['request_path']);atlas=safe(BOOK,man['atlas_path']);extractor=safe(BOOK,man['extractor_path'])
   prov={'method':c['method'],'source_image':rel(sp),'source_sha256':sha(sp),'candidate_image':rel(cp),'candidate_image_sha256':c['sha256'],'candidate_manifest':rel(MANIFEST),'candidate_manifest_sha256':sha(MANIFEST),'review_record':'reusable/views-additional/qa/page-equipment-facades-batch01-v1-candidate-review.json','review_sha256':sha(REVIEW),'atlas':rel(atlas),'atlas_sha256':sha(atlas),'request_path':rel(req),'request_sha256':sha(req),'extractor_path':rel(extractor),'extractor_sha256':sha(extractor),'raw_component_label':c['raw_component_label'],'raw_component_bbox_xyxy':c['raw_component_bbox_xyxy'],'crop_bbox_xyxy':c['crop_bbox_xyxy'],'alpha_threshold':c['raw_alpha_threshold'],'mask_dilation_8connected_iterations':c['mask_dilation_8connected_iterations'],'mask_dilation_footprint':c['mask_dilation_footprint'],'normalization':copy.deepcopy(c['normalization']),'notes':r['notes']}
   for k in ('source_image','candidate_image','candidate_manifest','review_record','atlas','request_path','extractor_path'):assert not prov[k].startswith('/') and safe(BOOK,prov[k]).is_file(),(aid,k)
   new['provenance']=prov;mt=json.dumps(new,indent=2)+'\n';mh=hashlib.sha256(mt.encode()).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
   ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':rel(cp).removeprefix('reusable/views-additional/'),'candidate_sha256':c['sha256'],'base_sha256':base,'final_sha256':c['sha256'],'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':'reusable/views-additional/qa/page-equipment-facades-batch01-v1-candidate-review.json','candidate_manifest_sha256':sha(MANIFEST)}
   if aid in emap:assert emap[aid]['final_sha256']==c['sha256'] and emap[aid]['metadata_sha256']==mh
   rows.append((aid,oid,dst,md,cp,base,c['sha256'],new,mt,mh,snap,ent))
 assert len(rows)==5
 for aid,oid,dst,md,cp,base,cs,new,mt,mh,snap,ent in rows:
  bp=BEFORE/(aid+'.png');jp=BEFORE/(aid+'.json');sp=safe(BOOK,snap)
  if not bp.exists():atomic(bp,dst.read_bytes())
  else:assert sha(bp)==base
  if not jp.exists():atomic(jp,md.read_bytes())
  else:assert json.loads(jp.read_text())['image']['sha256']==base
  if not sp.exists():atomic(sp,mt.encode())
  else:assert sha(sp)==mh
 for aid,oid,dst,md,cp,base,cs,new,mt,mh,snap,ent in rows:
  if sha(dst)==base:atomic(dst,cp.read_bytes())
  assert sha(dst)==cs
  if sha(md)!=mh:atomic(md,mt.encode())
  assert sha(md)==mh;assets[aid]=copy.deepcopy(new)
  if aid not in emap:entries.append(ent);emap[aid]=ent
  sets[oid]['complete']=False;sets[oid]['notes']='Accepted batch01 directions installed; waiting for fresh source-plus-six review.'
 ni=copy.deepcopy(idx);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in idx['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
 assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets'])
 atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n')
 print(json.dumps({'installed':[r[0] for r in rows],'excluded':'ghost-cemetery-spirit-box-trap.bottom','index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
