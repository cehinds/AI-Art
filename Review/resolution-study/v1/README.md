# Higher resolution candidates

User requested higher resolution sprites, potentially 64px or 128px. This study supplies six native transparent PNGs: Firion, Maria and Goblin at both **64 x 64** and **128 x 128**. `comparison.png` displays both sizes in equal 256 x 256 areas, using nearest-neighbor 4x and 2x respectively.

The master was newly generated with built-in ImageGen using the approved Firion/environment concepts and current Maria battle sheet as references. Prompt and original output path: `ArtSource/ResolutionStudy/v1/prompt.md`. The character design is a new candidate, not a pixel-identical continuation of every existing pose. Both export sizes share this master; the 64px images are not separately hand-tuned.

Recommendation for review: 64 x 64 regular actor frames; 128 x 128 large enemies and bosses. A uniform 128 x 128 actor set is also possible if the finer detail is preferred. Frame dimensions are texture sizes, not a decision to enlarge actors on screen. Any library migration must retain the intended world footprint through per-category pixels-per-unit, update tiles and camera sampling coherently, and reserve larger animation canvases where weapon reach requires it. The existing importer still declares 16 PPU; these candidates remain outside Assets and must not be dropped in as direct replacements with that setting.

Generate the mechanical exports with `node Tools/resolution-study/export-v1.cjs`. It checks clean alpha separators, native dimensions and binary alpha. `manifest.json` records source/output hashes, crops, native sizes, scales and pivots. All six exported images and the comparison were inspected; Unity import/play mode is not part of this study. Existing production files and manifests are unchanged.
