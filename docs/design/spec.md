# Catalog design specification

Source: built-in ImageGen, catalog-concept.png. A complete desktop catalog screen is the implementation reference. This is a static GitHub Pages deliverable using semantic HTML, CSS and JavaScript.

Palette: warm neutral #f7f7f4 background, #111820 ink, #46553b olive selection, #d8dad6 borders. Serif typography (Georgia fallback) throughout matches the reference. Header height 74px, left asset-type rail 258px at 1536px, main padding 46px, gallery four columns with 24px gaps. Image wells have a light checkerboard, contain artwork without cropping, and use nearest-neighbor scaling for pixel assets. Square corners with a subtle 3px radius.

Visible controls: AI Art; All assets; FFII; Dungeon Crawler; AshenSpire; Dovakiin; GitHub; Asset type; All types; Tiles; Weapons; Characters; Creatures; Environments; Props; Effects; Animations; UI; Concepts; Source sheets; References; Other; All art assets; Browse artwork across every game.; Search assets; All games; Production; Name A–Z; Assets; Previous; Next. Actual names and counts are derived from the source files. Dedicated pages use the game title and scoped introductory copy.

Functional extensions needed for this catalog: results count, category counts, empty-state explanation, provenance filter including sources/references/review/archive, original/source links, and an accessible asset-details dialog with dimensions, size and commit provenance. These are deliberate functional additions to the reference. The conceptual thumbnail examples are replaced with actual repository artwork, never fabricated assets.

Mobile: header navigation wraps, type rail becomes a labeled select, toolbar stacks, image grid has two columns, dialog fits viewport. Keyboard focus is visible. Search/filter/sort state is URL-addressable; pagination prevents loading thousands of images at once. Dialog closes with Escape and restores focus.
