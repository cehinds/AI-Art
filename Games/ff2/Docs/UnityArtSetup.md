# Unity art setup

## Higher-resolution RemasterExpansion

The new manifest at `Assets/Art/Production/RemasterExpansion/manifest.json` supplies 32 PPU for 32px tiles and 64px field/torch frames, and 64 PPU for 128px battle canvases. `RemasterArtReview.ApplyImportSettings` updates both importer and texture-settings PPU before settings are applied. This keeps texture dimensions separate from world scale. Existing Batch 01/Campaign import defaults remain scoped to those libraries.

After export, reimport the RemasterExpansion folder in a licensed editor. Run **FF2 > Art > Validate Remaster Expansion Imports**, then **FF2 > Art > Create Missing Remaster Animation Clips**. The latter creates missing `.anim` files targeting `SpriteRenderer.m_Sprite` using manifest sprite IDs, per-frame durations and loop flags; existing animation files are preserved. Scene and Animator-controller wiring is separate. Camera sampling must be chosen with the new texture density before judging the higher-resolution art in a scene; the old low-resolution preview camera is not automatically upgraded.

The external Unity API compilation passed with zero warnings and errors. The editor commands, Unity asset import, generated `.anim` assets and Play mode have not been exercised on this license-blocked host. The review package includes real encoded GIFs and independently checked native PNGs; that is separate from Unity runtime evidence.

## Campaign library

`Assets/Art/Production/Campaign/manifest.json` declares every exported campaign sprite's ID, native dimensions, 16 PPU and pivot. `ProductionSpriteImporter` reads campaign pivots through `CampaignArtReview.GetPivot`: actors and props use their declared bottom-center anchor; effects and icons use center. All production PNGs share point filtering, clamp wrapping, full-rectangle meshes, no mipmaps, no NPOT scaling and uncompressed import.

After an export finishes, reimport the Campaign folder in a licensed Unity editor and run **FF2 > Art > Validate Campaign Sprite Imports**. PNGs may arrive before the completed manifest during export, so reimport is required to apply final declarations. The command validates imported dimensions, pivots and texture settings; it does not wire sprites into combat or maps. Review the native images and frame cycles in `Review/campaign/index.html` independently.

The updated C# importer and validator compiled against installed Unity 6000.4.10f1 API assemblies with zero warnings/errors on 2026-10-24. Actual Unity import, Play mode and player builds remain unverified because the prior Editor attempt stopped at licensing (exit 198).

## Batch 01 preview

The art preview is separate from `CoreReview.unity` and its technical gameplay. It assembles the exported terrain and structures on a 16-pixel grid and previews Firion's four walk directions in place. The arrangement is an illustrative art study, not an original-game map or a playable campaign slice.

## Import contract

Source/generated sheets remain outside `Assets/Art/Production/`. The exporter creates individual native PNGs plus `Assets/Art/Production/Batch01/manifest.json`. `ProductionSpriteImporter` applies these settings only to production textures:

| Setting | Value |
|---|---|
| Sprite mode / geometry | Single / Full Rect |
| Filtering / wrapping | Point / Clamp |
| Pixels per unit | 16 |
| Mipmaps / compression / NPOT scaling | Disabled / Uncompressed / None |
| Alpha | Transparency enabled |
| Terrain / structures | 16 x 16; centered pivot |
| Firion field frames | 16 x 24; bottom-center pivot, specifically under `Batch01/firion/` |

No sprite-sheet slicing is needed because each exported PNG is one complete frame/tile. Texture-specific platform overrides should remain disabled; the validator checks actual imported sprite bounds, pivot, pixels per unit and default texture settings. It does not validate every possible platform override or build output.

The manifest uses repo-relative `path`, `group`, `name`, `width`, `height`, `ppu`, and Firion `animation.direction`/`animation.frame`. Required groups are `terrain`, `structures`, and `firion`. The editor resolves all required art before creating a scene and reports missing files or incorrect imports to the Console.

## Open the preview

1. Open the project in Unity **6000.4.10f1** with a valid Editor license. Let Unity finish compiling/importing.
2. Choose **FFII Review > Validate Batch 01 Imported Art**. If settings differ, select the affected PNG and choose **Reimport**; the production importer sets the contract above.
3. Choose **FFII Review > Create or Open Batch 01 Art Review**. On first use it creates `Assets/FF2/Scenes/Batch01ArtReview.unity`; subsequent uses open the existing scene without rebuilding it. Unity prompts to save current modified scenes before opening a different scene.
4. Enter Play mode. Inspect the assembled path, house/roof, water, grass, dungeon walls, chest variants, door variants, torch and stairs. Four preview actors across the bottom show down, left, right, up simultaneously. The main actor changes facing every two seconds.
5. Review frame alignment and silhouette in the `left-foot → idle → right-foot → idle` cycle at **6 frames/second**. Movement, collision, sorting around moving world objects, and campaign interactions are outside this preview.

The camera renders to a **256 x 240** point-filtered texture. The preview displays it at the largest whole-number scale that fits, centered with black bars and square pixels. Windows at least 320 pixels wide/high also show explanatory labels outside the image. Below 256 x 240 the image remains at 1x and may be cropped; enlarge the Game view. A Game view of 1024 x 768 provides a readable 2x view with labels.

The tool does not require Tilemap, 2D Animation, a render-pipeline package, or new dependencies. Each cell is a `SpriteRenderer`. It leaves the core scene and build settings untouched.

To review a later export while preserving an edited scene, choose **FFII Review > Create New Batch 01 Art Review Copy**. Unity gives the new scene a unique asset path. Scenes and imported PNG metadata remain reviewable assets; nothing is deleted or overwritten by the generator.

## Validation and remaining evidence

`dotnet build Tools/core-tests/UnityAdapterCompile.csproj --nologo --no-restore` compiles the editor and runtime sources against installed Unity API assemblies. This verifies API/type compatibility; it does not run Unity import, create a scene, inspect rendering, or exercise animation lifecycle.

The earlier Unity batch attempt on this host stopped at licensing with exit **198**. No new licensing/configuration changes are part of this work. Until licensed Editor validation passes, scene generation, sprite import behavior and Play mode animation remain **unverified**. The scene is generated through Unity's API once the Editor can run; no hand-authored scene YAML is supplied.

Once licensed, inspect native and integer-scaled art for seams, cluster quality, transparency halos, baseline drift and animation timing. PNG dimensions and successful imports are separate evidence from visual acceptance; generated source-sheet normalization alone does not prove seamless tiles or faithful original-game reconstruction.
