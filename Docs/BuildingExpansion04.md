# Building corners and procedural side tags

Two matching 64x64 / 64 PPU building kits provide 32 selected tiles: cream stone walls with flagstone floors and blue slate roofs with timber fascia. Each kit includes four convex corners, four concave corners, four straight edges, three interior fills and a grass exterior fill. All tiles are opaque; the roof kit is a separate layer/family rather than a transparent overlay.

The four initial lower concave corners did not keep their outside grass bites on the correct edges. They remain preserved as candidate PNGs, explicitly blocked in the procedural catalog and linked to their corrected `inner-sw-v2` / `inner-se-v2` replacements. The batch therefore contains 37 new PNGs, of which 32 form the selected kits. The stone southeast v2 also retained a top-edge grass intrusion and is superseded by inner-se-v3.

## Review

- [Selected tiles and actual assembled rooms/courtyards](../Review/remaster-expansion/building-expansion04/index.html)
- [Search every tile, inspect four side tags and compare neighbors](../Review/procedural-tiles/index.html)
- [Procedural tile sidecar](../Assets/Art/Production/procedural-tiles.json)
- [Matcher usage and tag semantics](ProceduralTiles.md)

Source masters and full ImageGen prompts are preserved in `ArtSource/RemasterExpansion/building-expansion04/`, with correction prompts in `corner-revisions/generation.json`. Original separator/gutter candidates and a rejected intermediate correction remain under `ArtSource/Revisions/building-expansion04/`. Only the selected correction cells are exported from the revised atlases; earlier source pixels and production PNGs are not overwritten.

The batch helper verifies the selected native sizes, hashes and opacity, creates four actual tile assemblies, and checks all 1,326 earlier production PNGs and their metadata byte for byte. The standard reconstruction verifier also covers all retained candidates.

```text
node Tools/remaster-expansion/building-expansion04.cjs
node Tools/remaster-expansion/verify.cjs
node Tools/procedural-tiles/build.cjs
node --test Tools/procedural-tiles/test.cjs
```

Logical edge profiles enable candidate matching; they do not prove pixel-perfect joins. Wall widths, texture phases and lighting can differ slightly at seams. Tags do not imply walkability or collision. Unity runtime generation and RuleTile/Tilemap integration remain unverified.
