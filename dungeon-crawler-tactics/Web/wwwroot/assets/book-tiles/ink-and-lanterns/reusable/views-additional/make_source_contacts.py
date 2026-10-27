#!/usr/bin/env python3
"""Build source and source+six QA contacts from kit source PNGs and current views."""
import argparse, json, pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'reusable/views-additional'
MANIFEST = json.loads((ROOT / 'manifest.json').read_text())['assets']
VIEWS = ('front', 'top', 'right', 'left', 'bottom', 'rear')

def source_path(object_id):
    name = object_id.removesuffix('--native')
    found = list(ROOT.glob(f'*/components/{name}.png'))
    if len(found) != 1:
        raise FileNotFoundError(f'expected one source image for {name}, got {found}')
    return found[0]

def fit(im, size):
    im = im.convert('RGBA')
    im.thumbnail((size, size), Image.Resampling.LANCZOS)
    return im

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, required=True)
    ap.add_argument('--count', type=int, default=6)
    args = ap.parse_args()
    if args.start < 0 or args.start + args.count > len(MANIFEST):
        raise ValueError('manifest range out of bounds')
    font = ImageFont.load_default()
    source_sheet = Image.new('RGBA', (256, args.count * 280), (239, 235, 226, 255))
    qa = Image.new('RGBA', (7 * 184, args.count * 216), (239, 235, 226, 255))
    sd = ImageDraw.Draw(source_sheet); qd = ImageDraw.Draw(qa)
    for row, item in enumerate(MANIFEST[args.start:args.start + args.count]):
        oid = item['id']; y = row * 280
        sd.text((4, y + 2), oid, font=font, fill=(15, 15, 15, 255))
        src = fit(Image.open(source_path(oid)), 224)
        source_sheet.alpha_composite(src, (16 + (224-src.width)//2, y + 30 + (224-src.height)//2))
        qy = row * 216
        qd.text((4, qy + 2), oid, font=font, fill=(15, 15, 15, 255))
        paths = [source_path(oid)] + [OUT / f'{oid.removesuffix("--native")}.{v}.png' for v in VIEWS]
        labels = ['source', *VIEWS]
        for col, (path, label) in enumerate(zip(paths, labels)):
            x = col * 184
            qd.text((x + 4, qy + 22), label, font=font, fill=(15, 15, 15, 255))
            if path.exists():
                im = fit(Image.open(path), 168)
                qa.alpha_composite(im, (x + 8 + (168-im.width)//2, qy + 42 + (168-im.height)//2))
            else:
                qd.text((x + 20, qy + 90), 'MISSING', font=font, fill=(180, 0, 0, 255))
    start_id, end_id = args.start + 1, args.start + args.count
    tag = f'{start_id:04d}-{end_id:04d}'
    raw = OUT / 'raw'; raw.mkdir(exist_ok=True)
    source_path_out = raw / f'book-objects-{tag}-source-contact.png'
    qa_path = OUT / f'qa-source-views-{tag}.png'
    source_sheet.convert('RGB').save(source_path_out, optimize=True)
    qa.convert('RGB').save(qa_path, optimize=True)
    print(source_path_out); print(qa_path)

if __name__ == '__main__':
    main()
