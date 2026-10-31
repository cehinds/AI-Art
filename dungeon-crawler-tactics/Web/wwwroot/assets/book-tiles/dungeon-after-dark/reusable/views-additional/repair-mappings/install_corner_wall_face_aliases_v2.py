"""Install source-specific aliases from approved matching-family wall faces."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
OUT=Path(__file__).resolve().parent.parent;BOOK=OUT.parent.parent;SPEC=json.loads((OUT/'candidates/corner-wall-face-aliases-v2.json').read_text());INDEX=OUT/'set-index.json';RECIPE=OUT/'repair-mappings/replay-installed-dark-repairs-v2.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,b):p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(b);os.replace(t,p)
def main():
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};rec=json.loads(RECIPE.read_text());existing={e['asset_id']:e for e in rec['entries']};prepared=[]
 for s in SPEC['sets']:
  oid=s['object_id'];source=safe(BOOK,s['source_image']);assert sha(source)==s['source_sha256']
  for e in s['views']:
   aid=e['asset_id'];a=assets[aid];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);cand=safe(OUT,e['candidate_path']);before=sha(dst)
   assert before==e['base_sha256'] and a['image']['sha256']==before and sha(cand)==e['candidate_sha256'],(aid,'current/candidate hash guard')
   new=json.loads(json.dumps(a));im=Image.open(cand).convert('RGBA');new['image'].update({'width':im.width,'height':im.height,'sha256':sha(cand),'rgba_sha256':rgba(cand)})
   new.setdefault('provenance_history',[]).append({'candidate_id':SPEC['candidate_id']+':'+aid,'previous_provenance':new.get('provenance',{}),'previous_image_sha256':before})
   new['provenance']={'method':'accepted-family-plain-wall-face-alias','source_image':s['source_image'],'source_sha256':s['source_sha256'],'derived_from_asset_id':e['derived_from_asset_id'],'derived_from_image_sha256':e['derived_from_sha256'],'retained_alias_png':e['candidate_path'],'alias_reason':'A plain broad wall face from the current-PASS matching family supplies the corner wing elevation; distinctive fixtures are retained only on the wing supported by the corner’s own source motif. The L footprint remains in the unmodified TOP/BOTTOM. This is inferred illustrative art, not recovered hidden geometry.','normalization':{'scale':1.0,'resampling':'none; exact retained approved PNG alias','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none'},'notes':'Material/cap/height derive from the matching family. No unrelated banner, lantern, porthole, or pipe motif is introduced.'}
   mdata=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(mdata).hexdigest();snaprel='reusable/views-additional/prebuilt/replay-sidecars-corner-wall-face-aliases-v2/'+aid+'.json';atomic(safe(BOOK,snaprel),mdata)
   prepared.append((aid,a,new,cand,dst,mdst,before,mdata,mh,snaprel,e))
 for aid,a,new,cand,dst,mdst,before,mdata,mh,snaprel,e in prepared:
  atomic(dst,cand.read_bytes());atomic(mdst,mdata);assets[aid].clear();assets[aid].update(new);existing[aid]={'asset_id':aid,'image_path':a['image']['path'],'candidate_path':e['candidate_path'],'candidate_sha256':e['candidate_sha256'],'base_sha256':before,'final_sha256':e['candidate_sha256'],'metadata_path':a['metadata_path'],'metadata_snapshot_path':snaprel,'metadata_sha256':mh,'live_before_install_sha256':before,'superseded_installed_sha256':before}
 # Record repeated broad elevations only where they are exact symmetric plain material faces.
 for s in SPEC['sets']:
  oid=s['object_id'];views={e['view']:e for e in s['views']};identical_groups={}
  for e in s['views']:identical_groups.setdefault(e['candidate_sha256'],[]).append(e['view'])
  for group in identical_groups.values():
   if len(group)>1:
    for v in group:assets[oid+'.'+v]['symmetry_declaration']={'views':group,'basis':'matching-family plain wall material and symmetric corner wings','reason':'The target source provides no supported directional fixture for these broad wing faces; matching plain wall pixels are reused symmetrically rather than inventing distinct hidden surfaces.'}
 for vs in idx['view_sets']:
  if any(vs['object_id']==s['object_id'] for s in SPEC['sets']):vs['complete']=False;vs['notes']='Four broad elevations replaced with source-specific matching-family wall faces; awaiting independent current-hash source-plus-six review.'
 changed={p[0] for p in prepared};order=[e['asset_id'] for e in rec['entries'] if e['asset_id'] not in changed]+[p[0] for p in prepared];rec['entries']=[existing[k] for k in order]
 atomic(RECIPE,(json.dumps(rec,indent=2)+'\n').encode());atomic(INDEX,(json.dumps(idx,indent=2)+'\n').encode());print(json.dumps({'views':len(prepared),'sets':len(SPEC['sets']),'recipe_entries':len(rec['entries'])},indent=2))
if __name__=='__main__':main()
