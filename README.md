# DOVAHKIIN II Art

Public visual-art archive for DOVAHKIIN II, maintained on the **Dovakiin** branch
of [cehinds/AI-Art](https://github.com/cehinds/AI-Art/tree/Dovakiin).
The branch spelling is intentional. `main` remains the shared repository index.

## Contents

- `assets/sprites/`: 39 original SVG character, creature, and object sprites.
- `assets/bg/`: 4 original SVG battle backdrops.
- `assets/icons/`: 2 PNG icons from the Blazor web client.
- `assets/{sprites,bg}/manifest.json`: original, unmodified asset manifests.
- `authoring/`: original palettes, sprite-part definitions, and model overrides.
- `asset-manifest.json`: SHA-256, Git blob hashes, and source locations for every
  imported file, with immutable commit IDs for all 74 inspected branch heads.
- `provenance/`: original asset documentation and Git author/coauthor records.
- `ATTRIBUTION.md`: provenance and licensing limits. No new license is granted.

Source: [cehinds/ff2_core](https://github.com/cehinds/ff2_core). The archive covers
all **45 distinct tracked visual files** at the scanned branch heads, plus five
art-definition/manifest files and the original asset README. Copies under
`assets/` and `legacy/assets/` with identical Git blobs are stored once; every
source branch/path/commit association is retained in `asset-manifest.json`.
The three primary snapshots are:

| Source branch | Commit |
| --- | --- |
| `release` | `c4e9d398b4769131e52eacd2e54b8801b601efbf` |
| `Development` | `ea91ed9df3451a259d412eb20e359bb4a9918a79` |
| `master` | `b0a24c2c139b5e8446be670d144921f0977126f0` |

`master` currently contains no tracked image files. Art was located on the
browser/legacy branches and the Blazor web-client branches, not inferred from
the default branch alone. Audio/music, release executables, gameplay data,
gameplay/rendering engines, archives, and files found only in deleted history
are outside this visual-art transfer.

## Game Compatibility

**No files, game references, branch heads, or build settings in `ff2_core` were
changed or removed.** The source game keeps its vendored runtime copies and
relative asset paths, including offline fallbacks. This branch is an additional,
independently managed home for the artwork, not a remote runtime dependency.
The PNG icons were organized into `assets/icons/` here only; their original
`src/Dovahkiin.Web/wwwroot/` paths remain untouched in the game.

For future art updates, vendor the selected files back into the game's existing
paths as an explicit, tested game change. Pin the art commit, verify the listed
hashes, and update every relevant manifest. Do not replace local asset paths
with branch-based GitHub/raw URLs: that would make offline builds depend on the
network and allow future branch updates to change released artwork.

## Verification

Requires Node.js 18 or newer; no dependencies or build/version bump required.

```sh
node tools/verify-art.mjs
node --test tools/verify-art.test.mjs
```

The verifier checks every imported byte against both SHA-256 and the original
Git blob hash, validates image signatures and JSON, checks manifest references,
and checks that each provenance entry points to an inspected branch snapshot.
Source game runtime tests are not claimed: game code and references are
unchanged by this transfer.

## Maintenance Instructions For Future Agents

Keep this README, `ATTRIBUTION.md`, and `asset-manifest.json` current for every
asset change. Preserve original filenames, file headers, license notices,
author/coauthor attribution, and source commit IDs. Never invent a license or
infer unrestricted reuse from this repository being public. Store differing
versions separately rather than silently replacing them. Use `.gitattributes`
to keep imported bytes intact and rerun both verification commands before
committing. Work only on `Dovakiin` for DOVAHKIIN art; do not change the other
game branches or delete runtime assets from the source game.
