"""Preview-only extraction of the eight composed-v5 addition effects.

Raw PNGs and game code are never modified. Three frames retain one scale and
one registration offset; only the review contacts have opaque backgrounds.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
SHEETS = {
    "defense": ["block-hit", "poise-hit", "block-break", "poise-break"],
    "statuses": ["status-apply", "status-tick", "status-clear", "status-resist"],
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    missing = [str(ROOT / "raw" / f"{name}.png") for name in SHEETS if not (ROOT / "raw" / f"{name}.png").is_file()]
    if missing:
        raise SystemExit("Missing raw PNGs; no exports written:\n" + "\n".join(missing))
    # Reuse the reviewed gutter/registration and contact-sheet implementation,
    # without executing v4's exporter or writing a byte into its folder.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("v4_export_helpers", ROOT.parent / "front-on-v4" / "exporter.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    base = json.loads((ROOT.parent / "front-on-v4" / "manifest.json").read_text(encoding="utf-8"))
    scale = base["global_scale"]
    reference = base["sources"]["physical"]["size"][0] / 3
    destination = ROOT / "additions"
    for name in ["frames", "strips", "review"]:
        (destination / name).mkdir(parents=True, exist_ok=True)
    frames, exports, sources, warnings = {}, {}, {}, []
    for sheet, names in SHEETS.items():
        path = ROOT / "raw" / f"{sheet}.png"
        if sheet == "defense" and (ROOT / "raw" / "defense-v2.png").is_file():
            path = ROOT / "raw" / "defense-v2.png"
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
        extrema = image.getchannel("A").getextrema()
        if extrema[0] == 255 or extrema[1] == 0:
            raise SystemExit(f"{path.name}: expected visible art with transparent background")
        grid = helper.rects(image, 4)
        if sheet == "statuses":
            # The landscape sheet has wide outside margins: nominal edge cells
            # are not centered on their artwork. Calibrate each source column
            # ONCE using all four rows, then crop equal-width windows. This is
            # layout extraction, not per-frame silhouette or scale normalization.
            columns = []
            for col in range(3):
                left, _, right, _ = grid[0][col]
                bounds = image.crop((left, 0, right, image.height)).getchannel("A").point(lambda a: 255 if a >= 64 else 0).getbbox()
                columns.append((left + (bounds[0] + bounds[2]) / 2, bounds[2] - bounds[0]))
            column_width = max(width for _, width in columns) + 24
            for row in grid:
                for col, (_, top, _, bottom) in enumerate(row):
                    left = round(columns[col][0] - column_width / 2)
                    row[col] = (left, top, left + column_width, bottom)
        unit = reference / (image.width / 3)
        source_scale = scale * unit
        sources[sheet] = {"path": f"../raw/{path.name}", "size": list(image.size), "sha256": digest(path), "unit_factor": unit}
        for row, name in enumerate(names):
            crops = [image.crop(rect) for rect in grid[row]]
            union = helper.union_bounds(crops)
            offset = [round(128 - (union[0] + union[2]) / 2 * source_scale),
                      round(128 - (union[1] + union[3]) / 2 * source_scale)]
            frames[name] = []
            frame_entries = []
            for index, crop in enumerate(crops):
                bounds = crop.getchannel("A").point(lambda a: 255 if a >= 64 else 0).getbbox()
                if bounds and (bounds[0] <= 1 or bounds[1] <= 1 or bounds[2] >= crop.width - 1 or bounds[3] >= crop.height - 1):
                    warnings.append(f"{name}/{index + 1}: inspect crop boundary")
                frame = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
                resized = crop.resize((max(1, round(crop.width * source_scale)), max(1, round(crop.height * source_scale))), Image.Resampling.NEAREST)
                frame.alpha_composite(resized, tuple(offset))
                output = destination / "frames" / f"{name}-{index + 1:02}.png"
                frame.save(output)
                frames[name].append(frame)
                frame_entries.append({"path": output.relative_to(destination).as_posix(), "sha256": digest(output)})
            strip = Image.new("RGBA", (768, 256), (0, 0, 0, 0))
            for index, frame in enumerate(frames[name]):
                strip.alpha_composite(frame, (index * 256, 0))
            output = destination / "strips" / f"{name}.png"
            strip.save(output)
            exports[name] = {"sheet": sheet, "row": row, "source_rects": grid[row], "scale": source_scale,
                             "shared_offset": offset, "frames": frame_entries,
                             "strip": {"path": output.relative_to(destination).as_posix(), "sha256": digest(output)}}
    helper.contact_sheet(destination / "review" / "defense-four.png", "DEFENSE / HIT & BREAK", SHEETS["defense"], frames, 1)
    helper.contact_sheet(destination / "review" / "status-four.png", "STATUS / APPLY, TICK, CLEAR & RESIST", SHEETS["statuses"], frames, 1)
    helper.contact_sheet(destination / "review" / "all-eight.png", "EIGHT ADDITIONAL EFFECTS / PREVIEW ONLY", [name for names in SHEETS.values() for name in names], frames, 2)
    manifest = {"purpose": "composed-v5 preview only; no runtime integration", "frame_count": 3,
                "frame_size": [256, 256], "reference_scale": scale, "sources": sources,
                "effects": exports, "warnings": warnings,
                "reviews": [{"path": p.relative_to(destination).as_posix(), "sha256": digest(p)} for p in sorted((destination / "review").glob("*.png"))]}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(exports)} strips / {len(exports) * 3} transparent frames / 3 contacts; {len(warnings)} crop warnings")
    for warning in warnings:
        print("WARNING:", warning)


if __name__ == "__main__":
    main()
