"""Losslessly replay approved 250x250 outer-corner art and its true canvas metadata."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;INDEX=OUT/'set-index.json';OID='hunting-shrines-village-stone-outer-corner';RETAIN=OUT/'prebuilt/retained-corner-250-2026-10-26'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};ss=[s for s in idx['view_sets'] if s['object_id']==OID];assert len(ss)==1
prepared=[]
for view,aid in ss[0]['views'].items():
 a=assets[aid];out=safe(BOOK,a['image']['path']);meta=safe(BOOK,a['metadata_path']);ret=RETAIN/f'{aid}.png';expected=a['image']['sha256']
 assert ret.exists() and sha(ret)==expected,f'{aid}: retained image changed'
 for p in (out,):
  assert not p.exists() or sha(p)==expected,f'{aid}: unexpected current image hash'
 im=Image.open(ret).convert('RGBA');assert im.size==(250,250),f'{aid}: unexpected retained dimensions'
 prepared.append((aid,a,out,meta,ret,im))
# All inputs are hash guarded before any writes.
for aid,a,out,meta,ret,im in prepared:
 if not out.exists():
  tmp=out.with_name(out.name+'.tmp');tmp.write_bytes(ret.read_bytes());os.replace(tmp,out)
 oldmeta=json.loads(meta.read_text()) if meta.exists() else dict(a);hist=a.setdefault('provenance_history',[])
 marker='retained-corner-250-exact-replay'
 if not any(h.get('candidate_id')==marker for h in hist):hist.append({'candidate_id':marker,'previous_provenance':a.get('provenance',{}),'previous_anchor_px':a.get('anchor_px')})
 a['image']['width']=im.width;a['image']['height']=im.height;a['image']['sha256']=sha(out);a['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest();a['anchor_px']=[125,125]
 a['provenance']={'method':'retained-approved-png-exact-copy','source_image':a['source']['source_image'],'source_sha256':a['source']['source_sha256'],'retained_png':str(ret.relative_to(BOOK)),'retained_png_sha256':sha(ret),'normalization':{'frame_size':[250,250],'anchor_px':[125,125],'resampling':'none; byte-exact retained PNG','distortion':'none'},'rebuild_command':'python3 reusable/views-additional/repair-mappings/replay_outer_corner_250.py','notes':'Existing independently approved art is retained byte-for-byte. Canvas is 250x250; hidden geometry remains illustrative.'}
 meta.parent.mkdir(parents=True,exist_ok=True);tmp=meta.with_name(meta.name+'.tmp');tmp.write_text(json.dumps(a,indent=2)+'\n');os.replace(tmp,meta)
tmp=INDEX.with_name(INDEX.name+'.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
print(json.dumps({'object_id':OID,'views_replayed':len(prepared),'canvas_size':[250,250]},indent=2))
