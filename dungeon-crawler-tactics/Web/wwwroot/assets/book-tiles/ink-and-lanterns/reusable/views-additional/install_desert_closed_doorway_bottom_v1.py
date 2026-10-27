#!/usr/bin/env python3
"""Install the scoped root-approved Desert closed-door BOTTOM candidate."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;P=H.parents[1];OID='bubble-desert-adobe-desert-plaster-closed-doorway';VIEWS=('front','top','right','left','bottom','rear');IDX=H/'set-index.json'
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
def main():
 idx=json.loads(IDX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};aid=OID+'.bottom';a=assets[aid];assert a['view']=='bottom' and a['image']['path'].endswith(OID+'.bottom.png');live=P/a['image']['path'];assert sha(live)=='49e0fcb585f14f3eee12793f4a16b9887e4568d418715c93a0d598e56cb9a985'
 rp=H/'raw'/f'{OID}.bottom-orthographic-v1-candidate.recipe.json';r=json.loads(rp.read_text());cand=H/'raw'/f'{OID}.bottom-orthographic-v1-candidate.png';assert r['status']=='candidate-ready-for-independent-review' and r['candidate_sha256']==sha(cand)
 source=P/'bubble-desert/components'/f'{OID}.png';assert sha(source)==r['canonical_source_sha256'];req=P/r['request_path'];assert sha(req)==r['request_sha256']
 for v,expected in r['preinstall_view_hashes'].items():assert sha(H/f'{OID}.{v}.png')==expected,(v,'preinstall changed')
 meta_path=P/a['metadata_path'];m=json.loads(meta_path.read_text());old=m['provenance'];prov=dict(old);prov['superseded_provenance']=[*old.get('superseded_provenance',[]),{k:x for k,x in old.items() if k!='superseded_provenance'}];prov.update({'method':'generated-inferred-orthographic','source_image':r['canonical_source'],'source_sha256':r['canonical_source_sha256'],'source_atlas':r['generated_atlas'],'source_atlas_sha256':r['generated_atlas_sha256'],'generation_recipe':r['request_path'],'generation_recipe_sha256':r['request_sha256'],'normalization_recipe':'reusable/views-additional/raw/'+rp.name,'normalization_recipe_sha256':sha(rp),'normalization':{k:r[k] for k in ['operation','alpha_threshold','component_label','component_bounds_xyxy_px','scale','resized_dimensions_px','canvas_offset_px']},'notes':r['inference_note']});atom(live,cand.read_bytes());im=Image.open(live).convert('RGBA');img={'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':sha(live),'rgba_sha256':hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()};m['image']=img;m['provenance']=prov;ja(meta_path,m);a['image']=img;a['provenance']=prov;groups[OID]['complete']=False;idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());ja(IDX,idx)
 sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));dr=ImageDraw.Draw(sheet)
 for i,(path,label) in enumerate(zip([source]+[H/f'{OID}.{v}.png' for v in VIEWS],['source',*VIEWS])):
  im=Image.open(path).convert('RGBA');im.thumbnail((168,168),Image.Resampling.LANCZOS);x=i*184;dr.text((x+4,20),label,fill=(20,20,20,255));sheet.alpha_composite(im,(x+8+(168-im.width)//2,42+(168-im.height)//2))
 import io;b=io.BytesIO();sheet.save(b,'PNG',optimize=True);contact=H/'qa-bubble-desert-closed-doorway-bottom-v1-installed-source-six.png';atom(contact,b.getvalue());ja(H/'desert-closed-door-bottom-v1-install-report.json',{'schema':'ink-desert-closed-door-bottom-v1-install','status':'installed-pending-current-source-six-review','object_id':OID,'view':'bottom','image_sha256':img['sha256'],'contact':contact.name,'contact_sha256':sha(contact),'preserved_directions':[v for v in VIEWS if v!='bottom'],'preserved_hashes':{v:sha(H/f'{OID}.{v}.png') for v in VIEWS if v!='bottom'}});print(json.dumps({'image_sha256':img['sha256'],'contact':contact.name,'contact_sha256':sha(contact)},indent=2))
if __name__=='__main__':main()
