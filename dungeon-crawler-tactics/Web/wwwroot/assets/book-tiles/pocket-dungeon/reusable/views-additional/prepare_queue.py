#!/usr/bin/env python3
"""Prepare role-aware six-object reference sheets and prompts for pending Pocket atlas batches."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

ROOT=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
RAW=WORK/'raw'
progress=json.loads((WORK/'progress.json').read_text())
font=ImageFont.load_default()

def object_description(a):
    oid=a['id']; layout=a.get('squareLayout',''); role=a.get('role',''); layer=a.get('layer','')
    if role=='floor' or layer=='ground' or layout in ('floor','ground','tile'):
        return 'flat walkable ground tile; preserve the exact top motif; four horizontal views are shallow natural edge profiles; bottom is full material-matched substrate viewed upward from below, with top decorations hidden and no added support frame'
    if layout=='north-wall':
        return 'upright wall running along map X; front and rear are broad wall faces, right and left are thin end profiles, top and bottom are long horizontal wall-plan footprints; keep one consistent physical height in all elevations'
    if layout=='west-wall':
        return 'upright wall running along map Y; front and rear are thin end profiles, right and left are broad wall faces, top and bottom are long vertical wall-plan footprints; keep one consistent physical height in all elevations'
    if 'doorway' in oid:
        return 'upright doorway in its wall orientation; preserve the opening through front, rear, sides and top plan; no invented door for open doorway'
    if 'stairs-up' in oid or 'stairs-down' in oid or 'stair' in oid:
        return 'horizontal ground stair/ramp; top shows upward or downward treads matching source; sides and front/rear show coherent step profile; bottom is the hidden underside, never duplicated top treads'
    if 'corner' in oid:
        return 'wall corner whose joined L-shaped footprint belongs in top/bottom plan; front, rear and side views are coherent elevations, not an upright L silhouette'
    if 'endcap' in oid:
        return 'wall endcap aligned to its named orientation; broad and thin elevations have the same physical height; top and bottom show plan footprint'
    if role in ('north-wall','west-wall'):
        return 'upright wall in its map orientation, with broad/thin faces determined by its named north/west direction; top/bottom are plan views and elevations keep consistent height'
    return 'physical prop in a stable upright world pose; front/rear, left/right, top/bottom show the same object with coherent proportions; bottom is the actual underside viewed upward, not a lying object or frontal face'

for batch in progress['batches']:
    if batch.get('status')!='pending':
        continue
    kit=batch['kit'];num=batch['batch']; manifest=json.loads((ROOT/kit/'manifest.json').read_text())
    byid={a['id']:a for a in manifest['assets']}; ids=batch['object_ids']
    srcs=[byid[x] for x in ids]
    guide='view-guide-floor.png' if batch['batch']==1 else ('view-guide-wall.png' if batch['batch']==2 else ('view-guide-wall.png' if batch['batch']==3 else 'view-guide-prop.png'))
    guide_path=RAW/'source-refs'/guide
    # Compose six original normalized source sprites in order; this is a labeled provenance/reference sheet, not generated art.
    cell=256; label_h=34; margin=8
    sheet=Image.new('RGBA',(6*cell,cell+label_h),(38,40,44,255))
    draw=ImageDraw.Draw(sheet)
    for col,a in enumerate(srcs):
        im=Image.open(ROOT/kit/a['file']).convert('RGBA')
        im.thumbnail((cell-12,cell-12),Image.Resampling.NEAREST)
        tile=Image.new('RGBA',(cell,cell),(38,40,44,255));tile.alpha_composite(im,((cell-im.width)//2,(cell-im.height)//2))
        sheet.alpha_composite(tile,(col*cell,0))
        draw.text((col*cell+4,cell+2),a['id'][:35],fill=(245,245,245,255),font=font)
    ref=RAW/'source-refs'/f'{kit}-batch-{num:02d}.png';ref.parent.mkdir(parents=True,exist_ok=True);sheet.save(ref)
    descriptions='\n'.join(f"Row {i+1}: {a['id']} — {object_description(a)}." for i,a in enumerate(srcs))
    prompt=(
      'Create a transparent-background SQUARE pixel-art atlas exactly 1536 by 1536 pixels, divided into 6 equal columns and 6 equal rows of 256 by 256 pixels each, one object per row. '
      'Columns from left to right are FRONT, TOP, RIGHT SIDE, LEFT SIDE, BOTTOM, REAR. '
      'The attached labeled contact sheet is source identity and palette reference only; copy the six row identities exactly and ignore labels as image content. '
      'The attached six-view geometry guide is only a layout and camera-direction reference; it is not an object to copy. '
      'Strict axis-aligned world orthographic views, no perspective, no isometric, no cast shadow, no background. '
      'Keep silhouettes complete inside individual cells, with no cell-to-cell bleed. Infer hidden faces conservatively from the source. '
      'Use crisp pixel clusters and NEAREST-style pixel-art detail; no photorealism.\n'+descriptions+'\n'
      'For true horizontal ground tiles, vertical edge views must show only thin side thickness and BOTTOM must be the full underside plane viewed upward; never substitute a vertical strip for a floor plane. '
      'For upright walls, TOP and BOTTOM are plan faces; face and side elevations follow each named map axis and have identical physical height. '
      'For props, maintain one stable upright object in all views; BOTTOM is directly below looking up, never a view of a person lying down. '
      'Do not add generic black bases, display plinths, bolts, supports or decorative structures absent from the source.'
    )
    pp=RAW/'prompts'/f'{kit}-batch-{num:02d}.txt';pp.parent.mkdir(parents=True,exist_ok=True);pp.write_text(prompt+'\n')
    batch['source_sheet']=ref.relative_to(ROOT).as_posix();batch['prompt_file']=pp.relative_to(ROOT).as_posix();batch['style_guide']=guide_path.relative_to(ROOT).as_posix()
progress['updated_by']='prepare_queue.py';(WORK/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
print('prepared pending batches',sum(b.get('status')=='pending' for b in progress['batches']))
