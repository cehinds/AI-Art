"""Install 24 hash-guarded, isotropically normalized plan rasters."""
from pathlib import Path
import hashlib,json,os,shutil,struct
from PIL import Image

OUT=Path(__file__).resolve().parent.parent
BOOK=OUT.parent.parent
SPEC=json.loads((OUT/'candidates/retained-plan-scale-12-v1.json').read_text())
INDEX=OUT/'set-index.json'
RECIPE=OUT/'repair-mappings/replay-installed-dark-repairs-v2.json'
SNAPDIR=OUT/'prebuilt/replay-sidecars-retained-plan-scale-v1'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic_bytes(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(data);os.replace(tmp,path)

def main():
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};recipe=json.loads(RECIPE.read_text());existing={e['asset_id']:e for e in recipe['entries']};prepared=[]
 for s in SPEC['sets']:
  oid=s['object_id']
  for v in s['views']:
   aid=f"{oid}.{v['view']}";a=assets[aid];candidate=safe(OUT,v['candidate_path']);dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path'])
   assert sha(candidate)==v['candidate_sha256'],(aid,'candidate hash')
   before=sha(dst);assert before==v['base_sha256'],(aid,'live before hash',before,v['base_sha256'])
   oldmeta=sha(mdst);assert a['image']['sha256']==before,(aid,'index/live hash mismatch')
   new=json.loads(json.dumps(a));source=a.get('source',{});source_image=source.get('source_image') or a.get('provenance',{}).get('source_image');source_sha=source.get('source_sha256') or a.get('provenance',{}).get('source_sha256');assert source_image and source_sha,(aid,'canonical source lineage missing')
   im=Image.open(candidate).convert('RGBA');new['image'].update({'width':im.width,'height':im.height,'sha256':sha(candidate),'rgba_sha256':rgba_sha(candidate)})
   hist=new.setdefault('provenance_history',[])
   hist.append({'candidate_id':SPEC['candidate_id']+':'+aid,'previous_provenance':new.get('provenance',{}),'previous_image_sha256':before})
   new['provenance']={
    'method':'retained-raster-plan-uniform-normalization',
    'source_image':source_image,'source_sha256':source_sha,
    'input_raster_path':v['retained_input_path'],'input_raster_sha256':v['input_raster_sha256'],
    'input_view_asset_id':v['input_view_asset_id'],'input_reviewed_image_sha256':v['base_sha256'],
    'component_bbox_threshold32':v['largest_component_bbox_threshold32'],
    'component_area_threshold32':v['largest_component_area_threshold32'],
    'crop_rect_with_padding':v['crop_rect_with_padding'],
    'normalization':{'scale':v['uniform_scale'],'offset_px':[128-v['normalized_size'][0]//2,128-v['normalized_size'][1]//2],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; one uniform isotropic scale'},
    'target_span_px':v['target_span_px'],
    'notes':'Retained existing plan-view raster, cropped to its largest alpha component with 2px padding and uniformly nearest-neighbor normalized to the mean width of the four reviewed elevations. No redraw, recoloring, or axis-specific scaling.'
   }
   metadata=json.dumps(new,indent=2)+'\n';mdsha=hashlib.sha256(metadata.encode()).hexdigest();snaprel='reusable/views-additional/prebuilt/replay-sidecars-retained-plan-scale-v1/'+aid+'.json';snapshot=safe(BOOK,snaprel)
   atomic_bytes(snapshot,metadata.encode())
   prepared.append((aid,a,new,candidate,dst,mdst,before,oldmeta,metadata,mdsha,snaprel,v))
 # Install image bytes and sidecars after all hash guards and snapshots are prepared.
 for aid,a,new,candidate,dst,mdst,before,oldmeta,metadata,mdsha,snaprel,v in prepared:
  atomic_bytes(dst,candidate.read_bytes());assert sha(dst)==v['candidate_sha256']
  atomic_bytes(mdst,metadata.encode());assert sha(mdst)==mdsha
  assets[aid].clear();assets[aid].update(new)
  existing[aid]={
   'asset_id':aid,'image_path':a['image']['path'],'candidate_path':v['candidate_path'],
   'candidate_sha256':v['candidate_sha256'],'base_sha256':before,'final_sha256':v['candidate_sha256'],
   'metadata_path':a['metadata_path'],'metadata_snapshot_path':snaprel,'metadata_sha256':mdsha,
   'live_before_install_sha256':before,'superseded_installed_sha256':before
  }
 touched={s['object_id'] for s in SPEC['sets']}
 for vs in idx['view_sets']:
  if vs['object_id'] in touched:
   vs['complete']=False
   vs['notes']='Plan views were uniformly normalized; awaiting independent current-hash source-plus-six review.'
 # Keep deterministic recipe order: existing order, then new entries in candidate spec order.
 order=[]
 for e in recipe['entries']:
  if e['asset_id'] not in {x[0] for x in prepared}:order.append(e['asset_id'])
 order.extend(x[0] for x in prepared)
 recipe['entries']=[existing[aid] for aid in order]
 atomic_bytes(RECIPE,(json.dumps(recipe,indent=2)+'\n').encode())
 atomic_bytes(INDEX,(json.dumps(idx,indent=2)+'\n').encode())
 print(json.dumps({'installed':len(prepared),'sets':len(touched),'recipe_entries':len(recipe['entries']),'index_assets':len(idx['assets']),'complete_flags_pending':len(touched)},indent=2))
if __name__=='__main__':main()
