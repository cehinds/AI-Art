"""Capture installed Page generated-11 results from the canonical index and source files."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json';REPORT=OUT/'page-generated11-v1-install-report.json';
VIEWS=('front','top','right','left','bottom','rear')
GEN=json.loads((OUT/'candidates/page-ink-six-props-20261026/generated-candidate-manifest-v1.json').read_text())
SOURCE={row['object_id']:row['source']['path'] for row in GEN['sets']}
IDS=('over-city-venues-circus-striped-platform','hunting-shrines-hunter-trap-mechanism','faction-larracos-drained-slum-house','starter-dungeon-simple-bed')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 index=json.loads(INDEX.read_text());assets={a['id']:a for a in index['assets']};groups={g['object_id']:g for g in index['view_sets']}
 report=json.loads(REPORT.read_text());
 for oid in IDS:
  assert oid in groups
 rows=[];sheet=Image.new('RGBA',(7*220,len(IDS)*236),(239,235,226,255));draw=ImageDraw.Draw(sheet)
 for r,oid in enumerate(IDS):
  group=groups[oid]; draw.text((3,r*236+2),oid,fill=(10,10,10,255))
  src=PACK/SOURCE[oid]; paths=[src]
  expected=[sha(src)]
  for v in VIEWS:
   aid=group['views'][v];a=assets[aid];p=PACK/a['image']['path'];paths.append(p);expected.append(sha(p));assert p.exists()
  for c,(path,label) in enumerate(zip(paths,('source',*VIEWS))):
   x=c*220;y=r*236;draw.text((x+4,y+22),label,fill=(10,10,10,255));im=Image.open(path).convert('RGBA');im.thumbnail((204,204),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+(204-im.width)//2,y+30+(204-im.height)//2))
  rows.append({'object_id':oid,'source_path':SOURCE[oid],'source_sha256':expected[0],'views':{v:{'asset_id':group['views'][v],'path':assets[group['views'][v]]['image']['path'],'sha256':expected[i+1]} for i,v in enumerate(VIEWS)}})
 path=OUT/'raw/qa-page-generated11-installed-source-plus-six-v1.png';path.parent.mkdir(parents=True,exist_ok=True);sheet.convert('RGB').save(path,optimize=True)
 receipt={'schema_version':1,'kind':'installed-current-source-plus-six-contact','contact_path':path.relative_to(PACK).as_posix(),'contact_sha256':sha(path),'install_report_path':REPORT.relative_to(PACK).as_posix(),'install_report_sha256':sha(REPORT),'index_sha256':sha(INDEX),'objects':rows}
 meta=path.with_suffix('.json');meta.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'path':str(path),'sha256':sha(path),'receipt':str(meta),'receipt_sha256':sha(meta)},indent=2))
if __name__=='__main__':main()
