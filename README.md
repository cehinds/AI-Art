# FFII art library

The `ff2` branch of [AI-Art](https://github.com/cehinds/AI-Art) is the canonical home for the artwork created for the original Japanese/Famicom Final Fantasy II remake project.

This transfer preserves 1,202 production PNGs, their Unity metadata, generated source masters, prompts, selected and rejected candidates, reference research, concept art, wireframes, animation previews, and portable packages. Files were copied byte-for-byte and verified by SHA-256. See [the migration inventory](Docs/FF2ArtMigration.json).

## Review the artwork

- [Procedural tile tags: search tiles and inspect compatible neighbors](Review/procedural-tiles/index.html)
- [Building Expansion 04: stone walls, slate roofs and inner/outer corners](Review/remaster-expansion/building-expansion04/index.html)
- [Exploration Expansion 03: Maria, Guy and Leon walks, 16 props and 16 cavern tiles](Review/remaster-expansion/exploration-expansion03/index.html)
- [Exploration Expansion 03 portable ZIP](Review/exploration-expansion03.zip)
- [World Builder Expansion 02: 24 props at 128px and 32 tiles at 64px](Review/remaster-expansion/worldbuilder-expansion02/index.html)
- [World Builder Expansion 02 portable ZIP](Review/worldbuilder-expansion02.zip)
- [World Builder 100: 100 biome tiles and 32 object sprites](Review/remaster-expansion/worldbuilder100/index.html)
- [World Builder portable ZIP](Review/world-builder-100.zip)
- [Higher-resolution sprites, animations and environment gallery](Review/remaster-expansion/index.html)
- [Campaign sprite gallery](Review/campaign/index.html)
- [Batch 01 gallery](Review/production/index.html)
- [Concept art and interactive wireframes](Review/index.html)
- [Remaining art work](Docs/ArtNextPass.md)

Open the HTML galleries locally after cloning. Production art is under `Assets/Art/Production/`: Batch01 has 44 PNGs, Campaign has 744, and RemasterExpansion has 575. The expansion includes 39 timed clips; vehicle views are static directions. These are candidate art libraries, not a completed playable campaign.

Building Expansion 04 provides 32 selected building tiles plus five preserved, blocked corner candidates. Every tile now has north/east/south/west material profiles in the [procedural sidecar](Assets/Art/Production/procedural-tiles.json), with a shared matcher and an offline neighbor viewer. [Usage and limitations](Docs/ProceduralTiles.md) distinguish logical connection candidates from seamless artwork and gameplay collision.

Exploration Expansion 03 adds 36 field frames for Maria, Guy and Leon, 12 candidate walk clips, 16 mine/crystal props and 16 cavern tiles. Its gallery includes native assets, a Firion scale comparison and three assembled maps. See [the batch notes](Docs/ExplorationExpansion03.md) for provenance and remaining pose/terrain polish.

World Builder Expansion 02 adds 24 transparent 128×128 props and 32 opaque 64×64 tiles at 64 PPU. Its review includes exact native contacts, three assembled maps and source/export SHA-256 records. All 1,202 earlier production PNGs and their Unity metadata remain byte-for-byte unchanged.

## Layout and validation

`ArtSource/` holds source masters, prompts and generation records. `References/` holds visual research and attribution. `Review/` holds galleries, wireframes, previews and preserved review candidates. `Tools/` holds the art pipelines and checks. `Docs/` preserves art documentation plus historical project context; gameplay implementation stays in [AI-Remake-FF2](https://github.com/cehinds/AI-Remake-FF2).

With Node.js and npm installed, run `npm install`, then `npm run verify:batch01`, `npm run verify:campaign`, `npm run verify:expansion`, and `npm run verify:wireframes`. The original repository-relative layout is retained so the existing pipelines, manifests and gallery links keep working.

For the Windows Unity project, run `Tools/connect-art.ps1` in the game repository. It connects its existing `ArtSource`, `Assets/Art`, `Review`, and `References` paths to an `ff2` checkout using directory junctions. It refuses to overwrite existing content. Keep this checkout on branch `ff2`; use separate checkouts for the other games. The Unity importer code remains in the game repository. Unity Editor import and playback still require validation on a licensed editor.

## Other games and provenance

The repository also has `dungeon-crawler` and `ashenspire` branches. Their artwork is separate from this branch. The original [repository index](Docs/RepositoryIndex.md) is preserved.

Existing source and licence records remain in their original locations. Reference images are research material outside the production asset tree. Inclusion in this repository does not establish a new licence or endorsement from the original game creators.
