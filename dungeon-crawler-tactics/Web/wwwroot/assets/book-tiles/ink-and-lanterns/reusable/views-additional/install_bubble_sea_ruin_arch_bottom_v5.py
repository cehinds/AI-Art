#!/usr/bin/env python3
"""Install root-approved bottom candidate, with strict direction/path preflight."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];OBJ='bubble-sea-underwater-ruin-arch';D='bottom';INDEX=HERE/'set-index.json'
CAND=HERE/'raw'/f'{OBJ}-{D}-v5-candidate.png';RECIPE=HERE/'raw'/f'{OBJ}-{D}-v5-candidate.recipe.json';REQUEST=HERE/'raw'/f'{OBJ}-{D}-v5.request.json';ATLAS=HERE/'raw'/f'{OBJ}-{D}-v5-atlas.png';SOURCE=PACK/'bubble-sea/components'/f'{OBJ}.png'
VIEWS=('front','top','right','left','bottom','rear')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,b):
 fd,tmp=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 except BaseException:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
def jatomic(p,x):atomic(p,(json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def main():
 r=json.loads(RECIPE.read_text());q=json.loads(REQUEST.read_text());idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']}
 aid=OBJ+'.'+D;a=assets[aid];assert a['id']==aid and a['view']==D and a['image']['path'].endswith(f'{OBJ}.{D}.png')
 live=PACK/a['image']['path'];mp=PACK/a['metadata_path'];assert mp==PACK/a['metadata_path'] and mp.name==f'{OBJ}.{D}.json'
 assert r['object_id']==OBJ and r['direction']==D and r['status']=='candidate-ready-for-independent-review'
 assert sha(REQUEST)==r['request_sha256'] and sha(ATLAS)==r['source_atlas_sha256'] and sha(SOURCE)==r['canonical_source_sha256'] and sha(CAND)==r['candidate_sha256']
 for v,h in r['preinstall_view_hashes'].items():assert sha(HERE/f'{OBJ}.{v}.png')==h,(v,sha(HERE/f'{OBJ}.{v}.png'),h)
 meta=json.loads(mp.read_text());old=meta.get('provenance',{})
 prov={**old,'superseded_provenance':[*old.get('superseded_provenance',[]),{k:v for k,v in old.items() if k!='superseded_provenance'}], 'method':'generated','source_image':'bubble-sea/components/'+SOURCE.name,'source_sha256':sha(SOURCE),'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,'source_atlas_sha256':sha(ATLAS),'generation_recipe':'reusable/views-additional/raw/'+REQUEST.name,'generation_recipe_sha256':sha(REQUEST),'normalization_recipe':'reusable/views-additional/raw/'+RECIPE.name,'normalization_recipe_sha256':sha(RECIPE),'normalization':{'operation':r['operation'],'alpha_threshold':r['alpha_threshold'],'component_labels':r['component_labels'],'component_bounds_xyxy_px':r['component_bounds_xyxy_px'],'scale':r['scale'],'resized_dimensions_px':r['resized_dimensions_px'],'canvas_offset_xy_px':r['canvas_offset_xy_px']},'notes':'Inferred orthographic underside: thick connected stone arch soffit band with two square foot blocks and open portal beyond; not recovered pixels or calibrated 3D.'}
 atomic(live,CAND.read_bytes());im=Image.open(live).convert('RGBA');image={'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':sha(live),'rgba_sha256':rgba_sha(im)};meta['image']=image;meta['provenance']=prov;jatomic(mp,meta);a['image']=image;a['provenance']=prov;groups[OBJ]['complete']=False;idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());jatomic(INDEX,idx)
 source=Image.open(SOURCE).convert('RGBA');cells=[Image.open(HERE/f'{OBJ}.{v}.png').convert('RGBA') for v in VIEWS];sheet=Image.new('RGBA',(7*184,216),(239,235,226,255));draw=ImageDraw.Draw(sheet)
 for i,(cell,label) in enumerate(zip([source]+cells,['source',*VIEWS])):
  x=i*184;draw.text((x+4,22),label,fill=(15,15,15,255));cell.thumbnail((168,168),Image.Resampling.LANCZOS);sheet.alpha_composite(cell,(x+8+(168-cell.width)//2,42+(168-cell.height)//2))
 import io
 b=io.BytesIO();sheet.save(b,'PNG',optimize=True);contact=HERE/'qa-bubble-sea-underwater-ruin-arch-bottom-v5-installed-source-six.png';atomic(contact,b.getvalue())
 report={'schema':'bubble-sea-ruin-arch-bottom-v5-install-v1','object_id':OBJ,'direction':D,'installed_image_sha256':image['sha256'],'rgba_sha256':image['rgba_sha256'],'source_sha256':sha(SOURCE),'request_sha256':sha(REQUEST),'recipe_sha256':sha(RECIPE),'contact':contact.name,'contact_sha256':sha(contact),'preserved_directions':[v for v in VIEWS if v!=D],'status':'installed-pending-current-source-six-review'};jatomic(HERE/'bubble-sea-ruin-arch-bottom-v5-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
