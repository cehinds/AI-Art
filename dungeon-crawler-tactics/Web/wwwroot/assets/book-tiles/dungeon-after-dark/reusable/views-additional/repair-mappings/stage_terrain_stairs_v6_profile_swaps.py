"""v6 terrain side-profile direction swap, replayed from exact v5 candidate leaves (no redraw)."""
from pathlib import Path
import json,hashlib,copy
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parents[1];PACK=OUT.parent.parent;CDIR=OUT/'candidates/page-dark-next-six-terrain-stairs-v1';M5=CDIR/'terrain-stairs-candidate-manifest-v5.json';IDX=json.loads((OUT/'set-index.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba(p):return Image.open(p).convert('RGBA')
def main():
 m=copy.deepcopy(json.loads(M5.read_text())); m['supersedes_manifest']='reusable/views-additional/candidates/page-dark-next-six-terrain-stairs-v1/terrain-stairs-candidate-manifest-v5.json';m['supersedes_manifest_sha256']=sha(M5);lookup={(c['object_id'],c['view']):c for c in m['candidates']}; changes=[]
 pairs=[('faction-battlefield-churned-battlefield-earth-stairs-up','right','left'),('ghost-cemetery-cemetery-flagstone-stairs-up','right','left')]
 for oid,a,b in pairs:
  ca,cb=lookup[(oid,a)],lookup[(oid,b)];pa=PACK/ca['candidate_path'];pb=PACK/cb['candidate_path'];assert sha(pa)==ca['candidate_sha256'] and sha(pb)==cb['candidate_sha256']
  ia,ib=rgba(pa),rgba(pb);assert ia.size==ib.size==(256,256)
  for target,src,label in [(ca,ib,b),(cb,ia,a)]:
   dest=CDIR/'images'/f"{oid}.{target['view']}.candidate-v6-swapped.png";src.save(dest,format='PNG',optimize=False);target['candidate_path']=dest.relative_to(PACK).as_posix();target['candidate_sha256']=sha(dest);target['extraction']['direction_mapping']={'method':'exact same-target opposite-side profile swap; no pixel transform','donor_view':label,'physical_basis':'UP staircase RIGHT projects high-to-left; LEFT projects high-to-right','source_identity':'canonical target source retained'};target['review_status']='v6 corrected UP-side profile orientation; Page hash review requested';target['notes']='Exact opposite-side connected profile reassigned to this direction; no redraw, scale, or pixel transform. Shared front-low/rear-high camera basis inferred. Other candidate leaves preserved byte-for-byte.';changes.append({'object_id':oid,'target_view':target['view'],'copied_from':label,'path':target['candidate_path'],'sha256':target['candidate_sha256']})
 contact=Image.new('RGBA',(200*12,220*6),(13,16,21,255));proofrows=[]
 for ri,o in enumerate(m['objects']):
  oid=o['object_id'];cs=[c for c in m['candidates'] if c['object_id']==oid];order=[('SOURCE',o['source'])]+[(v,o['base_six'][v]) for v in ['front','top','right','left','bottom','rear']]+[(c['view'].upper()+' NEW',{'path':c['candidate_path'],'sha256':c['candidate_sha256']}) for c in cs];cells=[]
  for ci,(lab,r) in enumerate(order):
   p=PACK/r['path'];assert sha(p)==r['sha256'],(oid,lab);im=rgba(p);im.thumbnail((180,180),Image.Resampling.NEAREST);tile=Image.new('RGBA',(200,220),(31,34,39,255));tile.alpha_composite(im,((200-im.width)//2,8+(180-im.height)//2));ImageDraw.Draw(tile).text((4,195),lab,fill='white');contact.alpha_composite(tile,(ci*200,ri*220));cells.append({'label':lab,**r})
  proofrows.append({'object_id':oid,'cells':cells})
 cp=CDIR/'terrain-stairs-source-six-candidates-v6.png';contact.save(cp,format='PNG',optimize=False);m['candidate_contact_path']=cp.relative_to(PACK).as_posix();m['candidate_contact_sha256']=sha(cp);m['status']='candidate-only; v6 exact profile direction re-key; Page review requested';mp=CDIR/'terrain-stairs-candidate-manifest-v6.json';mp.write_text(json.dumps(m,indent=2)+'\n');pf=CDIR/'terrain-stairs-candidate-contact-proof-v6.json';proof={'manifest_path':mp.relative_to(PACK).as_posix(),'manifest_sha256':sha(mp),'contact_path':cp.relative_to(PACK).as_posix(),'contact_sha256':sha(cp),'supersedes_manifest_path':M5.relative_to(PACK).as_posix(),'supersedes_manifest_sha256':sha(M5),'changes':changes,'rows':proofrows};pf.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'manifest':mp.relative_to(PACK).as_posix(),'manifest_sha256':sha(mp),'contact':cp.relative_to(PACK).as_posix(),'contact_sha256':sha(cp),'proof':pf.relative_to(PACK).as_posix(),'proof_sha256':sha(pf),'changes':changes},indent=2))
if __name__=='__main__':main()
