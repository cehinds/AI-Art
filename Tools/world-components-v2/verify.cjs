'use strict';
// Independent gate reads emitted PNGs; it does not call exporter or its port builder.
const {fs,path,sharp,root,out,review,hash,json,save}=require('./common.cjs');
const assert=(x,m)=>{if(!x)throw Error(m)};
const dirs={E:[1,0],S:[0,1]};
function boundary(raw,side,depth=4){let bytes=[];for(let d=0;d<depth;d++)for(let t=0;t<32;t++){let x=side==='E'?31-d:side==='W'?d:t,y=side==='S'?31-d:side==='N'?d:t;for(let c=0;c<4;c++)bytes.push(raw[(y*32+x)*4+c])}return Buffer.from(bytes)}
function compare(a,b,side){return boundary(a,side).equals(boundary(b,side==='E'?'W':'N'))}
function idAt(grid,x,y){if(!grid[y]?.[x])return 'ocean';let m=0;for(const [dx,dy,b] of [[0,-1,1],[1,0,2],[0,1,4],[-1,0,8],[1,-1,16],[1,1,32],[-1,1,64],[-1,-1,128]])if(grid[y+dy]?.[x+dx])m|=b;if(!(m&1)||!(m&2))m&=~16;if(!(m&2)||!(m&4))m&=~32;if(!(m&4)||!(m&8))m&=~64;if(!(m&8)||!(m&1))m&=~128;return 'coast-'+m}
async function main(){const manifest=JSON.parse(await fs.readFile(path.join(out,'manifest.json'))),raws=new Map();assert(manifest.assets.filter(a=>a.family==='coast').length===47,'Missing blob masks');assert(manifest.assets.filter(a=>a.family==='river').length===16,'Missing river masks');assert(hash(await fs.readFile(path.join(root,manifest.source.file)))===manifest.source.sha256,'Master hash changed');for(const a of manifest.assets){const png=await fs.readFile(path.join(root,a.file));assert(hash(png)===a.sha256,'File hash changed: '+a.id);const {data,info}=await sharp(png).ensureAlpha().raw().toBuffer({resolveWithObject:true});assert(info.width===32&&info.height===32,'Wrong native dimensions');assert(data.every((v,i)=>i%4!==3||v===255),'Unexpected alpha');raws.set(a.id,data)}
 for(const r of [...manifest.sourceRecords,manifest.riverSource,manifest.generationRecord])assert(hash(await fs.readFile(path.join(root,r.file)))===r.sha256,'Provenance file changed: '+r.file);let checks=0;const pairs=new Map();
 // Every possible 4x3 local occupancy patch: derives compatibility from world cells,
 // rather than trusting declared ports or skipping pairs with different signatures.
 for(let bits=0;bits<4096;bits++){const g=Array.from({length:3},(_,y)=>Array.from({length:4},(_,x)=>!!(bits&(1<<(y*4+x)))));const a=idAt(g,1,1),b=idAt(g,2,1);pairs.set(a+'|'+b+'|E',[a,b,'E']);const gt=Array.from({length:4},(_,y)=>Array.from({length:3},(_,x)=>g[x][y]));const c=idAt(gt,1,1),d=idAt(gt,1,2);pairs.set(c+'|'+d+'|S',[c,d,'S'])}
 for(const [a,b,s] of pairs.values()){assert(compare(raws.get(a),raws.get(b),s),'Occupancy-compatible four-pixel RGBA band mismatch: '+[a,b,s]);checks++}
 for(let a=0;a<16;a++)for(let b=0;b<16;b++)for(const [s,ab,bb] of [['E',2,8],['S',4,1]])if(!!(a&ab)===!!(b&bb)){assert(compare(raws.get('river-'+a),raws.get('river-'+b),s),'River compatible-band mismatch '+[a,b,s]);checks++}
 // Mutation gate exercises actual pixel comparison independently of file hashes.
 const clean=raws.get('ocean'),mutant=Buffer.from(clean);mutant[(10*32+0)*4]^=1;assert(!compare(clean,mutant,'E'),'Mutation gate failed to reject seam alteration');
 const proofs=JSON.parse(await fs.readFile(path.join(review,'proof-maps.json')));let proofChecks=0;for(const proof of proofs)for(let y=0;y<proof.cells.length;y++)for(let x=0;x<proof.cells[y].length;x++)for(const [s,[dx,dy]] of Object.entries(dirs)){const b=proof.cells[y+dy]?.[x+dx];if(b){assert(compare(raws.get(proof.cells[y][x]),raws.get(b),s),'Proof map seam mismatch: '+[proof.id,x,y,s]);proofChecks++}}
 const result={status:'PASS',nativeAssets:raws.size,coastUniqueCompatiblePairs:pairs.size,compatibleFourPixelRgbaBandChecks:checks,proofAdjacencies:proofChecks,mutationRejected:true,limits:'Exact source-fragment boundary continuity does not establish visual approval, native gameplay readability, runtime integration, collision or release readiness.'};await save(path.join(review,'verification.json'),json(result));console.log(json(result));}
main().catch(e=>{console.error(e.message);process.exitCode=1});
