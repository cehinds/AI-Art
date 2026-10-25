'use strict';
const {sharp,assert}=require('./common.cjs');
exports.bodyHeight=(data,w,h,b,anchor)=>{
 const half=Math.max(4,b.height*.18),left=Math.max(b.left,Math.floor(anchor.x-half)),right=Math.min(b.left+b.width,Math.ceil(anchor.x+half)),minimum=Math.max(3,Math.floor((right-left)*.25));let top=b.top;
 for(let y=b.top;y<anchor.y-3;y++){let stable=true;for(let row=y;row<y+3;row++){let ink=0;for(let x=left;x<right;x++)if(data[(row*w+x)*4+3]>=128)ink++;if(ink<minimum){stable=false;break}}if(stable){top=y;break}}
 return {height:anchor.y-top,top,band:{left,right},method:'first-pose-central-body-projection-three-row-run'};
};
exports.bodyAnchor=(data,w,h,b,pivot)=>{
 if(pivot.y===.5)return {x:b.left+b.width/2,y:b.top+b.height/2,method:'source-visible-center'};
 // Grounded clips: stabilize lower-body mass rather than the weapon-inclusive pose bounding-box center.
 const y0=b.top+Math.floor(b.height*.58),y1=b.top+Math.max(1,Math.floor(b.height*.94));let xsum=0,count=0;
 for(let y=y0;y<y1;y++)for(let x=b.left;x<b.left+b.width;x++)if(data[(y*w+x)*4+3]>=128){xsum+=x+.5;count++}
 assert(count>0,'Cannot infer lower-body registration anchor');return {x:xsum/count,y:b.top+b.height,method:'lower-body-alpha-centroid-and-ground-baseline'};
};
exports.sprite=async(data,info,b,anchor,scale,target,pivot,padding)=>{
 const [w,h]=target,destination={x:w/2,y:pivot.y===0?h-padding:h/2},bw=Math.max(1,Math.round(b.width*scale)),bh=Math.max(1,Math.round(b.height*scale)),left=Math.round(destination.x+(b.left-anchor.x)*scale),top=Math.round(destination.y+(b.top-anchor.y)*scale);
 assert(left>=0&&top>=0&&left+bw<=w&&top+bh<=h,`Registered pose escapes native canvas: ${left},${top} ${bw}x${bh} in ${w}x${h}`);
 const fg=await sharp(data,{raw:info}).extract({left:b.left,top:b.top,width:b.width,height:b.height}).resize(bw,bh,{kernel:'nearest'}).png().toBuffer(),png=await sharp({create:{width:w,height:h,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite([{input:fg,left,top}]).png().toBuffer();
 return {png,registration:{sourceAnchor:anchor,destinationAnchor:destination,scale,placement:{left,top,width:bw,height:bh},offsetFromVisibleBounds:{x:left,y:top}}};
};
