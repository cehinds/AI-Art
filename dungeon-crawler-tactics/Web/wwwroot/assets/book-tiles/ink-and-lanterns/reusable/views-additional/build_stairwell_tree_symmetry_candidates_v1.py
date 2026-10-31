"""Stage source-bound same-object projection aliases for square stairwell/tree objects."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageOps
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();idx=json.loads(INDEX.read_text());AS={a['id']:a for a in idx['assets']};GS={g['object_id']:g for g in idx['view_sets']}
OBJECTS={
 'starter-dungeon-stone-descent-stairwell':{'source':'starter-dungeon/components/starter-dungeon-stone-descent-stairwell.png','views':{'front':('right','identity'), 'rear':('left','mirror-x')},'rationale':'The four-sided stone stairwell has square XY rim and identical masonry side walls; use existing broad orthographic side elevations on the perpendicular axes, mirroring the opposite face. This lets the near rim occlude the stair opening in horizontal views.'},
 'surface-entry-snowy-sidewalk-tree':{'source':'surface-entry/components/surface-entry-snowy-sidewalk-tree.png','views':{'right':('front','identity'),'left':('rear','mirror-x')},'rationale':'The native object is a radial tree crown over a square planter. Front/rear full canopy extents approximate the orthogonal radial projection and match the square plan depth; mirror the opposite camera for a coherent full-width canopy.'}}
def main():
 rows=[];sheet=Image.new('RGB',(7*220,2*236),(239,235,226));draw=ImageDraw.Draw(sheet)
 for r,(oid,info) in enumerate(OBJECTS.items()):
  group=GS[oid];src=PACK/info['source'];paths=[src]
  for v in ('front','top','right','left','bottom','rear'):paths.append(PACK/AS[group['views'][v]]['image']['path'])
  candidates={}
  for view,(donor,transform) in info['views'].items():
   donor_path=PACK/AS[group['views'][donor]]['image']['path'];im=Image.open(donor_path).convert('RGBA');
   if transform=='mirror-x':im=ImageOps.mirror(im)
   dest=OUT/'raw'/f'{oid}.{view}.candidate-symmetry-v1.png';im.save(dest)
   candidates[view]={'path':dest.relative_to(PACK).as_posix(),'sha256':sha(dest),'donor_view':donor,'donor_path':AS[group['views'][donor]]['image']['path'],'donor_sha256':sha(donor_path),'transform':transform,'rationale':info['rationale']}
  for col,(p,label) in enumerate(zip(paths,('source','front','top','right','left','bottom','rear'))):
   draw.text((col*220+3,r*236+2),label,fill=(0,0,0));art=Image.open(p).convert('RGBA')
   if label in candidates:art=Image.open(PACK/candidates[label]['path']).convert('RGBA')
   art.thumbnail((208,208));sheet.paste(art,(col*220+(220-art.width)//2,r*236+24+(208-art.height)//2),art)
  rows.append({'object_id':oid,'source_path':info['source'],'source_sha256':sha(src),'current_views':{v:{'path':AS[group['views'][v]]['image']['path'],'sha256':sha(PACK/AS[group['views'][v]]['image']['path'])} for v in ('front','top','right','left','bottom','rear')},'candidates':candidates})
 contact=OUT/'raw/qa-stairwell-tree-symmetry-candidates-source-plus-six-v1.png';sheet.save(contact,optimize=True);receipt={'schema_version':1,'status':'candidate only; Root scoped review required','objects':rows,'contact_path':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'notes':'No live files changed. Symmetry candidates are inferred projection aliases, not recovered images.'};p=OUT/'raw/stairwell-tree-symmetry-candidates-v1.json';p.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'contact':contact.relative_to(PACK).as_posix(),'contact_sha256':sha(contact),'receipt':p.relative_to(PACK).as_posix(),'receipt_sha256':sha(p)},indent=2))
if __name__=='__main__':main()
