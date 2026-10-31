# Altair Kit V1

This add-on holds generated building, sign, prop, and terrain art for the Altair remake. Generated full-building PNG masters remain byte-for-byte under `ArtSource/AltairKitV1/`. Each building uses a paired black/white roof mask: white selects existing roof pixels, black retains facade pixels. The exporter derives both layers from the same source, alpha-trims transparent margins, then resizes to the declared tile footprint with nearest-neighbor sampling. It does not paint, recolor, or fill occluded areas.

Supported layers, back to front: `ground`, `terrain-edge`, `facade`, `trim`, `roof`, `detail`, `sign`. Optional additional layers must use the same full source canvas as the building source and receive the same crop and resize. The `Tools/altair-kit-v1/kit.json` manifest stores source and mask hashes, tile footprints, anchors, ground footprints, collision declarations, and reference notes.

The production binder contract is `Assets/Art/Production/AltairKitV1/buildings/{id}-facade.png`, `{id}-roof.png`, and optional `{id}-trim.png`; assembled composites use `{id}.png`. Signs, props, and terrain use their own `signs/`, `props/`, and `terrain/` directories. Building IDs and tile footprints are: `item-shop` 3×5, `inn` 5×5, `headquarters` 7×9, `sanctuary` 7×5, `magic-shop` 3×5, `armor-shop` 5×5, `home` 3×5, `weapon-shop` 5×5, and `smithy` 3×4. Headquarters art must preserve the southwest transparent notch at x<4,y≥5. The kit also exports six 32×32 signs, a transparent 64×64 fountain, and an opaque 32×32 cream-stone stair tile. The stair treads run horizontally and connect to matching copies; the map traversal runs north–south.

Coordinates use a top-left origin with x increasing right and y increasing down. Building anchors mark the pixel at the entrance threshold; the game places the object from its full canvas and owns all collision shapes separately. Exported art declares `collision: none` to avoid implying a second collider. Runtime footprint and collision are maintained in `AI-Remake-FF2/Assets/FF2/Core/AltairTownPlan.cs`.

Run from the repository root once the manifest has complete sources and descriptors:

```powershell
node Tools/altair-kit-v1/export.cjs
```

Validate the already-exported, frozen kit without writing assets or regenerating the contact sheet:

```powershell
node Tools/altair-kit-v1/verify.cjs
```

The read-only verifier checks manifest completeness, source/output/dependency SHA-256 values, PNG dimensions, binary masks, reconstructed composites and layer alpha, the headquarters door anchor and transparent southwest notch, all sign/fountain/steps outputs, and unlisted or missing production PNGs. It exits nonzero and prints each issue when a check fails.

The exporter writes only `Assets/Art/Production/AltairKitV1/` and `Review/altair-kit-v1/`. Derived files in these kit-owned directories can be refreshed from the manifest; raw generated masters remain unchanged. The standalone [review gallery](../../Review/altair-kit-v1/index.html) shows composites, source layers, dimensions, anchors, footprints, collision types, hashes, and the [nine-building contact sheet](../../Review/altair-kit-v1/contact-sheet.png). No existing catalog, root README, Unity metadata, or game checkout is modified by this kit.

`manifest.json` hashes the existing reusable cream wall, directional terrace edges, and horizontal/vertical bridge tiles by their repository paths. They are references to existing files; the kit does not create duplicate Unity assets or `.meta` GUIDs for them. Current stair candidates are excluded from runtime reuse because both are darker dungeon/castle art; use an orientation-aligned procedural stair or generate a matching Altair step set.

Reference screenshots inform composition and palette only. Do not use screenshot crops as production sprites. The generated assets are new artwork and inclusion here does not grant rights to Final Fantasy II assets or imply Square Enix endorsement. Preserve generation prompt/tool/date/output details beside each source master; do not imply a new license.

Validation covers PNG encoding/transparency, source hashes, mask dimensions and binary values, metadata bounds, and collisions. It does not prove pixel-art quality, exact map placement, licensing, Unity import, or runtime behavior.
