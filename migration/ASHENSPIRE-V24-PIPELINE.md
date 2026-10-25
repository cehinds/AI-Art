# AshenSpire v24 pipeline contract

This is a text-only draft based on AI-Art ashenspire commit
e71ff1f23d95da84deede90907f2f28f7aedb55a. No v24 archives have been built
or published. Pushing this pipeline to ashenspire activates publication and
requires the explicit review recorded outside this draft.

Schema 2 stays unchanged. The 675 game display exports become common records
with exactly path, bytes and sha256. IDs and ZIP paths remain assets-display/...
and repository files live under common/assets-display/.... There are 8,169 IDs:
7,348 high/light pairs and 821 common records. Common payload is 85,568,599 bytes.

migration/ashenspire-v24-display-contract.json records the six original game
catalogs at eaf770ce494655831273169e875c26daf9a0d095. All 675 existing Git
blobs were streamed without binary checkout/staging: actual lengths, SHA256
and positive PNG/WebP dimensions were checked against those catalogs.
Dimensions are validation metadata, never additional common record fields.

The expected common pack-index SHA256 is:
ed667bd375bba917f8f6581d7bbd094e9d4af216b1bb94d4be4913258c34fbb3

The serialized historical manifest header and all original records are retained.
The header's AshenSpire-art wording is archival compatibility text; the current
host is cehinds/AI-Art, branch ashenspire. Current source and host identity live
in the frozen contract and release notes. The required boolean policy
`release.json.preserveMigratedAssetBytes` is true. While true, EVERY allocated
release version must retain the reviewed manifest snapshot and complete v23
high/light ZIP hashes, including a v25 retry after an occupied or failed v24:
- high: 9739aec653cf8f2db8aec26d2f40bb2315356330aecabba4279797c5b79a45fc
- light: fcc45de4f47902ee40a3c1e4e18266217b0c965a405b0a9bc3d0d60e683780f0

The original root credit ledger and copied game ledger stay intact in Git.
Release CREDITS.md contains both ledgers verbatim, with an immutable link to
the copied game ledger. Existing notices and unresolved provenance remain.
The frozen copied game ledger is hash-checked; new art credits belong in the
current root ledger rather than overwriting that historical source receipt.

Only ashenspire pushes publish. PR validation has read-only permissions;
publication has contents-write permission and per-game concurrency. Tags are
ashenspire-hd-assets-vN, while the three ZIP basenames stay unprefixed.
Existing tags/releases, including v23, are never overwritten. A failed draft
is retained; a later run chooses a new unused version. Allocation preserves all
release.json policy fields. Missing or non-boolean policy values fail closed.
Future intentional asset changes require an explicit reviewed configuration
change to preserveMigratedAssetBytes: false, with review of the resulting loss
of the freeze and the changed manifest/notices. To establish a new freeze,
review the new contract hashes, policy and release-note wording together.
Version allocation never lifts it. Release notes describe the active policy.
Each new tag must be fresh and lightweight, naming the immutable event commit.
Only after packing and all local artifact checks does CI reserve that new ref
with GitHub's create-only POST git/refs; it never patches or forces a ref. Release
creation requires --verify-tag. After uploaded assets are verified, CI API-reads
the actual ref and checks its type and exact commit immediately before publishing.
Annotated tags and tags naming any other object are rejected before publication;
missing refs also fail closed. Orphan refs and existing drafts stay retained;
the next unused version still obeys the same migration freeze policy.

CI sparse-checks out the runtime trees and required class-smash source PNGs,
not the full authoring/archive collection. It checks the complete real manifest,
light provenance, reproducible ZIPs, the policy-controlled snapshot and archive
hashes. Source-integrity separately hashes the three class-smash packages'
original frame PNGs, original first/last bookends and source provenance JSON.
Those assertions check current source PNG/provenance bytes against the current
production.json records. They do not independently bind an edited production.json
to the immutable origin: the separate approved migration receipt records the
original source commit and exact copied Git blob IDs. No decoded-RGBA claim is made.
A separate read-only source workflow also runs these integrity assertions on
source-only pushes and pull requests, without packing or publication.
Only after eight uploaded artifacts match local sizes/SHA256 does a draft
become public; the published target and scoped tag are checked again.

The local projected manifest was derived as metadata from the verified frozen
contract. It still requires full-tree manifest/pack gates on CI before release.
Game adoption must update its pin and matching manifest atomically after that
verified release; game originals remain until resolver/editor checks succeed.
