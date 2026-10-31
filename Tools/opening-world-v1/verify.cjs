'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {sharp}=require('../remaster-expansion/common.cjs');
const root=path.resolve(__dirname,'../..'),dir='Assets/Art/Production/OpeningWorldV1';
const manifest=JSON.parse(fs.readFileSync(path.join(root,dir,'manifest.json'),'utf8'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const expected=['conifer','altair-town','fynn-town','grass'];
 if(JSON.stringify(manifest.assets.map(a=>a.id))!==JSON.stringify(expected))throw Error('Unexpected asset IDs/order');
 for(const a of manifest.assets){
  const source=fs.readFileSync(path.join(root,a.source)),output=fs.readFileSync(path.join(root,a.file));
  if(hash(source)!==a.sourceSha256||hash(output)!==a.sha256)throw Error(a.id+' hash mismatch');
  const {data,info}=await sharp(output).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  if(info.width!==a.width||info.height!==a.height)throw Error(a.id+' wrong dimensions');
  let solid=0,clear=0;
  for(let p=3;p<data.length;p+=4){if(data[p]>=128)solid++;if(data[p]===0)clear++;if(a.opaque&&data[p]!==255)throw Error(a.id+' not opaque');}
  if(!solid||(!a.opaque&&!clear))throw Error(a.id+' silhouette alpha invalid');
  const rebuilt=await sharp(source).extract(a.crop).resize(a.width,a.height,{fit:a.fit,position:'south',kernel:'nearest',background:{r:0,g:0,b:0,alpha:0}}).ensureAlpha().png().toBuffer();
  if(!output.equals(rebuilt))throw Error(a.id+' export not reproducible');
 }
 const actual=fs.readdirSync(path.join(root,dir)).filter(n=>n.endsWith('.png')).sort();
 if(JSON.stringify(actual)!==JSON.stringify(expected.map(x=>x+'.png').sort()))throw Error('Unexpected PNG inventory');
 console.log('PASS: 4 sources, 4 PNG hashes/dimensions/alpha and exact deterministic export reproduction. Integration deferred.');
})().catch(e=>{console.error(e);process.exitCode=1;});

