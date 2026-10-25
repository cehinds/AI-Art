# Campaign sprite pipeline

Run `node Tools/campaign-art/export.cjs`, then `node Tools/campaign-art/verify.cjs`, then `node Tools/campaign-art/coverage.cjs` from the repository root. `sharp` resolves from an installed package or the bundled Codex Node runtime. All work is offline; source generation is separate.

`ArtSource/Campaign/**/sheets.json` can contain an array or `{ "sheets": [], "excludedSources": [] }`. Every source PNG needs an exported descriptor or an exclusion with `source` and `reason`. Exclusions can also live in `excluded-sources.json` as an array or an object containing `sources` or `excludedSources`. Source paths can be repository-relative `ArtSource/...` paths or relative to the descriptor file. Do not store unrelated reference PNGs under Campaign.

Every sheet declares a globally unique `key`, `source`, `columns`, `rows`, `target: [width,height]`, `group`, and `pivot: {x:0.5,y:0}` (or `y:0.5` for effects/icons). Sprite descriptors support:

- `owner` and row-major `frameNames` for one animated character.
- `names` for a multi-owner static atlas, each with state `idle` (or explicit `state`).
- `owners` with one entry per row and `states` with one entry per column.
- `owners` and `frameNames` with one entry per cell.
- `cells: [{owner,state,target,pivot,animationSet}]` with one row-major entry per cell, for mixed sheets. Per-cell target and pivot are optional.

All keys, owners, states and groups use lowercase letters/digits separated by hyphens. `campaign:<group>.<owner>.<state>` IDs use one colon. PNG paths use `Assets/Art/Production/Campaign/<group>/<owner>/<state>.png`. Existing edited PNGs and existing `.meta` contents are preserved. The exporter never removes stale files; the verifier reports unregistered production PNGs for a separate maintenance decision.

Transparent/background alpha is thresholded at 128 by default, then visible pixels become fully opaque. Automatic row/column cuts seek alpha gaps or disconnected silhouettes near nominal boundaries, and record all exact rectangles. No painting, palette replacement, invented poses, or mirrored frames occur. If rectangular cuts cross connected ink, exact 8-connected alpha-component extraction separates visible source components using the nearest measured main-component anchor for each slot. Ambiguous component ownership or foreground spanning multiple slots is rejected. Component IDs and anchors are recorded and independently checked. No selected pixel is recolored or invented. `cellRects` can record visually inspected rectangle overrides; `rowBoundaries`, `columnBoundaries`, and `region` are also supported. Rectangles use source pixels. Enemy sprites retain at least one transparent pixel around all four sides, including the bottom. The verifier checks this safety margin.

Each owner's frames share one scale within a sheet. Different owners in a static atlas get separate scales. The optional `scaleMode: "per-cell"` is intended only for independently sized sprites, not character animation. Generated PNGs use nearest-neighbor resampling, transparent native canvases and the declared bottom/center alignment. Four-direction walk states group by direction; battle states show a comparison cycle. `animationSet` can group an arbitrary effect sequence. State-cycle playback in the gallery does not establish authored timing or gameplay behavior.

The verifier independently reconstructs each native PNG from its recorded source crop, binary-alpha threshold, scale and pivot and checks its hash against the delivery. It also checks descriptor/source inventories, crop bounds, native dimensions, unique IDs and GUIDs, owner scale consistency, nonempty binary-alpha canvases, and review files. Visual approval, original sprite fidelity, Unity import and runtime remain separate gates.

Open `Review/campaign/index.html` for offline review. `coverage.json` lists every owner and state, the original 128-enemy roster, nine required playable characters, and the 40 learnable spells plus 29 item/monster effect mappings. `Docs/CampaignSpriteCoverage.md` is generated from measured delivery. Reference catalogs are checked-in explicit data, not an assertion that every original map/event sprite has been audited.

For an explicitly partial inventory check during generation, use `node Tools/campaign-art/verify.cjs --allow-pending-sources`. It validates the delivered manifest and records PARTIAL when additional descriptors or source PNGs are pending. Final delivery always uses strict verification without this flag.
