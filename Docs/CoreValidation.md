# Core validation evidence

Date: 2026-10-24. Baseline: repository contained only `.git`, no commit and no existing Unity project, scenes, tests or Console baseline. The parent task independently verified an empty origin. Other agents' review/documentation work is outside this report.

## Executed: pure-core behavioral suite

```powershell
dotnet run --project Tools/core-tests/CoreTests.csproj -- 'C:\repos\AI-Remake-FF2'
```

SDK: .NET **10.0.402**. Last result recorded by the implementation agent: **38 passed, 0 failed**, exit code **0**. The runner compiles the actual `Assets/FF2/Core/*.cs` files, parses the actual authored JSON packs and runs behavior through public APIs. It does not mock Unity or claim Unity runtime execution.

Coverage by behavior:

- Stable IDs; two authored packs/ten entries; dependency-order independence; duplicate pack/entry rejection; missing dependency; dependency cycle; broken reference; undeclared/transitive dependency; unsupported schema; invalid actor stats; immutable catalog snapshots.
- Keyword learning, idempotence, content-kind validation and Ask gating.
- Speed/tie order; invalid-target state preservation; guard damage/duration; skipped defeated actors; victory/defeat; terminal action rejection; duplicate instance IDs; dead-only sides; enemy-turn ownership.
- Sample weapon-use counting/rank growth and no progression on Guard.
- Save round trip; version-one migration; future versions; unknown XML fields/attributes; truncated XML/DTD rejection; missing IDs/packs/ownership; invalid stats/duplicates/coordinates.
- Required pack dependency closure, loading after unrelated optional-pack removal, and faster-enemy opening turns.
- Real temporary-file writes: replacement retains the previous save as `.bak`; invalid writes leave the existing file byte-for-byte intact. Tests create unique temporary directories and remove only their own test files.

## Executed: Unity API compatibility compilation outside Editor

```powershell
dotnet build Tools/core-tests/UnityAdapterCompile.csproj --nologo
```

Result: **Build succeeded. 0 warnings, 0 errors**, exit code **0**. This compiles all authored core, runtime and editor C# files against assemblies from the installed Unity **6000.4.10f1** Editor. `UnityManagedPath` can be overridden with an MSBuild property for another installation. This catches C# and public Unity API mistakes; it does **not** prove Unity import, Mono runtime compatibility, asset references, scene execution or player building.

## Parent-run Unity batch validation

The parent attempted the following batch validation. Unity exited **198** before compilation with **`No valid Unity Editor license found. Please activate your license.`** Its headless licensing entitlement was unavailable. Log: `Logs/unity-core-batch.log`. **Editor import/compilation, scene generation, Unity smoke execution and player build are blocked by licensing**; their success is not inferred from .NET checks. No generated scene or player build is claimed.

```powershell
& 'C:\Program Files\Unity\Hub\Editor\6000.4.10f1\Editor\Unity.exe' `
  -batchmode -nographics -quit `
  -projectPath 'C:\repos\AI-Remake-FF2' `
  -executeMethod FF2.Editor.ReviewProject.ValidateBatch `
  -logFile 'C:\repos\AI-Remake-FF2\Logs\unity-core-batch.log'
```

`ValidateBatch` loads actual Unity resource JSON, validates merged content, exercises a deterministic battle to victory, verifies a save round trip and creates the review scene when absent. On success it writes `Logs/core-unity-validation.txt` and logs `FFII CORE VALIDATION PASS`. Stable GUID `.meta` files were created for authored core/runtime/editor/resource assets with local tooling because Unity import was unavailable; actual Unity import remains unverified. Retain these metadata files with source assets before any future commit.

To attempt a Windows development player, replace the method with `FF2.Editor.ReviewProject.BuildReviewPlayer`. Expected artifact: `Builds/Review/FF2Review.exe`. A build attempt requires installed Windows support and an available Unity license. Successful completion must be confirmed from process exit, log and artifact existence.

## Status and required follow-through

| Criterion | Evidence/status |
|---|---|
| Core data and rule behaviors | PASS: 38 executable tests |
| Authored Unity adapters compile against installed API | PASS: external compilation, zero warnings/errors |
| Unity Editor import and assembly compilation | BLOCKED: no valid Unity license |
| Serialized scene and `.meta` import | BLOCKED: no valid Unity license |
| Unity-side core/resource smoke | BLOCKED: no valid Unity license |
| Play Mode button/input/state interaction | NOT RUN |
| Windows player build/launch | NOT RUN |
| Pixel-art visual quality | NOT IMPLEMENTED in sandbox |
| Full campaign / faithful FFII mechanics | NOT IMPLEMENTED |

**Overall: Blocked for Unity integration validation; core behavior passed.** Activate the selected Unity Editor license, rerun the batch method, then exercise the review scene in Play Mode and build/launch the Windows player. Compilation/tests do not establish a finished remake or a playable player build. No pre-existing source failures existed in the empty-project baseline. No commit, push or release occurred.
