#!/usr/bin/env python3
"""Install approved Necropolis open-door plan/soffit plus scoped side candidates."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;P=H.parents[1];IDX=H/'set-index.json';OID='bubble-necropolis-ancient-tomb-masonry-open-doorway';VIEWS=('front','top','right','left','bottom','rear')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def atomic(p,b):
 fd,t=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 except BaseException:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def jatomic(p,d):atomic(p,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 idx=json.loads(IDX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};assert OID in groups
 source=P/'bubble-necropolis/components'/f'{OID}.png';source_hash='5c13553fe97d2aed2645624a677cfb0bd23be4d0a1f46201d42944ec79ff87b1';assert sha(source)==source_hash
 specs={
 'top':('raw/'+OID+'.top-geometry-guide-v1-candidate.png','raw/'+OID+'.top-geometry-guide-v1-candidate.recipe.json','054bbda9bb26657d8234ec6e863c31ae9cd83c88f0c8dc9ed03ffdc526ff67f8'),
 'right':('raw/'+OID+'.right-pocket-geometry-v1-candidate.png','raw/'+OID+'.right-pocket-geometry-v1-candidate.recipe.json','6fa85fbb30cb571e758ba0bd0dabad941245d6efb66ba219ad23ca1fd029f5d5'),
 'left':('raw/'+OID+'.left-mirrored-pocket-right-v1-candidate.png','raw/'+OID+'.left-mirrored-pocket-right-v1-candidate.recipe.json','1a3d31ffab3c9d64c67d6c11be7809fce39c099ec58d697ac5af8e7fc2ae8d29'),
 'bottom':('raw/'+OID+'.bottom-pocket-geometry-v1-candidate.png','raw/'+OID+'.bottom-pocket-geometry-v1-candidate.recipe.json','ffbe6a2704e40092c1a72bfe61395cc33921b491d4861dcaf9b3aa9bd0b2d8a8')}
 plans=[]
 for v,(crel,rrel,target) in specs.items():
  aid=f'{OID}.{v}';assert aid in assets and assets[aid]['view']==v
  a=assets[aid];live=P/a['image']['path'];assert live.name==f'{OID}.{v}.png' and sha(live)==target,(v,'target hash mismatch')
  cp=H/crel;rp=H/rrel;r=json.loads(rp.read_text());assert r['object_id']==OID and r.get('view',r.get('direction'))==v and r['status']=='candidate-ready-for-independent-review'
  assert sha(cp)==r['candidate_sha256'] and sha(source)==r.get('canonical_source_sha256',r.get('source_sha256'))
  mp=P/a['metadata_path'];m=json.loads(mp.read_text());assert m['object_id']==OID and m['view']==v
  # Existing index and sidecar must agree with the actual target before replacement.
  assert a['image']['sha256']==sha(live)==m['image']['sha256'],(v,'index/sidecar drift')
  plans.append((v,aid,a,live,cp,rp,r,mp,m))
 for v,aid,a,live,cp,rp,r,mp,m in plans:
  old=m.get('provenance',{});prov=dict(old);prov['superseded_provenance']=[*old.get('superseded_provenance',[]),{k:x for k,x in old.items() if k!='superseded_provenance'}]
  if v=='left':
   prov.update({'method':'mirrored-opposite-side-symmetry','source_image':'bubble-necropolis/components/'+source.name,'source_sha256':source_hash,'derivation':{'method':'horizontal-reflection','input_view':'right','input_path':r['input_candidate'],'input_sha256':r['input_candidate_sha256'],'transform':r['transform'],'recipe':'reusable/views-additional/raw/'+rp.name,'recipe_sha256':sha(rp)},'notes':r['inference_note']})
  else:
   req=P/r['request_path'];atlas=H/'raw'/Path(r['generated_atlas']).name
   prov.update({'method':'generated-inferred-orthographic','source_image':'bubble-necropolis/components/'+source.name,'source_sha256':source_hash,'source_atlas':'reusable/views-additional/raw/'+atlas.name,'source_atlas_sha256':r['generated_atlas_sha256'],'generation_recipe':r['request_path'],'generation_recipe_sha256':sha(req),'normalization_recipe':'reusable/views-additional/raw/'+rp.name,'normalization_recipe_sha256':sha(rp),'normalization':{k:r[k] for k in ('operation','alpha_threshold','component_label','component_bounds_xyxy_px','scale','resized_dimensions_px','canvas_offset_xy_px') if k in r},'notes':r.get('inference_note','Inferred orthographic view; not recovered pixels or calibrated 3D.')})
  atomic(live,cp.read_bytes());im=Image.open(live).convert('RGBA');image={'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':sha(live),'rgba_sha256':rgba(im)};m['image']=image;m['provenance']=prov;jatomic(mp,m);a['image']=image;a['provenance']=prov
 groups[OID]['complete']=False;idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());jatomic(IDX,idx)
 # Current authoritative source+six contact.
 sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));dr=ImageDraw.Draw(sheet)
 for i,(p,label) in enumerate(zip([source]+[H/f'{OID}.{v}.png' for v in VIEWS],['source',*VIEWS])):
  im=Image.open(p).convert('RGBA');im.thumbnail((168,168),Image.Resampling.LANCZOS);x=i*184;dr.text((x+4,20),label,fill=(20,20,20,255));sheet.alpha_composite(im,(x+8+(168-im.width)//2,42+(168-im.height)//2))
 import io;b=io.BytesIO();sheet.save(b,'PNG',optimize=True);contact=H/'qa-bubble-necropolis-open-doorway-geometry-v1-installed-source-six.png';atomic(contact,b.getvalue())
 report={'schema':'ink-necropolis-open-doorway-geometry-v1-install','status':'installed-pending-current-source-six-review','object_id':OID,'source_image':'bubble-necropolis/components/'+source.name,'source_sha256':source_hash,'installed':{v:{'path':assets[OID+'.'+v]['image']['path'],'sha256':assets[OID+'.'+v]['image']['sha256']} for v in ('top','right','left','bottom')},'preserved_directions':['front','rear'],'preserved_hashes':{v:sha(H/f'{OID}.{v}.png') for v in ('front','rear')},'contact':contact.name,'contact_sha256':sha(contact)};jatomic(H/'necropolis-open-doorway-geometry-v1-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
