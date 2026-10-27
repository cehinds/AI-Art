#!/usr/bin/env python3
"""Install scoped root-approved Desert doorway planes with exact hash guards."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;P=H.parents[1];IDX=H/'set-index.json'
PLANS=[('bubble-desert-adobe-desert-plaster-closed-doorway','top','top-orthographic-v2-candidate.recipe.json','d5022f770bc7891e022996274d5c7c06bda278168d94440fd87a0d343e090097'),('bubble-desert-adobe-desert-plaster-open-doorway','bottom','bottom-orthographic-v2-candidate.recipe.json','ab65270ae6c31c6d058d052428d24d21d633039a80bf99245b9c2790f96be7a2')]
VIEWS=('front','top','right','left','bottom','rear')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atom(p,b):
 fd,t=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 except BaseException:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def ja(p,d):atom(p,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def rgba(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def main():
 idx=json.loads(IDX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};tasks=[]
 for oid,view,rname,expected_cand in PLANS:
  aid=oid+'.'+view;assert aid in assets and assets[aid]['view']==view and assets[aid]['image']['path'].endswith(oid+'.'+view+'.png')
  a=assets[aid];live=P/a['image']['path'];rp=H/'raw'/f'{oid}.{rname}';r=json.loads(rp.read_text());cand=H/'raw'/f'{oid}.{view}-orthographic-v2-candidate.png'
  assert r['object_id']==oid and r['direction']==view and r['status']=='candidate-ready-for-independent-review'
  assert sha(cand)==expected_cand==r['candidate_sha256']
  assert sha(live)==r['preinstall_view_hashes'][view],(oid,view,'target changed')
  source=P/r['canonical_source'];assert sha(source)==r['canonical_source_sha256']
  req=P/r['request_path'];assert sha(req)==r['request_sha256']
  # Every unaffected direction must remain exactly what the candidate recipe saw, except accepted scoped changes installed after it.
  for v,old_hash in r['preinstall_view_hashes'].items():
   if v==view:continue
   actual=sha(H/f'{oid}.{v}.png')
   if oid.endswith('closed-doorway') and v=='bottom':
    assert actual=='a72c1fea13297497f700c34ebead43ff10eeb334151788c727bc58597f8c7721'
   elif oid.endswith('open-doorway') and v=='top':
    assert actual=='cbaa2e0fc620293b3cea6662f4a1579da4ea5f29fa14472c4bf3577e2f6dbe15'
   else:assert actual==old_hash,(oid,v,'unrelated view changed')
  meta_path=P/a['metadata_path'];meta=json.loads(meta_path.read_text());assert meta['view']==view and meta['object_id']==oid
  assert sha(live)==a['image']['sha256']==meta['image']['sha256']
  tasks.append((oid,view,aid,a,live,rp,r,cand,source,meta_path,meta))
 for oid,view,aid,a,live,rp,r,cand,source,mp,meta in tasks:
  old=meta.get('provenance',{});prov=dict(old);prov['superseded_provenance']=[*old.get('superseded_provenance',[]),{k:x for k,x in old.items() if k!='superseded_provenance'}];prov.update({'method':'generated-inferred-orthographic','source_image':r['canonical_source'],'source_sha256':r['canonical_source_sha256'],'source_atlas':r['generated_atlas'],'source_atlas_sha256':r['generated_atlas_sha256'],'generation_recipe':r['request_path'],'generation_recipe_sha256':r['request_sha256'],'normalization_recipe':'reusable/views-additional/raw/'+rp.name,'normalization_recipe_sha256':sha(rp),'normalization':{k:r[k] for k in ['operation','alpha_threshold','component_label','component_bounds_xyxy_px','scale','resized_dimensions_px','canvas_offset_px']},'notes':r['inference_note']});atom(live,cand.read_bytes());im=Image.open(live).convert('RGBA');image={'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':sha(live),'rgba_sha256':rgba(im)};meta['image']=image;meta['provenance']=prov;ja(mp,meta);a['image']=image;a['provenance']=prov;groups[oid]['complete']=False
 idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());ja(IDX,idx)
 results=[]
 for oid,view,*_ in tasks:
  source=P/'bubble-desert/components'/f'{oid}.png';sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));dr=ImageDraw.Draw(sheet)
  for i,(path,label) in enumerate(zip([source]+[H/f'{oid}.{v}.png' for v in VIEWS],['source',*VIEWS])):
   im=Image.open(path).convert('RGBA');im.thumbnail((168,168),Image.Resampling.LANCZOS);x=i*184;dr.text((x+4,20),label,fill=(20,20,20,255));sheet.alpha_composite(im,(x+8+(168-im.width)//2,42+(168-im.height)//2))
  import io;b=io.BytesIO();sheet.save(b,'PNG',optimize=True);contact=H/f'qa-{oid}-{view}-v2-installed-source-six.png';atom(contact,b.getvalue());a=assets[oid+'.'+view];results.append({'object_id':oid,'view':view,'image_sha256':a['image']['sha256'],'contact':contact.name,'contact_sha256':sha(contact),'preserved_directions':[v for v in VIEWS if v!=view],'preserved_hashes':{v:sha(H/f'{oid}.{v}.png') for v in VIEWS if v!=view}})
 ja(H/'desert-doorway-planes-v2-install-report.json',{'schema':'ink-desert-doorway-planes-v2-install','status':'installed-pending-current-source-six-review','updated_count':len(results),'updated':results});print(json.dumps(results,indent=2))
if __name__=='__main__':main()
