"""Install six clean same-family glass/metal corner view batches."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
OUT=Path(__file__).resolve().parent.parent;BOOK=OUT.parent.parent;SPEC=json.loads((OUT/'candidates/corner-wall-aliases-clean-v1.json').read_text());INDEX=OUT/'set-index.json';RECIPE=OUT/'repair-mappings/replay-installed-dark-repairs-v2.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,b):p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(b);os.replace(t,p)
def main():
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};rec=json.loads(RECIPE.read_text());entries={e['asset_id']:e for e in rec['entries']};prep=[]
 for s in SPEC['sets']:
  oid=s['object_id'];source=assets[oid+'.front']['source'];srcpath=safe(BOOK,source['source_image']);assert sha(srcpath)==source['source_sha256']
  for e in s['views']:
   if e.get('preserved'):continue
   aid=e['asset_id'];a=assets[aid];live=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);before=sha(live);assert before==e['base_sha256'] and a['image']['sha256']==before
   candidate=safe(OUT,e['candidate_path']);assert sha(candidate)==e['candidate_sha256']
   if e.get('derived_from_asset_id'):
    donor=e['derived_from_asset_id'];assert sha(safe(BOOK,assets[donor]['image']['path']))==e['derived_from_sha256']
   new=json.loads(json.dumps(a));im=Image.open(candidate).convert('RGBA');new['image'].update({'width':im.width,'height':im.height,'sha256':sha(candidate),'rgba_sha256':rgba(candidate)});new.setdefault('provenance_history',[]).append({'candidate_id':SPEC['candidate_id']+':'+aid,'previous_provenance':new.get('provenance',{}),'previous_image_sha256':before})
   if e.get('source_plan_path'):
    norm={'scale':e['uniform_scale'],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'normalized_size':e['normalized_size'],'distortion':'none; uniform scale'};prov={'method':'native-corner-plan-uniform-normalization','source_image':source['source_image'],'source_sha256':source['source_sha256'],'input_raster_path':e['source_plan_path'],'input_raster_sha256':e['source_plan_sha256'],'alpha_threshold':32,'source_alpha_bbox':e['source_alpha_bbox'],'normalization':norm,'notes':'Native hybrid map icon directly encodes the horizontal L corner footprint; normalized uniformly for TOP. Hidden bottom construction is inferred from this footprint.'}
    if e['view']=='bottom':prov.update({'method':'source-footprint-bottom-mirror','derived_from_asset_id':e.get('derived_from_asset_id'),'derived_from_sha256':e.get('derived_from_sha256'),'transform':e.get('transform'),'notes':'Inferred opaque underside preserving the exact L footprint of the native source plan; mirrored to preserve canonical footprint orientation.'})
   else:
    prov={'method':'accepted-family-broad-wall-face-alias','source_image':source['source_image'],'source_sha256':source['source_sha256'],'derived_from_asset_id':e['derived_from_asset_id'],'derived_from_image_sha256':e['derived_from_sha256'],'retained_alias_png':e['candidate_path'],'alias_reason':'Clean broad wall face from current-PASS same-family wall set supplies the corner wing elevation; target source has no added fixture motif on these wings. L plans remain source-shaped and are preserved except submarine native plan recovery. Inferred illustrative art, not recovered hidden pixels.','normalization':{'scale':1.0,'resampling':'none; exact approved wall PNG alias','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none'}}
   new['provenance']=prov
   new['symmetry_declaration']={'views':['front','right','left','rear'],'basis':'plain same-family broad glass/metal wall panels on orthogonal corner wings','reason':'The source corner supports a symmetric material panel on each wall wing; identical broad projections avoid unsupported directional ornament differences.'}
   md=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(md).hexdigest();snap='reusable/views-additional/prebuilt/replay-sidecars-corner-wall-aliases-clean-v1/'+aid+'.json';atomic(safe(BOOK,snap),md)
   prior=entries.get(aid);base=prior['base_sha256'] if prior else before;prep.append((aid,a,new,candidate,live,mdst,before,base,md,mh,snap,e,prior))
 for aid,a,new,candidate,live,mdst,before,base,md,mh,snap,e,prior in prep:
  atomic(live,candidate.read_bytes());atomic(mdst,md);assets[aid].clear();assets[aid].update(new);entries[aid]={'asset_id':aid,'image_path':a['image']['path'],'candidate_path':e['candidate_path'],'candidate_sha256':sha(candidate),'base_sha256':base,'final_sha256':sha(candidate),'metadata_path':a['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':before,'superseded_installed_sha256':before}
 touched={s['object_id'] for s in SPEC['sets']}
 for vs in idx['view_sets']:
  if vs['object_id'] in touched:vs['complete']=False;vs['notes']='Same-family broad elevations and source-derived submarine plans installed; awaiting current-hash source-plus-six review.'
 changed={p[0] for p in prep};order=[e['asset_id'] for e in rec['entries'] if e['asset_id'] not in changed]+[p[0] for p in prep];rec['entries']=[entries[k] for k in order]
 atomic(RECIPE,(json.dumps(rec,indent=2)+'\n').encode());atomic(INDEX,(json.dumps(idx,indent=2)+'\n').encode());print(json.dumps({'installed_views':len(prep),'sets':len(touched),'recipe_entries':len(rec['entries'])},indent=2))
if __name__=='__main__':main()
