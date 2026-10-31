# Furniture and rug refinement V5

Seven independent generated components: white sickbed, square table, flat crate, red/ivory seat, stool, bedside table/jug and Hilda's red/gold rug. The furniture parts retain their source alpha; crop bounds are measured from visible alpha, not painted masks.

Built-in image_gen produced the masters. `prompts.json` records initial generation and alpha correction; `palette-prompt.txt` records the final muted-wood correction. Earlier masters remain preserved. `export.cjs` performs crop export and records source/output hashes in `manifest.json`.

Original game screenshots are reference-only; no screenshot pixels are used as output components. Matching is approximate. Scott's lying pose is absent, table/bed details still differ, and Hilda's border is brighter and denser than the source pattern. The complete rug's unseen lower edge is an inferred design, not observed retail geometry. Review uses a clipped viewport.

These assets are candidates only. No Unity scenes, code, gameplay or builds changed.
