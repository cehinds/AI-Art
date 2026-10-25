#!/usr/bin/env node
// Build additive persistent stance high-tier sprites from reviewed transparent PNG masters.
// Usage: node build-stance-assets.cjs [--check]
// Requires cwebp from libwebp on PATH (or CWEBP absolute path).
const fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process');
const here=__dirname,repo=path.resolve(here,'../..'),source=path.join(here,'source-overrides');
const catalog=JSON.parse(fs.readFileSync(path.join(here,'catalog.json'),'utf8'));
const check=process.argv.includes('--check');
const cwebp=process.env.CWEBP||'cwebp';
const run=(args)=>{const r=spawnSync(cwebp,args,{encoding:'utf8'});if(r.error||r.status!==0)throw new Error(`cwebp failed: ${r.error||r.stderr||r.status}`);};
if(!check){
 for(const item of catalog.items){
  const src=path.join(source,item.id,`${item.pose}.png`);
  const dest=path.join(repo,'hd','assets','enemy-poses','expansion',item.id,`${item.pose}.webp`);
  if(!fs.existsSync(src))throw new Error(`Missing source master: ${src}`);
  fs.mkdirSync(path.dirname(dest),{recursive:true});
  run(['-quiet','-m','6','-q','90','-alpha_q','100','-alpha_filter','best',src,'-o',dest]);
 }
}
const missing=[];
for(const item of catalog.items){
 const src=path.join(source,item.id,`${item.pose}.png`);
 const dest=path.join(repo,'hd','assets','enemy-poses','expansion',item.id,`${item.pose}.webp`);
 if(!fs.existsSync(src)||!fs.existsSync(dest))missing.push(`${item.id}/${item.pose}`);
}
if(missing.length)throw new Error('Missing source/export: '+missing.join(', '));
console.log(JSON.stringify({poses:catalog.items.length,check,encoder:cwebp,quality:90,alphaQuality:100,effort:6}));
