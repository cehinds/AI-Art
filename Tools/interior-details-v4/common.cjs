'use strict';
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
let sharp;try{sharp=require('sharp')}catch{sharp=require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')}
const root=path.resolve(__dirname,'../..'),out=path.join(root,'Assets/Art/Production/InteriorDetailsV4'),review=path.join(root,'Review/interior-details-v4');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const json=x=>JSON.stringify(x,null,2)+'\n';
async function save(file,data){await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,data)}
function canonical(m){for(const [d,a,b] of [[16,1,2],[32,2,4],[64,4,8],[128,8,1]])if(!(m&a)||!(m&b))m&=~d;return m}
const masks=[...new Set(Array.from({length:256},(_,i)=>canonical(i)))].sort((a,b)=>a-b);
module.exports={fs,path,sharp,root,out,review,hash,json,save,canonical,masks};
