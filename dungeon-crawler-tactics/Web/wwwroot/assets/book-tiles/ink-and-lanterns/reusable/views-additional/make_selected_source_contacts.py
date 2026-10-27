#!/usr/bin/env python3
"""Create source+six QA contacts for an explicit, possibly non-contiguous ID list."""
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
MANIFEST = json.loads((PACK / 'manifest.json').read_text())['assets']
VIEWS = ('front', 'top', 'right', 'left', 'bottom', 'rear')
SOURCE = {a['id'].removesuffix('--native'): a for a in MANIFEST}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True, help='output filename in views-additional')
    ap.add_argument('object_ids', nargs='+')
    args = ap.parse_args()
    ids = args.object_ids
    font = ImageFont.load_default()
    sheet = Image.new('RGBA', (7 * 184, len(ids) * 216), (239, 235, 226, 255))
    draw = ImageDraw.Draw(sheet)
    for row, oid in enumerate(ids):
        rec = SOURCE[oid]
        src_rel = f"{rec['source']['sheet']}/components/{oid}.png"
        paths = [PACK / src_rel] + [OUT / f'{oid}.{v}.png' for v in VIEWS]
        y = row * 216
        draw.text((4, y + 2), oid, font=font, fill=(15, 15, 15, 255))
        for col, (path, label) in enumerate(zip(paths, ('source', *VIEWS))):
            x = col * 184
            draw.text((x + 4, y + 22), label, font=font, fill=(15, 15, 15, 255))
            if not path.exists():
                draw.text((x + 20, y + 90), 'MISSING', font=font, fill=(180, 0, 0, 255))
                continue
            im = Image.open(path).convert('RGBA')
            im.thumbnail((168, 168), Image.Resampling.LANCZOS)
            sheet.alpha_composite(im, (x + 8 + (168-im.width)//2, y + 42 + (168-im.height)//2))
    out = OUT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert('RGB').save(out, optimize=True)
    print(out)

if __name__ == '__main__':
    main()
