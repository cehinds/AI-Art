#!/usr/bin/env python3
"""Apply deterministic 90-degree raster rotations to selected inferred views."""
import argparse, hashlib, json, os, struct, tempfile
from pathlib import Path
from PIL import Image

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]

def atomic(path, value):
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    os.close(fd)
    Path(tmp).write_text(json.dumps(value, indent=2) + '\n')
    os.replace(tmp, path)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--degrees',type=int,choices=(90,180,270),default=90)
    ap.add_argument('targets',nargs='+',help='object_id:view')
    a=ap.parse_args()
    idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text())
    assets={x['id']:x for x in idx['assets']};sets={x['object_id']:x for x in idx['view_sets']}
    transpose={90:Image.Transpose.ROTATE_90,180:Image.Transpose.ROTATE_180,270:Image.Transpose.ROTATE_270}[a.degrees]
    changed=[]
    for target in a.targets:
        oid,view=target.rsplit(':',1)
        aid=sets[oid]['views'][view];asset=assets[aid];meta_path=PACK/asset['metadata_path'];meta=json.loads(meta_path.read_text())
        png=PACK/asset['image']['path'];im=Image.open(png).convert('RGBA');before=hashlib.sha256(png.read_bytes()).hexdigest();im=im.transpose(transpose);im.save(png,optimize=True)
        data=png.read_bytes();sha=hashlib.sha256(data).hexdigest();rgba=im.tobytes();canonical=hashlib.sha256(struct.pack('>II',*im.size)+rgba).hexdigest()
        meta['image']['sha256']=sha;meta['image']['rgba_sha256']=canonical
        prov=meta.setdefault('provenance',{});prov.update({'method':'deterministic-orientation-rotation','rotation_degrees_ccw':a.degrees,'superseded_file_sha256':before,'notes':prov.get('notes','')+' Deterministic orthographic axis correction; all RGBA values rotated without repainting.'})
        atomic(meta_path,meta);assets[aid].update(meta);changed.append({'object_id':oid,'view':view,'asset_id':aid,'sha256':sha,'rgba_sha256':canonical})
    idx['assets']=list(assets.values());atomic(idxp,idx)
    pendingp=OUT/'pending-review-batches.json'
    if pendingp.exists():
        pending=json.loads(pendingp.read_text());by={x['object_id']:x for x in pending.get('objects',[])}
        for x in changed:
            row=by.get(x['object_id'])
            if row and x['view'] in row.get('views',{}):row['views'][x['view']]['sha256']=x['sha256']
        atomic(pendingp,pending)
    print(json.dumps({'rotated':changed},indent=2))

if __name__=='__main__':main()
