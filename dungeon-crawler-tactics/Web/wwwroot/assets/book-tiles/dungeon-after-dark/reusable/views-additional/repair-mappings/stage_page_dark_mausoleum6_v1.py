"""Stage candidate-only six mausoleum/doorway plane repairs with per-object hash guards."""
import json,hashlib,shutil,pathlib,copy
from PIL import Image,ImageDraw
OUT=pathlib.Path(__file__).resolve().parents[1];PACK=OUT.parent.parent
HANDOFF=pathlib.Path('/workspace/scratch/page-dark-future-six-mausoleum-handoff-20261026.json')
CDIR=OUT/'candidates/page-dark-next-six-mausoleum-v1'; IMG=CDIR/'images';RAW=CDIR/'raw';PROMPT=CDIR/'prompts'
for p in (IMG,RAW,PROMPT):p.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def safe(path):
 p=pathlib.Path(path);p=p if p.is_absolute() else PACK/p
 p=p.resolve();p.relative_to(PACK.resolve());return p
def rel(p):return pathlib.Path(p).resolve().relative_to(PACK.resolve()).as_posix()
def rgba(p):return Image.open(p).convert('RGBA')
def saveim(im,p):im.save(p,format='PNG',optimize=False)
def normalize_generated(raw, dest):
 im=rgba(raw); alpha=im.getchannel('A'); bbox=alpha.getbbox()
 if not bbox:raise ValueError('transparent image')
 crop=im.crop(bbox); w,h=crop.size;scale=min(184/w,184/h,1.0)
 nw=max(1,round(w*scale));nh=max(1,round(h*scale))
 crop=crop.resize((nw,nh),Image.Resampling.NEAREST)
 frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop,((256-nw)//2,(256-nh)//2));saveim(frame,dest)
 return {'source_bbox_px':list(bbox),'source_crop_size_px':[w,h],'uniform_scale':scale,'output_bbox_px':[(256-nw)//2,(256-nh)//2,nw,nh],'resampling':'nearest','anchor_px':[128,128]}
def transform(src,dest,op):
 im=rgba(src)
 if op=='rotate180':im=im.transpose(Image.Transpose.ROTATE_180)
 elif op=='mirror_x':im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 elif op=='copy':pass
 else:raise ValueError(op)
 saveim(im,dest);return {'operation':op,'uniform_scale':1.0,'anchor_px':[128,128]}
def main():
 hand=json.loads(HANDOFF.read_text());proof={'handoff_path':'/workspace/scratch/page-dark-future-six-mausoleum-handoff-20261026.json','handoff_sha256':sha(HANDOFF),'objects':[]}
 objs={}
 for o in hand['objects']:
  cur={v:{'path':rel(e['path']),'sha256':e['sha256']} for v,e in o['views'].items()}
  for v,e in o['views'].items(): assert sha(safe(e['path']))==e['sha256'],(o['object_id'],v)
  src={'path':rel(o['source']['path']),'sha256':o['source']['sha256']};assert sha(safe(src['path']))==src['sha256']
  objs[o['object_id']]={'source':src,'base_six':cur,'affected_views':o['affected_views'],'notes':o['notes']}
  proof['objects'].append({'object_id':o['object_id'],'source':src,'base_six':cur,'affected_views':o['affected_views'],'notes':o['notes']})
 candidates=[]
 def add(oid,v,sourcefile,method,normalization,generated=None,derived=None,notes=''):
  aid=f'{oid}.{v}'; dest=IMG/(aid+'.candidate.png')
  if method in ('copy','rotate180','mirror_x'): transform(sourcefile,dest,method)
  else: raise ValueError(method)
  obj=objs[oid]; c={'object_id':oid,'asset_id':aid,'view':v,'candidate_path':rel(dest),'candidate_sha256':sha(dest),'dimensions_px':list(rgba(dest).size),'anchor_px':[128,128],'source_path':obj['source']['path'],'source_sha256':obj['source']['sha256'],'baseline_six':copy.deepcopy(obj['base_six']),'normalization':normalization,'notes':notes}
  if generated:
   c.update(generated)
  if derived:c['derived_from']=derived
  candidates.append(c);return c
 # north wall top: mirror-symmetric cap/underside strip
 oid='ghost-cemetery-white-mausoleum-masonry-north-wall'; donor=PACK/objs[oid]['base_six']['bottom']['path']
 add(oid,'top',donor,'rotate180',{'operation':'rotate180','uniform_scale':1.0,'anchor_px':[128,128]},derived={'view':'bottom','source_sha256':objs[oid]['base_six']['bottom']['sha256']},notes='Inferred symmetric reverse cap; retain accepted thin long-X strip geometry.')
 # square caps: shallow cardinal elevations from accepted side profiles; square plan undersides from TOP
 for oid in ['ghost-cemetery-white-mausoleum-masonry-north-cap','ghost-cemetery-white-mausoleum-masonry-west-cap']:
  o=objs[oid]
  add(oid,'front',PACK/o['base_six']['right']['path'],'copy',{'operation':'copy','uniform_scale':1.0,'anchor_px':[128,128]},derived={'view':'right','source_sha256':o['base_six']['right']['sha256']},notes='Inferred same-size square cap face; repeat unmarked block face.')
  add(oid,'rear',PACK/o['base_six']['left']['path'],'copy',{'operation':'copy','uniform_scale':1.0,'anchor_px':[128,128]},derived={'view':'left','source_sha256':o['base_six']['left']['sha256']},notes='Inferred symmetric opposite cap face; preserve square cap height.')
  add(oid,'bottom',PACK/o['base_six']['top']['path'],'rotate180',{'operation':'rotate180','uniform_scale':1.0,'anchor_px':[128,128]},derived={'view':'top','source_sha256':o['base_six']['top']['sha256']},notes='Inferred opaque same-footprint underside; square plan symmetry.')
 # Two generated doorway top plans and their exact opposite-camera aliases.
 generated_specs=[
 ('ghost-cemetery-white-mausoleum-masonry-open-doorway','top','exec-adb4b72a-26e3-46aa-9d89-09da12acf254.png','orthographic_top_open_mausoleum_doorway.txt','Open doorway overhead lintel and jamb caps; the passage remains transparent. Preserve pale mossy masonry and source-supported torches.'),
 ('ghost-cemetery-white-mausoleum-masonry-closed-doorway','top','exec-89d5cb01-a4f4-4a58-ad58-4f6a1be12935.png','orthographic_top_closed_mausoleum_doorway.txt','Closed doorway overhead lintel/cap strips and only the thin door edge; retain closed state and pale mossy masonry.')]
 prompts={
 'orthographic_top_open_mausoleum_doorway.txt':"Create ONE orthographic TOP-DOWN principal view sprite for the supplied open pale mausoleum doorway. Reference image 1 is the exact source identity/material; reference image 2 shows its current frontal silhouette and two side torches. Camera looks straight down along world Z, no perspective, no isometric tilt. Show only the shallow footprint of the stone lintel and the compact top caps of its two jambs, a narrow horizontal assembly across world X with very little depth along world Y. The open passage between jambs MUST remain transparent empty space; do not fill it with stone, dark floor, a facade, an arch front, or frontal-looking columns. Preserve exactly two side torches if their source-supported footprints appear at the jamb ends, but show only tiny top footprints/flames, not upright fire bodies. Keep pale weathered masonry, dark trim, green moss, black outline, matching source. Center the complete shallow silhouette on transparent 256x256 canvas. Isolated view art, no labels, no border, no contact sheet.",
 'orthographic_top_closed_mausoleum_doorway.txt':"Create ONE orthographic TOP-DOWN principal view sprite for the supplied CLOSED pale mausoleum doorway with its dark double door. Reference image 1 is the exact source identity/material; reference image 2 shows its current frontal silhouette and two side torches. Camera looks straight down along world Z, no perspective, no isometric tilt. Show only the shallow footprint of the stone lintel and compact top caps of its two jambs, a narrow horizontal assembly across world X with very little depth along world Y. The closed door contributes only a thin top edge/door slab line within that shallow footprint, not the full door face. Preserve closed state. Do not show the facade, arch face, tall columns, broad square panel or full door rectangle. Keep pale weathered masonry, dark trim, green moss, black outline, matching source. Center the complete shallow silhouette on transparent 256x256 canvas. Isolated view art, no labels, no border, no contact sheet."}
 for oid,v,rawname,promptname,notes in generated_specs:
  raw_src=pathlib.Path('/workspace/generated_images')/rawname;assert raw_src.is_file()
  rawdst=RAW/(oid+'.top.raw.png');shutil.copyfile(raw_src,rawdst)
  prompt=prompts[promptname];pp=PROMPT/promptname;pp.write_text(prompt+'\n')
  # normalize actual raw response, track its request-specific output mapping.
  dest=IMG/(oid+'.top.candidate.png');norm=normalize_generated(rawdst,dest)
  obj=objs[oid]; candidates.append({'object_id':oid,'asset_id':oid+'.top','view':'top','candidate_path':rel(dest),'candidate_sha256':sha(dest),'dimensions_px':[256,256],'anchor_px':[128,128],'source_path':obj['source']['path'],'source_sha256':obj['source']['sha256'],'baseline_six':copy.deepcopy(obj['base_six']),'raw_path':rel(rawdst),'raw_sha256':sha(rawdst),'prompt_path':rel(pp),'prompt_sha256':sha(pp),'request_id':'imagegen-'+oid+'.top-20261026','references':[obj['source']['path'],obj['base_six']['front']['path']],'normalization':norm,'notes':notes})
  add(oid,'bottom',dest,'rotate180',{'operation':'rotate180','uniform_scale':1.0,'anchor_px':[128,128]},derived={'view':'top','source_sha256':sha(dest)},notes='Declared inferred rotational symmetry of the shallow lintel footprint; open/closed state retained.')
 # Havana source-faithful transparent FRONT, reflected REAR, and lintel TOP from accepted BOTTOM.
 oid='ghost-havana-weathered-stucco-open-doorway';o=objs[oid]
 src=PACK/o['source']['path']
 add(oid,'front',src,'copy',{'operation':'copy','uniform_scale':1.0,'anchor_px':[128,128]},derived={'view':'canonical_source','source_sha256':o['source']['sha256']},notes='Reuse canonical native sprite to preserve its alpha-zero open passage.')
 add(oid,'rear',src,'mirror_x',{'operation':'horizontal_mirror','uniform_scale':1.0,'anchor_px':[128,128]},derived={'view':'canonical_source','source_sha256':o['source']['sha256']},notes='Inferred opposite-face symmetry; preserve transparent opening and native stucco/teal trim.')
 add(oid,'top',PACK/o['base_six']['bottom']['path'],'rotate180',{'operation':'rotate180','uniform_scale':1.0,'anchor_px':[128,128]},derived={'view':'bottom','source_sha256':o['base_six']['bottom']['sha256']},notes='Inferred same narrow lintel footprint; retain accepted opaque bottom.')
 # Build canonical source+six+candidate contact. Each row starts with source and six guarded current base views, then proposed views.
 from PIL import ImageOps
 contact_rows=[]
 for oid,obj in objs.items():
  labels=['SOURCE','front','top','right','left','bottom','rear']
  row=[]
  for label in labels:
   rec={'path':obj['source']['path'],'sha256':obj['source']['sha256']} if label=='SOURCE' else obj['base_six'][label]
   p=PACK/rec['path'];im=rgba(p);im.thumbnail((170,170),Image.Resampling.NEAREST)
   t=Image.new('RGBA',(190,220),(31,34,39,255));t.alpha_composite(im,((190-im.width)//2,8+(170-im.height)//2));ImageDraw.Draw(t).text((5,195),label,fill='white');row.append((label,t,rec))
  for c in [c for c in candidates if c['object_id']==oid]:
   p=PACK/c['candidate_path'];im=rgba(p);im.thumbnail((170,170),Image.Resampling.NEAREST)
   t=Image.new('RGBA',(190,220),(45,30,30,255));t.alpha_composite(im,((190-im.width)//2,8+(170-im.height)//2));ImageDraw.Draw(t).text((5,195),'NEW '+c['view'],fill='white');row.append(('NEW '+c['view'],t,{'path':c['candidate_path'],'sha256':c['candidate_sha256']}))
  contact_rows.append((oid,row))
 width=max(len(r) for _,r in contact_rows)*190; contact=Image.new('RGBA',(width,220*len(contact_rows)),(14,17,22,255)); contact_meta=[]
 for ri,(oid,row) in enumerate(contact_rows):
  cells=[]
  for ci,(label,t,rec) in enumerate(row):contact.alpha_composite(t,(ci*190,ri*220));cells.append({'label':label,**rec})
  contact_meta.append({'object_id':oid,'cells':cells})
 contactpath=CDIR/'mausoleum-source-six-candidates.png';contact.save(contactpath)
 manifest={'status':'candidate-only; Page review requested','scope':'six mausoleum/doorway objects; 14 scoped directions','handoff_path':'/workspace/scratch/page-dark-future-six-mausoleum-handoff-20261026.json','handoff_sha256':sha(HANDOFF),'base_contact_proof':'reusable/views-additional/candidates/page-dark-next-six-mausoleum-v1/mausoleum-source-six-base-proof.json','base_contact_sha256':sha(CDIR/'mausoleum-source-six-base-proof.json'),'candidate_contact_path':rel(contactpath),'candidate_contact_sha256':sha(contactpath),'objects':[{'object_id':oid,'source':o['source'],'base_six':o['base_six'],'affected_views':o['affected_views'],'notes':o['notes']} for oid,o in objs.items()],'candidates':candidates,'rules':['Source plus all six live hashes verified before staging.','Candidate paths and provenance are pack-relative.','Generated top projections were normalized isotropically; aliases state their symmetry explicitly.','Canonical Havana source pixels are retained for its alpha-zero open passage.']}
 mp=CDIR/'mausoleum6-candidate-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
 proof={'manifest_path':rel(mp),'manifest_sha256':sha(mp),'contact_path':rel(contactpath),'contact_sha256':sha(contactpath),'rows':contact_meta,'handoff_sha256':sha(HANDOFF)};(CDIR/'mausoleum6-candidate-contact-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
 reqmap={'requests':[{'request_id':'imagegen-'+oid+'.top-20261026','object_id':oid,'view':'top','raw_path':c['raw_path'],'raw_sha256':c['raw_sha256'],'prompt_path':c['prompt_path'],'prompt_sha256':c['prompt_sha256'],'candidate_path':c['candidate_path'],'candidate_sha256':c['candidate_sha256']} for c in candidates if c.get('raw_path')]};(CDIR/'request-result-mapping.json').write_text(json.dumps(reqmap,indent=2)+'\n')
 print(json.dumps({'manifest':rel(mp),'manifest_sha256':sha(mp),'contact':rel(contactpath),'contact_sha256':sha(contactpath),'candidate_count':len(candidates),'rows':len(contact_rows)},indent=2))
if __name__=='__main__':main()
