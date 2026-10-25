"""Export uncropped card paintings as runtime WebP images."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[1] / "assets" / "cards"
CARDS = (
    "slashing-strike", "shield-defend", "gorefire-slash", "weapon-technique",
    "bloodletting", "iron-resolve", "last-stand",
)
IDENTITIES = {
    "slashing-strike": {"kind": "equipmentProfile", "id": "bladeAttack"},
    "shield-defend": {"kind": "equipmentProfile", "id": "shieldGuard"},
    "gorefire-slash": {"kind": "card", "id": "gorefireSlash"},
    "weapon-technique": {"kind": "equipmentProfile", "id": "weaponTechnique"},
    "bloodletting": {"kind": "card", "id": "bloodletting"},
    "iron-resolve": {"kind": "card", "id": "ironResolve"},
    "last-stand": {"kind": "card", "id": "lastStand"},
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    for name in CARDS:
        source = HERE / "sources" / f"{name}.png"
        with Image.open(source) as image:
            image.load()
            if image.size != (1536, 1024):
                raise ValueError(f"Unexpected source size: {source}: {image.size}")
            entry = {
                "name": name,
                "identity": IDENTITIES[name],
                "source": str(source.relative_to(HERE)).replace("\\", "/"),
                "sourceSize": list(image.size),
                "sourceSha256": digest(source),
                "exports": [],
            }
            rgb = image.convert("RGB")
            for width in (1024, 512):
                export = ASSETS / f"{name}-{width}.webp"
                resized = rgb.resize((width, round(width * 2 / 3)), Image.Resampling.LANCZOS)
                resized.save(export, format="WEBP", quality=86, method=6)
                with Image.open(export) as check:
                    check.load()
                    if check.size != resized.size:
                        raise ValueError(f"Invalid export dimensions: {export}")
                entry["exports"].append({
                    "path": str(export.relative_to(HERE.parents[1])).replace("\\", "/"),
                    "size": list(resized.size),
                    "bytes": export.stat().st_size,
                    "sha256": digest(export),
                })
            manifest.append(entry)
    (HERE / "manifest.json").write_text(
        json.dumps({"version": 1, "cards": manifest}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
