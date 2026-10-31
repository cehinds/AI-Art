# Sickbed layer staging V1

This staging uses the existing `white-sickbed.png` component as the complete rear backing, with an alpha-trimmed Firion proxy, a visible sheet crop, a lower footboard crop, and a separately generated dialogue bubble. The backing retains pixels that sit behind the actor and sheet; it is not a clean reconstruction of hidden mattress or frame art. All build inputs, including the exact bubble prompt, are copied into `sources/`, so the build does not need the original asset repositories.

Workflow status follows `components → isolate → split layers → interpolate hidden`: existing components selected; mechanical PNG crop/scale only; visible artwork separated into the listed layers; no hidden mattress or frame pixels reconstructed. The manifest labels source visibility and hidden reconstruction explicitly.

## Layer contract

All exported layer PNGs use the same 214×398 canvas and origin. Composite in ascending `z` order from `manifest.json`:

1. `rear-backing.png` — existing visible bed artwork as rear backing.
2. `actor-proxy.png` — alpha-trimmed Firion down sprite, nearest-neighbor scaled to 80×140 and placed at `[67,64]`. This is only an occlusion proxy; the pose is standing, not lying Scott.
3. `sheet-overlay.png` — visible source crop `[12,122,190,176]`, placed at its source coordinate. It covers the proxy below the face; it does not reconstruct hidden mattress pixels.
4. `foreground-footboard.png` — crop of the existing lower bed, placed at y=278.
5. `dialogue-slot.png` — generated standalone bubble crop, topmost in the stack. Its master and exact prompt are preserved in `sources/`.

`index.html` is a local toggle gallery with each occlusion stage displayed below the controls. `assembled.png` includes the bubble layer.

## Rebuild and verify

From the repository root:

```powershell
node AssetWork/BedLayersV1/build.cjs
node AssetWork/BedLayersV1/verify.cjs
```

The builder only decodes PNGs, alpha-trims/crops existing pixels, nearest-neighbor scales the Firion proxy and bubble crop, and alpha-composites layers. The verifier checks common canvas dimensions, required z-order, stage outputs, visible occlusion of the proxy by the sheet, and the dialogue-stage difference.
