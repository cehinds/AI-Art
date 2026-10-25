# AI Art catalog

The combined art library lives on `main` and `dev`. Each game keeps its own source branch, and the catalog preserves a byte-verified snapshot under `Games/<game>/`.

## Browse the galleries

- [All art, organized by asset type](https://cehinds.github.io/AI-Art/)
- [Final Fantasy II](https://cehinds.github.io/AI-Art/games/ff2/)
- [Dungeon Crawler](https://cehinds.github.io/AI-Art/games/dungeon-crawler/)
- [AshenSpire](https://cehinds.github.io/AI-Art/games/ashenspire/)
- [Dovakiin](https://cehinds.github.io/AI-Art/games/dovakiin/)

Filter by tiles, weapons, characters, creatures, environments, props, effects, animations, UI and more. Search names and paths, select a game, and open an asset to see its original file, dimensions, hash and source commit. Production is the default collection; choose All collections to include concepts, source sheets, references, review images and archives. GIF details play the original animation. Large packages and non-image authoring files have direct original links.

The galleries use small previews. The complete original artwork, authoring files, manifests, attribution and provenance are stored in this repository. Previews may trim transparent padding for readability; originals are unchanged.

## Branches and publishing

- `ff2`, `dungeon-crawler`, `ashenspire`, and `Dovakiin`: game-specific source libraries.
- `dev`: combined catalog development and verification.
- `main`: combined published catalog. GitHub Actions builds and deploys the combined page and all game pages together.

Both combined branches contain the full source snapshots. They do not replace the game branches. Each `Games/<game>/_source.json` records the exact upstream commit and file hashes. Existing source/licence records remain in their original relative paths. Inclusion here does not establish a new licence.

## Build and verify locally

Requires Node.js 22 or newer.

```sh
npm ci
npm test
npm run verify
npm run build
npm run serve
```

Open `http://127.0.0.1:4173/AI-Art/`. `_site/` contains the generated Pages site and is excluded from Git. Snapshot originals stay in `Games/`; the site serves previews and links to commit-pinned originals.

## Refresh the collection

Fetch the source branches, verify and commit your current snapshot first, then run the reviewed update:

```sh
git fetch origin
npm run verify -- --committed
npm run import -- --update
npm test
npm run verify
npm run build
```

The importer refuses unrecorded files, local snapshot edits or an uncommitted previous snapshot. Updates retain old versions in Git history and record changed, added and removed upstream paths. Review the result on `dev` before promoting to `main`; only `main` publishes the site. Future game additions belong in `scripts/lib.mjs` and the page navigation.

After committing a verified snapshot update, connect the imported source histories before pushing:

```sh
git merge --no-ff --strategy=ours origin/ff2 origin/dungeon-crawler origin/ashenspire origin/Dovakiin
```

This records the game commits as parents while preserving the already verified `Games/` layout. It avoids re-uploading gigabytes of artwork GitHub already has; it does not replace the snapshot importer or its verification.

[Design reference and visual checks](docs/design/spec.md) · [Original repository index](docs/repository-index.md)
