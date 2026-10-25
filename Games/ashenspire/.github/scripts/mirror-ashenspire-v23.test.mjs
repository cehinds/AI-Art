import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, readdir, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  SOURCE_REPO, SOURCE_TAG, TARGET_REPO, TARGET_TAG, TARGET_BRANCH,
  assertAssetShape, findReleaseByTag, inspectExistingAssets, mirror,
  resolveGitTagObject, validatePublishedRelease, validateSourceRelease,
  verifyAssetBytes, verifyChecksumText, verifyDestinationTag, verifyTagBeforeDraft,
} from './mirror-ashenspire-v23.mjs';

const A = 'a'.repeat(40);
const B = 'b'.repeat(40);
const C = 'c'.repeat(40);
const hashBytes = (bytes) => createHash('sha256').update(bytes).digest('hex');
const digest = (n) => String(n).repeat(64);
const request = {
  schema: 1,
  source: { repository: SOURCE_REPO, releaseId: 10, tag: SOURCE_TAG, targetCommit: A },
  destination: { repository: TARGET_REPO, branch: TARGET_BRANCH, tag: TARGET_TAG },
  totalBytes: 4,
  assets: [
    { id: 1, name: 'hd-assets-v23.zip', size: 1, sha256: digest(1), url: `https://api.github.com/repos/${SOURCE_REPO}/releases/assets/1` },
    { id: 2, name: 'hd-assets-v23.zip.sha256', size: 1, sha256: digest(2), url: `https://api.github.com/repos/${SOURCE_REPO}/releases/assets/2` },
    { id: 3, name: 'light-assets-v23.zip', size: 1, sha256: digest(3), url: `https://api.github.com/repos/${SOURCE_REPO}/releases/assets/3` },
    { id: 4, name: 'light-assets-v23.zip.sha256', size: 1, sha256: digest(4), url: `https://api.github.com/repos/${SOURCE_REPO}/releases/assets/4` },
    { id: 5, name: 'common-assets-v23.zip', size: 0, sha256: digest(5), url: `https://api.github.com/repos/${SOURCE_REPO}/releases/assets/5` },
    { id: 6, name: 'common-assets-v23.zip.sha256', size: 0, sha256: digest(6), url: `https://api.github.com/repos/${SOURCE_REPO}/releases/assets/6` },
    { id: 7, name: 'art-manifest.json', size: 0, sha256: digest(7), url: `https://api.github.com/repos/${SOURCE_REPO}/releases/assets/7` },
    { id: 8, name: 'CREDITS.md', size: 0, sha256: digest(8), url: `https://api.github.com/repos/${SOURCE_REPO}/releases/assets/8` },
  ],
};
const releaseAssets = request.assets.map((asset) => ({
  id: asset.id + 100,
  name: asset.name,
  size: asset.size,
  digest: `sha256:${asset.sha256}`,
}));

test('the frozen request has the exact host, tag, names, IDs, and byte total', () => {
  assert.doesNotThrow(() => assertAssetShape(request));
  assert.throws(() => assertAssetShape({ ...request, totalBytes: 5 }), /total/);
});

test('source release metadata must match all expected assets exactly', () => {
  const source = {
    id: request.source.releaseId,
    tag_name: SOURCE_TAG,
    target_commitish: A,
    draft: false,
    prerelease: false,
    assets: request.assets.map((asset) => ({
      id: asset.id, name: asset.name, size: asset.size, digest: `sha256:${asset.sha256}`,
    })),
  };
  assert.equal(validateSourceRelease(source, request), true);
  assert.throws(() => validateSourceRelease({ ...source, assets: source.assets.slice(1) }, request), /asset count/);
  assert.throws(() => validateSourceRelease({ ...source, assets: source.assets.map((a, i) => i ? a : { ...a, name: source.assets[1].name }) }, request), /duplicate/);
});

test('a rerun finds and resumes a matching draft omitted by release-by-tag lookup', async () => {
  const draft = { id: 22, tag_name: TARGET_TAG, draft: true, prerelease: false, target_commitish: A, assets: [] };
  const calls = [];
  const getJson = async (path) => {
    calls.push(path);
    if (path.includes('/releases/tags/')) throw Object.assign(new Error('not found'), { status: 404 });
    if (path.endsWith('page=1')) return [draft];
    throw new Error(`Unexpected lookup: ${path}`);
  };
  assert.equal(await findReleaseByTag(TARGET_TAG, getJson), draft);
  assert.equal(calls.length, 2);
});

test('duplicate destination releases with the same tag are refused', async () => {
  const first = { id: 1, tag_name: TARGET_TAG };
  const second = { id: 2, tag_name: TARGET_TAG };
  const getJson = async (path) => {
    if (path.includes('/releases/tags/')) return first;
    return [second];
  };
  await assert.rejects(findReleaseByTag(TARGET_TAG, getJson), /Multiple destination releases/);
});

test('an annotated destination tag resolves to the release commit and is checked against branch ancestry', async () => {
  const calls = [];
  const getJson = async (path) => {
    calls.push(path);
    if (path.includes('/compare/')) return { status: 'identical' };
    if (path.includes('/git/ref/tags/')) return { object: { type: 'tag', sha: B } };
    if (path.endsWith(`/git/tags/${B}`)) return { object: { type: 'tag', sha: C } };
    if (path.endsWith(`/git/tags/${C}`)) return { object: { type: 'commit', sha: A } };
    throw new Error(`Unexpected lookup: ${path}`);
  };
  assert.deepEqual(await verifyDestinationTag({
    release: { target_commitish: A }, currentSha: A, getJson,
  }), { present: true, commitSha: A });
  assert.equal(calls.filter((path) => path.includes('/git/tags/')).length, 2);
});

test('a pre-existing foreign or otherwise wrong tag target fails even when release metadata claims the expected target', async () => {
  const getJson = async (path) => {
    if (path.includes('/compare/')) return { status: 'ahead' };
    if (path.includes('/git/ref/tags/')) return { object: { type: 'commit', sha: B } };
    throw new Error(`Unexpected lookup: ${path}`);
  };
  await assert.rejects(verifyDestinationTag({
    release: { target_commitish: A }, currentSha: A, getJson,
  }), /tag commit differs/);
});

test('draft with no published Git tag may resume only when its target is in the AshenSpire branch', async () => {
  const getJson = async (path) => {
    if (path.includes('/compare/')) return { status: 'ahead' };
    if (path.includes('/git/ref/tags/')) throw Object.assign(new Error('no ref yet'), { status: 404 });
    throw new Error(`Unexpected lookup: ${path}`);
  };
  assert.deepEqual(await verifyDestinationTag({
    release: { target_commitish: A }, currentSha: B, allowMissing: true, getJson,
  }), { present: false, commitSha: null });
  const diverged = async (path) => {
    if (path.includes('/compare/')) return { status: 'diverged' };
    if (path.includes('/git/ref/tags/')) throw Object.assign(new Error('no ref yet'), { status: 404 });
    throw new Error(`Unexpected lookup: ${path}`);
  };
  await assert.rejects(verifyDestinationTag({
    release: { target_commitish: C }, currentSha: B, allowMissing: true, getJson: diverged,
  }), /not an ancestor/);
});

test('a destination tag without a release is checked before draft creation', async () => {
  const getJson = async (path) => {
    if (path.includes('/git/ref/tags/')) return { object: { type: 'commit', sha: B } };
    throw new Error('Unexpected lookup: ' + path);
  };
  await assert.rejects(verifyTagBeforeDraft({ currentSha: A, getJson }), /without a release/);
});

test('published matching release is accepted without any asset mutation', () => {
  const published = {
    tag_name: TARGET_TAG,
    draft: false,
    prerelease: false,
    target_commitish: A,
    assets: releaseAssets,
  };
  assert.equal(validatePublishedRelease(published, request.assets), true);
});

test('asset digest mismatches and unexpected assets fail closed', () => {
  assert.throws(() => inspectExistingAssets({
    assets: [{ ...releaseAssets[0], digest: `sha256:${digest(9)}` }],
  }, request.assets, false), /differs in size or SHA-256/);
  assert.throws(() => inspectExistingAssets({
    assets: [{ name: 'foreign-game.zip', size: 0, digest: `sha256:${digest(9)}` }],
  }, request.assets, false), /unexpected asset/);
  assert.throws(() => validatePublishedRelease({
    tag_name: TARGET_TAG, draft: false, prerelease: false, target_commitish: A,
    assets: releaseAssets.slice(0, -1),
  }, request.assets), /incomplete/);
});

test('sidecar content must name the original zip basename and frozen zip hash', () => {
  assert.equal(verifyChecksumText(`${digest(1)}  hd-assets-v23.zip\n`, 'hd-assets-v23.zip', digest(1)), true);
  assert.throws(() => verifyChecksumText(`${digest(2)}  hd-assets-v23.zip\n`, 'hd-assets-v23.zip', digest(1)), /checksum sidecar/);
  assert.throws(() => verifyChecksumText(`${digest(1)}  other.zip\n`, 'hd-assets-v23.zip', digest(1)), /checksum sidecar/);
});

test('downloaded bytes are rejected when their size or SHA differs from the frozen request', () => {
  const bytes = Buffer.from('x');
  assert.deepEqual(verifyAssetBytes({ name: 'one', size: 1, sha256: '2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881' }, bytes), {
    size: 1, sha256: '2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881',
  });
  assert.throws(() => verifyAssetBytes({ name: 'one', size: 2, sha256: '2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881' }, bytes), /size\/SHA-256/);
});

function operationalFixture() {
  const zipRows = [
    ['hd-assets-v23.zip', Buffer.from('high pack fixture')],
    ['light-assets-v23.zip', Buffer.from('light pack fixture')],
    ['common-assets-v23.zip', Buffer.from('common pack fixture')],
  ];
  const bytesByName = new Map();
  for (const [name, bytes] of zipRows) {
    bytesByName.set(name, bytes);
    bytesByName.set(name + '.sha256', Buffer.from(hashBytes(bytes) + '  ' + name + '\n'));
  }
  bytesByName.set('art-manifest.json', Buffer.from('{"schema":2,"assets":{}}\n'));
  bytesByName.set('CREDITS.md', Buffer.from('Original credits and license records.\n'));
  const assets = [...bytesByName.entries()].map(([name, bytes], i) => ({
    id: i + 1,
    name,
    size: bytes.length,
    sha256: hashBytes(bytes),
    url: 'https://api.github.com/repos/' + SOURCE_REPO + '/releases/assets/' + (i + 1),
  }));
  const frozen = {
    schema: 1,
    source: { repository: SOURCE_REPO, releaseId: 10, tag: SOURCE_TAG, targetCommit: A },
    destination: { repository: TARGET_REPO, branch: TARGET_BRANCH, tag: TARGET_TAG },
    totalBytes: assets.reduce((n, asset) => n + asset.size, 0),
    assets,
  };
  const sourceRelease = {
    id: frozen.source.releaseId,
    tag_name: SOURCE_TAG,
    target_commitish: A,
    draft: false,
    prerelease: false,
    assets: assets.map((asset) => ({
      id: asset.id,
      name: asset.name,
      size: asset.size,
      digest: 'sha256:' + asset.sha256,
    })),
  };
  return { request: frozen, sourceRelease, bytesByName };
}

function jsonResponse(value, status = 200) {
  return new Response(value === null ? '' : JSON.stringify(value), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

function mockGitHub({ request: frozen, sourceRelease, bytesByName, mode, eventSha, calls, uploaded }) {
  let release = {
    id: 50,
    tag_name: TARGET_TAG,
    target_commitish: eventSha,
    draft: mode === 'draft',
    prerelease: false,
    assets: mode === 'published' ? frozen.assets.map((asset, i) => ({
      id: 100 + i,
      name: asset.name,
      size: asset.size,
      digest: 'sha256:' + asset.sha256,
    })) : [],
  };
  let nextUploadId = 100;
  return async (input, init = {}) => {
    const url = new URL(String(input));
    const method = init.method || 'GET';
    calls.push({ host: url.host, path: url.pathname, method });
    if (url.hostname === 'uploads.github.com') {
      assert.equal(method, 'POST');
      const name = url.searchParams.get('name');
      const body = Buffer.from(await new Response(init.body).arrayBuffer());
      const expected = frozen.assets.find((asset) => asset.name === name);
      assert.ok(expected, 'unexpected upload ' + name);
      assert.equal(body.length, expected.size);
      assert.equal(hashBytes(body), expected.sha256);
      const asset = { id: nextUploadId++, name, size: body.length, digest: 'sha256:' + hashBytes(body) };
      uploaded.set(name, asset);
      release.assets = [...uploaded.values()];
      return jsonResponse(asset);
    }
    if (url.hostname === 'api.github.com') {
      if (url.pathname === '/repos/' + SOURCE_REPO + '/releases/' + frozen.source.releaseId && method === 'GET') {
        return jsonResponse(sourceRelease);
      }
      if (url.pathname === '/repos/' + TARGET_REPO + '/releases/tags/' + TARGET_TAG && method === 'GET') {
        return mode === 'published' ? jsonResponse(release) : jsonResponse({ message: 'Not Found' }, 404);
      }
      if (url.pathname === '/repos/' + TARGET_REPO + '/releases' && method === 'GET') {
        return jsonResponse(mode === 'published' ? [release] : []);
      }
      if (url.pathname === '/repos/' + TARGET_REPO + '/releases' && method === 'POST') {
        assert.equal(mode, 'draft');
        assert.equal(JSON.parse(init.body).target_commitish, eventSha);
        return jsonResponse(release);
      }
      if (url.pathname === '/repos/' + TARGET_REPO + '/releases/' + release.id + '/assets' && method === 'GET') {
        return jsonResponse(release.assets);
      }
      if (url.pathname === '/repos/' + TARGET_REPO + '/releases/' + release.id && method === 'PATCH') {
        assert.equal(mode, 'draft');
        assert.deepEqual(JSON.parse(init.body), { draft: false });
        release = { ...release, draft: false };
        return jsonResponse(release);
      }
      if (url.pathname.startsWith('/repos/' + TARGET_REPO + '/releases/assets/') && method === 'GET') {
        const id = Number(url.pathname.split('/').at(-1));
        const asset = [...uploaded.values()].find((item) => item.id === id);
        return asset ? jsonResponse(asset) : jsonResponse({ message: 'Not Found' }, 404);
      }
      if (url.pathname === '/repos/' + TARGET_REPO + '/compare/' + eventSha + '...' + eventSha && method === 'GET') {
        return jsonResponse({ status: 'identical' });
      }
      if (url.pathname === '/repos/' + TARGET_REPO + '/git/ref/tags/' + TARGET_TAG && method === 'GET') {
        if (mode === 'wrong-tag-no-release') {
          return jsonResponse({ object: { type: 'commit', sha: B } });
        }
        return !release.draft
          ? jsonResponse({ object: { type: 'commit', sha: eventSha } })
          : jsonResponse({ message: 'Not Found' }, 404);
      }
      if (url.pathname.startsWith('/repos/' + SOURCE_REPO + '/releases/assets/') && method === 'GET') {
        const id = Number(url.pathname.split('/').at(-1));
        const asset = frozen.assets.find((item) => item.id === id);
        const bytes = asset && bytesByName.get(asset.name);
        return bytes ? new Response(bytes) : jsonResponse({ message: 'Not Found' }, 404);
      }
    }
    throw new Error('Unexpected fake HTTP request: ' + method + ' ' + url.href);
  };
}

test('operational entrypoint accepts a published matching release without writes', async () => {
  const fixture = operationalFixture();
  const calls = [];
  const uploaded = new Map();
  const eventSha = 'd'.repeat(40);
  const fetchImpl = mockGitHub({ ...fixture, mode: 'published', eventSha, calls, uploaded });
  const env = {
    GITHUB_TOKEN: 'test-token',
    GITHUB_REPOSITORY: TARGET_REPO,
    GITHUB_REF: 'refs/heads/' + TARGET_BRANCH,
    GITHUB_SHA: eventSha,
    RUNNER_TEMP: tmpdir(),
  };
  await mirror(fixture.request, { env, fetchImpl });
  assert.ok(calls.length > 0);
  assert.ok(calls.every((call) => call.method === 'GET'), 'published replay performs read-only requests only');
  assert.equal(calls.some((call) => call.host === 'uploads.github.com'), false);
  assert.equal(uploaded.size, 0);
});

test('operational entrypoint refuses a foreign tag before creating any release or uploading assets', async () => {
  const fixture = operationalFixture();
  const calls = [];
  const uploaded = new Map();
  const eventSha = 'f'.repeat(40);
  const fetchImpl = mockGitHub({ ...fixture, mode: 'wrong-tag-no-release', eventSha, calls, uploaded });
  const env = {
    GITHUB_TOKEN: 'test-token',
    GITHUB_REPOSITORY: TARGET_REPO,
    GITHUB_REF: 'refs/heads/' + TARGET_BRANCH,
    GITHUB_SHA: eventSha,
    RUNNER_TEMP: tmpdir(),
  };
  await assert.rejects(mirror(fixture.request, { env, fetchImpl }), /without a release/);
  assert.ok(calls.every((call) => call.method === 'GET'), 'conflict handling performs reads only');
  assert.equal(calls.some((call) => call.host === 'uploads.github.com'), false);
  assert.equal(uploaded.size, 0);
});

test('operational entrypoint downloads, verifies, uploads, and then publishes a complete draft', async () => {
  const fixture = operationalFixture();
  const calls = [];
  const uploaded = new Map();
  const eventSha = 'e'.repeat(40);
  const tempRoot = await mkdtemp(join(tmpdir(), 'mirror-operational-test-'));
  try {
    const fetchImpl = mockGitHub({ ...fixture, mode: 'draft', eventSha, calls, uploaded });
    const env = {
      GITHUB_TOKEN: 'test-token',
      GITHUB_REPOSITORY: TARGET_REPO,
      GITHUB_REF: 'refs/heads/' + TARGET_BRANCH,
      GITHUB_SHA: eventSha,
      RUNNER_TEMP: tempRoot,
    };
    await mirror(fixture.request, { env, fetchImpl });
    assert.equal(uploaded.size, fixture.request.assets.length);
    assert.equal(calls.filter((call) => call.method === 'POST' && call.host === 'api.github.com').length, 1, 'one draft release is created');
    assert.equal(calls.filter((call) => call.method === 'PATCH' && call.host === 'api.github.com').length, 1, 'the draft is published once');
    assert.equal(calls.filter((call) => call.host === 'uploads.github.com').length, fixture.request.assets.length);
    assert.equal(calls.filter((call) => call.path.startsWith('/repos/' + TARGET_REPO + '/releases/assets/')).length, fixture.request.assets.length, 'each uploaded asset is remotely rechecked');
    assert.deepEqual(await readdir(tempRoot), [], 'only the owned staging directory is removed after verification');
  } finally {
    await rm(tempRoot, { recursive: true, force: true });
  }
});
