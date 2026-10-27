"""Install six source-faithful TOP plan uniform-scale calibrations."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
OUT=Path(__file__).resolve().parent.parent;BOOK=OUT.parent.parent;SPEC=json.loads((OUT/'candidates/groundplan-scale-6-v1.json').read_text());INDEX=OUT/'set-index.json';RECIPE=OUT/'repair-mappings/replay-installed-dark-repairs-v2.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,b):p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(b);os.replace(t,p)
def main():
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};rec=json.loads(RECIPE.read_text());existing={e['asset_id']:e for e in rec['entries']};prepared=[]
 for s in SPEC['sets']:
  oid=s['object_id']
  for e in s['views']:
   aid=e['asset_id'];a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);cand=safe(OUT,e['candidate_path']);before=sha(dst);assert before==e['base_sha256'] and a['image']['sha256']==before and sha(cand)==e['candidate_sha256']
   raw=safe(BOOK,e['retained_input_path']);assert sha(raw)==e['input_raster_sha256']
   new=json.loads(json.dumps(a));src=a['source'];im=Image.open(cand).convert('RGBA');new['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)});new.setdefault('provenance_history',[]).append({'candidate_id':SPEC['candidate_id']+':'+aid,'previous_provenance':new.get('provenance',{}),'previous_image_sha256':before})
   new['provenance']={'method':'retained-native-plan-uniform-normalization','source_image':src['source_image'],'source_sha256':src['source_sha256'],'input_raster_path':e['retained_input_path'],'input_raster_sha256':e['input_raster_sha256'],'input_reviewed_image_sha256':before,'alpha_bounds_before':e['alpha_bbox'],'crop_rect':e['crop_rect'],'normalization':{'scale':e['uniform_scale'],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'normalized_size':e['normalized_size'],'distortion':'none; uniform isotropic scale'},'target_span_px':next(x['target_span_px'] for x in SPEC['sets'] if x['object_id']==oid),'reference_lateral_widths_px':next(x['lateral_view_widths_px'] for x in SPEC['sets'] if x['object_id']==oid),'notes':'Retained source-faithful horizontal TOP raster scaled uniformly to the mean X span of the four reviewed lateral elevations. Only TOP was changed; BOTTOM and elevations preserved.'}
   md=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(md).hexdigest();mr='reusable/views-additional/prebuilt/replay-sidecars-groundplan-scale-6-v1/'+aid+'.json';atomic(safe(BOOK,mr),md)
   prepared.append((aid,a,new,cand,dst,mdst,before,md,mh,mr,e))
 for aid,a,new,cand,dst,mdst,before,md,mh,mr,e in prepared:
  atomic(dst,cand.read_bytes());atomic(mdst,md);assets[aid].clear();assets[aid].update(new);existing[aid]={'asset_id':aid,'image_path':a['image']['path'],'candidate_path':e['candidate_path'],'candidate_sha256':e['candidate_sha256'],'base_sha256':before,'final_sha256':e['candidate_sha256'],'metadata_path':a['metadata_path'],'metadata_snapshot_path':mr,'metadata_sha256':mh,'live_before_install_sha256':before,'superseded_installed_sha256':before}
 touched={s['object_id'] for s in SPEC['sets']}
 for vs in idx['view_sets']:
  if vs['object_id'] in touched:vs['complete']=False;vs['notes']='TOP plan uniformly calibrated to reviewed lateral span; awaiting current-hash source-plus-six review.'
 order=[e['asset_id'] for e in rec['entries'] if e['asset_id'] not in {q[0] for q in prepared}]+[q[0] for q in prepared];rec['entries']=[existing[k] for k in order]
 atomic(RECIPE,(json.dumps(rec,indent=2)+'\n').encode());atomic(INDEX,(json.dumps(idx,indent=2)+'\n').encode());print(json.dumps({'views':len(prepared),'sets':len(touched),'recipe_entries':len(rec['entries'])},indent=2))
if __name__=='__main__':main()
