import { createRequire } from 'node:module';
import { readdirSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
const sharp = createRequire(import.meta.url)(process.env.SHARP_MODULE || 'sharp');
const root = fileURLToPath(new URL('../../../', import.meta.url));
const source = fileURLToPath(new URL('./masters/', import.meta.url));
for (const kind of ['covers', 'symbols']) {
  const dest = resolve(root, 'hd/assets/shop/painted', kind);
  mkdirSync(dest, {recursive:true});
  for (const file of readdirSync(resolve(source, kind)).filter((name)=>name.endsWith('.png'))) {
    await sharp(resolve(source,kind,file)).resize(640,640,{fit:'contain',background:'#00000000'})
      .webp({quality:94,alphaQuality:100}).toFile(resolve(dest,file.replace(/\.png$/,'.webp')));
  }
}
