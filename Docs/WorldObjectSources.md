# World-builder object sources

This pass adds 32 object sprites alongside, not inside, the requested 100-tile count. Sources were generated with the built-in ImageGen tool; exact prompts and original output paths are in [world-objects](../ArtSource/RemasterExpansion/world-objects/generation-record.json). [Online reference evidence](../References/WorldBuilder100/README.md) separates inspected images from the blocked archive download.

| Source | Native output | States and placement |
| --- | --- | --- |
| Canoe/rowboat | Four 128×128 sprites | Down, left, right, up; center pivot; 32 PPU |
| Sailing ship | Four 128×128 sprites | Down, left, right, up; center pivot; 32 PPU |
| Airship | Four 128×128 sprites | Down, left, right, up; center pivot; 32 PPU |
| Propeller plane | Four 128×128 sprites | Down, left, right, up; center pivot; 32 PPU; optional original extension |
| Trees | Eight 64×64 sprites | Oak, pine, snow pine, palm, mangrove, dead tree, autumn tree, jungle tree; bottom-center pivot; 32 PPU |
| Landmarks | Eight 64×64 sprites | Granite peak, snow peak, desert mesa, volcano, forest/snow/desert/lava cavern entrances; bottom-center pivot; 32 PPU |

The 128 px vehicle canvas spans four 32 px ground cells; the 64 px prop canvas spans two. Visible ink occupies less than the full canvas. A map designer can select suitable placement and collision footprints without assuming the transparent canvas is solid. These sheets supply static directions and objects; no vehicle movement, propeller animation, boarding behavior or collision logic is implemented by exporting them.

## Source inspection

All seven generated images were visually inspected. The chosen six preserve the approved warm timber, cream cloth, blue/red trim and gold vehicle fittings. Trees retain distinct crown silhouettes and complete roots/trunks. Mountain landmarks and cave mouths use matching rock families; cave recesses are opaque dark interiors, with alpha reserved for the outside silhouette.

Airship v1 repeated the front view in the up/rear slot. A targeted ImageGen edit created v2 with the nose at the top, red tail fins nearest the viewer and visible stern cabin. The original remains preserved and explicitly excluded. The corrected four directions are distinct. The other vehicle sheets have visible differences between bow/front and stern/back views. Side views follow the project's existing oblique sprite convention.

The plane is a requested optional fantasy vehicle in the same palette, not a claim that original FFII includes this aircraft. Mountains, trees and cave variants are reusable interpretations; they do not reconstruct specific original map coordinates.

Final native review inspected the complete 32-object contact sheet and actual terrain overlays. All four vehicle directions remain distinct, with the corrected airship rear view readable; trees retain separate crown/trunk silhouettes and the four cave entrances have dark recesses and intact arches. No obvious clipping was seen. The object contact sheet uses separate integer zoom factors for 64 px and 128 px objects; scene proofs preserve their actual shared 32 PPU scale. The full exporter checks native source reconstruction and alpha separately. These are static sprite candidates; runtime integration and Unity playback remain pending.
