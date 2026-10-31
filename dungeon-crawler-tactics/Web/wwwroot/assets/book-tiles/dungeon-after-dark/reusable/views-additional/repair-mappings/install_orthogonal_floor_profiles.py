"""Alias accepted edge silhouettes across symmetric square floor elevations."""
from pathlib import Path
import hashlib,json,os,struct,shutil
from PIL import Image

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;BOOK=ROOT.parent.parent;INDEX=ROOT/'set-index.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(rel):
 p=(BOOK/rel).resolve();p.relative_to(BOOK.resolve());return p
idx=json.loads(INDEX.read_text());A={a['id']:a for a in idx['assets']};S={s['object_id']:s for s in idx['view_sets']}
families=[
 ('industry-menagerie-industrial-brick-floor','rear',['front','right','left']),
 ('industry-menagerie-cracked-industrial-brick-floor','rear',['front','right','left']),
 ('industry-menagerie-wet-industrial-brick-floor','rear',['front','right','left']),
 ('industry-menagerie-worn-industrial-brick-floor','rear',['front','right','left']),
 ('iron-stations-station-concrete-floor','left',['front','right']),
 ('iron-stations-cracked-station-concrete-floor','left',['front','right']),
 ('iron-stations-wet-station-concrete-floor','left',['front','right']),
 ('iron-stations-worn-station-concrete-floor','left',['front','right'])]
spec=[];prepared=[]
for oid,srcview,targets in families:
 assert oid in S;ss=S[oid];srcid=ss['views'][srcview];sa=A[srcid];src=safe(sa['image']['path']);srcsha=sha(src)
 for view in targets:
  aid=ss['views'][view];a=A[aid];dst=safe(a['image']['path']);mdst=safe(a['metadata_path']);snap=ROOT/'prebuilt/floor-profile-before-v1'/f'{aid}.png';snap.parent.mkdir(parents=True,exist_ok=True)
  before=sha(dst);beforemeta=sha(mdst)
  if not snap.exists():snap.write_bytes(dst.read_bytes())
  assert sha(snap)==before
  cand=ROOT/'candidates/floor-profile-aliases-v1'/f'{aid}.png';cand.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,cand)
  entry={'object_id':oid,'asset_id':aid,'view':view,'alias_from_asset_id':srcid,'alias_from_view':srcview,'source_image':sa['source']['source_image'],'source_sha256':sa['source']['source_sha256'],'alias_png_path':str(src.relative_to(BOOK)),'alias_png_sha256':srcsha,'candidate_path':str(cand.relative_to(ROOT)),'candidate_sha256':sha(cand),'before_sha256':before,'before_metadata_sha256':beforemeta,'snapshot_path':str(snap.relative_to(BOOK))}
  spec.append(entry);prepared.append((entry,a,dst,mdst,cand))
# Source and target screenshots show all seven columns with aliases labeled.
for oid,srcview,targets in families:
 ss=S[oid];src=BOOK/A[ss['views']['front']]['source']['source_image'];ims=[Image.open(src).convert('RGBA')];labels=['SOURCE']; proof={'object_id':oid,'source_image':str(src.relative_to(BOOK)),'source_sha256':sha(src),'views':{}}
 for v in ('front','top','right','left','bottom','rear'):
  a=A[ss['views'][v]];p=BOOK/a['image']['path'];im=Image.open(p).convert('RGBA');ims.append(im);labels.append(v.upper());proof['views'][v]={'asset_id':a['id'],'path':a['image']['path'],'sha256':sha(p),'status':'LIVE'}
 for e in [e for e in spec if e['object_id']==oid]:
  a=A[e['asset_id']];p=ROOT/e['candidate_path'];im=Image.open(p).convert('RGBA');ims[1+('front','top','right','left','bottom','rear').index(e['view'])]=im;labels[1+('front','top','right','left','bottom','rear').index(e['view'])]='PROPOSED '+e['view'].upper();proof['views'][e['view']]={'asset_id':e['asset_id'],'path':e['candidate_path'],'sha256':sha(p),'status':'PROPOSED'}
 from PIL import ImageDraw
 tile=272;sheet=Image.new('RGB',(tile*7,300),(238,238,238));d=ImageDraw.Draw(sheet)
 for j,(im,label) in enumerate(zip(ims,labels)):
  bg=Image.new('RGBA',(256,256),(140,140,140,255));bg.alpha_composite(im.resize((256,256),Image.Resampling.NEAREST));sheet.paste(bg.convert('RGB'),(j*tile,28));d.text((j*tile+4,6),label,fill=(0,0,0))
 cp=ROOT/'qa'/f'{oid}-floor-profile-v1-candidate-source-six.png';sheet.save(cp);proof['contact_path']=str(cp.relative_to(ROOT));proof['contact_sha256']=sha(cp);cp.with_suffix('.json').write_text(json.dumps(proof,indent=2)+'\n')
 spec[0].setdefault('_proofs',[]).append({'object_id':oid,'contact_path':str(cp.relative_to(ROOT)),'contact_sha256':sha(cp)})
(ROOT/'repair-mappings/floor-profile-aliases-v1.json').write_text(json.dumps({'recipe_id':'floor-profile-aliases-v1','entries':spec},indent=2)+'\n')
log=[]
for e,a,dst,mdst,cand in prepared:
 assert sha(dst)==e['before_sha256'] and sha(mdst)==e['before_metadata_sha256'],f"{e['asset_id']}: unexpected current bytes"
 assert sha(cand)==e['candidate_sha256'] and sha(safe(e['alias_png_path']))==e['alias_png_sha256']
 tmp=dst.with_name(dst.name+'.tmp');tmp.write_bytes(cand.read_bytes());os.replace(tmp,dst)
 im=Image.open(dst).convert('RGBA');a['image']['sha256']=sha(dst);a['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();a['anchor_px']=[128,128]
 hist=a.setdefault('provenance_history',[]);marker='floor-profile-aliases-v1:'+e['asset_id']
 if not any(h.get('candidate_id')==marker for h in hist):hist.append({'candidate_id':marker,'previous_provenance':a.get('provenance',{}),'previous_image_sha256':e['before_sha256']})
 a['provenance']={'method':'symmetric-floor-edge-view-alias','source_image':e['source_image'],'source_sha256':e['source_sha256'],'alias_from_asset_id':e['alias_from_asset_id'],'alias_from_view':e['alias_from_view'],'alias_png_path':e['alias_png_path'],'alias_png_sha256':e['alias_png_sha256'],'retained_before_png':e['snapshot_path'],'normalization':{'frame_size':list(im.size),'anchor_px':[128,128],'distortion':'none; exact symmetric-view byte alias'},'notes':'The square floor uses the same homogeneous slab edge on each horizontal side; alias does not change the source TOP plan.'}
 tmp=mdst.with_name(mdst.name+'.tmp');tmp.write_text(json.dumps(a,indent=2)+'\n');os.replace(tmp,mdst)
 log.append({'asset_id':e['asset_id'],'before_sha256':e['before_sha256'],'after_sha256':sha(dst)})
for oid,_,_ in families:
 S[oid]['complete']=False;S[oid]['notes']='Symmetric square-floor edge profiles corrected; awaiting current-hash source-plus-six review.'
tmp=INDEX.with_name(INDEX.name+'.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
(ROOT/'repair-mappings/install-floor-profile-aliases-v1.json').write_text(json.dumps({'installed':log},indent=2)+'\n')
print(json.dumps({'installed':len(log),'object_ids':[x[0] for x in families]},indent=2))
