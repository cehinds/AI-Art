'use strict';
// Mechanical normalization of the generated study; no painted or synthesized sprite pixels.
const {fs,path,sharp,root,hash,bbox}=require('../campaign-art/common.cjs');
async function main(){
  const source='ArtSource/ResolutionStudy/v1/master.png';
  const out=path.join(root,'Review/resolution-study/v1');
  const bytes=await fs.readFile(path.join(root,source));
  const raw=await sharp(bytes).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  const {width,height}=raw.info;
  for(let p=0;p<raw.data.length;p+=4){if(raw.data[p+3]<128)raw.data.fill(0,p,p+4);else raw.data[p+3]=255;}
  const ink=Array(width).fill(0);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++)if(raw.data[(y*width+x)*4+3])ink[x]++;
  const cuts=[0];
  for(let n=1;n<3;n++){
    const nominal=width*n/3,radius=Math.floor(width/12);
    const candidates=[];
    for(let x=Math.floor(nominal-radius);x<nominal+radius;x++)if(!ink[x]&&!ink[x-1]&&!ink[x+1])candidates.push(x);
    if(!candidates.length)throw Error('No clean transparent separator for slot '+n);
    candidates.sort((a,b)=>Math.abs(a-nominal)-Math.abs(b-nominal));cuts.push(candidates[0]);
  }
  cuts.push(width);
  await fs.mkdir(out,{recursive:true});
  const names=['firion','maria','goblin'],assets=[],composites=[];
  for(let i=0;i<3;i++){
    const rect={left:cuts[i],top:0,width:cuts[i+1]-cuts[i],height};
    const cell=await sharp(raw.data,{raw:raw.info}).extract(rect).raw().toBuffer({resolveWithObject:true});
    const b=bbox(cell.data,cell.info.width,cell.info.height);
    if(b.left===0||b.left+b.width===rect.width)throw Error('Study touches crop boundary '+names[i]);
    for(const [row,size]of[64,128].entries()){
      const pad=size/32,scale=Math.min((size-pad*2)/b.width,(size-pad*2)/b.height);
      const w=Math.round(b.width*scale),h=Math.round(b.height*scale);
      const fg=await sharp(cell.data,{raw:cell.info}).extract({left:b.left,top:b.top,width:b.width,height:b.height}).resize(w,h,{kernel:'nearest'}).png().toBuffer();
      const png=await sharp({create:{width:size,height:size,channels:4,background:'#00000000'}}).composite([{input:fg,left:Math.floor((size-w)/2),top:size-pad-h}]).png().toBuffer();
      const file=names[i]+'-'+size+'.png';await fs.writeFile(path.join(out,file),png);
      const check=await sharp(png).raw().toBuffer({resolveWithObject:true});
      if(check.info.width!==size||check.info.height!==size)throw Error('Invalid native size');
      for(let p=3;p<check.data.length;p+=4)if(check.data[p]!==0&&check.data[p]!==255)throw Error('Nonbinary alpha');
      assets.push({name:names[i],size,path:'Review/resolution-study/v1/'+file,sha256:hash(png),sourceRect:rect,alphaBounds:b,scale,padding:pad,pivot:{x:.5,y:0}});
      composites.push({input:await sharp(png).resize(256,256,{kernel:'nearest'}).png().toBuffer(),left:124+i*300,top:140+row*340});
    }
  }
  const svg='<svg width="1060" height="830" xmlns="http://www.w3.org/2000/svg"><style>text{font-family:Segoe UI,Arial;fill:#eee9d9}.small{font-size:17px;fill:#b5c2bd}</style><rect width="1060" height="830" fill="#17272c"/><text x="28" y="42" font-size="28" font-weight="bold">FFII · Higher-resolution sprite study</text><text x="28" y="72" class="small">Same new source art at two native sizes · both displayed at 256 × 256</text><text x="225" y="120" font-size="21">Firion</text><text x="525" y="120" font-size="21">Maria</text><text x="825" y="120" font-size="21">Goblin</text><text x="22" y="242" font-size="22">64 × 64</text><text x="22" y="268" class="small">4× preview</text><text x="22" y="582" font-size="22">128 × 128</text><text x="22" y="608" class="small">2× preview</text><path d="M28 435H1032" stroke="#405156"/><text x="28" y="787" class="small">Crisp nearest-neighbor exports from a newly generated master. Review candidates.</text><text x="28" y="813" class="small">Frame resolution is independent of the character’s world size and camera framing.</text></svg>';
  await sharp(Buffer.from(svg)).composite(composites).png().toFile(path.join(out,'comparison.png'));
  await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify({source,sourceSha256:hash(bytes),sourceWidth:width,sourceHeight:height,alphaThreshold:128,selectedColumnCuts:cuts,method:'Generated master cropped once per subject; binary alpha and nearest-neighbor normalized separately to 64 and 128. No enlargement of old production PNGs.',assets},null,2)+'\n');
  console.log('PASS: 6 native transparent PNGs; 64/128 dimensions and binary alpha verified. Existing production unchanged.');
}
main().catch(e=>{console.error(e);process.exitCode=1});
