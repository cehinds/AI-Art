"""Rebuild the two Root-reviewed Ticket Gate v2 candidates, using only same-target views."""
from pathlib import Path
from PIL import Image
import hashlib,json
VA=Path(__file__).resolve().parents[1].parent;BOOK=VA.parent.parent
MANIFEST=VA/'candidates/root-dark-frame-cleanup-v2/root-dark-frame-cleanup-v2-ticket-gate-manifest.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 m=json.loads(MANIFEST.read_text());o=m['object'];
 for c in o['affected_views']:
  assert sha(BOOK/c['base_path'])==c['base_sha256']
 left=Image.open(BOOK/o['affected_views'][0]['base_path']).convert('RGBA')
 a=left.load()
 for y in range(95,161):
  for x in range(192,231):a[x,y]=(0,0,0,0)
 lp=VA/o['affected_views'][0]['candidate_path'];left.save(lp,optimize=True);assert sha(lp)==o['affected_views'][0]['candidate_sha256']
 base=Image.open(BOOK/o['affected_views'][1]['base_path']).convert('RGBA')
 top=Image.open(BOOK/'reusable/views-additional/images/iron-stations-ticket-gate.top.png').convert('RGBA')
 out=Image.new('RGBA',(256,256),(0,0,0,0));plate=base.crop((79,95,117,160))
 for x in [47,109,171]:out.alpha_composite(plate,(x,95))
 for box,dest in [((81,119,112,143),(81,119)),((144,119,175,143),(144,119))]:out.alpha_composite(top.crop(box),dest)
 bp=VA/o['affected_views'][1]['candidate_path'];out.save(bp,optimize=True);assert sha(bp)==o['affected_views'][1]['candidate_sha256']
 print('Ticket Gate v2 candidate hashes reproduced')
if __name__=='__main__':main()
