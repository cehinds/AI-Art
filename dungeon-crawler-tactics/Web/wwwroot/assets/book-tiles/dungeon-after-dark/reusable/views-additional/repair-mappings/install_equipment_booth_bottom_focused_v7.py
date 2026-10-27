from pathlib import Path
import copy,hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;INDEX=OUT/'set-index.json';RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
MAN=OUT/'candidates/equipment-dark-last-seven-fixtures-20261026/candidate-manifest-last7-booth-bottom-v7.json';MAN_SHA='a28d3595e45700d316efc7394219fb53b8a658cdc76bd2a76593b57f496e59b0';CID='equipment-last7-booth-bottom-v7-root-approved';BEFORE=OUT/'prebuilt/equipment-last7-booth-bottom-v7-before'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):
 im=Image.open(p).convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def safe(root,p):
 q=(Path(p) if Path(p).is_absolute() else root/p).resolve();q.relative_to(root.resolve());return q
def rel(p):return Path(p).resolve().relative_to(BOOK.resolve()).as_posix()
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_bytes(data if isinstance(data,bytes) else data.encode());os.replace(t,p)
def main():
 assert sha(MAN)==MAN_SHA;m=json.loads(MAN.read_text());assert m['installer']=='views_dark_books';ix=json.loads(INDEX.read_text());recipe=json.loads(RECIPE.read_text());assets={a['id']:copy.deepcopy(a) for a in ix['assets']};sets={s['object_id']:copy.deepcopy(s) for s in ix['view_sets']};entries=recipe['entries'];emap={e['asset_id']:e for e in entries};prep=[]
 for s in m['sets']:
  oid=s['object_id'];src=safe(BOOK,s['source']['path']);assert sha(src)==s['source']['sha256']
  for v,b in s['base_current_views'].items():assert sha(safe(BOOK,b['path']))==b['sha256'],(oid,v)
  c=s['candidates']['bottom'];aid=oid+'.bottom';cp=safe(BOOK,c['path']);assert sha(cp)==c['sha256'];base=s['base_current_views']['bottom']['sha256'];a=assets[aid];dst=safe(BOOK,a['image']['path']);md=safe(BOOK,a['metadata_path']);assert sha(dst)==base
  old=json.loads(md.read_text());new=copy.deepcopy(old);im=Image.open(cp).convert('RGBA');new['image'].update(width=im.width,height=im.height,sha256=sha(cp),rgba_sha256=rgba(cp));new.setdefault('provenance_history',[]).append({'candidate_id':CID+':'+aid,'previous_provenance':copy.deepcopy(old.get('provenance',{})),'previous_image_sha256':base})
  deriv={k:v for k,v in c.items() if k not in ('path','sha256')}
  for k,v in list(deriv.items()):
   if k.endswith('_path') and isinstance(v,str):deriv[k]=rel(Path(v)) if Path(v).is_absolute() else v
  contact=Path(s['candidate_contact_path']); contact_rel=rel(contact)
  prov={'method':c['method'],'source_image':rel(src),'source_sha256':sha(src),'candidate_image':rel(cp),'candidate_image_sha256':sha(cp),'candidate_manifest':rel(MAN),'candidate_manifest_sha256':sha(MAN),'candidate_contact':contact_rel,'candidate_contact_sha256':s['candidate_contact_sha256'],'source_six_proof_sha256':m['source_six_proof_sha256'],'derivation':deriv,'notes':'Root accepted revised underside; inferred hidden support geometry is qualified as inference.'};new['provenance']=prov;mb=(json.dumps(new,indent=2)+'\n').encode();mh=hashlib.sha256(mb).hexdigest();snap=f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json';ent={'asset_id':aid,'image_path':new['image']['path'],'candidate_path':rel(cp).removeprefix('reusable/views-additional/'),'candidate_sha256':sha(cp),'base_sha256':base,'final_sha256':sha(cp),'metadata_path':new['metadata_path'],'metadata_snapshot_path':snap,'metadata_sha256':mh,'live_before_install_sha256':base,'superseded_installed_sha256':base,'review_record':rel(MAN),'candidate_manifest_sha256':sha(MAN)}
  if aid in emap:assert emap[aid]['final_sha256']==base
  prep.append((aid,oid,dst,md,cp,base,new,mb,mh,snap,ent))
 assert len(prep)==1
 for aid,oid,dst,md,cp,base,new,mb,mh,snap,ent in prep:
  bp=BEFORE/f'{aid}.png';jp=BEFORE/f'{aid}.json';sp=safe(BOOK,snap)
  if bp.exists():assert sha(bp)==base
  if jp.exists():assert json.loads(jp.read_text())['image']['sha256']==base
  if sp.exists():assert sha(sp)==mh
 for aid,oid,dst,md,cp,base,new,mb,mh,snap,ent in prep:
  bp=BEFORE/f'{aid}.png';jp=BEFORE/f'{aid}.json';sp=safe(BOOK,snap)
  if not bp.exists():atomic(bp,dst.read_bytes())
  if not jp.exists():atomic(jp,md.read_bytes())
  if not sp.exists():atomic(sp,mb)
  atomic(dst,cp.read_bytes());atomic(md,mb);assert sha(dst)==sha(cp) and sha(md)==mh;assets[aid]=copy.deepcopy(new)
  if aid in emap:entries[entries.index(emap[aid])]=ent
  else:entries.append(ent)
  emap[aid]=ent;sets[oid]['complete']=False;sets[oid]['notes']='Booth R/L/B candidates installed under scoped approval; awaiting fresh whole-set review.'
 ni=copy.deepcopy(ix);ni['assets']=[copy.deepcopy(assets[a['id']]) for a in ix['assets']];ni['view_sets']=[copy.deepcopy(sets[s['object_id']]) for s in ix['view_sets']];assert len({a['id'] for a in ni['assets']})==len(ni['assets']) and len({s['object_id'] for s in ni['view_sets']})==len(ni['view_sets']);atomic(RECIPE,json.dumps(recipe,indent=2)+'\n');atomic(INDEX,json.dumps(ni,indent=2)+'\n');print(json.dumps({'installed':[r[0] for r in prep],'index_sha256':sha(INDEX),'recipe_entries':len(entries)},indent=2))
if __name__=='__main__':main()
