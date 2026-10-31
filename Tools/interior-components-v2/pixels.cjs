'use strict';
const C=require('./common.cjs'),{sharp,fs,path,root,hash}=C;
const pixel=(raw,w,x,y)=>raw.subarray((y*w+x)*4,(y*w+x+1)*4);
const transparent=Buffer.from([0,0,0,0]);
async function raw(bytes,w,h,crop){const image=sharp(bytes);if(crop)image.extract(crop);return image.resize(w,h,{fit:'fill',kernel:'nearest'}).ensureAlpha().raw().toBuffer()}
function periodic(input,w=32,h=32,depth=4){const r=Buffer.from(input);for(let y=0;y<h;y++)for(let x=0;x<w;x++){if(x<depth||x>=w-depth||y<depth||y>=h-depth){const xx=x>=w-depth?w-1-x:x,yy=y>=h-depth?h-1-y:y;pixel(input,w,xx,yy).copy(r,(y*w+x)*4)}}return r}
function profile(raw,w,h,side,depth=4){const n=side==='E'||side==='W'?h:w,b=Buffer.alloc(n*depth*4);for(let d=0;d<depth;d++)for(let t=0;t<n;t++){const x=side==='W'?d:side==='E'?w-1-d:t,y=side==='N'?d:side==='S'?h-1-d:t;pixel(raw,w,x,y).copy(b,(d*n+t)*4)}return b}
function applyProfile(raw,w,h,side,p,depth=4){const n=side==='E'||side==='W'?h:w;for(let d=0;d<depth;d++)for(let t=0;t<n;t++){const x=side==='W'?d:side==='E'?w-1-d:t,y=side==='N'?d:side==='S'?h-1-d:t;p.subarray((d*n+t)*4,(d*n+t+1)*4).copy(raw,(y*w+x)*4)}}
function corners(raw,w,h,source,solid,depth=4){for(const [cx,cy,which] of [[0,0,0],[w-depth,0,1],[w-depth,h-depth,2],[0,h-depth,3]])for(let y=0;y<depth;y++)for(let x=0;x<depth;x++){const xx=cx?depth-1-x:x,yy=cy?depth-1-y:y;(solid[which]?pixel(source,depth,xx,yy):transparent).copy(raw,((cy+y)*w+cx+x)*4)}}
async function dependency(file){const candidates=[path.join(root,file),path.join(process.env.ART_DEPENDENCY_ROOT||'C:/repos/AI-Art-FF2',file)];for(const p of candidates)try{return {bytes:await fs.readFile(p),file,sha256:hash(await fs.readFile(p))}}catch(e){if(e.code!=='ENOENT')throw e}throw Error('Missing unchanged dependency '+file+'; set ART_DEPENDENCY_ROOT to art repository')}
module.exports={...C,pixel,transparent,raw,periodic,profile,applyProfile,corners,dependency};
