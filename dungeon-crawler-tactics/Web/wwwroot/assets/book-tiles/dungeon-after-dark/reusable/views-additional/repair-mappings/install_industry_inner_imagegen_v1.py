"""Install reviewed imagegen right/left face art for the Industry inner corner."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
OUT=Path(__file__).resolve().parent.parent;BOOK=OUT.parent.parent;OID='industry-menagerie-soot-stained-brick-inner-corner';INDEX=OUT/'set-index.json';RECIPE=OUT/'repair-mappings/replay-installed-dark-repairs-v2.json';MAN=OUT/'repair-mappings/industry-inner-imagegen-v1.json';CAND=OUT/'candidates/industry-inner-imagegen-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
def atomic(p,b):p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(b);os.replace(t,p)
def main():
 meta=json.loads(MAN.read_text());assert meta['request_id']=='exec-dbd02bcc-003c-43c3-a677-827e01fb8494';rawrel=meta['retained_raw_path'];raw=safe(OUT,rawrel);assert sha(raw)==meta['raw_sha256'];prompt=safe(OUT,meta['prompt_path']);assert sha(prompt)==meta['prompt_sha256']
 idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};recipe=json.loads(RECIPE.read_text());entries={e['asset_id']:e for e in recipe['entries']};prep=[]
 for v in ['right','left']:
  aid=OID+'.'+v;a=assets[aid];live=safe(BOOK,a['image']['path']);old=entries[aid];candidate=CAND/(aid+'.png');assert sha(live)==old['final_sha256'] and sha(candidate)==meta['output_'+v+'_sha256'];
  # Preserve the immediately superseded art as a pack-local recovery input.
  previous_rel='reusable/views-additional/prebuilt/industry-inner-imagegen-v1-before/'+aid+'.png';previous=safe(BOOK,previous_rel);atomic(previous,live.read_bytes());assert sha(previous)==sha(live)
  new=json.loads(json.dumps(a));im=Image.open(candidate).convert('RGBA');new['image'].update({'width':im.width,'height':im.height,'sha256':sha(candidate),'rgba_sha256':rgba(candidate)});new.setdefault('provenance_history',[]).append({'candidate_id':'industry-inner-imagegen-v1:'+aid,'previous_provenance':new.get('provenance',{}),'previous_image_sha256':sha(live)})
  refs=[{'path':r['path'],'sha256':r['sha256']} for r in meta['references'].values()]
  new['provenance']={'method':'imagegen-edited-orthographic-wall-face','source_image':a['source']['source_image'],'source_sha256':a['source']['source_sha256'],'raw_atlas':'reusable/views-additional/'+rawrel,'raw_atlas_sha256':meta['raw_sha256'],'prompt_path':'reusable/views-additional/'+meta['prompt_path'],'prompt_sha256':meta['prompt_sha256'],'generator_request_id':meta['request_id'],'reference_images':refs,'source_rect':{'alpha_threshold':meta['threshold_alpha'],'alpha_bounds':meta['raw_alpha_bbox'],'component_count':1},'normalization':{'scale':meta['uniform_scale'],'offset_px':[128-meta['normalized_size'][0]//2,128-meta['normalized_size'][1]//2],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'normalized_size':meta['normalized_size'],'distortion':'none; uniform scale'},'notes':'The generated right elevation preserves the source-specific single vent and pipe within the accepted common-height 2:1 wall silhouette. LEFT is an exact horizontal mirror of RIGHT. No extra fixtures are introduced; surfaces absent from the source are inferred.' if v=='right' else 'Exact horizontal mirror of the generated RIGHT elevation to preserve the single vent and pipe identity in the opposite camera; hidden surface detail is inferred.'}
  new['symmetry_declaration']={'views':['right','left'],'basis':'the Y-axis inner-corner wall face is mirrored across opposite horizontal cameras','reason':'The pipe/window pair is retained as one matching fixture set; LEFT mirrors RIGHT without changing count, height, or span.'}
  md=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(md).hexdigest();snap='reusable/views-additional/prebuilt/replay-sidecars-industry-inner-imagegen-v1/'+aid+'.json';atomic(safe(BOOK,snap),md)
  prep.append((aid,a,new,candidate,live,safe(BOOK,a['metadata_path']),md,mh,snap,old,previous_rel,v))
 for aid,a,new,candidate,live,mdst,md,mh,snap,old,previous_rel,v in prep:
  atomic(live,candidate.read_bytes());atomic(mdst,md);assets[aid].clear();assets[aid].update(new);old.update({'candidate_path':candidate.relative_to(OUT).as_posix(),'candidate_sha256':sha(candidate),'final_sha256':sha(candidate),'metadata_snapshot_path':snap,'metadata_sha256':mh,'superseded_installed_sha256':old['final_sha256'],'live_before_install_sha256':old['final_sha256'],'previous_live_snapshot':previous_rel})
 for s in idx['view_sets']:
  if s['object_id']==OID:s['complete']=False;s['notes']='Industry inner-corner RIGHT/LEFT source-specific pipe/window art installed at accepted common wall height; awaiting whole-set current-hash review.'
 atomic(RECIPE,(json.dumps(recipe,indent=2)+'\n').encode());atomic(INDEX,(json.dumps(idx,indent=2)+'\n').encode());print(json.dumps({'installed_views':len(prep),'sets':1,'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
