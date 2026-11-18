import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { verifyFrozenArchives, verifyMigrationSnapshot } from '../tools/ashenspire-release.mjs';
import { commonIndexText, CONTRACT, packRecords } from '../tools/display-snapshot.mjs';
import { packManifest } from '../tools/pack.mjs';
import { serialize } from '../tools/manifest.mjs';
import { writeZip } from '../tools/zip.mjs';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const hash = value => createHash('sha256').update(Buffer.isBuffer(value) || typeof value === 'string' ? value : JSON.stringify(value)).digest('hex');
const catalogPath = 'provenance/recipient-effects/v5/recipient-effects-catalog.json';
function fixture(dir) {
  const original = Buffer.from('unchanged original art');
  const row = path => ({ path, bytes: original.length, sha256: hash(original) });
  const manifest = { _: 'frozen test header', schema: 2, tiers: { high: 'high', light: 'light', common: 'common' }, count: 2, assets: {
    'assets/old.webp': { light: row('assets-mobile/old.webp'), high: row('assets/old.webp') },
    'assets-display/layered/old.webp': { common: row('assets-display/layered/old.webp') },
  } };
  const common = packRecords(manifest, 'common');
  const contract = { schema: 1, manifestSchema: 2, displayCount: 1, displayPayloadBytes: original.length,
    images: [{ id: 'assets-display/layered/old.webp', bytes: original.length, sha256: hash(original), width: 1, height: 1 }],
    base: { headerDigest: hash({ _: manifest._, schema: 2, tiers: manifest.tiers }), packs: {} },
    projected: { manifestCount: 2, commonCount: 1, commonRecordDigest: hash(common), commonPackIndexSha256: hash(commonIndexText(common)) },
    preservedZipSha256: {},
  };
  mkdirSync(join(dir, 'dist'), { recursive: true });
  for (const pack of ['high', 'light', 'common']) {
    const rows = packRecords(manifest, pack, id => !id.startsWith('assets-display/'));
    contract.base.packs[pack] = { count: Object.keys(rows).length, payloadBytes: Object.values(rows).reduce((n, r) => n + r.bytes, 0), recordDigest: hash(rows) };
  }
  for (const pack of ['high', 'light']) {
    const zip = join(dir, `dist/${pack === 'high' ? 'hd' : 'light'}-assets-v27.zip`);
    writeZip(zip, [{ name: 'art-manifest.json', data: Buffer.from(serialize(packManifest(manifest, pack))) },
      { name: manifest.assets['assets/old.webp'][pack].path, data: original }]);
    contract.preservedZipSha256[pack] = hash(readFileSync(zip));
  }
  const catalogBytes = readFileSync(join(root, catalogPath));
  mkdirSync(dirname(join(dir, catalogPath)), { recursive: true });
  writeFileSync(join(dir, catalogPath), catalogBytes);
  writeFileSync(join(dir, 'release.json'), JSON.stringify({ version: 27, preserveMigratedAssetBytes: true, reviewedRecipientEffects: { catalogSha256: hash(catalogBytes) } }));
  for (const entry of Object.values(JSON.parse(catalogBytes).entries)) {
    const record = {};
    for (const [pack, tier] of [['light', 'light'], ['high', 'hd']]) {
      const target = join(dir, entry.tiers[tier]); mkdirSync(dirname(target), { recursive: true });
      copyFileSync(join(root, entry.tiers[tier]), target);
      record[pack] = { path: pack === 'light' ? entry.asset.replace('assets/', 'assets-mobile/') : entry.asset,
        bytes: readFileSync(target).length, sha256: entry.sha256, width: 768, height: 256 };
    }
    manifest.assets[entry.asset] = record; manifest.count++;
  }
  mkdirSync(join(dir, 'migration')); writeFileSync(join(dir, CONTRACT), JSON.stringify(contract));
  const save = () => writeFileSync(join(dir, 'art-manifest.json'), JSON.stringify(manifest)); save();
  const pack = (oldBytes = original, extra = []) => {
    for (const tier of ['high', 'light']) {
      const entries = [{ name: 'art-manifest.json', data: Buffer.from(serialize(packManifest(manifest, tier))) }];
      for (const [id, entry] of Object.entries(manifest.assets)) if (entry[tier]) {
        entries.push({ name: entry[tier].path, data: id === 'assets/old.webp' ? oldBytes : readFileSync(join(dir, tier === 'high' ? 'hd' : 'light', id)) });
      }
      writeZip(join(dir, `dist/${tier === 'high' ? 'hd' : 'light'}-assets-v27.zip`), [...entries, ...extra]);
    }
  };
  pack(); return { manifest, save, pack, original };
}

test('reviewed runtime additions preserve original archive identity and reject old/additional byte changes', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'recipient-release-'));
  try {
    const f = fixture(dir);
    assert.equal(verifyMigrationSnapshot(dir), true);
    await verifyFrozenArchives(dir, 27);
    f.manifest.assets['assets/old.webp'].high.bytes++; f.save();
    assert.throws(() => verifyMigrationSnapshot(dir), /Existing high records/);
    f.manifest.assets['assets/old.webp'].high.bytes--; f.save();
    f.pack(Buffer.from('tampered old payload'));
    await assert.rejects(verifyFrozenArchives(dir, 27), /archive verification/);
    f.pack();
    f.manifest.assets['assets/recipient-effects/v5/unlisted.png'] = structuredClone(f.manifest.assets['assets/old.webp']); f.manifest.count++; f.save();
    assert.throws(() => verifyMigrationSnapshot(dir), /Existing high records/);
    delete f.manifest.assets['assets/recipient-effects/v5/unlisted.png']; f.manifest.count--; f.save();
    const file = join(dir, 'hd/assets/recipient-effects/v5/slash.png'), bytes = readFileSync(file);
    writeFileSync(file, Buffer.concat([bytes, Buffer.from('tampered')]));
    assert.throws(() => verifyMigrationSnapshot(dir), /Reviewed recipient bytes changed/);
    writeFileSync(file, bytes);
    f.pack(f.original, [{ name: 'assets/unlisted.png', data: Buffer.from('unlisted') }]);
    await assert.rejects(verifyFrozenArchives(dir, 27), /not in its manifest/);
    f.pack();
    const cat = readFileSync(join(dir, catalogPath)); writeFileSync(join(dir, catalogPath), Buffer.concat([cat, Buffer.from('\n')]));
    assert.throws(() => verifyMigrationSnapshot(dir), /catalog hash changed/);
    writeFileSync(join(dir, catalogPath), cat);
    const contract = JSON.parse(readFileSync(join(dir, CONTRACT))); contract.preservedZipSha256.high = 'f'.repeat(64);
    writeFileSync(join(dir, CONTRACT), JSON.stringify(contract));
    await assert.rejects(verifyFrozenArchives(dir, 27), /changed the original high ZIP bytes/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
