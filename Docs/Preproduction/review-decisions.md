# Review Decisions

Status values: **Proposed** means ready for review; **Pending** means the decision needs evidence or an explicit approval; **Constraint** means preserve as a project requirement.

| ID | Topic | Current decision / proposal | Status | Evidence or approval needed |
|---|---|---|---|---|
| RD-01 | Game identity | Japanese *Final Fantasy II*, centered on Firion, Maria, Guy, and Leon; not *Final Fantasy IV* | Constraint | Preserve in all references and scope documents |
| RD-02 | Core mechanics | Retain use-based character growth and keyword-driven dialogue progression; do not replace with XP levels | Constraint | Confirm behavior against the original-game reference/audit |
| RD-03 | Fidelity target | Preserve original compositions, layouts, and mechanics while improving palette richness and shading | Proposed | Review vertical-slice comparisons against captures |
| RD-04 | Reference canvas and display | 256 x 240 square-pixel canvas (16:15); integer-scale and center in 4:3 viewport with side bars; no stretch by default | Pending | Proposed, not a verified historical render mode; review any 5:4 horizontal pixel-aspect correction against captures |
| RD-05 | Tile density | 16 x 16 px field tiles | Pending | Confirm tile boundaries and density in representative scenes |
| RD-06 | Field actor | Candidate production frames use 16 x 24 px over a 16 x 16 ground footprint; party has three poses per direction and NPCs two | Implemented candidate | Native exports available in the production and campaign galleries; historical dimensions and motion approval remain pending |
| RD-07 | Battle actor cell | 24 x 32 px provisional frame cell | Pending | Confirm actual composition and dimensions; cell proposal does not assert source dimensions |
| RD-08 | Art style | Match the approved Firion and environment concept studies: crisp clustered pixels, compact silhouettes, restrained palette ramps, and consistent material treatment | Approved (style direction only) | Constantine approved `Review/art/02-firion-study.png` and `Review/art/03-environment-kit.png` on 2026-10-24; production assets still require comparison to this direction |
| RD-09 | UI layout | Preserve relative placement, footprint, hierarchy, and party/enemy alignment | Constraint | Capture all representative screen families before locking layouts |
| RD-10 | Campaign inventory | Nine playable characters and 128 original enemies enumerated; spell catalog has 40 learnable plus 29 special entries with explicit visual-family reuse | Measured partial coverage | See CampaignSpriteCoverage.md; full map and scripted-event asset audit remains pending |
| RD-11 | Concept boards | Raster boards remain concepts only and are not production assets; approval of the art style does not approve their layouts or dimensions | Constraint | Preserve as visual references; track production exports and sources separately |
| RD-12 | Future expansion | Keep optional expansion separate from complete base campaign scope | Proposed | Estimate and approve independently after base enumeration |

No provisional dimension in this package is presented as a verified historical specification. Record any approved change here and update `visual-spec.md` and `asset-inventory.csv` together.

## Approval history

- **2026-10-24 — Style direction approved.** Constantine: “art direction looks good, make sure art style matches. start building assets and tiles”. Applies to visual style represented by `Review/art/02-firion-study.png` and `Review/art/03-environment-kit.png`; authorizes production to begin. It does not approve exact maps, gameplay mechanics, screen layouts, campaign inventory, or historical dimensions. Batch 01's 16 x 16 terrain/structure cells and 16 x 24 Firion frames are production targets, with a 16 x 16 bottom-centered ground footprint, not historical claims.
- **2026-10-24 — Campaign sprite production authorized.** Constantine: “keep going, make all teh sprites needed”. GPT-6.1 and Luna produced the campaign candidate library, with original sheets and rejected revisions preserved. Source counts, file checks and coverage are recorded separately from visual approval and Unity runtime evidence.
