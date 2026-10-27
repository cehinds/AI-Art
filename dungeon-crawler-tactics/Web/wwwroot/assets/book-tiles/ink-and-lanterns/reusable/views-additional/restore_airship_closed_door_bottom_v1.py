#!/usr/bin/env python3
"""Restore the accepted BOTTOM after the copied top installer targeted it."""
import hashlib,json,os,struct,tempfile
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];OBJ='bubble-airship-riveted-scrap-hull-closed-doorway';INDEX=HERE/'set-index.json'
TOP_RECIPE=HERE/'raw'/f'{OBJ}-top-v1-candidate.recipe.json';BOTTOM_RECIPE=HERE/'raw'/f'{OBJ}-bottom-v1-candidate.recipe.json';CAND=HERE/'raw'/f'{OBJ}-bottom-v1-candidate.png';SOURCE=PACK/'bubble-airship'/'components'/f'{OBJ}.png'
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
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};topr=json.loads(TOP_RECIPE.read_text());botr=json.loads(BOTTOM_RECIPE.read_text());assert sha(CAND)==botr['candidate_sha256'] and sha(SOURCE)==botr['canonical_source_sha256']
 before={d:sha(HERE/f'{OBJ}.{d}.png') for d in ('front','top','right','left','bottom','rear')}
 assert before['top']==topr['preinstall_view_hashes']['top'] and before['bottom']==topr['candidate_sha256'],before
 for d in ('front','right','left','rear'):assert before[d]==topr['preinstall_view_hashes'][d],(d,before[d])
 current=HERE/f'{OBJ}.bottom.png';meta_path=PACK/assets[OBJ+'.bottom']['metadata_path'];meta=json.loads(meta_path.read_text());current_prov=meta.get('provenance',{});chain=current_prov.get('superseded_provenance',[])
 accepted_bottom=next((x for x in reversed(chain) if x.get('generation_recipe','').endswith(f'{OBJ}-bottom-v1.request.json')),None)
 if accepted_bottom is None:
  accepted_bottom={k:v for k,v in current_prov.items() if k not in ('superseded_provenance','normalization_recipe','normalization_recipe_sha256','normalization')}
 # Preserve both original base provenance and the mistaken top-installed provenance as history.
 hist=[x for x in chain if x is not accepted_bottom]+[{k:v for k,v in current_prov.items() if k!='superseded_provenance'}]
 prov={**accepted_bottom,'superseded_provenance':hist,'method':'generated','source_image':'bubble-airship/components/'+SOURCE.name,'source_sha256':sha(SOURCE),'source_atlas':'reusable/views-additional/raw/'+f'{OBJ}-bottom-v1-atlas.png','source_atlas_sha256':sha(HERE/'raw'/f'{OBJ}-bottom-v1-atlas.png'),'generation_recipe':'reusable/views-additional/raw/'+f'{OBJ}-bottom-v1.request.json','generation_recipe_sha256':sha(HERE/'raw'/f'{OBJ}-bottom-v1.request.json'),'normalization_recipe':'reusable/views-additional/raw/'+BOTTOM_RECIPE.name,'normalization_recipe_sha256':sha(BOTTOM_RECIPE),'normalization':{k:botr[k] for k in ('operation','alpha_threshold','component_labels','component_bounds_xyxy_px','scale','resized_dimensions_px','canvas_offset_xy_px')},'notes':'Restored the accepted narrow bottom door/threshold edge and jamb feet from its immutable v1 candidate after a copied installer targeted this asset accidentally. Inferred view, not recovered pixels or calibrated 3D.'}
 atomic(current,CAND.read_bytes());im=Image.open(current).convert('RGBA');fh=sha(current);image={'path':assets[OBJ+'.bottom']['image']['path'],'width':im.width,'height':im.height,'sha256':fh,'rgba_sha256':hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()};meta['image']=image;meta['provenance']=prov;jwrite(meta_path,meta);a=assets[OBJ+'.bottom'];a['image']=image;a['provenance']=prov;groups[OBJ]['complete']=False;idx['assets']=list(assets.values());idx['view_sets']=list(groups.values());jwrite(INDEX,idx)
 record={'schema':'airship-closed-door-misinstall-repair-v1','phase':'bottom-restored-top-not-yet-installed','object_id':OBJ,'source_sha256':sha(SOURCE),'before_view_hashes':before,'bottom_candidate_sha256':sha(CAND),'restored_bottom_sha256':fh,'top_candidate_sha256':topr['candidate_sha256'],'expected_top_target_path':'reusable/views-additional/'+f'{OBJ}.top.png','expected_bottom_target_path':'reusable/views-additional/'+f'{OBJ}.bottom.png','preserved_other_four':['front','right','left','rear'],'note':'The previous copied installer selected the .bottom asset ID. Restored the accepted bottom first; corrected top install follows with an explicit direction/path assertion.'};jwrite(HERE/'airship-closed-door-misinstall-repair-v1.json',record);print(json.dumps(record,indent=2))
if __name__=='__main__':main()
