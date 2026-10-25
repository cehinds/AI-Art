#!/usr/bin/env node
// One-time, byte-exact mirror of the already-published AshenSpire v23 release.
// It does not build packs or import source-repository Git history.
import { createHash } from 'node:crypto';
import { createReadStream, createWriteStream } from 'node:fs';
import { mkdtemp, readFile, rm, stat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

export const API = 'https://api.github.com';
export const TARGET_REPO = 'cehinds/AI-Art';
export const TARGET_BRANCH = 'ashenspire';
export const TARGET_TAG = 'ashenspire-hd-assets-v23';
export const SOURCE_REPO = 'cehinds/AshenSpire-art';
export const SOURCE_TAG = 'hd-assets-v23';
const sha256 = (b) => createHash('sha256').update(b).digest('hex');
const authHeaders = (extra = {}, env = process.env) => ({
  authorization: `Bearer ${env.GITHUB_TOKEN}`,
  accept: 'application/vnd.github+json',
  'x-github-api-version': '2022-11-28',
  'user-agent': 'AI-Art-AshenSpire-Release-Mirror',
  ...extra,
});

export function requireEnvironment(env = process.env) {
  if (!env.GITHUB_TOKEN) throw new Error('GITHUB_TOKEN is required');
  if (env.GITHUB_REPOSITORY !== TARGET_REPO) throw new Error('This mirror can only publish to cehinds/AI-Art');
  if (env.GITHUB_REF !== `refs/heads/${TARGET_BRANCH}`) throw new Error('This mirror can only run from refs/heads/ashenspire');
  if (!/^[0-9a-f]{40}$/.test(env.GITHUB_SHA || '')) throw new Error('GITHUB_SHA is missing or invalid');
}

export async function apiJson(path, init = {}, { env = process.env, fetchImpl = fetch } = {}) {
  const response = await fetchImpl(`${API}${path}`, {
    ...init,
    headers: authHeaders(init.headers || {}, env),
  });
  const body = await response.text();
  if (!response.ok) {
    throw Object.assign(
      new Error(`GitHub API ${init.method || 'GET'} ${path}: HTTP ${response.status}: ${body.slice(0, 600)}`),
      { status: response.status },
    );
  }
  return body ? JSON.parse(body) : null;
}

export function verifyAssetBytes(asset, bytes) {
  const gotSha = sha256(bytes);
  if (bytes.length !== asset.size || gotSha !== asset.sha256) {
    throw new Error(`Bytes for ${asset.name} differ from frozen size/SHA-256`);
  }
  return { size: bytes.length, sha256: gotSha };
}

export function assertAssetShape(request) {
  if (request.schema !== 1 || request.source.repository !== SOURCE_REPO ||
      request.source.tag !== SOURCE_TAG || request.destination.repository !== TARGET_REPO ||
      request.destination.branch !== TARGET_BRANCH || request.destination.tag !== TARGET_TAG) {
    throw new Error('The frozen mirror request does not match this workflow');
  }
  const expected = [
    'hd-assets-v23.zip', 'hd-assets-v23.zip.sha256',
    'light-assets-v23.zip', 'light-assets-v23.zip.sha256',
    'common-assets-v23.zip', 'common-assets-v23.zip.sha256',
    'art-manifest.json', 'CREDITS.md',
  ];
  if (!Array.isArray(request.assets) || request.assets.length !== expected.length ||
      request.assets.some((asset, i) => asset.name !== expected[i])) {
    throw new Error('The mirror request must carry exactly the frozen v23 assets in order');
  }
  let total = 0;
  for (const asset of request.assets) {
    if (!Number.isSafeInteger(asset.id) || !Number.isSafeInteger(asset.size) || asset.size < 0 ||
        !/^[0-9a-f]{64}$/.test(asset.sha256) ||
        asset.url !== `https://api.github.com/repos/${SOURCE_REPO}/releases/assets/${asset.id}`) {
      throw new Error(`Invalid frozen source metadata for ${asset.name}`);
    }
    total += asset.size;
  }
  if (total !== request.totalBytes) throw new Error('The frozen request total does not match its asset sizes');
}

export function validateSourceRelease(release, request) {
  if (release.id !== request.source.releaseId || release.tag_name !== SOURCE_TAG ||
      release.target_commitish !== request.source.targetCommit || release.draft || release.prerelease) {
    throw new Error('The original public v23 release metadata changed');
  }
  if (!Array.isArray(release.assets) || release.assets.length !== request.assets.length) {
    throw new Error('The original release has an unexpected asset count');
  }
  const byName = new Map();
  for (const asset of release.assets) {
    if (byName.has(asset.name)) throw new Error(`Original release has duplicate asset ${asset.name}`);
    byName.set(asset.name, asset);
  }
  if (byName.size !== request.assets.length) throw new Error('The original release has an unexpected asset set');
  for (const wanted of request.assets) {
    const got = byName.get(wanted.name);
    if (!got || got.id !== wanted.id || got.size !== wanted.size || got.digest !== `sha256:${wanted.sha256}`) {
      throw new Error(`Original release metadata mismatch for ${wanted.name}`);
    }
  }
  return true;
}

export async function findReleaseByTag(tag, getJson = apiJson) {
  const path = `/repos/${TARGET_REPO}/releases/tags/${encodeURIComponent(tag)}`;
  let direct = null;
  try { direct = await getJson(path); }
  catch (error) { if (error.status !== 404) throw error; }

  const matches = [];
  if (direct?.tag_name === tag) matches.push(direct);
  for (let page = 1; page <= 10; page++) {
    const rows = await getJson(`/repos/${TARGET_REPO}/releases?per_page=100&page=${page}`);
    if (!Array.isArray(rows)) throw new Error('GitHub release list is not an array');
    matches.push(...rows.filter((release) => release.tag_name === tag));
    if (rows.length < 100) break;
  }
  const unique = [...new Map(matches.map((release) => [release.id, release])).values()];
  if (unique.length > 1) throw new Error(`Multiple destination releases claim tag ${tag}`);
  return unique[0] || null;
}

export async function resolveGitTagObject(object, getJson = apiJson) {
  const seen = new Set();
  let current = object;
  while (current?.type === 'tag') {
    if (!/^[0-9a-f]{40}$/.test(current.sha || '') || seen.has(current.sha)) {
      throw new Error('Destination tag contains a malformed or cyclic annotated tag');
    }
    seen.add(current.sha);
    const tag = await getJson(`/repos/${TARGET_REPO}/git/tags/${current.sha}`);
    current = tag.object;
  }
  if (current?.type !== 'commit' || !/^[0-9a-f]{40}$/.test(current.sha || '')) {
    throw new Error('Destination tag does not resolve to a commit');
  }
  return current.sha;
}

export async function verifyTagBeforeDraft({ currentSha, getJson = apiJson }) {
  let ref;
  try {
    ref = await getJson("/repos/" + TARGET_REPO + "/git/ref/tags/" + encodeURIComponent(TARGET_TAG));
  } catch (error) {
    if (error.status === 404) return { present: false, commitSha: null };
    throw error;
  }
  const commitSha = await resolveGitTagObject(ref.object, getJson);
  if (commitSha !== currentSha) {
    throw new Error("Destination tag exists without a release and does not point to this ashenspire event commit");
  }
  return { present: true, commitSha };
}

export async function verifyDestinationTag({ release, currentSha, allowMissing = false, getJson = apiJson }) {
  const expectedCommit = release.target_commitish;
  if (!/^[0-9a-f]{40}$/.test(expectedCommit || '')) {
    throw new Error('Destination release target is not an immutable commit SHA');
  }
  const comparison = await getJson(`/repos/${TARGET_REPO}/compare/${expectedCommit}...${currentSha}`);
  if (!['ahead', 'identical'].includes(comparison.status)) {
    throw new Error('Destination release target is not an ancestor of this ashenspire branch run');
  }
  let ref;
  try {
    ref = await getJson(`/repos/${TARGET_REPO}/git/ref/tags/${encodeURIComponent(TARGET_TAG)}`);
  } catch (error) {
    if (error.status === 404 && allowMissing) return { present: false, commitSha: null };
    throw error;
  }
  const commitSha = await resolveGitTagObject(ref.object, getJson);
  if (commitSha !== expectedCommit) {
    throw new Error('Destination tag commit differs from the release immutable target');
  }
  return { present: true, commitSha };
}

export function inspectExistingAssets(release, assets, isPublished) {
  const expected = new Map(assets.map((asset) => [asset.name, asset]));
  const existing = new Map();
  for (const got of release.assets || []) {
    const wanted = expected.get(got.name);
    if (!wanted) throw new Error(`Destination release has unexpected asset ${got.name}; refusing to alter it`);
    if (existing.has(got.name)) throw new Error(`Destination release has duplicate asset ${got.name}`);
    if (got.size !== wanted.size || got.digest !== `sha256:${wanted.sha256}`) {
      throw new Error(`Destination asset ${got.name} differs in size or SHA-256; refusing to replace it`);
    }
    existing.set(got.name, got);
  }
  if (isPublished && existing.size !== expected.size) {
    throw new Error('The published destination release is incomplete; refusing to modify it');
  }
  return existing;
}

export function validatePublishedRelease(release, assets) {
  if (release.tag_name !== TARGET_TAG || release.draft || release.prerelease) {
    throw new Error('The destination release is not the expected published release');
  }
  inspectExistingAssets(release, assets, true);
  return true;
}

export function verifyChecksumText(text, zipName, zipSha) {
  const match = text.match(/^([0-9a-f]{64})[ \t]+\*?([^\r\n]+)\r?\n?$/);
  if (!match || match[1] !== zipSha || match[2].trim() !== zipName) {
    throw new Error(`checksum sidecar for ${zipName} does not name its frozen zip hash`);
  }
  return true;
}

async function hashFile(path) {
  const hash = createHash('sha256');
  let size = 0;
  for await (const chunk of createReadStream(path)) {
    hash.update(chunk);
    size += chunk.length;
  }
  return { sha256: hash.digest('hex'), size };
}

async function verifySourceRelease(request, getJson) {
  const release = await getJson(`/repos/${SOURCE_REPO}/releases/${request.source.releaseId}`);
  validateSourceRelease(release, request);
}

async function makeDraft(getJson, env) {
  const body = [
    'Byte-exact mirror of the previously published AshenSpire art release.',
    '',
    `Original release: https://github.com/${SOURCE_REPO}/releases/tag/${SOURCE_TAG}`,
    `Original source tree commit recorded in the request: ${sourceCommit}`,
    'The original source repository history is not represented by this destination release tag.',
    'The attached zip, checksum, manifest, and credits files are copied byte-for-byte and verified by SHA-256.',
  ].join('\n');
  return getJson(`/repos/${TARGET_REPO}/releases`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      tag_name: TARGET_TAG,
      target_commitish: env.GITHUB_SHA,
      name: TARGET_TAG,
      body,
      draft: true,
      prerelease: false,
    }),
  });
}

async function downloadAndVerify(asset, stage, fetchImpl, env) {
  const response = await fetchImpl(asset.url, {
    headers: authHeaders({ accept: 'application/octet-stream' }, env),
    redirect: 'follow',
  });
  if (!response.ok || !response.body) throw new Error(`Source download failed for ${asset.name}: HTTP ${response.status}`);
  const path = resolve(stage, asset.name);
  await pipeline(Readable.fromWeb(response.body), createWriteStream(path, { flags: 'wx' }));
  const got = await hashFile(path);
  if (got.size !== asset.size || got.sha256 !== asset.sha256) {
    throw new Error(`Source bytes for ${asset.name} differ from frozen size/SHA-256`);
  }
  return path;
}

async function uploadOne(release, asset, path, getJson, fetchImpl, env) {
  const size = (await stat(path)).size;
  const uploadUrl = new URL(
    `https://uploads.github.com/repos/${TARGET_REPO}/releases/${release.id}/assets`,
  );
  uploadUrl.searchParams.set('name', asset.name);
  const response = await fetchImpl(uploadUrl, {
    method: 'POST',
    headers: authHeaders({
      accept: 'application/vnd.github+json',
      'content-type': 'application/octet-stream',
      'content-length': String(size),
    }, env),
    body: Readable.toWeb(createReadStream(path)),
    duplex: 'half',
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`Upload failed for ${asset.name}: HTTP ${response.status}: ${text.slice(0, 600)}`);
  const uploaded = JSON.parse(text);
  if (uploaded.name !== asset.name || uploaded.size !== asset.size ||
      uploaded.digest !== `sha256:${asset.sha256}`) {
    throw new Error(`GitHub did not verify the uploaded bytes for ${asset.name}`);
  }
  const remote = await getJson(`/repos/${TARGET_REPO}/releases/assets/${uploaded.id}`);
  if (remote.name !== asset.name || remote.size !== asset.size ||
      remote.digest !== `sha256:${asset.sha256}`) {
    throw new Error(`Remote verification failed for ${asset.name}`);
  }
}

async function listReleaseAssets(release, getJson) {
  const assets = await getJson(`/repos/${TARGET_REPO}/releases/${release.id}/assets?per_page=100`);
  return { ...release, assets };
}

async function publishDraft(release, getJson) {
  return getJson(`/repos/${TARGET_REPO}/releases/${release.id}`, {
    method: 'PATCH',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ draft: false }),
  });
}

export async function mirror(request, { env = process.env, fetchImpl = fetch } = {}) {
  requireEnvironment(env);
  assertAssetShape(request);
  // Tests can inject a closed fake HTTP transport; importing this module alone
  // cannot reach GitHub or create a release.
  const getJson = (path, init = {}) => apiJson(path, init, { env, fetchImpl });
  await verifySourceRelease(request, getJson);

  let release = await findReleaseByTag(TARGET_TAG, getJson);
  if (!release) {
    await verifyTagBeforeDraft({ currentSha: env.GITHUB_SHA, getJson });
    release = await makeDraft(getJson, env);
  }
  if (release.tag_name !== TARGET_TAG || release.prerelease) throw new Error('Destination tag is occupied by an incompatible release');
  await verifyDestinationTag({ release, currentSha: env.GITHUB_SHA, allowMissing: Boolean(release.draft), getJson });
  if (!release.draft) {
    const complete = await listReleaseAssets(release, getJson);
    validatePublishedRelease(complete, request.assets);
    await verifyDestinationTag({ release: complete, currentSha: env.GITHUB_SHA, getJson });
    console.log(`Already published and verified ${TARGET_TAG}; no destination assets were changed.`);
    return;
  }

  let draft = await listReleaseAssets(release, getJson);
  const present = inspectExistingAssets(draft, request.assets, false);
  const stage = await mkdtemp(resolve(env.RUNNER_TEMP || tmpdir(), 'ashenspire-v23-mirror-'));
  let verifiedAll = false;
  try {
    const zipHashes = new Map();
    for (const asset of request.assets) {
      if (asset.name.endsWith('.zip')) zipHashes.set(asset.name, asset.sha256);
      if (asset.name.endsWith('.zip.sha256')) {
        const zipName = asset.name.slice(0, -'.sha256'.length);
        if (!zipHashes.has(zipName)) throw new Error(`Missing preceding zip pin for ${asset.name}`);
      }
      if (present.has(asset.name)) continue;
      const path = await downloadAndVerify(asset, stage, fetchImpl, env);
      if (asset.name.endsWith('.zip.sha256')) {
        const zipName = asset.name.slice(0, -'.sha256'.length);
        verifyChecksumText(await readFile(path, 'utf8'), zipName, zipHashes.get(zipName));
      }
      await uploadOne(release, asset, path, getJson, fetchImpl, env);
      await rm(path, { force: true });
    }
    draft = await listReleaseAssets(release, getJson);
    inspectExistingAssets(draft, request.assets, true);
    if (draft.assets.length !== request.assets.length) throw new Error('Destination draft is incomplete after upload');
    const published = await publishDraft(release, getJson);
    if (published.draft) throw new Error('GitHub left the release in draft state');
    const finalRelease = await listReleaseAssets(published, getJson);
    validatePublishedRelease(finalRelease, request.assets);
    await verifyDestinationTag({ release: finalRelease, currentSha: env.GITHUB_SHA, getJson });
    verifiedAll = true;
    console.log(`Published and verified byte-exact mirror ${TARGET_TAG}.`);
  } finally {
    // The only removed path is this invocation's newly-created private staging directory.
    // Retain it on failure for diagnosis; runner teardown removes it afterward.
    if (verifiedAll) await rm(stage, { recursive: true, force: true });
  }
}

const requestPath = resolve(process.argv[2] || '.github/art-releases/ashenspire-v23.request.json');
const sourceCommit = 'b9daa888a83b0cf430fc606e983673778dec1a2d';
const invokedPath = process.argv[1] && pathToFileURL(resolve(process.argv[1])).href;
if (import.meta.url === invokedPath) {
  const request = JSON.parse(await readFile(requestPath, 'utf8'));
  await mirror(request);
}
