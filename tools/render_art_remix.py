#!/usr/bin/env python3
"""Render an Art Lab schema2 mixed-library export from a local assets checkout.

Local Git HEAD is the default provenance revision. For detached archives, pass
--art-commit with their recorded40-character source revision. Principal source
reconstruction uses render_pocket_map.py; this tool reproduces semantic remixes.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path
from PIL import Image
from validate_pocket_reusable import contained, image_info, unique_records

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_ASSETS=ROOT/'dungeon-crawler-tactics/Web/wwwroot/assets'
REVISION=re.compile(r'^[0-9a-f]{40}$')


def local_revision(assets, override=None):
    if override:
        if not REVISION.fullmatch(override):raise ValueError('--art-commit must be a40-character lowercase Git revision')
        return override
    result=subprocess.run(['git','-C',str(assets),'rev-parse','HEAD'],text=True,capture_output=True,check=False)
    revision=result.stdout.strip()
    if result.returncode or not REVISION.fullmatch(revision):
        raise ValueError('No local Git revision; pass --art-commit from the trusted archive provenance')
    return revision


def eligible(asset, catalog, view_sets=()):
    if asset.get('reusable') is False or asset.get('kind') in {'composition_layer','reconstruction_patch','residual'}:return False
    if asset.get('view') in {'front','top','right','left','bottom','rear'}:
        parent=catalog.get(asset.get('object_id'))
        if not parent:return False
        direction=asset['view']
        def matches(views):
            if isinstance(views,list):
                views={row.get('view',row.get('direction')):row for row in views if isinstance(row,dict)}
            if not isinstance(views,dict):return False
            target=views.get(direction)
            if isinstance(target,dict):target=target.get('asset_id',target.get('id'))
            return target==asset['id']
        return matches(parent.get('views')) or any(
            group.get('object_id')==parent['id'] and matches(group.get('views',group.get('directions')))
            for group in view_sets if isinstance(group,dict))
    return True


def render(assets_root, document, art_commit=None):
    assets_root=Path(assets_root).resolve()
    registry=json.loads((assets_root/'reusable-library.json').read_text())
    libraries=unique_records(registry['libraries'],'id','library registry')
    if not isinstance(document,dict):raise ValueError('Remix document must be a JSON object')
    if document.get('schema_version')!=2 or document.get('kind')!='semantic-remix':
        raise ValueError('Expected an Art Lab schema2 semantic-remix JSON document')
    canvas=document.get('canvas',{})
    width,height=canvas.get('width'),canvas.get('height')
    if any(type(v) is not int or v<=0 or v>8192 for v in (width,height)):
        raise ValueError('Canvas dimensions must be positive integers no larger than8192')
    dependency_rows=document.get('dependencies',[])
    if not isinstance(dependency_rows,list) or any(not isinstance(row,dict) for row in dependency_rows):raise ValueError('Dependencies must be an array of objects')
    dependencies=unique_records(dependency_rows,'library_id','remix dependencies')
    placements=document.get('placements',[])
    if not isinstance(placements,list) or len(placements)>10000 or any(not isinstance(item,dict) for item in placements):raise ValueError('Invalid or excessive placement list')
    used={item.get('library_id') for item in placements}
    if used!=set(dependencies):raise ValueError('Dependencies must match exactly the libraries used by placements')
    revision=None;catalogs={};packs={};view_sets={}
    for library_id,dependency in dependencies.items():
        if library_id not in libraries:raise ValueError('Unknown library: '+library_id)
        requested=dependency.get('art_commit','')
        if not isinstance(requested,str) or not REVISION.fullmatch(requested):raise ValueError('Dependency requires exact40-character art_commit')
        entry=libraries[library_id]
        expected=entry.get('art_commit') or registry.get('art_commit')
        if not expected:
            if revision is None:revision=local_revision(assets_root,art_commit)
            expected=revision
        if requested!=expected:raise ValueError(f'Art revision mismatch for {library_id}: export {requested}, local {expected}')
        pack=contained(assets_root,entry['base'])
        index=contained(assets_root,entry['index'])
        catalog=json.loads(index.read_text())
        catalogs[library_id]=unique_records(catalog['assets'],'id',library_id)
        view_sets[library_id]=catalog.get('view_sets',[])
        packs[library_id]=pack
    output=Image.new('RGBA',(width,height),(0,0,0,0))
    for placement in placements:
        library_id=placement['library_id'];catalog=catalogs[library_id]
        asset_id=placement.get('asset_id');asset=catalog.get(asset_id)
        if asset is None:raise ValueError(f'Unknown asset {library_id}::{asset_id}')
        if not eligible(asset,catalog,view_sets[library_id]):raise ValueError('Asset is not eligible for semantic remix: '+asset_id)
        if placement.get('path')!=asset['image']['path']:raise ValueError('Placement path differs from trusted asset metadata')
        x,y,rotation=placement.get('x'),placement.get('y'),placement.get('rotation_deg')
        if type(x) is not int or type(y) is not int or not (0<=x<=width and 0<=y<=height):raise ValueError('Anchor coordinates must be integers inside the canvas')
        if type(rotation) is not int or rotation not in (0,90,180,270) or type(placement.get('scale')) not in (int,float) or placement.get('scale')!=1 or placement.get('anchor')!='center':
            raise ValueError('Remix requires center anchor, scale1, and a clockwise right-angle rotation')
        source=image_info(packs[library_id],asset['image'])
        w,h=source.size
        offsets={0:(-(w//2),-(h//2)),90:(-(h-h//2),-(w//2)),180:(-(w-w//2),-(h-h//2)),270:(-(h//2),-(w-w//2))}
        dx,dy=offsets[rotation]
        if rotation:source=source.rotate(-rotation,expand=True,resample=Image.Resampling.NEAREST)
        output.alpha_composite(source,(x+dx,y+dy))
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assets',type=Path,default=DEFAULT_ASSETS)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--art-commit')
    args=p.parse_args()
    try:
        if args.output.suffix.lower()!='.png':raise ValueError('Output must be PNG')
        if args.output.resolve().is_relative_to(args.assets.resolve()):raise ValueError('Write rendered output outside the source assets tree')
        if args.output.resolve()==args.input.resolve():raise ValueError('Output must not replace the input recipe')
        document=json.loads(args.input.read_text())
        image=render(args.assets,document,args.art_commit)
        args.output.parent.mkdir(parents=True,exist_ok=True);image.save(args.output)
        print(json.dumps({'output':str(args.output),'width':image.width,'height':image.height,'placements':len(document['placements']),
            'note':'Deterministic Pillow source-over rendering. Browser premultiplication may normalize invisible RGB or round low-alpha RGB.'}))
    except (ValueError,KeyError,OSError,json.JSONDecodeError) as exc:p.exit(2,f'render_art_remix: {exc}\n')

if __name__=='__main__':main()
