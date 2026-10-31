"""Install the reviewed-bounds, isotropic low-cost wall/cap scale candidates."""
from pathlib import Path
import hashlib,json,os,shutil,struct
from PIL import Image
OUT=Path(__file__).resolve().parent.parent;BOOK=OUT.parent.parent
SPEC=json.loads((OUT/'candidates/small-scale-batch-v1.json').read_text());INDEX=OUT/'set-index.json';RECIPE=OUT/'repair-mappings/replay-installed-dark-repairs-v2.json';SNAPDIR=OUT/'prebuilt/replay-sidecars-small-scale-batch-v1';INPUTDIR=OUT/'prebuilt/small-scale-batch-inputs-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,data):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data);os.replace(t,p)
def main():
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};rec=json.loads(RECIPE.read_text());old={e['asset_id']:e for e in rec['entries']};prepared=[]
 # Candidate preparation and hash checks are completed before any live mutation.
 for s in SPEC['sets']:
  oid=s['object_id']
  for e in s['views']:
   aid=e['asset_id'];a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);cand=safe(OUT,e['candidate_path']);before=sha(dst)
   assert before==e['base_sha256'],(aid,'base hash changed');assert sha(cand)==e['candidate_sha256'];assert a['image']['sha256']==before
   rawrel='reusable/views-additional/prebuilt/small-scale-batch-inputs-v1/'+aid+'.png';raw=safe(BOOK,rawrel)
   if raw.exists():assert sha(raw)==before
   else:atomic(raw,dst.read_bytes())
   new=json.loads(json.dumps(a));src=a['source'];source_image=src['source_image'];source_sha=src['source_sha256'];im=Image.open(cand).convert('RGBA');new['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba_sha(cand)})
   new.setdefault('provenance_history',[]).append({'candidate_id':SPEC['candidate_id']+':'+aid,'previous_provenance':new.get('provenance',{}),'previous_image_sha256':before})
   new['provenance']={'method':'retained-raster-uniform-scale-calibration','source_image':source_image,'source_sha256':source_sha,'input_raster_path':rawrel,'input_raster_sha256':sha(raw),'input_reviewed_image_sha256':before,'crop_rect':e['crop_rect'],'alpha_bounds_before':e['input_bbox'],'normalization':{'scale':e['uniform_scale'],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'normalized_size':e['normalized_size'],'distortion':'none; uniform isotropic scale'},'target_span_px':e['target_span_px'],'notes':'Existing retained projection normalized with one uniform nearest-neighbor scale to match the measured shared footprint/height. No redrawing, recoloring, or axis-specific stretching.'}
   mdata=(json.dumps(new,indent=2)+'\n').encode();msha=hashlib.sha256(mdata).hexdigest();snaprel='reusable/views-additional/prebuilt/replay-sidecars-small-scale-batch-v1/'+aid+'.json';atomic(safe(BOOK,snaprel),mdata)
   prepared.append((aid,a,new,cand,dst,mdst,before,mdata,msha,snaprel,e))
 for aid,a,new,cand,dst,mdst,before,mdata,msha,snaprel,e in prepared:
  atomic(dst,cand.read_bytes());assert sha(dst)==e['candidate_sha256'];atomic(mdst,mdata);assert sha(mdst)==msha;assets[aid].clear();assets[aid].update(new)
  old[aid]={'asset_id':aid,'image_path':a['image']['path'],'candidate_path':e['candidate_path'],'candidate_sha256':e['candidate_sha256'],'base_sha256':before,'final_sha256':e['candidate_sha256'],'metadata_path':a['metadata_path'],'metadata_snapshot_path':snaprel,'metadata_sha256':msha,'live_before_install_sha256':before,'superseded_installed_sha256':before}
 touched={s['object_id'] for s in SPEC['sets']}
 for vs in idx['view_sets']:
  if vs['object_id'] in touched:vs['complete']=False;vs['notes']='Targeted uniform scale calibration installed; awaiting current-hash source-plus-six review.'
 order=[];changed={x[0] for x in prepared}
 for e in rec['entries']:
  if e['asset_id'] not in changed:order.append(e['asset_id'])
 order.extend(x[0] for x in prepared);rec['entries']=[old[k] for k in order]
 atomic(RECIPE,(json.dumps(rec,indent=2)+'\n').encode());atomic(INDEX,(json.dumps(idx,indent=2)+'\n').encode())
 print(json.dumps({'installed_views':len(prepared),'sets':len(touched),'recipe_entries':len(rec['entries'])},indent=2))
if __name__=='__main__':main()
