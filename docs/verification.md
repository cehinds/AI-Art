# Catalog verification

The combined catalog preserves game source snapshots in `Games/`. Before publication, 39,721 files (9,570,687,806 bytes) were verified against source Git blobs, byte lengths and SHA-256 records. The initial snapshot is preserved in commit `64d3eddc803c980a9e3b1fbff31f6b65e345162c`; reviewed updates record their previous source and catalog commits.

| Game | Source commit | Files |
| --- | --- | ---: |
| Final Fantasy II | faa286eef99510b5bb6e84c2f40f262ae0296a3b | 3,823 |
| Dungeon Crawler | 4aab2055cdfbd2ff0d6955d082007ecee0e6cb5b | 4,746 |
| AshenSpire | e71ff1f23d95da84deede90907f2f28f7aedb55a | 31,094 |
| Dovakiin | 4f2269a339b3e01a16eb43092acc77307b08017e | 58 |

The site build generates thumbnails only; full source files are retained in Git and linked at their pinned upstream commit. Transparent preview padding is trimmed mechanically. Opaque backgrounds are preserved. Original pixels, dimensions, metadata and rights records are unchanged.

## Visual comparison

Reference: `design/catalog-concept.png`, generated with the built-in ImageGen tool. The in-app browser successfully loaded the catalog, but its large-viewport screenshots were clipped and affected by desktop scaling. Full visual and interaction verification therefore uses headless Chromium through Playwright at 1536×1024 and 390×844. Native in-app browser testing is retained for opening the delivered site.

Compared with the concept using `view_image`:

- Header and navigation: 75px header, serif AI Art wordmark, game links, olive active underline.
- Layout: 258px category rail, aligned main content, four desktop columns and two mobile columns.
- Palette: warm neutral background, dark ink, olive selection and subtle gray borders.
- Typography and spacing: Georgia headings and labels, consistent toolbar height, regular image wells and caption spacing.
- Asset treatment: actual repository art replaces illustrative concept examples; transparent checkerboards and contained previews preserve silhouettes.
- Responsive behavior: wrapping navigation, labeled type selector, no horizontal overflow, and a viewport-fitting detail dialog.

Intentional functional additions: measured category/result counts, category section headings, HD/Light/theme variant labels, empty states, provenance collection selection and a metadata dialog. Consequently image rows start lower than the illustrative concept. Category labels are clarified to UI & icons, Concept art and Other assets. Above-the-fold copy is restricted to the design specification and these documented data-driven additions.

Browser interaction outcomes and screenshots are recorded in `design/browser-qa.json`, `design/catalog-desktop.png`, and `design/catalog-mobile.png`. No claim of Unity/game runtime verification is made by this catalog.

Final local result: 34,488 catalog entries across all four games, 29,659 unique image previews, zero preview-generation warnings, ten pipeline tests passed and all browser checks passed. The catalog preserves duplicate source paths as separate records. Final previews and metadata total approximately 594 MB, versus 9.57 GB of originals. Desktop and mobile screenshots were inspected against the concept; no unresolved layout, overflow or image-loading issue remained in the tested flows.

CI uses a shallow checkout with only catalog code and snapshot inventories in the worktree. Verification reads the committed original blobs directly from Git and validates path sets, modes, bytes, blob IDs and SHA-256 against inventories. The build reads those same blobs for thumbnails and manifest metadata. A real sparse-checkout test verifies that Git-backed and filesystem builds produce identical catalog and preview bytes. Local snapshot imports additionally verify the upstream source trees.
