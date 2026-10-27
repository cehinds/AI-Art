#!/usr/bin/env python3
"""Install only root-approved, hash-guarded closed-door BOTTOM candidates."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent; PACK=HERE.parents[1]; INDEX=HERE/'set-index.json'
PLANS=[
('bubble-necropolis-ancient-tomb-masonry-closed-doorway','bubble-necropolis-ancient-tomb-masonry-closed-doorway.bottom-geometry-guide-v1-candidate.recipe.json'),
('starter-dungeon-dark-stone-block-closed-doorway','starter-dungeon-dark-stone-block-closed-doorway.bottom-geometry-guide-v1-candidate.recipe.json')]
VIEWS=('front','top','right','left','bottom','rear')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im): return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True); fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 except BaseException:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
def jatomic(path,obj): atomic(path,(json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 idx=json.loads(INDEX.read_text()); assets={a['id']:a for a in idx['assets']}; groups={g['object_id']:g for g in idx['view_sets']}; actions=[]
 for oid,rname in PLANS:
  rp=HERE/'raw'/rname; recipe=json.loads(rp.read_text()); aid=f'{oid}.bottom'
  assert recipe['status']=='candidate-ready-for-independent-review' and recipe['object_id']==oid and recipe['direction']=='bottom'
  assert aid in assets and assets[aid]['id']==aid and assets[aid]['view']=='bottom'
  live=PACK/assets[aid]['image']['path']; assert live.name==f'{oid}.bottom.png'
  source=PACK/recipe['canonical_source']; cand=HERE/recipe['candidate_path'].removeprefix('reusable/views-additional/')
  assert sha(source)==recipe['canonical_source_sha256']
  assert sha(cand)==recipe['candidate_sha256']
  request=HERE/Path(recipe['request_path']).relative_to('reusable/views-additional') if False else HERE/'raw'/f'{oid}.bottom-geometry-guide-v1.request.json'
  assert sha(request)==recipe['request_sha256']
  assert sha(HERE/'raw'/Path(recipe['generated_atlas']).name)==recipe['generated_atlas_sha256']
  for direction,expected in recipe['preinstall_view_hashes'].items():
   path=HERE/f'{oid}.{direction}.png'; assert sha(path)==expected,(oid,direction,'preinstall hash mismatch')
  meta_path=PACK/assets[aid]['metadata_path']; assert Path(meta_path).name==f'{oid}.bottom.json'
  meta=json.loads((PACK/meta_path).read_text()); assert meta['view']=='bottom' and meta['object_id']==oid
  actions.append((oid,rp,recipe,aid,live,cand,source,meta_path,meta))
 result=[]
 for oid,rp,recipe,aid,live,cand,source,meta_path,meta in actions:
  old=meta.get('provenance',{}); prov=dict(old); prov['superseded_provenance']=[*old.get('superseded_provenance',[]),{k:v for k,v in old.items() if k!='superseded_provenance'}]
  prov.update({'method':'generated-inferred-orthographic','source_image':recipe['canonical_source'],'source_sha256':recipe['canonical_source_sha256'],'source_atlas':recipe['generated_atlas'],'source_atlas_sha256':recipe['generated_atlas_sha256'],'generation_recipe':recipe['request_path'],'generation_recipe_sha256':recipe['request_sha256'],'normalization_recipe':'reusable/views-additional/raw/'+rp.name,'normalization_recipe_sha256':sha(rp),'normalization':{k:recipe[k] for k in ('operation','alpha_threshold','component_labels','component_bounds_xyxy_px','scale','resized_dimensions_px','canvas_offset_xy_px')},'inference_note':recipe['inference_note'],'review_status':'installed-root-approved-pending-current-source-six-capture'})
  atomic(live,cand.read_bytes()); im=Image.open(live).convert('RGBA'); image={'path':assets[aid]['image']['path'],'width':im.width,'height':im.height,'sha256':sha(live),'rgba_sha256':rgba_sha(im)}
  meta['image']=image; meta['provenance']=prov; jatomic(PACK/meta_path,meta); assets[aid]['image']=image; assets[aid]['provenance']=prov; groups[oid]['complete']=False
  result.append({'object_id':oid,'view':'bottom','image_path':image['path'],'image_sha256':image['sha256'],'rgba_sha256':image['rgba_sha256'],'candidate_sha256':recipe['candidate_sha256'],'request_sha256':sha(rp),'preserved_view_hashes':{v:sha(HERE/f'{oid}.{v}.png') for v in VIEWS if v!='bottom'}})
 idx['assets']=list(assets.values()); idx['view_sets']=list(groups.values()); jatomic(INDEX,idx)
 # Fresh source + all six installed assets for scoped root review.
 for oid,*_ in PLANS:
  source=PACK/'assets'/f'{oid}.png'
  if not source.is_file(): source=next(PACK.glob('**/'+oid+'.png'))
  sheet=Image.new('RGBA',(7*184,216),(239,235,226,255)); draw=ImageDraw.Draw(sheet)
  files=[source]+[HERE/f'{oid}.{v}.png' for v in VIEWS]
  for i,(path,label) in enumerate(zip(files,['source',*VIEWS])):
   im=Image.open(path).convert('RGBA'); im.thumbnail((168,168),Image.Resampling.LANCZOS); x=i*184; draw.text((x+4,22),label,fill=(20,20,20,255)); sheet.alpha_composite(im,(x+8+(168-im.width)//2,42+(168-im.height)//2))
  contact=HERE/f'qa-{oid}-bottom-geometry-guide-v1-installed-source-six.png'; import io; b=io.BytesIO();sheet.save(b,'PNG',optimize=True); atomic(contact,b.getvalue())
  result_entry=next(x for x in result if x['object_id']==oid); result_entry.update({'contact':contact.name,'contact_sha256':sha(contact)})
 jatomic(HERE/'door-bottom-geometry-guides-v1-install-report.json',{'schema':'ink-door-bottom-geometry-guides-v1-install','status':'installed-pending-independent-current-source-six-review','updated_count':len(result),'updated':result})
 print(json.dumps(result,indent=2))
if __name__=='__main__': main()
