"""Rebuild root-dark-frame-cleanup-v1 candidates from immutable pack-local inputs."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import hashlib,json
import numpy as np
from scipy import ndimage
VA=Path(__file__).resolve().parents[1].parent
BOOK=VA.parent.parent
CAND=VA/'candidates/root-dark-frame-cleanup-v1'
BEFORE=VA/'prebuilt/root-dark-frame-cleanup-v1-before'
MANIFEST=CAND/'root-dark-frame-cleanup-v1-candidate-manifest.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def base_view(oid,view,expected):
 p=BEFORE/f'{oid}.{view}.png'
 if not p.exists():p=VA/f'images/{oid}.{view}.png'
 assert sha(p)==expected,(oid,view,sha(p),expected)
 return Image.open(p).convert('RGBA')
def save(oid,v,im,expected):
 p=CAND/f'{oid}.{v}.candidate.png';im.save(p,optimize=True);assert sha(p)==expected,(oid,v,sha(p),expected)
def main():
 m=json.loads(MANIFEST.read_text())
 for o in m['objects']:
  oid=o['object_id']
  for c in o['affected_views']:
   v=c['view'];expected=c['candidate_sha256']
   if oid=='iron-tracks-tunnel-portal-frame':
    im=base_view(oid,v,c['base_sha256']);arr=np.array(im);mask=Image.new('L',im.size,0);d=ImageDraw.Draw(mask)
    d.polygon([(96,96),(99,91),(104,87),(111,83),(119,80),(128,78),(137,80),(145,83),(152,87),(157,91),(160,96),(163,108),(165,124),(166,143),(166,208),(90,208),(90,143),(91,124),(93,108)],fill=255)
    d.polygon([(96,96),(99,91),(104,87),(111,83),(119,80),(128,78),(137,80),(145,83),(152,87),(157,91),(160,96),(163,108),(164,124),(164,143),(92,143),(92,124),(93,108)],fill=255)
    a=np.array(im);z=np.array(mask)>0;a[z,:3]=0;a[z,3]=0;im=Image.fromarray(a,'RGBA')
   elif oid=='starter-dungeon-dark-stone-block-open-doorway':
    im=base_view(oid,v,c['base_sha256']);a=np.array(im);a[101:183,101:155,:]=0;im=Image.fromarray(a,'RGBA')
   elif oid=='surface-entry-urban-brick-open-doorway':
    im=base_view(oid,v,c['base_sha256']);a=np.array(im);a[94:179,96:159,:]=0;im=Image.fromarray(a,'RGBA')
   elif oid=='iron-stations-ticket-gate':
    # v1 left candidate is intentionally the unchanged held base (wrong stray-plate cleanup); v2 supersedes it.
    # The v1 bottom held candidate repeats a footplate at the old touching spacing.
    if v=='left':
     srcpath=BEFORE/f'{oid}.{v}.png';
     if not srcpath.exists():srcpath=VA/f'images/{oid}.{v}.png'
     assert sha(srcpath)==c['base_sha256'];(CAND/f'{oid}.{v}.candidate.png').write_bytes(srcpath.read_bytes());continue
    im=base_view(oid,v,c['base_sha256']);patch=im.crop((79,95,117,160));im.alpha_composite(patch,(109,95))
   elif oid=='iron-trains-riveted-carriage-metal-wall-northeast':
    src=base_view(oid,v,c['base_sha256']);im=Image.new('RGBA',(256,256),(0,0,0,0));x=108;y=27
    cap0=src.crop((108,72,149,96));body=src.crop((108,96,149,159));cap1=src.crop((108,159,149,184));strip=src.crop((108,105,149,150))
    for tile in (cap0,body,strip,strip,cap1):im.alpha_composite(tile,(x,y));y+=tile.height
   elif oid=='over-city-weathered-city-masonry-wall-northeast':
    source=Image.open(BOOK/'reusable/views-additional/raw/frame-cleanup-20261026/over-city-wall-left-request-output.png').convert('RGBA');a=np.array(source.getchannel('A'));lab,n=ndimage.label(a>32);sizes=np.bincount(lab.ravel());idx=int(np.argmax(sizes[1:])+1);yy,xx=np.where(lab==idx);wall=source.crop((int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)));sz=(round(wall.width*151/wall.height),151);wall=wall.resize(sz,Image.Resampling.LANCZOS);im=Image.new('RGBA',(256,256),(0,0,0,0));im.alpha_composite(wall,((256-sz[0])//2,203-sz[1]));
    if v=='right':im=ImageOps.mirror(im)
   else:raise ValueError(oid)
   save(oid,v,im,expected)
 print('all candidate PNG hashes reproduced')
if __name__=='__main__':main()
