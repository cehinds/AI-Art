"""Install six source-guided clean wall-corner corrections."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
OUT=Path(__file__).resolve().parent.parent;BOOK=OUT.parent.parent;SPEC=json.loads((OUT/'candidates/corner-wall-aliases-clean-v2.json').read_text());INDEX=OUT/'set-index.json';RECIPE=OUT/'repair-mappings/replay-installed-dark-repairs-v2.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,b):p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(b);os.replace(t,p)
def main():
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};rec=json.loads(RECIPE.read_text());entries={e['asset_id']:e for e in rec['entries']};prepared=[]
 for s in SPEC['sets']:
  oid=s['object_id'];source=assets[oid+'.front']['source'];sp=safe(BOOK,source['source_image']);assert sha(sp)==source['source_sha256']
  for e in s['views']:
   aid=e['asset_id'];a=assets[aid];live=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);before=sha(live);assert before==e['base_sha256'] and a['image']['sha256']==before
   cand=safe(OUT,e['candidate_path']);assert sha(cand)==e['candidate_sha256']
   if e.get('derived_from_asset_id'):assert sha(safe(BOOK,assets[e['derived_from_asset_id']]['image']['path']))==e['derived_from_sha256']
   if e.get('source_plan_path'):assert sha(safe(BOOK,e['source_plan_path']))==e['source_plan_sha256']
   new=json.loads(json.dumps(a));im=Image.open(cand).convert('RGBA');new['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)});new.setdefault('provenance_history',[]).append({'candidate_id':SPEC['candidate_id']+':'+aid,'previous_provenance':new.get('provenance',{}),'previous_image_sha256':before})
   if e.get('source_plan_path'):
    new['provenance']={'method':'native-corner-plan-uniform-normalization' if e['view']=='top' else 'native-corner-plan-inferred-underside','source_image':source['source_image'],'source_sha256':source['source_sha256'],'input_raster_path':e['source_plan_path'],'input_raster_sha256':e['source_plan_sha256'],'alpha_threshold':32,'source_alpha_bbox':e['source_alpha_bbox'],'normalization':{'scale':e['uniform_scale'],'resampling':'nearest','transform':e.get('transform'),'frame_size':[256,256],'anchor_px':[128,128],'normalized_size':e['normalized_size'],'distortion':'none; uniform scale'},'target_span_px':e['target_span_px'],'notes':'Native hybrid map icon encodes the horizontal L wall footprint. TOP is uniformly normalized; BOTTOM is inferred by a 180-degree rotation to preserve that footprint. Hidden underside surfaces are not claimed as recovered pixels.'}
   else:
    new['provenance']={'method':'accepted-family-broad-wall-face-alias','source_image':source['source_image'],'source_sha256':source['source_sha256'],'derived_from_asset_id':e['derived_from_asset_id'],'derived_from_image_sha256':e['derived_from_sha256'],'retained_alias_png':e['candidate_path'],'alias_reason':'Clean current-PASS same-family broad wall face supplies a constant-height corner wing elevation without importing an unrelated fixture. The corner footprint remains in the preserved/native TOP/BOTTOM. This is inferred illustrative art, not recovered hidden geometry.','normalization':{'scale':1.0,'resampling':'none; exact approved family wall PNG alias','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none'}}
   new['symmetry_declaration']={'views':['front','right','left','rear'],'basis':'same-family plain material on orthogonal corner wall wings','reason':'Source lacks supported distinct fixture differences across these broad wall faces; matching broad wall surfaces are used symmetrically.'}
   md=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(md).hexdigest();snap='reusable/views-additional/prebuilt/replay-sidecars-corner-wall-aliases-clean-v2/'+aid+'.json';atomic(safe(BOOK,snap),md);old=entries.get(aid);base=old['base_sha256'] if old else before;prepared.append((aid,a,new,cand,live,mdst,before,base,md,mh,snap,e))
 for aid,a,new,cand,live,mdst,before,base,md,mh,snap,e in prepared:
  atomic(live,cand.read_bytes());atomic(mdst,md);assets[aid].clear();assets[aid].update(new);entries[aid]={'asset_id':aid,'image_path':a['image']['path'],'candidate_path':e['candidate_path'],'candidate_sha256':sha(cand),'base_sha256':base,'final_sha256':sha(cand),'metadata_path':a['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':before,'superseded_installed_sha256':before}
 touched={s['object_id'] for s in SPEC['sets']}
 for vs in idx['view_sets']:
  if vs['object_id'] in touched:vs['complete']=False;vs['notes']='Clean same-family broad corner faces and source-derived cemetery plans installed; awaiting independent current-hash review.'
 changed={p[0] for p in prepared};order=[e['asset_id'] for e in rec['entries'] if e['asset_id'] not in changed]+[p[0] for p in prepared];rec['entries']=[entries[k] for k in order]
 atomic(RECIPE,(json.dumps(rec,indent=2)+'\n').encode());atomic(INDEX,(json.dumps(idx,indent=2)+'\n').encode());print(json.dumps({'views':len(prepared),'sets':len(touched),'recipe_entries':len(rec['entries'])},indent=2))
if __name__=='__main__':main()
