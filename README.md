# FFII art library

The `ff2` branch of [AI-Art](https://github.com/cehinds/AI-Art) is the canonical home for the artwork created for the original Japanese/Famicom Final Fantasy II remake project.

This transfer preserves 1,202 production PNGs, their Unity metadata, generated source masters, prompts, selected and rejected candidates, reference research, concept art, wireframes, animation previews, and portable packages. Files were copied byte-for-byte and verified by SHA-256. See [the migration inventory](Docs/FF2ArtMigration.json).

## Review the artwork

- [World Builder 100: 100 biome tiles and 32 object sprites](Review/remaster-expansion/worldbuilder100/index.html)
- [World Builder portable ZIP](Review/world-builder-100.zip)
- [Higher-resolution sprites, animations and environment gallery](Review/remaster-expansion/index.html)
- [Campaign sprite gallery](Review/campaign/index.html)
- [Batch 01 gallery](Review/production/index.html)
- [Concept art and interactive wireframes](Review/index.html)
- [Remaining art work](Docs/ArtNextPass.md)

Open the HTML galleries locally after cloning. Production art is under `Assets/Art/Production/`: Batch01 has 44 PNGs, Campaign has 744, and RemasterExpansion has 414. The expansion includes 27 timed clips; the latest vehicle views are static directions. These are candidate art libraries, not a completed playable campaign.

## Layout and validation

`ArtSource/` holds source masters, prompts and generation records. `References/` holds visual research and attribution. `Review/` holds galleries, wireframes, previews and preserved review candidates. `Tools/` holds the art pipelines and checks. `Docs/` preserves art documentation plus historical project context; gameplay implementation stays in [AI-Remake-FF2](https://github.com/cehinds/AI-Remake-FF2).

With Node.js and npm installed, run `npm install`, then `npm run verify:batch01`, `npm run verify:campaign`, `npm run verify:expansion`, and `npm run verify:wireframes`. The original repository-relative layout is retained so the existing pipelines, manifests and gallery links keep working.

For the Windows Unity project, run `Tools/connect-art.ps1` in the game repository. It connects its existing `ArtSource`, `Assets/Art`, `Review`, and `References` paths to an `ff2` checkout using directory junctions. It refuses to overwrite existing content. Keep this checkout on branch `ff2`; use separate checkouts for the other games. The Unity importer code remains in the game repository. Unity Editor import and playback still require validation on a licensed editor.

## Other games and provenance

The repository also has `dungeon-crawler` and `ashenspire` branches. Their artwork is separate from this branch. The original [repository index](Docs/RepositoryIndex.md) is preserved.

Existing source and licence records remain in their original locations. Reference images are research material outside the production asset tree. Inclusion in this repository does not establish a new licence or endorsement from the original game creators.
