# AshenSpire authoring source contract

Run `node --test checks/ashenspire-source-contract.test.mjs` for synthetic
corruption/missing/path/geometry fixtures, then
`node checks/ashenspire-source-contract.mjs --root <AI-Art-checkout>` for the real
source checks. Python with Pillow 12.3.0 is the decoder used by CI. The verifier
does not generate, rewrite, pack or publish anything.

The source receipt records 399 original Git paths, modes, blob IDs and byte
lengths from published commit `59663d814b62ab96cb5309b4e0720cd871782ee1`
(`ashenspire-hd-assets-v24`). These are the two registries, referenced rigs and
base manifests, all required HIGH/LITE WebP files, and the selected-source boards,
sheets, production metadata and preview inputs. Repeated actor aliases
are checked against the same original paths. No mutable Game checkout or
external asset-root fallback is used.

The production check covers all 41 stance actors (123 frame references) and all
four base-action families (48 frames). It requires complete inputs, exact Git
identity/length, valid single-frame WebP bytes, actual full decode, HIGH 512×512
and LITE 256×256 dimensions, declared anchors `[256,464]`, valid crop bounds,
and decoded HIGH alpha bounds using the original exporters' thresholds (>32 for
stances, >8 for base actions). Every HIGH file equals its rig's embedded HIGH.
Both stance tiers also match their original declared SHA256. Base manifests
declare no per-file LITE SHA256: their LITE identity comes from the explicitly
frozen Git receipt, alongside original per-family byte totals. This does not
invent an original LITE hash declaration.

The selected-source checks decode original PNG/WebP bytes at their declared
dimensions, check SHA256 for all twelve owner-selected stance choices and all
24 greatsword source records, and bind SM03/SW09 records to their copied
production metadata. The weapon-source projection was generated from the
unchanged original Game catalog; its repository/commit/blob/SHA256 are recorded
in the receipt. That code file is not represented as present in AI-Art. The
original copied selection manifests remain authoritative for the twelve board
choices. Source paths that originally used `assets-display/` resolve to the
exact copied `common/assets-display/` blobs, not to Game files.

All 15 sequence-review inputs must match actual source bytes. Historical AT3
must differ from current Counter, preserve the recorded attack-3 identity, and
retain the real original-sheet recipe bytes/hash/dimensions. PNG CRC/decoding
and WebP full decoding are required. These checks preserve input reproducibility;
they do not rerun an exporter or promise byte-identical re-encoding with a newer
encoder. Runtime output hashes and preview approval links remain Game checks.

The Game retains portable-project validation, runtime raster/hash checks,
animation/selection behavior and gameplay-binding assertions. This checker
supplies the real loose-image evidence that embedded-HIGH-only Game fixtures
cannot supply. Passing synthetic tests locally is not a production source pass;
the separate read-only CI job performs the production verification.

Intentional source updates require a reviewed update of the source metadata,
files and this receipt, with the replacement origin and evidence recorded. Do
not automatically refresh the receipt to make an unexplained failure pass.
The workflow has `contents: read`, is scoped to `ashenspire`, and only checks
sources. Its own files live outside the art-release workflow's path filters;
adding these checks does not allocate another art release or change v24.
