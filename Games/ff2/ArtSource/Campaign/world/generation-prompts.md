# World Sprite Generation Prompts and Provenance

All listed images were produced through the built-in ImageGen tool. Sources are original generated artwork, not extracted game sprites. The two review boards were supplied as style references only. Final source dimensions and selection status are in `../../../../Docs/WorldSpriteCoverage.md` and `excluded-sources.json`.

## NPC sheets

### Named characters: Hilda, Scott, Cid, Paul

Initial static-direction source: `npc-named-hilda-scott-cid-paul-4x4.png` (kept as a rejected predecessor after the animation layout was requested).

```text
Use case: stylized-concept. Asset type: source sprite sheet for an original FFII-inspired Unity remake. Reference image 1 Review/art/02-firion-study.png and reference image 2 Review/art/03-environment-kit.png are style references only; match their crisp pixel clusters, compact proportions, dark navy outlines, restrained highlights, and rich but controlled palette. Primary request: one coherent transparent sprite sheet containing exactly sixteen distinct named-character sprites in a perfectly regular 4-column by 4-row grid, cells equal size. Each row is one character, top to bottom: Hilda, Scott, Cid, Paul. Each column is one direction, left to right: facing down toward viewer, facing left, facing right, facing up away. Visually approximate recognizable role-appropriate FFII character identities using restrained, readable costume cues; do not claim historical sprite accuracy. All are complete standing field sprites, same consistent compact proportions and scale, bottom-center aligned, generous cell padding. Style/medium: polished GBA-era pixel art, large square pixel clusters, no smoothing. Composition: strict regular grid, identical transparent cells, every sprite fully inside its cell, no overlap. Constraints: true transparent background and transparent gaps; no labels, text, letters, numerals, grid lines, borders, panels, scenery, floor, shadows, watermarks, or collage; no extra sprites; original redrawn artwork, not extracted game sprites.
```

Rejected first animated layout: `npc-named-hilda-scott-cid-paul-candidate-8x4.png`.

```text
Use case: stylized-concept. Asset type: original source sprite sheet for an original FFII-inspired Unity remake. Input images: reference image 1 Review/art/02-firion-study.png and reference image 2 Review/art/03-environment-kit.png are style references only; match its crisp square pixel clusters, dark navy outlines, compact GBA-era proportions, restrained bright highlights, rich controlled palette. Primary request: exactly 32 complete field-character sprites in one coherent, perfectly regular 8-column by 4-row transparent grid, wide landscape 2:1 sheet. Rows top to bottom show four distinct character identities: Hilda, Scott, Cid, Paul. Columns left to right show that row's same character and exact sequence: down-facing idle, down-facing walk-step, left-facing idle, left-facing walk-step, right-facing idle, right-facing walk-step, up-facing idle, up-facing walk-step. Give the step pose a small clearly readable alternating foot/arm change while preserving body placement, costume, palette, scale, and direction. Role-appropriate visual approximations only; do not claim historical pixel-accurate costumes. All cells exactly equal size with generous gutters, each complete figure fully inside its cell, feet aligned to a shared bottom baseline per row, consistent silhouette scale. Transparent empty backdrop and gutters. Constraints: no text, labels, letters, numerals, grid lines, borders, panels, floor, shadows, scenery, watermarks, or extra images; no cell may contain multiple poses; no smoothing; original redrawn art, not extracted game sprites.
```

Final selected edit: `npc-named-hilda-scott-cid-paul-edited-transparent-8x4.png`.

```text
Edit the supplied sprite sheet into a true transparent PNG. Preserve exactly 8 columns × 4 rows, cell layout, transparent background, character identities, costumes, palettes, scale, bottom baselines, and all four facing directions. Change ONLY the second pose in each directional pair for every character: columns 2, 4, 6, and 8 (1-based) must show a clearly readable alternate walking step, with opposite foot forward and matching opposite arm swing from the preceding idle/step pose. The current pairs are too similar; make the stance unmistakably different without changing facing direction or silhouette proportions. Keep first pose of each pair as idle. Do not add text, labels, borders, shadows, or extra characters. Entire sheet remains original crisp pixel art.
```

The first edit attempt (`npc-named-hilda-scott-cid-paul-edited-8x4.png`) was rejected because it rendered an opaque checkerboard. It is preserved and listed in `excluded-sources.json`. Its prompt was:

```text
Edit the supplied transparent sprite sheet. Preserve its exact 8 columns by 4 rows, cell boundaries, transparent background, character identities, costumes, palettes, scale, bottom baselines, and all four facing directions. Change ONLY the second pose in each directional pair for every character: columns 2, 4, 6, and 8 (1-based) must show a clearly readable alternate walking step, with opposite foot forward and matching opposite arm swing from the preceding idle/step pose. The current pairs are too similar; make the stance unmistakably different without changing facing direction or silhouette proportions. Keep first pose of each pair as idle. Do not add text, labels, borders, shadows, or extra characters. Entire sheet remains original crisp pixel art.
```

### Named characters: King of Fynn, Nelly, Elina, Kain

Initial candidate: `npc-named-king-nelly-elina-kain-candidate-8x4.png`.

```text
Use case: stylized-concept. Asset type: original source sprite sheet for an FFII-inspired Unity remake. Input images: reference image 1 is Review/art/02-firion-study.png and reference image 2 is Review/art/03-environment-kit.png, style only; match crisp square pixel clusters, dark navy outlines, compact GBA-era proportions, restrained bright highlights, rich but controlled palette. Primary request: exactly 32 complete field-character sprites in one coherent, perfectly regular 8-column by 4-row transparent grid, wide landscape 2:1 sheet. Rows top to bottom show four distinct character identities: King of Fynn, Nelly, Elina, Kain. Columns left to right show that row's same character and exact sequence: down-facing idle, down-facing walk-step, left-facing idle, left-facing walk-step, right-facing idle, right-facing walk-step, up-facing idle, up-facing walk-step. Give the step pose a small clearly readable alternating foot/arm change while preserving body placement, costume, palette, scale, and direction. Role-appropriate visual approximations only; do not claim historical pixel-accurate costumes. All cells exactly equal size with generous gutters, each complete figure fully inside its cell, feet aligned to a shared bottom baseline per row, consistent silhouette scale. Transparent empty backdrop and gutters. Constraints: no text, labels, letters, numerals, grid lines, borders, panels, floor, shadows, scenery, watermarks, or extra images; no cell may contain multiple poses; no smoothing; original redrawn art, not extracted game sprites.
```

Final selected edit: `npc-named-king-nelly-elina-kain-edited-transparent-8x4.png`.

```text
Edit this exact transparent field-sprite sheet, preserving its 8-column by 4-row layout, all four characters, their costume/palette, identity, scale, cell positions and facing directions. Keep columns 1,3,5,7 as standing idle key poses. Change ONLY columns 2,4,6,8 (one-based) into very clear alternate walk poses for each matching direction: opposite foot visibly forward and matching opposite arm swing; separate the legs enough to read at small size. Do not let duplicate silhouettes remain. Keep stable bottom baseline and same cell sizes. Maintain genuinely transparent empty cells/background, no checkerboard. No labels, scenery, shadows, text, extra figures or borders. Crisp original pixel art.
```

### Generic adults: man, woman, elder man, elder woman

Initial candidate: `npc-generic-adult-candidate-8x4.png`.

```text
Use case: stylized-concept. Asset type: original source sprite sheet for an FFII-inspired Unity remake. Input images: reference image 1 is Review/art/02-firion-study.png and reference image 2 is Review/art/03-environment-kit.png, style only; match crisp square pixel clusters, dark navy outlines, compact GBA-era proportions, restrained bright highlights, rich but controlled palette. Primary request: exactly 32 complete field-character sprites in one coherent, perfectly regular 8-column by 4-row transparent grid, wide landscape 2:1 sheet. Rows top to bottom show four distinct character identities: man, woman, elder man, elder woman. Columns left to right show that row's same character and exact sequence: down-facing idle, down-facing walk-step, left-facing idle, left-facing walk-step, right-facing idle, right-facing walk-step, up-facing idle, up-facing walk-step. Give the step pose a small clearly readable alternating foot/arm change while preserving body placement, costume, palette, scale, and direction. Role-appropriate visual approximations only; do not claim historical pixel-accurate costumes. All cells exactly equal size with generous gutters, each complete figure fully inside its cell, feet aligned to a shared bottom baseline per row, consistent silhouette scale. Transparent empty backdrop and gutters. Constraints: no text, labels, letters, numerals, grid lines, borders, panels, floor, shadows, scenery, watermarks, or extra images; no cell may contain multiple poses; no smoothing; original redrawn art, not extracted game sprites.
```

Final selected edit: `npc-generic-adult-edited-transparent-8x4.png`.

```text
Edit this exact transparent field-NPC sheet, preserving the 8×4 cell grid, four existing adult townsperson identities, outfits, palette, scale, and each direction. Keep columns 1,3,5,7 as neutral standing. Change ONLY columns 2,4,6,8 (one-based) into distinct opposite-foot-forward walk steps, with one leg extended and opposite arm forward; clearly show a different leg silhouette from the paired idle. Retain each person's age/gender features and outfit; do not switch identity between cells. Keep same bottom baseline and cell position. Background truly transparent, never a checkerboard. No text, labels, scenery, shadow, borders, or extra people. Crisp original pixel art.
```

### Generic children and services: boy, girl, shopkeeper, innkeeper

Initial candidate: `npc-generic-child-services-candidate-8x4.png`.

```text
Use case: stylized-concept. Asset type: original source sprite sheet for an FFII-inspired Unity remake. Input images: reference image 1 is Review/art/02-firion-study.png and reference image 2 is Review/art/03-environment-kit.png, style only; match crisp square pixel clusters, dark navy outlines, compact GBA-era proportions, restrained bright highlights, rich but controlled palette. Primary request: exactly 32 complete field-character sprites in one coherent, perfectly regular 8-column by 4-row transparent grid, wide landscape 2:1 sheet. Rows top to bottom show four distinct character identities: boy, girl, shopkeeper, innkeeper. Columns left to right show that row's same character and exact sequence: down-facing idle, down-facing walk-step, left-facing idle, left-facing walk-step, right-facing idle, right-facing walk-step, up-facing idle, up-facing walk-step. Give the step pose a small clearly readable alternating foot/arm change while preserving body placement, costume, palette, scale, and direction. Role-appropriate visual approximations only; do not claim historical pixel-accurate costumes. All cells exactly equal size with generous gutters, each complete figure fully inside its cell, feet aligned to a shared bottom baseline per row, consistent silhouette scale. Transparent empty backdrop and gutters. Constraints: no text, labels, letters, numerals, grid lines, borders, panels, floor, shadows, scenery, watermarks, or extra images; no cell may contain multiple poses; no smoothing; original redrawn art, not extracted game sprites.
```

Final selected edit: `npc-generic-child-services-edited-transparent-8x4.png`.

```text
Edit this exact transparent field-NPC sheet while preserving its 8-column × 4-row grid, all four rows/identities, costumes, palette, proportions, cell positions and facing directions. Keep columns 1,3,5,7 as neutral poses. Replace ONLY columns 2,4,6,8 (one-based) with unmistakably different walk steps: alternate feet, one leg extended forward, opposite arm swing, clear leg separation and natural movement for each character; preserve row identity. Keep child scale and adult shopkeeper/innkeeper proportions unchanged. Same bottom baseline, exact even cells and transparent gutters. Real alpha transparency, not checkerboard. No text, labels, scenery, floor, shadows, borders, or extra people; crisp pixel art.
```

### Imperial guard, rebel guard, pirate, robed mage

Initial candidate: `npc-guards-pirate-mage-candidate-8x4.png`.

```text
Use case: stylized-concept. Asset type: original source sprite sheet for an FFII-inspired Unity remake. Input images: reference image 1 is Review/art/02-firion-study.png and reference image 2 is Review/art/03-environment-kit.png, style only; match crisp square pixel clusters, dark navy outlines, compact GBA-era proportions, restrained bright highlights, rich but controlled palette. Primary request: exactly 32 complete field-character sprites in one coherent, perfectly regular 8-column by 4-row transparent grid, wide landscape 2:1 sheet. Rows top to bottom show four distinct character identities: imperial guard, rebel guard, pirate, robed mage. Columns left to right show that row's same character and exact sequence: down-facing idle, down-facing walk-step, left-facing idle, left-facing walk-step, right-facing idle, right-facing walk-step, up-facing idle, up-facing walk-step. Give the step pose a small clearly readable alternating foot/arm change while preserving body placement, costume, palette, scale, and direction. Role-appropriate visual approximations only; do not claim historical pixel-accurate costumes. All cells exactly equal size with generous gutters, each complete figure fully inside its cell, feet aligned to a shared bottom baseline per row, consistent silhouette scale. Transparent empty backdrop and gutters. Constraints: no text, labels, letters, numerals, grid lines, borders, panels, floor, shadows, scenery, watermarks, or extra images; no cell may contain multiple poses; no smoothing; original redrawn art, not extracted game sprites.
```

Final selected edit: `npc-guards-pirate-mage-edited-transparent-8x4.png`.

```text
Edit this exact transparent 8-column × 4-row field-sprite sheet. Preserve the four row identities and costumes: imperial guard, rebel guard, pirate, robed mage. Preserve palette, scale, cell geometry and each facing direction. Columns 1,3,5,7 are the idle poses. Change only columns 2,4,6,8 (one-based) into clear alternate walk steps with opposite foot forward, separated legs and matching opposite arm or equipment swing. Distinguish each pair strongly at game scale while keeping the same character and facing direction. Keep all poses inside their exact cell and bottom baseline. Real transparent alpha, not checkerboard. No text, labels, scenery, floor, shadows, borders, or additional characters. Crisp original pixel art.
```

## Transport

Selected source: `transport-canoe-ship-airship-chocobo-4x4.png`.

```text
Use case: stylized-concept. Asset type: transparent 4 by 4 transport sprite sheet for FFII-inspired field map. Input images Review/art/02-firion-study.png and Review/art/03-environment-kit.png are style references only: crisp clustered pixel art, dark navy outlines, vivid restrained palette. Exactly sixteen complete small vehicle or mount sprites in a regular 4-column by 4-row grid. Columns left-to-right: canoe, sailing ship, airship, chocobo. Rows top-to-bottom: facing down/toward viewer, facing left, facing right, facing up/away. Each cell a distinct readable overhead/three-quarter field-game sprite with stable scale and palette, transparent background/gutters. No riders unless integral silhouette is needed to clarify the chocobo; no labels, scenery, water, shadow, grid lines, borders, watermark. Original artwork; no historical source sprite extraction. Approximate 32x32 native target.
```

## Equipment

Rejected character-and-weapon source: `weapons-two-poses-4x4.png`.

```text
Use case: stylized-concept. Asset type: original 16-cell equipment source sprite sheet for FFII-inspired remake. Input images Review/art/02-firion-study.png and Review/art/03-environment-kit.png are style references only; crisp square pixel clusters, navy outlines, compact readable GBA-era palette. Exactly 16 independent centered equipment sprites in a strict 4-column by 4-row grid, transparent cells and gutters, no labels/text/grid/borders/shadows/scenery/watermarks. Row-major item and pose order: sword-guarded, sword-raised; axe-resting, axe-raised; spear-resting, spear-thrust; bow-lowered, bow-drawn; staff-resting, staff-raised; dagger-lowered, dagger-thrust; shield-forward, shield-angled; unarmed-neutral, unarmed-guard. Each pair clearly distinct while retaining same weapon design. These are small equipment icons suitable for 16x16 target resampling, original redrawn art, not copied historical sprites.
```

Selected replacement: `weapons-equipment-only-4x4.png`.

```text
Use case: stylized-concept. Asset type: standalone equipment sprites for an FFII-inspired remake. Input images Review/art/02-firion-study.png and Review/art/03-environment-kit.png are style references only: crisp GBA-era pixel clusters, restrained highlights, dark outline palette. Create exactly sixteen isolated item sprites in a strict 4-column × 4-row transparent grid, two poses per row-major weapon family: sword-guarded, sword-raised; axe-resting, axe-raised; spear-resting, spear-thrust; bow-lowered, bow-drawn; staff-resting, staff-raised; dagger-lowered, dagger-thrust; shield-forward, shield-angled; unarmed-neutral, unarmed-guard (two small floating fist/hand shapes). Every cell contains ONLY the centered weapon or shield object, never a person, body, arm, hand holding it, character, costume, or scene; unarmed cells contain just a pair of fists. Each item fully fits its equal-size cell, paired poses have clearly different weapon angles. True transparent background and gutters. No labels, text, numbers, grid lines, borders, scenery, floor, shadows, people, watermarks. Original redrawn pixel art, small-item silhouettes tuned for 16×16 target.
```

## World props

Selected source: `world-props-4x4.png`.

```text
Use case: stylized-concept. Asset type: original 16-cell world-prop source sprite sheet for FFII-inspired remake. Input images Review/art/02-firion-study.png and Review/art/03-environment-kit.png are style references only; match crisp square pixel clusters and restrained GBA-era palette. Exactly 16 distinct standalone readable props in a strict 4-column by 4-row row-major grid, transparent background and gutters. Row-major names: wyvern-facing-left, wyvern-facing-right, wyvern-egg, sunfire-flame, bell, pendant, mask, mirror, torch-unlit, torch-lit, raft, gate-closed, gate-open, throne, bed, coffin. These are visual approximations, not historically verified designs. Every prop fully within cell, no text, labels, numerals, grid lines, borders, scenery, floor, shadows, watermarks. Original redrawn art, not extracted game sprites; target resampling 32x32.
```

## Spell effects

Each selected atlas is four columns by four rows: each column is one visual family and each row is one animation frame. They are effects only and do not imply spell implementation coverage.

### Fire, blizzard, thunder, cure

```text
Use case: stylized-concept. Asset type: reusable transparent spell-effect sprite atlas for FFII-inspired remake. Input images Review/art/02-firion-study.png and Review/art/03-environment-kit.png are style references only. GBA-era crisp pixel clusters, compact clear silhouettes, controlled bright palette. Exactly four columns by four rows, uniform transparent cells and gutters. Columns left-to-right are fire, blizzard, thunder, cure; rows top-to-bottom are animation frames 1,2,3,4 for that column's same effect. Each sequence must visibly change coherently over time while keeping effect color/scale stable. Fire is orange flame burst, blizzard is pale blue snow/ice burst, thunder is yellow-violet lightning strike, cure is soft green healing sparkle. No text, labels, numbers, grid lines, border, scenery, shadow, watermark or extra effects. All are reusable visual families, not a claim each spell is implemented.
```

### Poison, stone, sleep, silence

```text
Use case: stylized-concept. Asset type: reusable transparent spell-effect sprite atlas for FFII-inspired remake. Input images Review/art/02-firion-study.png and Review/art/03-environment-kit.png are style references only. GBA-era crisp pixel clusters, compact clear silhouettes, controlled palette. Exactly four columns by four rows, uniform transparent cells and gutters. Columns left-to-right are poison, stone, sleep, silence; rows top-to-bottom are four distinct animation frames for each same effect. Poison is purple toxic puff, stone is earthy petrifying pulse, sleep is blue-violet stars, silence is muted grey-violet sound-cancel glyph-like burst without letters. Maintain visible progression and stable scale per sequence. No text, labels, numbers, letters, grid lines, borders, scenery, shadow, watermark or unrelated effects. These are reusable visual families; spell implementation coverage is not asserted.
```

### Protect, shell, haste, berserk

Rejected initial source `fx-protect-shell-haste-berserk-4x4.png` included a tiny character inside each effect cell. Selected revision `fx-protect-shell-haste-berserk-revised-4x4.png` uses this prompt:

```text
Use case: stylized-concept. Asset type: reusable transparent spell-effect sprite atlas for FFII-inspired remake. Input images Review/art/02-firion-study.png and Review/art/03-environment-kit.png are style references only. Crisp GBA-era pixel clusters, restrained palette. Exactly four columns by four rows in equal transparent cells. Columns left to right: protect, shell, haste, berserk. Rows top to bottom: four distinct sequential animation frames of that one effect. Protect is a gold translucent shield ring with small sparks; shell is a cool blue crystalline spherical barrier; haste is red-orange wind streaks; berserk is crimson aura flames. Each cell contains ONLY the magic visual effect itself, no person, actor, character silhouette, body, face, weapon, or creature. Clear per-family identity, coherent progression and stable effect scale. True transparent background and gutters. No text, labels, numbers, letters, grid lines, borders, scenery, shadow, watermark, or unrelated effects. Reusable visual family atlas, not evidence of spell implementation.
```

### Holy, ultima, drain, teleport

```text
Use case: stylized-concept. Asset type: reusable transparent spell-effect sprite atlas for FFII-inspired remake. Input images Review/art/02-firion-study.png and Review/art/03-environment-kit.png style only. Crisp pixel clusters, restrained GBA palette. Exactly four columns by four rows in equal transparent cells. Columns: holy, ultima, drain, teleport; rows: four sequential animation frames for each column's same effect. Holy is luminous gold-white radiance; ultima is violet-blue cosmic burst; drain is dark crimson/magenta siphon vortex; teleport is pale cyan dimensional warp rings. Each effect sequence changes subtly and coherently at stable scale. Transparent background and gutters; no text, labels, numbers, letters, grid lines, borders, scenery, shadows, watermark or unrelated spells. Reusable effect families only; no implication of implementation coverage.
```
