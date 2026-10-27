"""Rebuild only these staged candidates from immutable pack-local input copies."""
from pathlib import Path
import hashlib,io,json
from PIL import Image
base=Path(__file__).resolve().parent
root=base.parents[3]
m=json.loads((base/'candidate-manifest-v1.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
count=0
for obj in m['objects']:
 for view,row in obj['candidates'].items():
  r=row['recipe'];p=root/r['input_path'];assert sha(p)==r['input_sha256'],p
  im=Image.open(p).convert('RGBA');assert list(im.getbbox())==r['alpha_bbox_xyxy'];im=im.crop(r['alpha_bbox_xyxy'])
  if r['rotation_ccw_degrees']:im=im.transpose(Image.Transpose.ROTATE_90 if r['rotation_ccw_degrees']==90 else Image.Transpose.ROTATE_180)
  expected=[round(im.width*r['uniform_scale']),max(1,round(im.height*r['uniform_scale']))];assert expected==r['resized_dimensions']
  im=im.resize(expected,Image.Resampling.NEAREST);out=Image.new('RGBA',r['canvas']);out.paste(im,r['offset_px']);buf=io.BytesIO();out.save(buf,format='PNG');assert hashlib.sha256(buf.getvalue()).hexdigest()==row['sha256'],(obj['object_id'],view)
  assert sha(root/row['path'])==row['sha256'];count+=1
print(f'{count} staged candidates reproduced byte-for-byte from immutable pack-local inputs; no writes')
