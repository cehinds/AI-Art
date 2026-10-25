# Visual Specification (Review Draft)

## Approved art direction and production convention

On 2026-10-24, Constantine approved the art direction represented by `Review/art/02-firion-study.png` and `Review/art/03-environment-kit.png` (“art direction looks good, make sure art style matches. start building assets and tiles”). This approval covers the visual style vocabulary: compact FFII silhouettes, crisp clustered pixels, restrained color ramps, and the material/palette treatment shown in those studies. The boards remain concept references, not production assets. It does not approve exact source-game maps, screen composition, mechanics, campaign coverage, or historical sprite dimensions; see `review-decisions.md`.

Batch 01 has exported review candidates: 16 terrain cells at 16 x 16 px, 16 structure cells at 16 x 16 px, and 12 Firion field-walk frames at 16 x 24 px. The character cell is bottom-centered on a 16 x 16 px ground footprint, allowing the upper body to extend above one tile. These are production conventions chosen to preserve the approved proportions, not claims about original-game frame dimensions. See `Docs/Batch01StyleReview.md` and `Assets/Art/Production/Batch01/manifest.json`. Exported candidates are not final gameplay approval: source-game fidelity and Unity rendering remain unverified.

## Goal

Recreate the original Japanese *Final Fantasy II* (Firion, Maria, Guy, and Leon), preserving its composition, screen layouts, scene logic, and gameplay information hierarchy. This is not *Final Fantasy IV*. Keep the presentation recognizably faithful while using a richer palette, cleaner pixel clusters, and restrained shading at roughly Game Boy Advance-era polish. Higher color depth must not silently enlarge sprites, tiles, or UI elements.

## Working presentation constraints

| Property | Review proposal | Status |
|---|---|---|
| Reference canvas | 256 x 240 square pixels (16:15) | Proposed native design grid; not verified as an exact historical render mode |
| Field grid | 16 x 16 pixel tiles | Proposed; retain the original's compact tile density |
| Field actor | 16 x 24 pixels per frame over a 16 x 16 ground footprint; party 4 directions x 3 poses; NPC 4 directions x 2 poses | Production convention used by Batch 01 and Campaign; original dimensions and motion fidelity remain unverified |
| Battle actor cell | 24 x 32 pixels per frame | Provisional cell, not a claim about source sprite dimensions; needs review |
| Presentation scaling | Square-pixel integer scaling; center in a 4:3 viewport with side bars when needed. No stretch by default. | Proposed |
| Palette | Platform-specific, role-based palette ramps with clear value grouping | Proposed; choose exact colors after visual review |
| Pixel treatment | Crisp pixel edges, deliberate clusters, no filtering that blurs authored pixels | Proposed |

The proposed 256 x 240 square-pixel canvas is 16:15, not 4:3. Preserve square pixels and scale by integer factors; in a 4:3 viewport, center the image and use side bars rather than stretch it. An optional 5:4 horizontal pixel-aspect correction can be reviewed if captures establish that reproducing the original television display shape is required. The canvas is a composition reference, not a mandate to stretch source art. If a real capture establishes a different viewport or sprite cell, record the evidence and revise this spec before production export.

## Composition and readability

- Preserve the original scene's arrangement, actor placement, text-box footprint, menu order, battle party/enemy alignment, and relative screen-space emphasis. Build a reference sheet from captures before treating any recreation as approved.
- Preserve the distinction between world map, town, interior, dungeon, battle, dialogue, menus, and status screens. Scene transitions should not introduce new composition without an explicit review decision.
- Use contrast and palette separation to clarify terrain, interactable objects, actors, and text. Do not add decorative detail that obscures tile boundaries or gameplay cues.
- Match Japanese-original terminology and ordering in the reference layer; localization and legibility adaptations belong in a separately reviewed text specification.
- Keep UI typography and borders pixel-aligned. Text, icons, cursors, and party/status panels should occupy comparable areas to the reference composition.

## Scope boundaries

This package plans the complete campaign asset families without asserting an unverified total count. Exact locations, variants, and counts remain **enumeration pending** until source-game reference capture and a content audit. The initial inventory is a concrete vertical-slice set, not a claim of complete coverage.

The art style does not authorize gameplay changes. The remake retains FFII's use-based character growth and keyword-driven dialogue progression; it does not substitute a conventional XP/level progression system. See `review-decisions.md` for open approvals and `asset-inventory.csv` for initial IDs and targets.
