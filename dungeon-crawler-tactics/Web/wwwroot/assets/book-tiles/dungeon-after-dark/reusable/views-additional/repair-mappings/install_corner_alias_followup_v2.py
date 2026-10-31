"""Install Airship plan and Shrines broad ivy face corrections."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
OUT=Path(__file__).resolve().parent.parent;BOOK=OUT.parent.parent;SPEC=json.loads((OUT/'candidates/corner-alias-followup-v2.json').read_text());INDEX=OUT/'set-index.json';RECIPE=OUT/'repair-mappings/replay-installed-dark-repairs-v2.json'
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
   aid=e['asset_id'];a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);cand=safe(OUT,e['candidate_path']);before=sha(dst);assert before==e['base_sha256'] and a['image']['sha256']==before and sha(cand)==e['candidate_sha256'],aid
   new=json.loads(json.dumps(a));im=Image.open(cand).convert('RGBA');new['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)});new.setdefault('provenance_history',[]).append({'candidate_id':SPEC['candidate_id']+':'+aid,'previous_provenance':new.get('provenance',{}),'previous_image_sha256':before})
   new['provenance']={'method':'exact-symmetric-view-alias','source_image':source['source_image'],'source_sha256':source['source_sha256'],'alias_from_asset_id':e['derived_from_asset_id'],'alias_from_sha256':e['derived_from_sha256'],'retained_alias_png':e['candidate_path'],'alias_reason':e['transform'],'normalization':{'scale':1.0,'resampling':'none' if e['view'] in ('right','left') else 'nearest horizontal mirror','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none'},'notes':'Inferred illustrative geometry sourced from the matching target-family footprint or accepted broad ivy face; hidden surfaces are not claimed as recovered pixels.'}
   if e['view'] in ('right','left'):new['symmetry_declaration']={'views':['front','right','left','rear'],'basis':'matching source-family ivy wall faces and equal-height full-span corner wings','reason':'The native source does not support distinct ornament differences between orthogonal broad stone wings; accepted front/rear faces are reused symmetrically with the same ivy and wall height.'}
   md=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(md).hexdigest();snap='reusable/views-additional/prebuilt/replay-sidecars-corner-alias-followup-v2/'+aid+'.json';atomic(safe(BOOK,snap),md);prep.append((aid,a,new,cand,dst,mdst,before,md,mh,snap,e))
 for aid,a,new,cand,dst,mdst,before,md,mh,snap,e in prep:
  atomic(dst,cand.read_bytes());atomic(mdst,md);assets[aid].clear();assets[aid].update(new);entries[aid]={'asset_id':aid,'image_path':a['image']['path'],'candidate_path':e['candidate_path'],'candidate_sha256':e['candidate_sha256'],'base_sha256':before,'final_sha256':e['candidate_sha256'],'metadata_path':a['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':before,'superseded_installed_sha256':before}
 touched={s['object_id'] for s in SPEC['sets']}
 for vs in idx['view_sets']:
  if vs['object_id'] in touched:vs['complete']=False;vs['notes']='Targeted source-footprint/broad-face symmetry corrections installed; awaiting current-hash review.'
 changed={p[0] for p in prep};order=[e['asset_id'] for e in rec['entries'] if e['asset_id'] not in changed]+[p[0] for p in prep];rec['entries']=[entries[k] for k in order]
 atomic(RECIPE,(json.dumps(rec,indent=2)+'\n').encode());atomic(INDEX,(json.dumps(idx,indent=2)+'\n').encode());print(json.dumps({'views':len(prep),'sets':len(touched),'recipe_entries':len(rec['entries'])},indent=2))
if __name__=='__main__':main()
