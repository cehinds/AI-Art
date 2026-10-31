# Interior, city and UI component comparison V1

Status: **visual breakdown completed; asset production is the active scope. Game integration is deferred by the latest user instruction.** This is an independent screenshot/code comparison of Final Fantasy II Pixel Remaster and the local remake. It is not a new interactive playtest or a claim of retail parity.

## Visual evidence

- [Interior side-by-side sheet](../../Review/interiors-city-ui-comparison-v1/01-interiors.png): Tobul, Scott, Hilda.
- [UI side-by-side sheet, V2](../../Review/interiors-city-ui-comparison-v1/02-ui-v2.png): top dialogue/speaker, status gauges, battle-item panes. The first UI sheet is preserved as an earlier report revision.
- [City component sheet](../../Review/interiors-city-ui-comparison-v1/03-city.png): Altair topology, current generated structures, historical town baseline.
- [Current native Altair pair](../../Review/interiors-city-ui-comparison-v1/05-current-city.png): main agent's 30 October capture, new kit visible.
- [Component atlas](../../Review/interiors-city-ui-comparison-v1/04-components.png): sixteen exact roof/wall/floor/rug/furniture/UI samples.
- [Annotated reference and local captures](../../Review/interiors-city-ui-comparison-v1/annotated/), [source/hash/crop manifest](../../Review/interiors-city-ui-comparison-v1/evidence-manifest.json), and [gallery](../../Review/interiors-city-ui-comparison-v1/index.html).

The interior native captures date to **30 October, approximately 09:05–09:09**. The status and party-menu captures are **27 October historical evidence**, including old debug spell provisioning. They do not prove current menu content. Current source code was inspected separately. The newly supplied Altair native capture is later on 30 October and shows AltairKitV1 and the terrace revision. Different camera positions, resolutions and story progress prevent meaningful whole-image pixel scores.

## Comparison steps and health

1. **Interior architecture — large visual gap.** Existing rooms are functional compact adaptations, with props and collision already present. Their walls, floor materials and room composition visibly differ.
2. **City structure layers — partial match.** Altair now has role-specific structures and the hideout's L silhouette. Natural cliff geometry and retail town/event density remain gaps.
3. **Dialogue framing — clear reference target.** The PR capture separates speaker, top dialogue and lower keyword panes while retaining the room. Local dialogue code previously reused a dimmed central modal.
4. **Status and list UI — partial match.** Values and progress exist, but column hierarchy, portrait/side navigation, panel treatment and gauge construction differ.
5. **Component generation — active next step.** Produce and review the assets in [component-contracts.json](component-contracts.json) before integrating them into the game.

## Layer comparison and prioritized gaps

| Component / layer | Observed retail evidence | Local evidence | Priority / asset correction |
|---|---|---|---|
| North interior wall | Scott and Tobul captures show a tall, front-facing cream/timber wall, cap/beam and room-facing depth. | `warmInteriorWall` uses a square cream-brick tile, repeated around every boundary and partition. | **P0**: separate 32×64 north wall face with horizontal repeat; separate wall-cap/side/corner pieces later. A square exterior brick tile is not an interior wall face. |
| Floor versus rug | Tobul has a red ground field and a pale patterned customer rug. Scott has warm stone and a blue/cream bed niche. | Smithy uses wood under a red/gold rug; refuge uses cool stone and no blue rug. | **P1**: plain red field, warm stone repeat and two distinct rug families. Avoid tinting the same ornate red carpet into every material. |
| Counter | Tobul's counter forms a substantial continuous L service boundary with a visible front face. | Two table-derived straight counter wings leave a central aisle. | **P1**: counter top/front/corners/end caps. Changing collision or service layout is later integration work. |
| Furniture / work bay | Scott's bed, tall bookcase, crates and rug form a cohesive eastern niche. Tobul has a distinct forge/work area. | Reused beds, chairs, shelves and mining equipment are small, distributed substitutes. | **P1/P2**: forge, tall shelf, bed states, throne and storage modules with consistent ground anchors. |
| Audience hall | Hilda's color capture has a broad red/gold carpet, throne pair and visible room around the party. The separate hideout map shows a multi-room complex. | One compact audience runner with two side bays; the full hideout complex is condensed. | **P1 art / later map work**: carpet border/field, throne pair, interior walls. The multi-room complex is not a bounded asset-only correction. |
| City buildings | The Altair map establishes narrow/wide shops, a distinct sanctuary and L-shaped headquarters. | Current kit has nine role IDs, matched canvases, facade/roof layers and aligned doors; several IDs reuse source families. | Preserve layer/canvas/door contracts. Add distinct variants only where a reference establishes a meaningful difference. |
| City terrain | The Altair sepia map shows natural irregular raised ground and stairs around the eastern districts. | The current native capture still reads as straight stone retaining rails/paved rims. | **P1**: natural cliff face/top/foot/corners and slope/step joins. Existing paved terrace borders do not solve the natural-rock shape. |
| Dialogue panel | The accepted Hilda still shows a blue top panel with speaker tab; the field remains visible. Bottom panes contain keyword actions/list. | Previous source used a central 1060×546 modal plus full-field dimming. | **P1**: cobalt-to-navy center, light silver/teal frame, speaker tab. Ask/Learn/Key Items is a separate gameplay/menu implementation, not implied by a new frame. |
| Status hierarchy | English/Japanese status captures show portrait/HP/MP, attribute/derived-value region, framed proficiency gauges and separate main navigation. | Current source has three text columns, XP text and bare thin progress rules; no portrait/sidebar in this view. | **P2**: frame/gauge/portrait-window/icon assets. Reordering the complete menu is later integration. |
| Item list | The accepted item still is a battle state: description panel above item list and actor pane, with scroll affordance. | Current field inventory is a single choice list. No same-state current field-inventory capture was accepted. | **P2**: reusable description/list/actor frames, scroll indicators and item glyphs. Do not copy battle layout into field inventory based on an unmatched still. |

## Exact generation contracts

The [JSON contract](component-contracts.json) is the production queue. Dimensions are **native output pixels**, with 32 pixels per world tile. Larger generated masters must be preserved before nearest-neighbor normalization. Every asset needs transparent/opaque intent, anchor, repeating edges, output dimensions and provenance.

North-wall first contract: a **32×64**, horizontally repeatable, front-facing cream/timber wall panel. No floor, characters, furniture, windows, torches, perspective corner or baked scene shadow. Align side posts at both horizontal ends; the bottom is the wall/floor junction. Later integration must place its bottom exactly at the first walkable floor boundary, extending upward into blocked/outside space rather than painting over floor or actors.

Rug families need independent center/edge/corner samples so borders remain constant at different extents. Furniture should keep one feet/base anchor and enough transparent margin for height. UI frames need an untextured safe text region, separate borders/corners and matching center color. The user already selected cursor option 10: preserve its existing pixels and hotspot; do not generate or replace it. Asset previews and cropped references remain separate.

## Held code edits — not integrated

Before the user's asset-only scope override arrived, two local game files were edited:

- `Assets/FF2/Runtime/ReviewSandbox.Chapter.cs`: top dialogue box/speaker tab, visible world, existing Continue/Enter/Space/A behavior retained.
- `Assets/FF2/Runtime/ReviewSandbox.Status.cs`: light-framed warm progress gauges; numeric rank/XP retained; complete column layout retained.

The Unity adapter compiled with **0 warnings and 0 errors** before the override. No Unity build or native UI test was performed by this agent. These edits are preserved in place for later integration; this report does not claim their visual result is delivered. No new interior renderer, wall binding, map layout, event, save change or gameplay mechanic was added in this component task. Work on further game code stopped immediately when the override arrived.

## Evidence and uncertainty

**Observed:** the pixels visible in the cited captures, preserved with hashes; the dated local native views; current asset canvases; current renderer/menu source. All sheets were visually inspected.

**Inferred/authoring choices:** proposed reusable tile dimensions, nine-slice divisions, furniture anchors and production priorities. They are practical remake contracts, not extracted retail engine metadata.

**Not verified:** exact retail tile coordinates, hidden surfaces, complete room/city event logic, animation, interaction timing, font license, accessibility compliance or post-change native appearance. Still-image typography and contrast observations require later real-size/high-DPI tests. Proficiency must retain numeric labels so progress is not conveyed by color alone. The dialogue panel must be checked against the longest authored message after integration.

The other-town Klardendum color capture is material research only. It must never introduce its canal/quay into Altair geography. The excluded FFI spell-menu image and U.S. SNES Final Fantasy II/FFIV material are not used.

## Sources and attribution

- [RPGFan FFII Pixel Remaster gallery](https://www.rpgfan.com/gallery/final-fantasy-ii-pixel-remaster-screenshots/), [Hilda image 005](https://www.rpgfan.com/wp-content/uploads/2021/06/Final-Fantasy-II-Pixel-Remaster-Screenshot-005.jpg): accepted color Hilda/dialogue composition. Platform/build unknown.
- [Solo Play Guide Altair](https://www.soloplayguide.com/games/final-fantasy-ii-pixel-remaster/walkthrough/01-altair): annotated sepia hideout layout; not a gameplay color source.
- [Vorxu Altair/Fynn](https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn), [Scott image](https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn/scott-gives-you-ring-960w.webp), [Tobul image](https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/walkthrough/salamand-and-semitt-falls/tobul-960w.webp): accepted interior captures; platform/build unknown.
- [Vorxu leveling](https://vorxu.com/final-fantasy-2-pixel-remaster/leveling), [English status image](https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/leveling/character-stats-960w.webp), [GCGX PR status](https://gcgx.games/ff2/re/status.html), [Japanese status image](https://gcgx.games/ff2/re/img/slv.webp): accepted status captures.
- [Game Center GX item article](https://note.com/gamecentergx/n/n3ea79e79dabc): accepted Japanese battle-item screenshot. Its exact original image URL is preserved in the evidence manifest.
- [Vorxu Altair map image](https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/towns/altair-start-game.png): actual Altair topology. [Klardendum review](https://klardendum.com/review/o-tempora-final-fantasy-ii-pixel-remaster/), [color town image](https://klardendum.com/wp-content/uploads/2021/11/ff2pr1.jpg): other-town material reference only.

Original FFII PR imagery remains copyrighted to Square Enix and attributable to the cited publishers/capturers. Preserving research images grants no new license or endorsement. Reference crops are outside runtime Assets and are not generated production art. Existing local screenshots/source files remain unchanged.

## Generated asset result

The accepted generated masters have now been exported as [InteriorComponentsV1](../InteriorComponentsV1/README.md): **21 components / 109 production PNGs**, with five raw masters preserved, separate UI/rug layers, nine-slice parts, repeat proofs and hash verification. [Generated asset gallery](../../Review/interior-components-v1/index.html). The original 18-item priority list is an authoring queue; the final production manifest is authoritative for actual dimensions and contents. Game integration remains deferred. The existing cursor option 10 was referenced and hash-checked without replacement.
