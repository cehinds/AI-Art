#!/usr/bin/env python3
"""Rebuild the retained gear/armor atlases from pack-local sidecar recipes."""
from pathlib import Path
import hashlib,json,subprocess,sys
from PIL import Image

OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];INDEX=OUT/'set-index.json'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    index=json.loads(INDEX.read_text());assets={a['id']:a for a in index.get('assets',[])}
    batches={}
    skipped_repair_views=[]
    for group in index.get('view_sets',[]):
        rows=[]
        for view,aid in group.get('views',{}).items():
            if aid not in assets:raise ValueError(f"{group['object_id']}.{view}: missing indexed asset {aid}")
            asset=assets[aid];meta_path=PACK/asset['metadata_path'];meta=json.loads(meta_path.read_text())
            prov=meta.get('provenance',{});raw_rel=prov.get('generated_atlas');cell=prov.get('source_rect',{}).get('cell_px')
            # Targeted view replacements may use a dedicated one-view atlas
            # whose source_rect records a named cell rather than pixel bounds.
            # Their exact output is installed by apply_targeted_repairs after
            # the base atlas pass, so do not misinterpret that source as a
            # six-view grid or demand a fictitious cell_px rectangle.
            if prov.get('repair_recipe'):
                skipped_repair_views.append(aid)
                continue
            if not raw_rel or not cell:raise ValueError(f"{aid}: generated_atlas/source_rect.cell_px provenance is required for non-repair views")
            raw=PACK/raw_rel
            if not raw.is_file():raise FileNotFoundError(raw)
            expected=prov.get('generated_atlas_sha256')
            if expected and sha(raw)!=expected:raise ValueError(f"{aid}: raw atlas hash mismatch: {raw_rel}")
            row=round(cell[1]/(cell[3]-cell[1])) if cell[3]>cell[1] else -1
            # cell y bounds are emitted as fractional grid boundaries; derive
            # the row from its center, avoiding assumptions about atlas height.
            row=round((cell[1]+cell[3])/2/(cell[3]-cell[1])-0.5)
            grid_rows=round(Image.open(raw).height/(cell[3]-cell[1]))
            obj=batches.setdefault(raw_rel,{}).setdefault(group['object_id'],{'row':row,'grid_rows':grid_rows,'name':meta.get('name',group['object_id']).rsplit(' ',1)[0],'kind':meta.get('kind','sprite')})
            if obj['row']!=row:raise ValueError(f"{group['object_id']}: inconsistent row for {raw_rel}: {obj['row']} vs {row}")
            if obj['grid_rows']!=grid_rows:raise ValueError(f"{raw_rel}: inconsistent source grid row count")
        if len(rows)>1:raise AssertionError(rows)
    script=OUT/'normalize_atlas.py'
    for seq,(raw_rel,objects) in enumerate(sorted(batches.items())):
        ordered=sorted(objects.items(),key=lambda item:item[1]['row'])
        row_ids=[x[1]['row'] for x in ordered];grid_rows={x[1]['grid_rows'] for x in ordered}
        if len(set(row_ids))!=len(row_ids) or len(grid_rows)!=1:
            raise ValueError(f'{raw_rel}: object source rows must be unique and share a grid, got {row_ids}/{grid_rows}')
        obj_arg=','.join(f"{oid}|{row['name']}|{row['kind']}" for oid,row in ordered)
        batch=Path(raw_rel).stem
        subprocess.run([sys.executable,str(script),str(PACK/raw_rel),'--batch',batch,'--objects',obj_arg,'--grid-rows',str(next(iter(grid_rows))),'--object-rows',','.join(str(row['row']) for _,row in ordered)],cwd=PACK,check=True)
    # Targeted corrections are deterministic and hash-guarded by their recipe
    # inputs. normalize_atlas calls the repair applier per batch; run once at
    # the end as well so repairs for the final batch are not order-sensitive.
    from apply_targeted_repairs import apply_all
    apply_all()
    print(json.dumps({'batches':len(batches),'objects':len(index.get('view_sets',[])),'views':len(index.get('assets',[])),'repair_views_deferred':len(skipped_repair_views),'repair_view_ids':skipped_repair_views}))

if __name__=='__main__':main()
