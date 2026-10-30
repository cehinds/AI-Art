// AshenSpire-only release policy. Network mutations belong to the reviewed workflow.
import { createHash } from 'node:crypto';
import { createReadStream, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { zipName } from './pack.mjs';
import { CONTRACT, verifyDisplayManifest } from './display-snapshot.mjs';
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const REPOSITORY = 'cehinds/AI-Art';
export const BRANCH = 'ashenspire';
export const TAG_PREFIX = 'ashenspire-hd-assets-v';
export function requireReleaseEnvironment(env = process.env) {
  if (env.GITHUB_REPOSITORY !== REPOSITORY || env.GITHUB_REF !== 'refs/heads/' + BRANCH
      || !/^[0-9a-f]{40}$/.test(env.GITHUB_SHA || '')) throw new Error('Release requires the immutable AI-Art ashenspire event commit');
}
export function tagFor(version) {
  if (!Number.isSafeInteger(version) || version < 1) throw new Error('Release version must be a positive safe integer');
  return TAG_PREFIX + version;
}
export function nextVersion(tags, floor) {
  tagFor(floor);
  let highest = 0;
  for (const tag of tags) {
    const match = /^ashenspire-hd-assets-v([1-9][0-9]*)$/.exec(tag);
    if (!match) continue;
    const number = Number(match[1]);
    tagFor(number);
    highest = Math.max(highest, number);
  }
  const next = Math.max(floor, highest + 1);
  tagFor(next);
  return next;
}
export function readReleaseConfig(root = ROOT) {
  const config = JSON.parse(readFileSync(resolve(root, 'release.json'), 'utf8'));
  if (!config || typeof config !== 'object' || Array.isArray(config)
      || typeof config.preserveMigratedAssetBytes !== 'boolean') {
    throw new Error('release.json requires boolean preserveMigratedAssetBytes; policy changes require explicit review');
  }
  tagFor(config.version);
  return config;
}
export function allocateReleaseVersion(root, tags) {
  const config = readReleaseConfig(root);
  const version = nextVersion(tags, config.version);
  // Preserve the reviewed migration policy and any other config fields.
  writeFileSync(resolve(root, 'release.json'), JSON.stringify({ ...config, version }, null, 2) + '\n');
  return version;
}
export function migrationPolicyNote(root = ROOT) {
  return readReleaseConfig(root).preserveMigratedAssetBytes
    ? 'Active preserveMigratedAssetBytes policy: this release retains the reviewed migration snapshot and complete v23 high/light ZIP bytes, regardless of allocated version. Historical manifest header text is retained for archive identity.'
    : 'The migration byte freeze was explicitly disabled in reviewed release.json; this release does not promise the frozen migration snapshot or v23 high/light ZIP identity.';
}
export function combinedCredits(legacy, game) {
  if (!legacy.trim() || !game.trim()) throw new Error('Both original credit ledgers are required');
  return '# AshenSpire art release credits\n\n'
    + 'These two original ledgers retain their own authorship, source and unresolved-rights records. '
    + 'Their inclusion does not relicense artwork. Relative paths retain their original repository context.\n\n'
    + '## Original AshenSpire-art ledger\n\n' + legacy
    + '\n\n## Additional game-source ledger\n\n'
    + 'Source: cehinds/AshenSpire@eaf770ce494655831273169e875c26daf9a0d095; '
    + 'preserved at https://github.com/cehinds/AI-Art/blob/e71ff1f23d95da84deede90907f2f28f7aedb55a/provenance/AshenSpire/CREDITS.md.\n\n' + game;
}
async function fileHash(path) {
  const hash = createHash('sha256');
  let bytes = 0;
  for await (const chunk of createReadStream(path)) { hash.update(chunk); bytes += chunk.length; }
  return { bytes, sha256: hash.digest('hex') };
}
export function artifactNames(version) {
  tagFor(version);
  return ['high', 'light', 'common'].flatMap((pack) => [zipName(pack, version), zipName(pack, version) + '.sha256'])
    .concat(['art-manifest.json', 'CREDITS.md']);
}
export async function artifactRecords(root, version) {
  return Promise.all(artifactNames(version).map(async (name) => ({ name, ...await fileHash(resolve(root, 'dist', name)) })));
}
export function verifyReleaseMetadata(release, expected, version, sha, draft) {
  if (release.tag_name !== tagFor(version) || release.target_commitish !== sha
      || release.draft !== draft || release.prerelease || !Number.isSafeInteger(release.id)) throw new Error('Release state/tag/target mismatch');
  if (!Array.isArray(release.assets) || release.assets.length !== expected.length) throw new Error('Release asset count mismatch');
  const seen = new Set();
  for (const asset of release.assets) {
    const wanted = expected.find((item) => item.name === asset.name);
    if (!wanted || seen.has(asset.name) || asset.size !== wanted.bytes || asset.digest !== 'sha256:' + wanted.sha256) {
      throw new Error('Release asset size/hash/name mismatch: ' + asset.name);
    }
    seen.add(asset.name);
  }
  return release.id;
}
export function verifyTag(ref, sha) {
  if (ref?.object?.type !== 'commit' || ref.object.sha !== sha) throw new Error('Scoped release tag must be lightweight and name the event commit');
}
export function verifyMigrationSnapshot(root = ROOT) {
  const config = readReleaseConfig(root);
  if (!config.preserveMigratedAssetBytes) return false;
  const contract = JSON.parse(readFileSync(resolve(root, CONTRACT), 'utf8'));
  const manifest = JSON.parse(readFileSync(resolve(root, 'art-manifest.json'), 'utf8'));
  // A reviewed additive export does not unfreeze any migrated byte. Verify its
  // exact records, then verify the complete original snapshot independently.
  if (config.reviewedCardCutouts === true) {
    const additions = JSON.parse(readFileSync(resolve(root, 'provenance/AshenSpire/reviewed-card-cutouts.json'), 'utf8')).assets;
    const seen = new Set();
    for (const asset of Object.values(additions)) {
      if (!/^assets-display\/card-cutouts\/[A-Za-z0-9.]+\.png$/.test(asset.path) || seen.has(asset.path)) throw new Error('Invalid reviewed display addition');
      seen.add(asset.path);
      const expected = {common:{path:asset.path,bytes:asset.bytes,sha256:asset.sha256}};
      if (JSON.stringify(manifest.assets[asset.path]) !== JSON.stringify(expected)) throw new Error('Reviewed display addition changed: '+asset.path);
      delete manifest.assets[asset.path];
      manifest.count--;
    }
  } else if (config.reviewedCardCutouts !== undefined) throw new Error('reviewedCardCutouts must be true when present');
  verifyDisplayManifest(manifest, contract);
  return true;
}
export async function verifyFrozenArchives(root, version) {
  tagFor(version);
  if (!verifyMigrationSnapshot(root)) return;
  const contract = JSON.parse(readFileSync(resolve(root, CONTRACT), 'utf8'));
  for (const pack of ['high', 'light']) {
    const actual = await fileHash(resolve(root, 'dist', zipName(pack, version)));
    if (actual.sha256 !== contract.preservedZipSha256[pack]) throw new Error('Migration policy: release v' + version + ' changed the original ' + pack + ' ZIP bytes');
  }
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  requireReleaseEnvironment();
  const config = readReleaseConfig(ROOT);
  const command = process.argv[2], version = Number(process.argv[3]);
  if (command === '--next-version') {
    console.log(nextVersion(readFileSync(0, 'utf8').split(/\r?\n/), config.version));
  } else if (command === '--allocate-version') {
    console.log(allocateReleaseVersion(ROOT, readFileSync(0, 'utf8').split(/\r?\n/)));
  } else if (command === '--verify-snapshot') {
    verifyMigrationSnapshot(ROOT);
  } else if (command === '--policy-note') {
    console.log(migrationPolicyNote(ROOT));
  } else if (command === '--credits') {
    const game = readFileSync(resolve(ROOT, 'provenance/AshenSpire/CREDITS.md'), 'utf8');
    const contract = JSON.parse(readFileSync(resolve(ROOT, CONTRACT), 'utf8'));
    if (createHash('sha256').update(game).digest('hex') !== contract.source.creditsSha256) throw new Error('Frozen game credit ledger changed');
    writeFileSync(resolve(ROOT, 'dist/CREDITS.md'), combinedCredits(readFileSync(resolve(ROOT, 'CREDITS.md'), 'utf8'), game));
  } else if (command === '--verify-archives') {
    await verifyFrozenArchives(ROOT, version);
  } else if (command === '--verify-draft' || command === '--verify-published') {
    const input = JSON.parse(readFileSync(0, 'utf8'));
    const matches = Array.isArray(input) ? input.filter((release) => release.tag_name === tagFor(version)) : [input];
    if (matches.length !== 1) throw new Error('Expected exactly one scoped release');
    console.log(verifyReleaseMetadata(matches[0], await artifactRecords(ROOT, version), version, process.env.GITHUB_SHA, command === '--verify-draft'));
  } else if (command === '--verify-tag') {
    verifyTag(JSON.parse(readFileSync(0, 'utf8')), process.env.GITHUB_SHA);
  } else throw new Error('Unknown AshenSpire release command');
}
