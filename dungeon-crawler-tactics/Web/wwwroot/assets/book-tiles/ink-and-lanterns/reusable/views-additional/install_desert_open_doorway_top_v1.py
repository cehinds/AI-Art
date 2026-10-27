#!/usr/bin/env python3
"""Install scoped root-approved Desert open-door TOP."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;P=H.parents[1];O='bubble-desert-adobe-desert-plaster-open-doorway';IDX=H/'set-index.json';V=('front','top','right','left','bottom','rear')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,b):
 fd,t=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 except BaseException:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def ja(p,d):atomic(p,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 idx=json.loads(IDX.read_text());am={a['id']:a for a in idx['assets']};gm={g['object_id']:g for g in idx['view_sets']};aid=O+'.top';a=am[aid];assert a['view']=='top' and a['image']['path'].endswith(O+'.top.png');live=P/a['image']['path'];assert sha(live)=='a8b7fbd0c76991e77adb6104070f67a1278b133a7792153b30c3eb0c2a5b4719'
 rp=H/'raw'/f'{O}.top-orthographic-v1-candidate.recipe.json';r=json.loads(rp.read_text());cand=H/'raw'/f'{O}.top-orthographic-v1-candidate.png';req=P/r['request_path'];src=P/r['canonical_source'];assert sha(cand)==r['candidate_sha256'] and sha(req)==r['request_sha256'] and sha(src)==r['canonical_source_sha256']
 for v,h in r['preinstall_view_hashes'].items():assert sha(H/f'{O}.{v}.png')==h,(v,'changed since candidate')
 mp=P/a['metadata_path'];m=json.loads(mp.read_text());old=m['provenance'];prov=dict(old);prov['superseded_provenance']=[*old.get('superseded_provenance',[]),{k:x for k,x in old.items() if k!='superseded_provenance'}];prov.update({'method':'generated-inferred-orthographic','source_image':r['canonical_source'],'source_sha256':r['canonical_source_sha256'],'source_atlas':r['generated_atlas'],'source_atlas_sha256':r['generated_atlas_sha256'],'generation_recipe':r['request_path'],'generation_recipe_sha256':r['request_sha256'],'normalization_recipe':'reusable/views-additional/raw/'+rp.name,'normalization_recipe_sha256':sha(rp),'normalization':{k:r[k] for k in ['operation','alpha_threshold','component_label','component_bounds_xyxy_px','scale','resized_dimensions_px','canvas_offset_px']},'notes':r['inference_note']});atomic(live,cand.read_bytes());im=Image.open(live).convert('RGBA');img={'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':sha(live),'rgba_sha256':hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()};m['image']=img;m['provenance']=prov;ja(mp,m);a['image']=img;a['provenance']=prov;gm[O]['complete']=False;idx['assets']=list(am.values());idx['view_sets']=list(gm.values());ja(IDX,idx)
 srcpath=P/'bubble-desert/components'/f'{O}.png';sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));dr=ImageDraw.Draw(sheet)
 for i,(p,l) in enumerate(zip([srcpath]+[H/f'{O}.{x}.png' for x in V],['source',*V])):
  im=Image.open(p).convert('RGBA');im.thumbnail((168,168),Image.Resampling.LANCZOS);x=i*184;dr.text((x+4,20),l,fill=(20,20,20,255));sheet.alpha_composite(im,(x+8+(168-im.width)//2,42+(168-im.height)//2))
 import io;b=io.BytesIO();sheet.save(b,'PNG',optimize=True);c=H/'qa-bubble-desert-open-doorway-top-v1-installed-source-six.png';atomic(c,b.getvalue());ja(H/'desert-open-door-top-v1-install-report.json',{'schema':'ink-desert-open-door-top-v1-install','status':'installed-pending-current-source-six-review','object_id':O,'view':'top','image_sha256':img['sha256'],'contact':c.name,'contact_sha256':sha(c),'preserved_directions':[x for x in V if x!='top'],'preserved_hashes':{x:sha(H/f'{O}.{x}.png') for x in V if x!='top'}});print(json.dumps({'image_sha256':img['sha256'],'contact':c.name,'contact_sha256':sha(c)},indent=2))
if __name__=='__main__':main()
