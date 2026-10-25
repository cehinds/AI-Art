# Extreme biome source tiles

Five selected built-in image_gen sheets supply 50 original terrain tiles for the WorldBuilder100 collection. They cover snow/tundra, desert dunes, volcanic ash, cavern stone and mountain cliffs. Source generation and source inspection are complete. All five native patch sets are accepted as candidates after independent proof review.

## Selected sources and contract

| Sheet key | Selected source | Owner | Inside material |
|---|---|---|---|
| snow-tundra-v2 | ArtSource/RemasterExpansion/biomes-extreme/snow-tundra-v2.png | biome-snow-tundra-v2 | Pale blue-white textured snow with frost flecks |
| desert-dunes | ArtSource/RemasterExpansion/biomes-extreme/desert-dunes-v2.png | biome-desert-dunes | Golden wind-rippled sand |
| volcanic-ash | ArtSource/RemasterExpansion/biomes-extreme/volcanic-ash-v2.png | biome-volcanic-ash | Dark ash/basalt and muted cinder flecks |
| cavern-stone | ArtSource/RemasterExpansion/biomes-extreme/cavern-stone-v2.png | biome-cavern-stone | Walkable warm-brown cave floor |
| mountain-cliffs | ArtSource/RemasterExpansion/biomes-extreme/mountain-cliffs-v3.png | biome-mountain-cliffs | Grey cracked stone plateau |

Every sheet is five columns by two rows with square source cells. Row-major states: nw, n, ne, w, center, e, sw, s, se, center-alt. Descriptor kind tile, group tiles, target32x32, PPU32 and center pivot {x:0.5,y:0.5}. Owners are prefixed biome- to distinguish older terrain families.

Source masters are1983x793 pixels, a small integer rounding difference from exact2.5:1. The inspected extraction region is {left:0,top:0,width:1980,height:792}, giving ten396x396 square cells. Only the final3 source columns and1 source row are outside that region. This is an explicit square-cell crop, not distortion of nonsquare cells; exporter provenance records the actual source rectangles.

All tiles use full opaque material coverage. No source is a transparent prop, scenic screenshot, copied published tile or enlarged legacy production PNG.

## Online visual research actually inspected

I searched official FFII/Pixel Remaster sources, read the [Square Enix-published FFII Steam page](https://store.steampowered.com/app/1173780/FINAL_FANTASY_II/?l=english) and [official Pixel Remaster site](https://finalfantasypixelremaster.square-enix-games.com/en_US/), then fetched the official Steam screenshot list through its appdetails endpoint.

Four Square Enix-published Steam screenshots were downloaded as JPEGs under ArtSource/RemasterExpansion/biomes-extreme/references/ and actually inspected with view_image. They are outside Assets and are research references only. Exact image URLs and JPEG hashes are recorded in references/research.json.

- [Steam screenshot0: world terrain](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1173780/ss_2af62101b84c99e100b677124fd77dd41e55ba4b.1920x1080.jpg?t=1773222959): repeated grass at consistent density, dark lower forest shadows, narrow ochre coastline and cobalt water ripples.
- [Steam screenshot3: interior](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1173780/ss_db301c64d4f5e368e87a9076d79b95ca53a9cadd.1920x1080.jpg?t=1773222959): repeatable low-contrast floor material and consistent wall/carpet boundary thickness. Used only for pixel density/material treatment.
- [Steam screenshot6: marsh and river](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1173780/ss_6e7a0e5fd4140c569eb2913f85efa92655cc8c69.1920x1080.jpg?t=1773222959): blue-green ground patch with irregular pixel transitions to grass, fully material-filled center, thin riverbank and uniform ripple scale.
- [Steam screenshot9: terrain in bestiary view](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1173780/ss_ee65e10ec3d6007dbaec3473d11c490040ab00e3.1920x1080.jpg?t=1773222959): repeated grey-ochre mountain masses with top highlights/lower slopes and material repetition across grass/forest. Its perspective framing, UI and characters were not adopted.

These screenshots inform topology, density and lighting, not literal reproduction. They do not directly depict all five new biomes. Snow/desert/ash/cave palettes are original variations guided by the already approved project environment sheets. No published screenshot pixels were extracted into the deliverable tiles, and the screenshots were not passed as imagegen copying targets.

## Creative source process and preservation

The project snow-ice, desert-ruins and cave environment masters were inspected before generation and served as style/material inputs. All art pixels came from built-in image_gen. No code painted, filled, aligned or synthesized terrain pixels.

Each source requests one coherent nine-piece transition patch, packed into ten cells, with the tenth cell a fully textured center variant. Corners are L-shaped boundaries and edge cells have one boundary. Both center states contain full ground material to every edge; the snow center has no isolated white island in a pond.

First candidates for desert, volcanic, cavern and mountain included unwanted atlas divider/frame strokes. Targeted imagegen revisions removed those lines while preserving cell order, palette and transition design. The four earlier PNGs remain preserved and listed in excluded-sources.json. Ten source PNGs are registered: five selected and five excluded. Mountain v2 was additionally excluded after native proof revealed a structural side-border defect; see the native review below.

Full prompts, original Codex image output paths, reference paths, dimensions, hashes and selected flags are in sibling .prompt.txt files and generation-record.json. Existing production sources and the shared exporter were not edited by this source task.

## Source QA and pending native proof

All five selected generated images were visually inspected for the ten-state layout, opaque coverage, coherent material scale, filled center/center-alt and removed atlas divider lines. Snow-tundra-v2 was also independently checked by the root agent: slot orientation/order and full textured snow center read correctly.

Joining edge wavelengths and texture phases can differ between independently drawn cells. Therefore source inspection alone does not establish seamlessness, repeatability at32px, collision meaning or original-map completeness. The pipeline produced actual native PNG nine-patch assemblies and center repetitions under Review/remaster-expansion/worldbuilder100/. Independent review of all five initial native sets confirms the ten-state role order, fully filled center variants, opaque art and no surviving atlas-divider strokes. Snow, desert, volcanic and cavern form readable rectangular material patches; texture phase and boundary wavelengths remain visible on close inspection, so they are candidates rather than claims of pixel-perfect seamlessness.

Mountain v2 failed the visual assembly check: repeated W/E side cells created horizontal notches and stepped brown intrusions. This was treated as a structural defect requiring correction, not merely a caveat. Targeted imagegen v3 replaced only the side-border design with continuous vertical boulder strips and no horizontal endcaps. Root independently inspected the v3 source and confirmed the material improvement; corner widths still vary naturally.

Before descriptor mutation, the pipeline backed up all132 current-batch native PNGs and metadata plus manifest/review artifacts to Review/remaster-expansion/worldbuilder100/rejected-candidates/001-worldbuilder100-visual-candidate. Root explicitly authorized a controlled current-batch revision while all282 pre-existing production PNGs/metadata remain immutable. The mountain descriptor now selects v3 with the same tile IDs; both earlier source versions remain preserved/excluded. Refreshed mountain native proof was independently inspected, including base, alternate-center and decorated-scene assemblies. The W/E horizontal endcaps and stepped brown intrusions are gone, vertical cliff bands are continuous, and no black atlas divider strokes remain. Root independently confirmed the same correction. No further source generation was necessary.

Final result: NATIVE_PATCH_CANDIDATE_PASS for all five kits. The packed32px contacts preserve all ten roles per biome; center and center-alt remain fully textured. Independent native PNG inspection confirms all50 tiles are32x32, fully opaque, PPU32 and center-pivoted. ArtSource/RemasterExpansion/biomes-extreme/visual-qa.json records native asset hashes, proof hashes and per-biome findings.

Remaining limits: snow frost patterns, sand ripples, ash/pebble motifs and mountain cracks have visible repetition and phase changes; minor boundary wavelength/corner width variation remains. This is approval of readable candidate patch structure, not pixel-perfect seamlessness, exact original-map reconstruction, collision semantics, Unity import or gameplay runtime.



