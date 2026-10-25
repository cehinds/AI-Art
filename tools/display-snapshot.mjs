// Initial v24 projection/verification. This module never reads image payloads
// or builds archives. Full-tree manifest and pack checks remain separate CI gates.
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { isDisplayArtId, serialize } from './manifest.mjs';
import { MIME } from './assetmime.mjs';
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const CONTRACT = 'migration/ashenspire-v24-display-contract.json';
const hash = (value) => createHash('sha256').update(typeof value === 'string' ? value : JSON.stringify(value)).digest('hex');
export function packRecords(manifest, pack, include = () => true) {
  return Object.fromEntries(Object.keys(manifest.assets).sort().filter((id) => manifest.assets[id][pack] && include(id))
    .map((id) => [id, manifest.assets[id][pack]]));
}
export function commonIndexText(records) {
  const ids = Object.keys(records).sort();
  return '{\n' + ids.map((id) => {
    const rec = records[id], ext = id.slice(id.lastIndexOf('.'));
    const mime = MIME[ext] || ({ '.json': 'application/json', '.txt': 'text/plain' })[ext];
    if (!mime) throw new Error('No common MIME: ' + id);
    return JSON.stringify(id) + ':' + JSON.stringify([rec.sha256, rec.bytes, mime]);
  }).join(',\n') + '\n}\n';
}
export function displayRecords(contract) {
  if (contract.schema !== 1 || contract.manifestSchema !== 2 || !Array.isArray(contract.images)
      || contract.images.length !== contract.displayCount) throw new Error('Invalid display contract/count');
  const result = {};
  for (const row of contract.images) {
    if (!isDisplayArtId(row.id) || !Number.isSafeInteger(row.bytes) || row.bytes < 1
        || !/^[0-9a-f]{64}$/.test(row.sha256)
        || ![row.width, row.height].every((v) => Number.isSafeInteger(v) && v > 0)) {
      throw new Error('Invalid display path/hash/length/dimensions: ' + row.id);
    }
    if (Object.hasOwn(result, row.id)) throw new Error('Duplicate display ID: ' + row.id);
    result[row.id] = { path: row.id, bytes: row.bytes, sha256: row.sha256 };
  }
  if (Object.values(result).reduce((n, row) => n + row.bytes, 0) !== contract.displayPayloadBytes) {
    throw new Error('Display payload total changed');
  }
  return result;
}
function verifyLegacy(manifest, contract) {
  if (manifest.schema !== 2) throw new Error('Manifest schema must remain 2');
  const header = { _: manifest._, schema: manifest.schema, tiers: manifest.tiers };
  if (hash(header) !== contract.base.headerDigest) throw new Error('Historical header changed');
  for (const pack of ['high', 'light', 'common']) {
    const rows = packRecords(manifest, pack, (id) => !id.startsWith('assets-display/'));
    const expected = contract.base.packs[pack];
    if (Object.keys(rows).length !== expected.count || hash(rows) !== expected.recordDigest
        || Object.values(rows).reduce((n, row) => n + row.bytes, 0) !== expected.payloadBytes) {
      throw new Error('Existing ' + pack + ' records changed');
    }
  }
}
export function projectDisplayManifest(baseline, contract) {
  verifyLegacy(baseline, contract);
  const rows = displayRecords(contract);
  const assets = { ...baseline.assets };
  for (const [id, common] of Object.entries(rows)) {
    if (assets[id] && JSON.stringify(assets[id]) !== JSON.stringify({ common })) throw new Error('Display collision: ' + id);
    assets[id] = { common };
  }
  const result = { ...baseline, count: Object.keys(assets).length, assets };
  verifyDisplayManifest(result, contract);
  return result;
}
export function verifyDisplayManifest(manifest, contract) {
  verifyLegacy(manifest, contract);
  const expected = displayRecords(contract);
  const actual = packRecords(manifest, 'common');
  const displayIds = Object.keys(manifest.assets).filter((id) => id.startsWith('assets-display/'));
  if (displayIds.length !== contract.displayCount) throw new Error('Display manifest count changed');
  for (const [id, row] of Object.entries(expected)) {
    if (JSON.stringify(manifest.assets[id]) !== JSON.stringify({ common: row })) throw new Error('Display record mismatch: ' + id);
  }
  if (manifest.count !== contract.projected.manifestCount || Object.keys(manifest.assets).length !== manifest.count
      || Object.keys(actual).length !== contract.projected.commonCount
      || hash(actual) !== contract.projected.commonRecordDigest
      || hash(commonIndexText(actual)) !== contract.projected.commonPackIndexSha256) {
    throw new Error('Projected manifest/common index changed');
  }
  return true;
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const contract = JSON.parse(readFileSync(resolve(ROOT, CONTRACT), 'utf8'));
  const path = resolve(ROOT, 'art-manifest.json');
  const manifest = JSON.parse(readFileSync(path, 'utf8'));
  if (process.argv.includes('--project')) {
    writeFileSync(path, serialize(projectDisplayManifest(manifest, contract)));
    console.log('Projected metadata only: 675 display records; no assets or archives read/written.');
  } else if (process.argv.includes('--check')) {
    verifyDisplayManifest(manifest, contract);
    console.log('v24 contract: 8169 IDs; 821 common; normalized common index ' + contract.projected.commonPackIndexSha256);
  } else throw new Error('Usage: display-snapshot.mjs --project | --check');
}
