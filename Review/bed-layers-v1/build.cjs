const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const crypto = require('node:crypto');

const root = __dirname;
const bedPath = path.join(root, 'sources', 'white-sickbed.png');
const actorPath = path.join(root, 'sources', 'firion-down-02.png');
const bubblePath = path.join(root, 'sources', 'books-jug-bubble-master.png');

function crc32(buf) {
  let c = 0xffffffff;
  for (const byte of buf) {
    c ^= byte;
    for (let k = 0; k < 8; k++) c = (c >>> 1) ^ ((c & 1) ? 0xedb88320 : 0);
  }
  return (c ^ 0xffffffff) >>> 0;
}
function readPng(file) {
  const b = fs.readFileSync(file);
  if (b.toString('hex', 0, 8) !== '89504e470d0a1a0a') throw new Error(`Not PNG: ${file}`);
  let p = 8, width, height, depth, color, interlace;
  const chunks = [];
  while (p < b.length) {
    const n = b.readUInt32BE(p); p += 4;
    const type = b.toString('ascii', p, p + 4); p += 4;
    const data = b.subarray(p, p + n); p += n;
    p += 4;
    if (type === 'IHDR') { width=data.readUInt32BE(0); height=data.readUInt32BE(4); depth=data[8]; color=data[9]; interlace=data[12]; }
    if (type === 'IDAT') chunks.push(data);
    if (type === 'IEND') break;
  }
  if (depth !== 8 || ![2,6].includes(color) || interlace !== 0) throw new Error(`Unsupported PNG format: ${file}`);
  const channels = color === 6 ? 4 : 3, stride = width * channels;
  const raw = zlib.inflateSync(Buffer.concat(chunks));
  const pixels = Buffer.alloc(height * stride);
  let ri = 0;
  for (let y=0; y<height; y++) {
    const filter = raw[ri++], row = y * stride;
    for (let x=0; x<stride; x++) {
      const v=raw[ri++], a=x>=channels?pixels[row+x-channels]:0, up=y?pixels[row-stride+x]:0, ul=(y&&x>=channels)?pixels[row-stride+x-channels]:0;
      let q;
      if(filter===0)q=v;
      else if(filter===1)q=(v+a)&255;
      else if(filter===2)q=(v+up)&255;
      else if(filter===3)q=(v+Math.floor((a+up)/2))&255;
      else if(filter===4){const z=a+up-ul,pa=Math.abs(z-a),pb=Math.abs(z-up),pc=Math.abs(z-ul);q=(v+(pa<=pb&&pa<=pc?a:pb<=pc?up:ul))&255;}
      else throw new Error(`Unknown PNG filter ${filter}`);
      pixels[row+x]=q;
    }
  }
  if (channels===3) {
    const rgba=Buffer.alloc(width*height*4);
    for(let i=0,j=0;i<pixels.length;i+=3,j+=4){rgba[j]=pixels[i];rgba[j+1]=pixels[i+1];rgba[j+2]=pixels[i+2];rgba[j+3]=255;}
    return {width,height,data:rgba};
  }
  return {width,height,data:pixels};
}
function pngChunk(type,data){const t=Buffer.from(type), len=Buffer.alloc(4);len.writeUInt32BE(data.length);const c=Buffer.alloc(4);c.writeUInt32BE(crc32(Buffer.concat([t,data])));return Buffer.concat([len,t,data,c]);}
function writePng(file,img){
  const {width,height,data}=img, ih=Buffer.alloc(13);ih.writeUInt32BE(width,0);ih.writeUInt32BE(height,4);ih[8]=8;ih[9]=6;
  const raw=Buffer.alloc(height*(width*4+1));
  for(let y=0;y<height;y++){const at=y*(width*4+1);raw[at]=0;data.copy(raw,at+1,y*width*4,(y+1)*width*4);}
  fs.writeFileSync(file,Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),pngChunk('IHDR',ih),pngChunk('IDAT',zlib.deflateSync(raw)),pngChunk('IEND',Buffer.alloc(0))]));
}
function blank(w,h){return {width:w,height:h,data:Buffer.alloc(w*h*4)};}
function crop(img,x,y,w,h){const out=blank(w,h);for(let j=0;j<h;j++){const sy=y+j;if(sy<0||sy>=img.height)continue;const sx=Math.max(0,x),ex=Math.min(img.width,x+w);if(ex<=sx)continue;img.data.copy(out.data,(j*w+(sx-x))*4,(sy*img.width+sx)*4,(sy*img.width+ex)*4);}return out;}
function alphaTrim(img){let x0=img.width,y0=img.height,x1=-1,y1=-1;for(let y=0;y<img.height;y++)for(let x=0;x<img.width;x++)if(img.data[(y*img.width+x)*4+3]){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}if(x1<0)throw new Error('Actor source has no visible alpha.');return {image:crop(img,x0,y0,x1-x0+1,y1-y0+1),crop:[x0,y0,x1-x0+1,y1-y0+1]};}
function resizeNearest(img,w,h){const out=blank(w,h);for(let y=0;y<h;y++){const sy=Math.floor(y*img.height/h);for(let x=0;x<w;x++){const sx=Math.floor(x*img.width/w);img.data.copy(out.data,(y*w+x)*4,(sy*img.width+sx)*4,(sy*img.width+sx+1)*4);}}return out;}
function over(dst,src,x=0,y=0){for(let sy=0;sy<src.height;sy++)for(let sx=0;sx<src.width;sx++){const dx=sx+x,dy=sy+y;if(dx<0||dy<0||dx>=dst.width||dy>=dst.height)continue;const si=(sy*src.width+sx)*4,di=(dy*dst.width+dx)*4,sa=src.data[si+3]/255;if(!sa)continue;const da=dst.data[di+3]/255,oa=sa+da*(1-sa);for(let c=0;c<3;c++)dst.data[di+c]=Math.round((src.data[si+c]*sa+dst.data[di+c]*da*(1-sa))/oa);dst.data[di+3]=Math.round(oa*255);}}
function hash(file){return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');}
function save(name,img){const file=path.join(root,name);writePng(file,img);return file;}

fs.mkdirSync(root,{recursive:true});
const bed=readPng(bedPath), actorMaster=readPng(actorPath), bubbleSource=readPng(bubblePath);
const trimmedActor=alphaTrim(actorMaster), actorSource=trimmedActor.image;
const actor=resizeNearest(actorSource,80,140), actorAt={x:67,y:64};
const backing=bed;
const sheet=crop(bed,12,122,190,176);
const footboard=crop(bed,0,278,bed.width,bed.height-278);
const bubbleCrop=crop(bubbleSource,762,930,337,257), bubbleArt=resizeNearest(bubbleCrop,64,48), bubbleAt={x:75,y:17};
const actorLayer=blank(bed.width,bed.height);over(actorLayer,actor,actorAt.x,actorAt.y);
const sheetLayer=blank(bed.width,bed.height);over(sheetLayer,sheet,12,122);
const footboardLayer=blank(bed.width,bed.height);over(footboardLayer,footboard,0,278);
const bubbleLayer=blank(bed.width,bed.height);over(bubbleLayer,bubbleArt,bubbleAt.x,bubbleAt.y);
save('rear-backing.png',backing);save('actor-proxy.png',actorLayer);save('sheet-overlay.png',sheetLayer);save('foreground-footboard.png',footboardLayer);save('dialogue-slot.png',bubbleLayer);
const actorStage=blank(bed.width,bed.height);over(actorStage,backing);over(actorStage,actorLayer);save('stage-02-actor.png',actorStage);
const sheetStage=blank(bed.width,bed.height);over(sheetStage,backing);over(sheetStage,actorLayer);over(sheetStage,sheetLayer);save('stage-03-sheets.png',sheetStage);
const preBubble=blank(bed.width,bed.height);over(preBubble,backing);over(preBubble,actorLayer);over(preBubble,sheetLayer);over(preBubble,footboardLayer);
const final=blank(bed.width,bed.height);over(final,preBubble);over(final,bubbleLayer);save('assembled.png',final);
save('stage-01-backing.png',backing);save('stage-04-footboard.png',preBubble);
const promptPath=path.join(root,'sources','books-jug-bubble-prompt.txt');
const manifest={schema:1,id:'bed-layers-v1',title:'Sickbed layer and occlusion staging',canvas:[bed.width,bed.height],workflow:[{step:'components',status:'selected-existing-components'},{step:'isolate',status:'mechanical-alpha-trim-crop-and-nearest-scale-only'},{step:'split-layers',status:'visible-crop-decomposition'},{step:'interpolate-hidden',status:'none; no hidden mattress or frame pixels reconstructed'}],source:{file:'sources/white-sickbed.png',sha256:hash(bedPath),originalFile:'AssetWork/InteriorRefinementV5/components/white-sickbed.png',visibility:'existing cropped component artwork; visible source pixels',note:'Existing bed pixels retained as rear backing. It is not a clean reconstruction of hidden mattress/frame pixels.'},actorProxy:{file:'sources/firion-down-02.png',sha256:hash(actorPath),originalFile:'C:/repos/AI-Art-FF2/Assets/Art/Production/RemasterExpansion/field/firion/down-02.png',label:'Higher-resolution Firion down sprite; standing pose is only an occlusion proxy, not an authentic lying Scott pose.',sourceSize:[actorMaster.width,actorMaster.height],alphaCrop:trimmedActor.crop,trimmedSize:[actorSource.width,actorSource.height],renderSize:[actor.width,actor.height],at:[actorAt.x,actorAt.y]},dialogueBubble:{master:'sources/books-jug-bubble-master.png',masterSha256:hash(bubblePath),prompt:'sources/books-jug-bubble-prompt.txt',promptSha256:hash(promptPath),sourceCrop:[762,930,337,257],normalizedSize:[bubbleArt.width,bubbleArt.height],at:[bubbleAt.x,bubbleAt.y],note:'Generated standalone bubble cropped from supplied master; exact prompt retained alongside the source.'},layers:[{id:'rear-backing',file:'rear-backing.png',at:[0,0],z:0,canvasSize:[bed.width,bed.height],sourceVisibility:'existing visible bed crop; concealed pixels in this full component are not treated as cleanly reconstructed'},{id:'actor-proxy',file:'actor-proxy.png',at:[0,0],z:1,canvasSize:[bed.width,bed.height],spriteAt:[actorAt.x,actorAt.y],spriteSize:[actor.width,actor.height],sourceVisibility:'existing Firion sprite'},{id:'sheets',file:'sheet-overlay.png',at:[0,0],z:2,canvasSize:[bed.width,bed.height],sourceCrop:[12,122,190,176],placement:[12,122],sourceVisibility:'visible bed crop; placed at source coordinate without hidden-pixel reconstruction'},{id:'foreground-footboard',file:'foreground-footboard.png',at:[0,0],z:3,canvasSize:[bed.width,bed.height],sourceCrop:[0,278,bed.width,bed.height-278],sourceVisibility:'visible crop from existing bed component'},{id:'dialogue-bubble',file:'dialogue-slot.png',at:[0,0],z:4,canvasSize:[bed.width,bed.height],spriteAt:[bubbleAt.x,bubbleAt.y],spriteSize:[bubbleArt.width,bubbleArt.height],sourceVisibility:'cropped standalone generated artwork'}],stages:['stage-01-backing.png','stage-02-actor.png','stage-03-sheets.png','stage-04-footboard.png'],output:'assembled.png',caveats:['The sheet and footboard layers are source crops; backing still includes the existing bed pixels behind them.','No hidden mattress/frame reconstruction is present.','Firion is a standing proxy for confirming occlusion only.']};
fs.writeFileSync(path.join(root,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(`Built ${bed.width}x${bed.height} bed layers in ${root}`);
