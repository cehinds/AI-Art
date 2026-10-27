#!/usr/bin/env python3
"""Install the root-approved solid concrete top plan after source/hash preflight."""
import hashlib, json, os, struct, tempfile
from pathlib import Path
from PIL import Image

HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1]
OBJ='ghost-havana-ghost-traffic-road-barrier';INDEX=HERE/'set-index.json'
REQ=HERE/'raw'/f'{OBJ}-top-v6.request.json';ATLAS=HERE/'raw'/f'{OBJ}-top-v6-atlas.png'
RECIPE=HERE/'raw'/f'{OBJ}-top-v6-candidate.recipe.json';CAND=HERE/'raw'/f'{OBJ}-top-v6-candidate.png'
SOURCE=PACK/'ghost-havana'/'components'/f'{OBJ}.png'
CONTACT=HERE/f'qa-{OBJ}-top-v6-candidate-source-six.png'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,data):
 fd,tmp=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 except BaseException:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise
def jwrite(p,d):atomic(p,(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 r=json.loads(RECIPE.read_text());idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};aid=OBJ+'.top';a=assets[aid];assert a['id']==aid and a['view']=='top' and a['image']['path'].endswith(OBJ+'.top.png');live=PACK/a['image']['path'];mp=PACK/a['metadata_path'];meta=json.loads(mp.read_text())
 assert r['status']=='candidate-ready-for-independent-review'
 assert sha(REQ)==r['request_sha256'] and sha(ATLAS)==r['source_atlas_sha256'] and sha(SOURCE)==r['canonical_source_sha256']
 assert sha(PACK/r['evidence_contact'])==r['evidence_contact_sha256'] and sha(CONTACT)==r['candidate_contact_sha256'] and sha(CAND)==r['candidate_sha256']
 for d,h in r['preinstall_view_hashes'].items():assert sha(HERE/f'{OBJ}.{d}.png')==h,(d,sha(HERE/f'{OBJ}.{d}.png'),h)
 old=meta.get('provenance',{});prov={**old,'superseded_provenance':[*old.get('superseded_provenance',[]),{k:v for k,v in old.items() if k!='superseded_provenance'}],'method':'generated','source_image':'ghost-havana/components/'+SOURCE.name,'source_sha256':sha(SOURCE),'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,'source_atlas_sha256':sha(ATLAS),'generation_recipe':'reusable/views-additional/raw/'+REQ.name,'generation_recipe_sha256':sha(REQ),'normalization_recipe':'reusable/views-additional/raw/'+RECIPE.name,'normalization_recipe_sha256':sha(RECIPE),'normalization':{'operation':r['operation'],'alpha_threshold':r['alpha_threshold'],'component_labels':r['component_labels'],'component_bounds_xyxy_px':r['component_bounds_xyxy_px'],'scale':r['scale'],'resized_dimensions_px':r['resized_dimensions_px'],'canvas_offset_xy_px':r['canvas_offset_xy_px']},'notes':'Inferred strict overhead view of a single solid Jersey concrete barrier: full tapered footprint, central ridge and upward-facing painted flanks. Not recovered pixels or calibrated 3D.'}
 atomic(live,CAND.read_bytes());im=Image.open(live).convert('RGBA');fh=sha(live);image={'path':a['image']['path'],'width':im.width,'height':im.height,'sha256':fh,'rgba_sha256':hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()};meta['image']=image;meta['provenance']=prov;jwrite(mp,meta);a['image']=image;a['provenance']=prov;groups[OBJ]['complete']=False;idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());jwrite(INDEX,idx)
 report={'schema':'ghost-barrier-top-v6-install-v1','object_id':OBJ,'direction':'top','image_sha256':fh,'rgba_sha256':image['rgba_sha256'],'preinstall_sha256':r['preinstall_view_hashes']['top'],'preserved_directions':['front','right','left','bottom','rear'],'candidate_contact_sha256':sha(CONTACT),'status':'installed-pending-current-source-six-review'};jwrite(HERE/'ghost-barrier-top-v6-install-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
