# Production Plan (Review Draft)

## Delivery sequence

1. **Reference and decisions** — collect Japanese-original captures for representative field, map, town, interior, dungeon, battle, dialogue, and status/menu screens. Record canvas, placements, tile boundaries, animation states, and source/provenance. Resolve the approvals in `review-decisions.md` before locking dimensions.
2. **Vertical-slice art proof** — produce Firion, one Goblin, representative overworld/town/interior/dungeon tiles, one spell effect, and reference-layout UI. Compare them side by side with captures at native scale and integer-scaled presentation. Review composition fidelity and readability before expanding.
3. **Import and rendering foundation** — establish Unity import settings under `Assets/Art/Production/`, sprite slicing, point filtering, pixels-per-unit, palettes, sorting, animation clips, and square-pixel integer scaling. Center in a 4:3 viewport with side bars unless a reviewed pixel-aspect correction is approved. Keep IDs stable between the inventory, source files, and Unity assets.
4. **Campaign enumeration** — audit the full game in sequence and enumerate characters/poses, enemy families, locations/tilesets, objects, effects, UI screens, and variants. Update inventory rows with stable IDs, evidence, sizes, status, and import destinations; keep uncertain counts marked enumeration pending.
5. **Content production** — create and review assets by family, tracking source match and game readability separately. Implement gameplay with FFII use-based growth and keyword dialogue progression; no XP/level replacement. Validate asset hooks against the intended extensible data model.
6. **Integration and acceptance** — compare every screen family to its reference captures; check animation timing, tile seams, sorting, text placement, import settings, and in-game composition. Record accepted deviations and their rationale. Approve any optional expansion as a separate scope.

## Asset lifecycle and provenance

Use the inventory's stable `asset_id` as the source-file stem or metadata key. For each production asset, record at minimum: source/reference identifier, capture or license provenance, original-game scene/location, dimensions and frame order, palette/version, author or generator, review status, and Unity import target. Keep concept boards distinct from production assets and label them `concept / not approved` until an explicit art review accepts them.

Suggested status flow: `proposed` → `in progress` → `review` → `approved` → `integrated`. Record rejected or superseded assets rather than silently reusing their IDs. Store source masters separately from Unity-imported outputs and preserve editable layers where available.

## Scope control

The base remake covers the complete original Japanese FFII campaign. The current package only enumerates a starter slice; remaining content counts are **enumeration pending**. Optional post-campaign content, additional modes, or new story material must be estimated and approved as a separate expansion after base-game enumeration. Do not let expansion assets displace the original campaign coverage.

## Review gates

- **Gate A — reference agreement:** composition and measured source dimensions documented; provisional sizes resolved or explicitly retained.
- **Gate B — style approval:** vertical slice accepted at native scale and in the Unity preview.
- **Gate C — inventory completeness:** campaign audit reconciled against the source-game sequence, with unresolved items clearly marked.
- **Gate D — integration acceptance:** imported assets preserve intended pixel edges, frame timing, sorting, and layout in representative gameplay scenes.

No gate is implied by a concept board or a successful import alone.
