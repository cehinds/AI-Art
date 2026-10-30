// Register byte-identical approved components without rewriting other assets.
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {commonRecord,serialize} from './manifest.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const source=JSON.parse(readFileSync(root+'provenance/AshenSpire/reviewed-card-cutouts.json','utf8'));
const manifest=JSON.parse(readFileSync(root+'art-manifest.json','utf8'));
for(const asset of Object.values(source.assets)){
  if(!/^assets-display\/card-cutouts\/[A-Za-z0-9.]+\.png$/.test(asset.path))throw Error('Invalid component path');
  const actual=commonRecord(root+'common/'+asset.path,asset.path);
  if(actual.sha256!==asset.sha256 || actual.bytes!==asset.bytes)throw Error(`Source mismatch: ${asset.id}`);
  if(process.argv.includes('--write'))manifest.assets[asset.path]={common:actual};
  else if(JSON.stringify(manifest.assets[asset.path])!==JSON.stringify({common:actual}))throw Error(`Unregistered component: ${asset.id}`);
}
manifest.count=Object.keys(manifest.assets).length;
if(process.argv.includes('--write'))writeFileSync(root+'art-manifest.json',serialize(manifest));
console.log(`Verified ${Object.keys(source.assets).length} approved component PNGs`);
