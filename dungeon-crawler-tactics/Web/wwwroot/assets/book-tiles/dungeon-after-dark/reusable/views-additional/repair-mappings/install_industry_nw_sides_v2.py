from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
OUT=Path(__file__).resolve().parent.parent;BOOK=OUT.parent.parent;SPEC=json.loads((OUT/'candidates/industry-nw-wall-sides-v2.json').read_text());INDEX=OUT/'set-index.json';RECIPE=OUT/'repair-mappings/replay-installed-dark-repairs-v2.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,b):p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(b);os.replace(t,p)
def main():
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};recipe=json.loads(RECIPE.read_text());old={e['asset_id']:e for e in recipe['entries']};prep=[]
 for e in SPEC['views']:
  aid=e['asset_id'];a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);cand=safe(OUT,e['candidate_path']);before=sha(dst);assert before==e['base_sha256'] and a['image']['sha256']==before and sha(cand)==e['candidate_sha256']
  rawrel='reusable/views-additional/prebuilt/industry-nw-wall-sides-inputs-v2/'+aid+'.png';raw=safe(BOOK,rawrel)
  if raw.exists():assert sha(raw)==before
  else:atomic(raw,dst.read_bytes())
  new=json.loads(json.dumps(a));src=a['source'];im=Image.open(cand).convert('RGBA');new['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)});new.setdefault('provenance_history',[]).append({'candidate_id':SPEC['candidate_id']+':'+aid,'previous_provenance':new.get('provenance',{}),'previous_image_sha256':before})
  new['provenance']={'method':'retained-raster-uniform-z-calibration','source_image':src['source_image'],'source_sha256':src['source_sha256'],'input_raster_path':rawrel,'input_raster_sha256':sha(raw),'input_reviewed_image_sha256':before,'alpha_bounds_before':e['input_bbox'],'crop_rect':e['crop_rect'],'normalization':{'scale':e['uniform_scale'],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'normalized_size':e['normalized_size'],'distortion':'none; uniform isotropic scale'},'target_height_px':e['target_height_px'],'notes':'Retained right/left elevations uniformly nearest-neighbor scaled to the already-reviewed front/rear Z height. No axis-specific stretching.'}
  md=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(md).hexdigest();mr='reusable/views-additional/prebuilt/replay-sidecars-industry-nw-sides-v2/'+aid+'.json';atomic(safe(BOOK,mr),md)
  prep.append((aid,a,new,cand,dst,mdst,before,md,mh,mr,e))
 for aid,a,new,cand,dst,mdst,before,md,mh,mr,e in prep:
  atomic(dst,cand.read_bytes());atomic(mdst,md);assets[aid].clear();assets[aid].update(new);old[aid]={'asset_id':aid,'image_path':a['image']['path'],'candidate_path':e['candidate_path'],'candidate_sha256':e['candidate_sha256'],'base_sha256':before,'final_sha256':e['candidate_sha256'],'metadata_path':a['metadata_path'],'metadata_snapshot_path':mr,'metadata_sha256':mh,'live_before_install_sha256':before,'superseded_installed_sha256':before}
 oid=SPEC['object_id']
 for s in idx['view_sets']:
  if s['object_id']==oid:s['complete']=False;s['notes']='RIGHT/LEFT uniform Z-scale calibrated; awaiting current-hash review.'
 existing=[e['asset_id'] for e in recipe['entries'] if e['asset_id'] not in {p[0] for p in prep}];order=existing+[p[0] for p in prep];recipe['entries']=[old[k] for k in order]
 atomic(RECIPE,(json.dumps(recipe,indent=2)+'\n').encode());atomic(INDEX,(json.dumps(idx,indent=2)+'\n').encode());print(json.dumps({'views':len(prep),'recipe_entries':len(recipe['entries'])},indent=2))
if __name__=='__main__':main()
