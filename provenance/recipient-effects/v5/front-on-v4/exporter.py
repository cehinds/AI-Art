"""Extract generated front-on effect sheets into review-only PNG deliverables.

Does not repaint, recolor, threshold, or remove any source pixels. Raw PNGs are
read-only. Every frame uses the same scale; three frames share one row offset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SHEETS = {
    "physical": ["slash", "multi-slash", "smash", "thrust"],
    "actions": ["sweep", "counter", "spell", "skill"],
    "support": ["ward", "buff", "debuff", "heal"],
    "elements": ["fire", "frost", "lightning", "earth"],
    "schools": ["status", "force", "illusion", "decay"],
    "reactions": ["spell-circle", "block", "evade", "retreat"],
    "advance": ["advance"],
    "evade-afterimage": ["evade-afterimage"],
}
PHYSICAL = ["slash", "multi-slash", "smash", "thrust", "sweep", "counter"]
PHASES = ["ONSET", "IMPACT", "DECAY"]
BG = (19, 27, 33, 255)
CELL = (27, 38, 44, 255)
TEXT = (230, 237, 237, 255)
MUTED = (150, 174, 183, 255)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    roots = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")]
    names = ["arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for root in roots:
        for name in names:
            if (root / name).exists():
                return ImageFont.truetype(str(root / name), size)
    return ImageFont.load_default(size=size)


def quiet_cuts(mass: list[int], count: int) -> list[int]:
    size = len(mass)
    cuts = [0]
    radius = round(size / count * .38)
    for i in range(1, count):
        expected = round(i * size / count)
        choices = range(max(cuts[-1] + 1, expected - radius), min(size, expected + radius + 1))
        # Choose a quiet BAND, not the very first transparent pixel touching a
        # sprite. This keeps a small safe gutter on either side of the cut.
        cuts.append(min(choices, key=lambda value: (sum(mass[max(0, value - 6):min(size, value + 7)]), abs(value - expected))))
    return cuts + [size]


def rects(image: Image.Image, rows: int = 4) -> list[list[tuple[int, int, int, int]]]:
    width, height = image.size
    # Search only the whitespace around nominal grid boundaries. Low-alpha
    # generation residue does not define a sprite edge or registration point.
    alpha = image.getchannel("A")
    values = list(alpha.get_flattened_data())
    x_mass, y_mass = [0] * width, [0] * height
    for y in range(height):
        row = values[y * width:(y + 1) * width]
        for x, value in enumerate(row):
            if value >= 64:
                x_mass[x] += value
                y_mass[y] += value
    xs, ys = quiet_cuts(x_mass, 3), quiet_cuts(y_mass, rows)
    return [[(xs[col], ys[row], xs[col + 1], ys[row + 1]) for col in range(3)] for row in range(rows)]


def union_bounds(frames: list[Image.Image]) -> tuple[int, int, int, int]:
    bounds = [frame.getchannel("A").point(lambda a: 255 if a >= 64 else 0).getbbox() for frame in frames]
    visible = [bound for bound in bounds if bound]
    if not visible:
        raise ValueError("Entire effect row is transparent")
    return (min(b[0] for b in visible), min(b[1] for b in visible),
            max(b[2] for b in visible), max(b[3] for b in visible))


def contact_sheet(path: Path, title: str, names: list[str], frames: dict[str, list[Image.Image]], columns: int) -> None:
    margin, gap, card_width, card_height, header = 24, 16, 628, 226, 106
    rows = math.ceil(len(names) / columns)
    canvas = Image.new("RGBA", (margin * 2 + columns * card_width + (columns - 1) * gap,
                                header + rows * card_height + (rows - 1) * gap + margin), BG)
    draw = ImageDraw.Draw(canvas)
    title_size = 26
    while draw.textlength(title, font=font(title_size, True)) > canvas.width - margin * 2 and title_size > 14:
        title_size -= 1
    draw.text((margin, 18), title, font=font(title_size, True), fill=TEXT)
    draw.text((margin, 58), "FRONT-ON GBA STYLE / 3 FRAMES / PREVIEW ONLY", font=font(14), fill=MUTED)
    for index, name in enumerate(names):
        x = margin + (index % columns) * (card_width + gap)
        y = header + (index // columns) * (card_height + gap)
        draw.rounded_rectangle((x, y, x + card_width, y + card_height), radius=8, fill=CELL)
        draw.text((x + 14, y + 10), name.replace("-", " ").upper(), font=font(18, True), fill=TEXT)
        for col, frame in enumerate(frames[name]):
            slot_x = x + 14 + col * 202
            draw.text((slot_x + 4, y + 41), PHASES[col], font=font(12), fill=MUTED)
            # nearest-neighbour preview preserves the flat pixel clusters.
            thumb = frame.resize((156, 156), Image.Resampling.NEAREST)
            canvas.alpha_composite(thumb, (slot_x + 18, y + 65))
    canvas.convert("RGB").save(path)


def run(root: Path, frame_size: int = 256) -> None:
    root = root.resolve()
    raw = root / "raw"
    missing = [str(raw / f"{name}.png") for name in SHEETS if not (raw / f"{name}.png").is_file()]
    if missing:
        raise SystemExit("Missing raw sheets; no exports written:\n" + "\n".join(missing))
    if frame_size < 32:
        raise SystemExit("Frame size must be at least 32 px")
    images, grids = {}, {}
    source_manifest = {}
    warnings = []
    for name in SHEETS:
        source = raw / f"{name}.png"
        with Image.open(source) as opened:
            image = opened.convert("RGBA")
        alpha = image.getchannel("A")
        lo, hi = alpha.getextrema()
        if lo == 255:
            raise SystemExit(f"{source}: opaque background; extraction cannot remove it")
        if hi == 0:
            raise SystemExit(f"{source}: no visible pixels")
        images[name], grids[name] = image, rects(image, len(SHEETS[name]))
        source_manifest[name] = {"path": f"raw/{name}.png", "sha256": sha256(source),
                                 "size": list(image.size), "alpha_extrema": [lo, hi]}
    # Advance is a separate single-row generation at twice the source pixel
    # resolution. Match its units to the existing sheets without resizing them.
    reference_cell = images["physical"].width / 3
    source_units = {name: reference_cell / (image.width / 3) for name, image in images.items()}
    reference_grids = [grid for name, grid in grids.items() if len(SHEETS[name]) == 4]
    max_width = max(b[2] - b[0] for grid in reference_grids for row in grid for b in row)
    max_height = max(b[3] - b[1] for grid in reference_grids for row in grid for b in row)
    # Shared over ALL 60 frames, not just within a row. This cannot equalize a
    # small onset and a large impact, or enlarge one effect relative to another.
    scale = min((frame_size - 24) / max_width, (frame_size - 24) / max_height)
    for directory in ["frames", "strips", "review"]:
        (root / directory).mkdir(parents=True, exist_ok=True)
    normalized = {}
    exports = {}
    for sheet, names in SHEETS.items():
        image = images[sheet]
        sheet_scale = scale * source_units[sheet]
        for row, name in enumerate(names):
            crops = [image.crop(rect) for rect in grids[sheet][row]]
            bounds = union_bounds(crops)
            center_x, center_y = (bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2
            left = round(frame_size / 2 - center_x * sheet_scale)
            top = round(frame_size / 2 - center_y * sheet_scale)
            output_frames = []
            paths = []
            for index, crop in enumerate(crops):
                # Generated transparency may contain near-zero alpha over the
                # whole canvas. Ignore it ONLY for geometric measurement; the
                # copied/resampled pixels retain original unthresholded alpha.
                bbox = crop.getchannel("A").point(lambda a: 255 if a >= 64 else 0).getbbox()
                if bbox and (bbox[0] <= 1 or bbox[1] <= 1 or bbox[2] >= crop.width - 1 or bbox[3] >= crop.height - 1):
                    warnings.append(f"{sheet}/{name}/frame-{index + 1}: alpha >= 64 reaches a crop boundary; inspect for clipping or adjacent art")
                frame = Image.new("RGBA", (frame_size, frame_size), (0, 0, 0, 0))
                resized = crop.resize((max(1, round(crop.width * sheet_scale)), max(1, round(crop.height * sheet_scale))), Image.Resampling.NEAREST)
                frame.alpha_composite(resized, (left, top))
                frame_path = root / "frames" / f"{name}-{index + 1:02}.png"
                frame.save(frame_path)
                paths.append({"path": frame_path.relative_to(root).as_posix(), "sha256": sha256(frame_path),
                              "alpha_bbox": frame.getchannel("A").getbbox()})
                output_frames.append(frame)
            strip = Image.new("RGBA", (frame_size * 3, frame_size), (0, 0, 0, 0))
            for col, frame in enumerate(output_frames):
                strip.alpha_composite(frame, (col * frame_size, 0))
            strip_path = root / "strips" / f"{name}.png"
            strip.save(strip_path)
            normalized[name] = output_frames
            exports[name] = {"sheet": sheet, "row": row, "source_rects": grids[sheet][row], "source_unit_factor": source_units[sheet], "scale": sheet_scale,
                             "union_alpha_bounds": bounds, "shared_row_offset": [left, top],
                             "frames": paths, "strip": {"path": strip_path.relative_to(root).as_posix(), "sha256": sha256(strip_path)}}
    original_names = [name for sheet, names in SHEETS.items() if sheet not in ["reactions", "advance", "evade-afterimage"] for name in names]
    all_names = [name for names in SHEETS.values() for name in names]
    other_names = [name for name in original_names if name not in PHYSICAL]
    contact_sheet(root / "review" / "physical-six.png", "PHYSICAL IMPACTS / SIX EFFECTS", PHYSICAL, normalized, 1)
    contact_sheet(root / "review" / "other-fourteen.png", "MAGIC, SUPPORT & STATUS / FOURTEEN EFFECTS", other_names, normalized, 2)
    contact_sheet(root / "review" / "all-twenty.png", "TWENTY IMPACT & SUPPORT EFFECTS / FRONT-ON REVIEW", original_names, normalized, 2)
    contact_sheet(root / "review" / "all-twenty-four.png", "TWENTY-FOUR EFFECTS / FRONT-ON REVIEW", [name for name in all_names if name not in ["advance", "evade-afterimage"]], normalized, 2)
    contact_sheet(root / "review" / "reactions-five.png", "CASTING & REACTIONS / FIVE EFFECTS", ["spell-circle", "block", "counter", "evade", "retreat"], normalized, 1)
    contact_sheet(root / "review" / "reactions-six.png", "CASTING & REACTIONS / SIX EFFECTS", ["spell-circle", "block", "counter", "evade", "retreat", "advance"], normalized, 1)
    contact_sheet(root / "review" / "all-twenty-five.png", "TWENTY-FIVE EFFECTS / FRONT-ON REVIEW", [name for name in all_names if name != "evade-afterimage"], normalized, 2)
    contact_sheet(root / "review" / "all-twenty-six.png", "ALL TWENTY-SIX EFFECTS / FRONT-ON REVIEW", all_names, normalized, 2)
    contact_sheet(root / "review" / "evade-afterimage.png", "EVADE / AFTERIMAGE OPTION", ["evade-afterimage"], normalized, 1)
    manifest = {"purpose": "preview-only; no game integration", "frame_count": 3,
                "frame_size": [frame_size, frame_size], "global_scale": scale,
                "resampling": "nearest-neighbour", "centering": "union of all three frames; one offset per row",
                "crop_boundaries": "quiet gutters near nominal grid: 3 columns; 4 rows, or 1 for Advance/afterimage",
                "source_unit_factors": source_units,
                "measurement_alpha_threshold": 64, "sources": source_manifest, "effects": exports, "warnings": warnings,
                "reviews": [{"path": p.relative_to(root).as_posix(), "sha256": sha256(p)} for p in sorted((root / "review").glob("*.png"))]}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(exports)} effects, {len(exports) * 3} transparent frames, {len(exports)} strips, 9 review sheets")
    print(f"Global scale: {scale:.6f}; {len(warnings)} crop warnings")
    for warning in warnings:
        print("WARNING:", warning)
    package = root / "front-on-v4-review.zip"
    package_files = sorted(path for path in root.rglob("*") if path.is_file() and path != package and "__pycache__" not in path.parts)
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in package_files:
            archive.write(path, path.relative_to(root).as_posix())
    print(f"ZIP: {package.name}; {len(package_files)} files; SHA256 {sha256(package)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--frame-size", type=int, default=256)
    args = parser.parse_args()
    run(args.root, args.frame_size)
