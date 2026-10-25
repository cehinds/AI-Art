'use strict';
const {fs,path,sharp,review,json}=require('./common.cjs');
const configurations=[
 {owner:'snow-ice',prefix:'snow-ice',surround:'snow-field-01',center:'snow-ice-center',label:'Snow / ice transition test'},
 {owner:'desert-ruins',prefix:'ruin',surround:'sand-floor-01',center:'ruin-center',label:'Sandstone ruin transition test'},
 {owner:'ship-dock',prefix:'dock',surround:'water-01',center:'dock-center',label:'Dock / water transition test'},
 {owner:'dungeon-transitions',prefix:'wall',surround:'floor-flagstone-01',center:'floor-flagstone-01',label:'Dungeon wall / floor test',unusedCenterVariant:'wall-door-open'}
];
exports.write=async(m,planned)=>{
 const directions=['nw','n','ne','w','center','e','sw','s','se'],results=[];
 for(const c of configurations){const items=planned.filter(p=>p.asset.kind==='tile'&&p.asset.group==='tiles'&&p.asset.owner===c.owner);if(!items.length)continue;const names=new Map(items.map(p=>[p.asset.name,p])),ordered=directions.map(d=>d==='center'?c.center:c.prefix+'-'+d),required=[c.surround,...ordered],missing=[...new Set(required.filter(name=>!names.has(name)))];if(missing.length){results.push({...c,state:'NONCONFORMING',missing,scope:'No adjacency proof forced from missing or renamed directional pieces'});continue}
  const parts=[],constituents=[];for(let y=0;y<5;y++)for(let x=0;x<5;x++){const inside=x>=1&&x<=3&&y>=1&&y<=3,name=inside?ordered[(y-1)*3+x-1]:c.surround,p=names.get(name);parts.push({input:p.native,left:x*32,top:y*32});constituents.push({x,y,id:p.asset.id})}
  const native=await sharp({create:{width:160,height:160,channels:4,background:'#17262a'}}).composite(parts).png().toBuffer(),key=c.owner+'-adjacency-test';await fs.writeFile(path.join(review,key+'-native.png'),native);await sharp(native).resize(640,640,{kernel:'nearest'}).png().toFile(path.join(review,key+'-4x.png'));results.push({...c,state:'ASSEMBLED_CANDIDATE',native:key+'-native.png',proof:key+'-4x.png',constituents,seamlessness:'NOT_CLAIMED; inspect actual joins',scope:'Named actual exported transition pieces with specified material surround; no tile painting or edge correction',centerNote:c.unusedCenterVariant?'Floor used at room center. The freestanding open-arch tile remains exported separately and is not presented as a valid floating room-center doorway.':null});
 }
 await fs.writeFile(path.join(review,'environment-extras-proofs.json'),json(results));
 const rendered=results.filter(p=>p.state==='ASSEMBLED_CANDIDATE');if(!rendered.length)return;const cols=2,cw=512,ch=528,header=48,rows=Math.ceil(rendered.length/cols),w=cols*cw,h=header+rows*ch,layers=[],labels=[];for(let i=0;i<rendered.length;i++){const x=i%cols*cw,y=header+Math.floor(i/cols)*ch;layers.push({input:await sharp(await fs.readFile(path.join(review,rendered[i].native))).resize(480,480,{kernel:'nearest'}).png().toBuffer(),left:x+16,top:y+32});labels.push(`<text x="${x+16}" y="${y+22}" font-size="16">${rendered[i].label}</text>`)}layers.push({input:Buffer.from(`<svg width="${w}" height="${h}"><g font-family="sans-serif" fill="#f1e8d6"><text x="16" y="27" font-size="18">TEST LAYOUTS · actual32px PNGs · visible joins remain review findings</text>${labels.join('')}</g></svg>`),left:0,top:0});await sharp({create:{width:w,height:h,channels:4,background:'#17262a'}}).composite(layers).png().toFile(path.join(review,'environment-extras-overview.png'));
};
